# Changelog

## Render Deployment Fixes

[2026-06-10] Fix Render deploy health check race condition
└── File: Dockerfile.render, render.yaml, build/gateway.js
    ├── Choice: Gateway handles /health directly before forwarding to inspector
    └── Changes:
        ├── health-check -> gateway returns 200 immediately on /health without
        │                   waiting for inspector subprocess to boot
        └── render.yaml -> added healthCheckPath: /health so Render uses the
                           always-ready endpoint instead of defaulting to GET /

[2026-06-10] Add missing find_large_functions to MCP contract
└── File: contracts/mcp/tools.json, contracts/mcp/changelog.md
    ├── Choice: Contract-first rule — tool was implemented but never defined in contract
    └── Changes:
        ├── tools.json -> added find_large_functions tool definition
        └── changelog.md -> updated to include find_large_functions

[2026-06-10] Fix gateway proxy routing — /stdio, /mcp, /message endpoints
└── File: build/gateway.js
    ├── Choice: Read inspector v0.15.0 source to confirm actual endpoint paths used
    └── Changes:
        ├── /stdio -> added to proxy routing (browser→proxy for stdio transport,
        │            was going to UI server port 6274 — MCP server never reached)
        ├── /mcp   -> added to proxy routing (streamable-http transport path)
        ├── /message (singular) -> fixed from /messages (plural); inspector POSTs
        │            MCP JSON-RPC to /message?sessionId=<id>, wrong routing caused
        │            "proxy session token" connection error
        └── /health -> changed response from plain "OK" to JSON {"status":"ok"};
                       inspector's checkProxyHealth() calls response.json() and
                       checks .status === "ok" — plain text caused a parse error
                       and every connect attempt failed silently

[2026-06-10] Fix auto-connect on browser open
└── File: Dockerfile.render, build/gateway.js
    ├── Choice: Inject JS into inspector index.html; no native auto-connect in v0.15.0
    └── Changes:
        ├── gateway.js -> redirect GET / to /?MCP_PROXY_FULL_ADDRESS=<public-host>
        │                 (MCP_PROXY_FULL_ADDRESS is a real config key in configUtils.ts;
        │                  ?url= and ?autoConnect=true do not exist in v0.15.0)
        ├── Dockerfile.render -> inject <script> into inspector index.html that polls
        │                        every 500ms for a button with text "Connect" (confirmed
        │                        in Sidebar.tsx v0.15.0 line 745) and clicks it
        └── Dockerfile.render -> fixed glob path from build/client/index.html to
                                 **/index.html (recursive); actual path is
                                 client/dist/index.html — verified against local install
