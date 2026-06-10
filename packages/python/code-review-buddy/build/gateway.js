const http = require('http');
const { spawn } = require('child_process');

// Ensure the environment runs without requiring authentication tokens in the URL
process.env.DANGEROUSLY_OMIT_AUTH = 'true';
process.env.PYTHONUNBUFFERED = '1';
process.env.PYTHONPATH = '/app';

console.log('Starting MCP server and Inspector processes...');

// 1. Spawn the MCP Inspector running locally inside the container
const inspector = spawn('npx', [
  '@modelcontextprotocol/inspector',
  'python3', '-m', 'src.api.mcp.server'
], { 
  stdio: 'inherit',
  shell: true
});

// 2. Start a single-port gateway on Port 10000 (exposing to Render)
const server = http.createServer((req, res) => {
  // Route /config, /health, /sse, /messages to the Proxy Server (6277).
  // Route static assets and UI routes to the Inspector Web Server (6274).
  const isProxy = req.url.startsWith('/config') || req.url.startsWith('/health') || req.url.startsWith('/sse') || req.url.startsWith('/see') || req.url.startsWith('/messages');
  const targetPort = isProxy ? 6277 : 6274;

  const connector = http.request({
    host: '127.0.0.1',
    port: targetPort,
    path: req.url,
    method: req.method,
    headers: req.headers
  }, (targetRes) => {
    const headers = { ...targetRes.headers };
    // Prevent Cloudflare/Render Nginx reverse proxies from buffering SSE streams
    if (req.url.includes('/sse') || req.url.includes('/see')) {
      headers['x-accel-buffering'] = 'no';
      headers['cache-control'] = 'no-cache';
      headers['connection'] = 'keep-alive';
    }
    res.writeHead(targetRes.statusCode, headers);
    targetRes.pipe(res);
  });

  connector.on('error', (err) => {
    res.writeHead(502);
    res.end(`Gateway connection to local port ${targetPort} failed: ${err.message}`);
  });

  req.pipe(connector);
});

// Listen on Render's required port (10000)
server.listen(10000, '0.0.0.0', () => {
  console.log('Single-Port Gateway is successfully running on port 10000!');
});

// Handle graceful termination
process.on('SIGTERM', () => {
  inspector.kill();
  server.close();
  process.exit(0);
});
