# Gateway Rules

A gateway is a single-port HTTP reverse proxy that routes browser/client traffic to internal services running on local ports inside the same container. It is the only outward-facing process.

---

## 1. Core Structural Rules

- **One gateway per deployment unit.** A package that exposes multiple internal services (e.g. inspector UI + inspector proxy) must consolidate them behind a single gateway port. No internal port must ever be exposed directly to the outside.
- **Gateway owns the entry port.** The container EXPOSE and the platform's configured port (e.g. Render port 10000) must point to the gateway only.
- **Gateway is stateless.** It must not hold session state, buffer full request/response bodies, or modify payloads beyond header rewrites. All state lives in the upstream services.
- **Gateway must start immediately.** It must bind and respond to the health check endpoint before any upstream service is ready. Never block startup waiting for a subprocess.

---

## 2. Health Check Rule

- The gateway must handle `GET /health` itself — do not forward it upstream.
- Response must be `200 application/json` with body `{"status":"ok"}`.
- This applies even when all upstream services are still booting.
- The platform health check path must be set to `/health` (e.g. `healthCheckPath: /health` in render.yaml).

**Why:** Platform deploy systems (Render, Railway, Fly) fail the deploy if the first health check times out. Upstream services can take several seconds to boot.

---

## 3. Routing Rules

- Define routing by URL prefix. Group prefixes into two buckets: `isProxy` (internal proxy service) and everything else (UI / static assets).
- **Document every prefix** with a comment explaining which transport or protocol uses it.
- When adding a new tool or transport, update the routing table first — do not rely on catch-all fallback behavior.
- Known proxy prefixes for MCP Inspector stdio/SSE/HTTP transports:

| Prefix | Transport | Notes |
|---|---|---|
| `/stdio` | stdio | Main browser→proxy connection path |
| `/sse` | SSE | SSE transport connection |
| `/mcp` | Streamable-HTTP | HTTP transport |
| `/message` | all | JSON-RPC POST channel (singular, not /messages) |
| `/config` | all | Inspector UI fetches server defaults on load |

- Use `startsWith` checks, not exact matches, for prefix routing. A prefix like `/message` also correctly covers any sub-paths.

---

## 4. Header Rewrite Rules

- **Always rewrite `Origin` and `Host` headers** when forwarding to an internal service that enforces DNS-rebinding protection (e.g. MCP proxy).
  - Set `Origin` to `http://localhost:<target-port>`.
  - Set `Host` to `localhost:<target-port>`.
- Do not strip `Authorization`, `Content-Type`, or other semantic headers.
- Spread the original headers object first, then apply rewrites — never mutate `req.headers` directly.

```js
// Correct pattern
const forwardHeaders = { ...req.headers };
if (targetPort === PROXY_PORT) {
  forwardHeaders['origin'] = `http://localhost:${PROXY_PORT}`;
  forwardHeaders['host']   = `localhost:${PROXY_PORT}`;
}
```

**Why:** Internal services like the MCP proxy block requests with a public domain as Origin as a DNS-rebinding guard. Since the gateway is the sole ingress point this rewrite is safe and necessary.

---

## 5. Streaming Response Rules

- For streaming endpoints (`/sse`, `/see`, `/stdio`) set the following response headers before piping:
  - `x-accel-buffering: no` — disables Nginx/Cloudflare buffering
  - `cache-control: no-cache`
  - `connection: keep-alive`
- Use `targetRes.pipe(res)` — never buffer streaming responses into memory.
- Do not set `Content-Length` on streaming responses.

---

## 6. Root Redirect Rule

- `GET /` with no query string must redirect (302) to the URL with the correct proxy address query param so the inspector UI knows the public host.
- Use `MCP_PROXY_FULL_ADDRESS` as the query key — this is the real config key read by `configUtils.ts` in MCP Inspector v0.15.0.
- Derive proto from `x-forwarded-proto` header (set by Render/Cloudflare), fallback to `https`.
- Never hardcode the hostname; always read it from `req.headers.host`.

```js
// Correct pattern
if (req.url === '/') {
  const proto = req.headers['x-forwarded-proto'] || 'https';
  const host  = req.headers.host;
  res.writeHead(302, {
    Location: `/?MCP_PROXY_FULL_ADDRESS=${encodeURIComponent(`${proto}://${host}`)}`
  });
  res.end();
  return;
}
```

---

## 7. Error Handling Rules

- On upstream connection error (ECONNREFUSED, ETIMEDOUT), respond `502` with a plain-text message that includes the target port and error reason.
- Never swallow errors silently — always log them to stderr.
- The gateway itself must never crash on upstream failure; upstream processes restart independently.

---

## 8. Logging Rules

- Log every forwarded request in the format:
  ```
  [Gateway] --> METHOD /path (Routing to local port NNNN)
  [Gateway] <-- STATUS for /path from local port NNNN
  ```
- Log every upstream error with `[Gateway] ERROR: ...`.
- Do not log `/health` requests — they are high-frequency and add noise.

---

## 9. Process Lifecycle Rules

- The gateway must handle `SIGTERM`: kill all spawned child processes and close the HTTP server before exiting.
- Child processes (e.g. MCP server, inspector) must be spawned with `PYTHONUNBUFFERED=1` to prevent subprocess output buffering that causes apparent hangs.
- Set `DANGEROUSLY_OMIT_AUTH=true` for MCP Inspector when the service is locked behind platform-level auth (e.g. Render private service, VPN) and token-based auth is not required.

---

## 10. Environment Variable Defaults

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `PYTHONUNBUFFERED` | yes | `1` | Prevent Python subprocess output buffering |
| `PYTHONPATH` | yes | `/app` | Python module resolution root |
| `DANGEROUSLY_OMIT_AUTH` | yes | `true` | Skip inspector auth token requirement |
| `REPO_ROOT` | yes | `/app` | Root path passed to MCP server tools |

---

## 11. Troubleshooting: Real Issues Encountered on Render

Every entry below is a real bug that occurred during deployment of the MCP Inspector + FastMCP stdio server on Render (free tier). Each section explains what went wrong, why it happened internally, and what the exact fix was.

---

### Issue 1 — Render deploy failed: health check 502 before inspector was ready

**Symptom:**
Render marked the deploy as failed immediately after the container started. Logs showed the gateway running but upstream returning ECONNREFUSED.

**Why it happened internally:**
Render sends `GET /` (or the configured health check path) within ~2 seconds of the container starting. The gateway was forwarding `/` to the inspector UI at port 6274. The inspector subprocess (`npx @modelcontextprotocol/inspector ...`) takes ~5 seconds to install packages and bind. During that window every health check request hit ECONNREFUSED and returned a 502 to Render, causing the deploy to fail.

**Fix:**
1. Added a dedicated `GET /health` handler inside the gateway that returns `200 {"status":"ok"}` immediately without touching any upstream service.
2. Added `healthCheckPath: /health` to `render.yaml` so Render probes this endpoint instead of `/`.

```js
if (req.url === '/health') {
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ status: 'ok' }));
  return;
}
```

**Key insight:** The gateway starts in milliseconds (pure Node.js `http.createServer`). The upstream inspector needs 5+ seconds. These must never be coupled. The gateway owns the health check; upstream readiness is irrelevant to it.

---

### Issue 2 — Inspector silently failed to connect: `/health` returned plain text

**Symptom:**
The inspector UI loaded but the connection spinner never resolved. No visible error. The "Connect" button did nothing.

**Why it happened internally:**
The MCP Inspector proxy has an internal function `checkProxyHealth()` in `client/src/lib/hooks/useConnection.ts`. It calls `fetch('/health').then(r => r.json())` and checks that `result.status === "ok"`. The gateway was returning `200 OK` as plain text. `response.json()` on plain text throws a JSON parse error. The error was caught silently inside the hook and treated as "proxy not ready", so the connection was never attempted — no error shown to the user.

**Fix:**
Changed `/health` response to `application/json` with body `{"status":"ok"}`.

```js
res.writeHead(200, { 'Content-Type': 'application/json' });
res.end(JSON.stringify({ status: 'ok' }));
```

**Key insight:** `/health` has two consumers with different contracts — Render needs any `200`, but the inspector's own internal health check requires valid JSON with `status: "ok"`. Always satisfy the stricter contract.

---

### Issue 3 — MCP server never reached: `/stdio` routed to wrong port

**Symptom:**
Browser showed "Connection Error" immediately after clicking Connect. Network tab showed `/stdio?command=...` returning HTML (the inspector UI page) instead of an SSE stream.

**Why it happened internally:**
The gateway's `isProxy` check only included `/sse`. When using stdio transport the inspector browser-side code opens an EventSource to `/stdio?command=python3&args=...`. This path was not in the proxy prefix list so the gateway forwarded it to port 6274 (the UI server). The UI server has no `/stdio` route — it returned its catch-all HTML page with a 200. The browser received HTML where it expected an SSE stream and the connection failed.

**Fix:**
Added `/stdio` and `/mcp` to the `isProxy` routing check:

```js
const isProxy = req.url.startsWith('/stdio') || req.url.startsWith('/sse') ||
  req.url.startsWith('/see')  || req.url.startsWith('/mcp') ||
  req.url.startsWith('/config') || req.url.startsWith('/message');
```

**Key insight:** Read the actual inspector source to find every path the browser uses. Do not guess from the transport name. Stdio transport uses `/stdio`, not `/sse`.

---

### Issue 4 — JSON-RPC messages lost: `/message` routed to wrong port

**Symptom:**
After the SSE connection opened, no tools appeared. The browser network tab showed `POST /message?sessionId=...` returning HTML instead of JSON.

**Why it happened internally:**
After the SSE stream opens the inspector browser sends all MCP JSON-RPC requests (initialize, list tools, call tool) as `POST /message?sessionId=<id>`. The gateway had `startsWith('/messages')` (plural). The actual path `/message` (singular) did not match. It fell through to port 6274 (the UI), which returned its HTML catch-all. The proxy never received any JSON-RPC messages so no session was established — hence the "Did you add the proxy session token?" error.

**Fix:**
Changed `/messages` to `/message` (singular):

```js
req.url.startsWith('/message')  // covers /message and any /message/* sub-path
```

**Key insight:** Verify endpoint names from source, not documentation or assumption. The inspector uses `/message` (singular) as the JSON-RPC POST channel. `startsWith('/message')` also future-proofs against any `/message/...` variants.

---

### Issue 5 — DNS-rebinding guard blocked all proxy requests: 403 "Forbidden - invalid origin"

**Symptom:**
Render logs showed `[Gateway] <-- 403 for /config from local port 6277` and `Invalid origin: https://mcp-code-review-buddy.onrender.com`. Every proxy request was blocked.

**Why it happened internally:**
The MCP proxy (`server/build/index.js`) has Express middleware that checks every request's `Origin` header against an allowed list. The default allowed list is:
```
["http://localhost:6274", "http://127.0.0.1:6274"]
```
These are the inspector UI's addresses — the only legitimate origin in a normal local setup. When a browser on the public internet hits the Render URL its requests carry `Origin: https://mcp-code-review-buddy.onrender.com`. The proxy does not recognise this and returns 403.

**Fix:**
Before forwarding to port 6277 the gateway rewrites the `Origin` and `Host` headers:

```js
const forwardHeaders = { ...req.headers };
if (targetPort === 6277) {
  forwardHeaders['origin'] = 'http://localhost:6274';
  forwardHeaders['host']   = 'localhost:6277';
}
```

**Key insight:** The gateway is the only ingress. Requests reaching port 6277 have already passed through public-facing auth (Render's network boundary + `DANGEROUSLY_OMIT_AUTH`). Rewriting Origin to the expected localhost value is safe here. Never mutate `req.headers` directly — always spread into a new object first.

---

### Issue 6 — Origin rewrite used wrong port: 6277 instead of 6274

**Symptom:**
After adding the Origin rewrite the logs still showed `Invalid origin: http://localhost:6277`.

**Why it happened internally:**
The proxy's allowed list contains `http://localhost:6274` (the UI port), not `http://localhost:6277` (the proxy's own port). The rewrite was set to the proxy's own port under the assumption that "the proxy should accept its own address". But the guard is designed to verify that requests come from the inspector UI, not from the proxy itself. The relevant source:

```js
// server/build/index.js:75-80
const clientPort = process.env.CLIENT_PORT || "6274";
const defaultOrigins = [
  `http://localhost:${clientPort}`,
  `http://127.0.0.1:${clientPort}`,
];
const allowedOrigins = process.env.ALLOWED_ORIGINS?.split(",") || defaultOrigins;
```

**Fix:**
Changed the rewritten `Origin` from `http://localhost:6277` to `http://localhost:6274`:

```js
forwardHeaders['origin'] = 'http://localhost:6274';  // UI port, not proxy port
```

**Key insight:** Read the source before guessing port numbers. The allowed list is keyed on `CLIENT_PORT` (UI port 6274), not the proxy's own listen port. This can also be overridden at the proxy level with env var `ALLOWED_ORIGINS` if needed.

---

### Issue 7 — Auto-connect used non-existent query params

**Symptom:**
Opening the URL did not trigger a connection. Browser loaded the inspector in a disconnected state waiting for a manual click.

**Why it happened internally:**
The gateway initially redirected `/` to `/?url=<host>&autoConnect=true`. Neither `url` nor `autoConnect` exist as recognised query params in MCP Inspector v0.15.0. The inspector's `configUtils.ts` only reads `MCP_PROXY_FULL_ADDRESS` (and `MCP_PROXY_AUTH_TOKEN`). The unrecognised params were ignored and the proxy address defaulted to `http://localhost:6277`, which is unreachable from the browser.

**Fix (two parts):**

1. Redirect to `?MCP_PROXY_FULL_ADDRESS=<encoded-public-host>` so the inspector uses the correct proxy address:

```js
if (req.url === '/') {
  const proto = req.headers['x-forwarded-proto'] || 'https';
  const host  = req.headers.host;
  res.writeHead(302, {
    Location: `/?MCP_PROXY_FULL_ADDRESS=${encodeURIComponent(`${proto}://${host}`)}`
  });
  res.end();
  return;
}
```

2. Inject a polling script into inspector's `index.html` at build time (Dockerfile.render) that clicks "Connect" automatically:

```html
<script>(function(){
  var t = setInterval(function(){
    var b = document.querySelectorAll("button");
    for(var i=0;i<b.length;i++){
      if(b[i].textContent.trim()==="Connect"){b[i].click();clearInterval(t);return;}
    }
  },500);
  setTimeout(function(){clearInterval(t);},30000);
})();</script>
```

Button text "Connect" was verified in `client/src/components/Sidebar.tsx` line 745 of v0.15.0.

**Key insight:** Always verify query param names against the actual source (`configUtils.ts`) before using them. Inspector config keys are not documented — they must be read from source.

---

### Issue 8 — Dockerfile RUN syntax error: Python heredoc on multiple lines

**Symptom:**
Docker build failed with `unknown instruction: import` or `unknown instruction: content`.

**Why it happened internally:**
A `RUN` command written as:
```dockerfile
RUN python3 -c "
import glob
content = open(...).read()
"
```
causes Docker to parse each newline as a new Dockerfile instruction. After the opening `"` Docker sees `import glob` as the next line and tries to interpret it as a Dockerfile keyword — which fails.

**Fix:**
Rewrite using semicolons and backslash line continuations (all one logical shell line):

```dockerfile
RUN python3 -c "import glob; \
js_file = glob.glob('...', recursive=True)[0]; \
content = open(js_file).read(); \
open(js_file, 'w').write(content.replace(old, new))"
```

**Key insight:** In Dockerfiles `RUN python3 -c "..."` must be a single logical line. Use semicolons to chain Python statements. Use `\` at the end of each shell line to continue. Never use heredoc (`<<EOF`) inside `RUN` for Python one-liners.

---

### Issue 9 — Wrong glob path for `index.html` in Dockerfile patch

**Symptom:**
Docker build succeeded but auto-connect script was not injected. The `assert '</body>' in content` check passed (no assertion error) but the file being patched was not the one served by the inspector.

**Why it happened internally:**
The initial glob used `build/client/index.html` as a hardcoded relative path inside the npm global install. The actual installed structure of `@modelcontextprotocol/inspector@0.15.0` is:

```
/usr/local/lib/node_modules/@modelcontextprotocol/inspector/
└── client/
    └── dist/
        └── index.html          ← actual served file
```

The hardcoded path resolved to nothing (glob returned an empty list) and the `[0]` index raised an IndexError — or matched a different file if the glob was too broad.

**Fix:**
Use a recursive glob that matches any `index.html` under the package directory:

```python
html_file = glob.glob(
  '/usr/local/lib/node_modules/@modelcontextprotocol/inspector/**/index.html',
  recursive=True
)[0]
```

Verified against a local install: `npm install @modelcontextprotocol/inspector@0.15.0` then `find . -name index.html` to confirm the actual path before writing the Dockerfile.

**Key insight:** Never hardcode paths inside npm global packages. Package internal structure can change between minor versions. Always use recursive glob and verify with a local install before writing the Dockerfile patch.
