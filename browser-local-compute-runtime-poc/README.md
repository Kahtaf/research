# Browser-Local MCP Server PoC

A proof of concept for an API and MCP server that runs inside an active browser
tab. The public relay forwards opaque TLS bytes by SNI. TLS, HTTP parsing, MCP
tool execution, npm-package computation, and IndexedDB storage all happen in the
browser.

Live app:

```text
https://browser-local-compute-runtime-poc.vana.workers.dev
```

Source:

```text
https://github.com/Kahtaf/research/tree/main/browser-local-compute-runtime-poc
```

## What Runs Where

Browser tab:

- Static UI hosted by Cloudflare Workers assets.
- Browser Worker runtime for MCP request handling.
- Browser-local TLS server backed by Rustls compiled to WebAssembly.
- Browser-local private key, CSR generation, certificate cache, and IndexedDB
  text/request-count storage.
- API endpoint: `GET /api/process?input=hello`.
- Streamable HTTP MCP endpoint: `POST /mcp`.

Blind relay VM:

- Browser control WebSocket:
  `wss://control.34.16.49.200.sslip.io:8443/browser/<sessionId>`.
- Public TCP ingress on `34.16.49.200:443`.
- SNI-based routing from `<sessionId>.34.16.49.200.sslip.io` to the connected
  browser tab.
- ACME issuer endpoint for browser-generated CSRs.
- Opaque byte forwarding only.

Cloudflare:

- Hosts the static browser app.
- Does not relay API or MCP traffic in the current architecture.

## Architecture

```text
API client / MCP client
        │
        │ HTTPS to https://<session>.34.16.49.200.sslip.io
        ▼
┌──────────────────────────────┐
│ Blind relay VM               │
│ - accepts TCP on :443        │
│ - peeks TLS SNI only         │
│ - forwards opaque TLS bytes  │
└──────────────┬───────────────┘
               │ framed stream bytes over WSS control channel
               ▼
┌──────────────────────────────┐
│ Active browser tab           │
│ - terminates TLS with Rustls │
│ - parses HTTP                │
│ - handles /api/process       │
│ - handles /mcp tools         │
│ - reads/writes IndexedDB     │
└──────────────────────────────┘
```

The relay can observe source IPs, SNI/session ids, timing, and byte counts. It
should not see HTTP paths, MCP methods, tool arguments, textarea content, or
response bodies.

## MCP Interface

Endpoint:

```text
https://<sessionId>.34.16.49.200.sslip.io/mcp
```

Supported JSON-RPC methods:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `tools/call`

Tools:

- `get_text`: read browser-stored text by `offset` and `maxChars`.
- `search_text`: return literal case-insensitive snippets.
- `get_text_stats`: return character, byte, line, and word counts.

`get_text` defaults to `20000` chars and has a hard max of `100000` chars.

Claude Code config for the current live session:

```text
.claude/.mcp.json
```

Replace the URL in that file after opening a new browser session.

## Local Development

Install dependencies:

```bash
npm install
```

Build the browser app:

```bash
npm run build
```

The build compiles the Rustls WASM module, runs TypeScript, and builds the Vite
app.

Run the browser app locally:

```bash
npm run dev
```

Run the relay locally:

```bash
npm run reverse-relay:dev
```

Build the relay:

```bash
npm run reverse-relay:build
```

## Deploy

Static app:

```bash
npm run deploy
```

Relay VM:

```bash
npm run reverse-relay:deploy:gcp-vm
```

Current deployed static app version:

```text
8193bebc-04f6-4949-976d-3360046611dc
```

## Verification

Open the deployed app, wait for `Connected`, then use the displayed session URL.

API:

```bash
curl -sS "https://<sessionId>.34.16.49.200.sslip.io/api/process?input=hello"
```

MCP `tools/list`:

```bash
curl -sS "https://<sessionId>.34.16.49.200.sslip.io/mcp" \
  -H 'content-type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

MCP `get_text_stats`:

```bash
curl -sS "https://<sessionId>.34.16.49.200.sslip.io/mcp" \
  -H 'content-type: application/json' \
  --data '{"jsonrpc":"2.0","id":"stats-1","method":"tools/call","params":{"name":"get_text_stats","arguments":{}}}'
```

Claude Code:

```bash
claude --mcp-config <(echo '{"mcpServers":{"browser-local-demo":{"type":"http","url":"https://<sessionId>.34.16.49.200.sslip.io/mcp"}}}') --permission-mode bypassPermissions "tell me my music preference using the browser-local-demo mcp"
```

## Trusted TLS

The browser creates the TLS private key locally and sends only a CSR to the
relay issuer. The relay completes ACME issuance and returns the certificate
chain. The private key stays in browser storage.

Current PoC suffix:

```text
34.16.49.200.sslip.io
```

Production-style suffix:

```text
*.mcp.example.com -> 34.16.49.200
```

For production domains, use DNS-01 with a narrowly scoped DNS token. For this
`sslip.io` PoC, HTTP-01 works because the hostname resolves directly to the VM.

## Limitations

- The server exists only while the browser tab is open and connected.
- Mobile browsers can pause tabs, Workers, WebSockets, timers, and IndexedDB
  while backgrounded.
- IndexedDB data can be evicted under storage pressure.
- The demo has no auth. Anyone with the session URL can query the tab.
- A malicious static host could serve modified JavaScript. A real system needs
  an app integrity story.
- The relay is blind to HTTP/MCP payloads, but it still sees SNI/session ids,
  connection metadata, timing, and byte counts.
- ACME rate limits make per-session certificates a PoC strategy, not a final
  production scaling model.

## File Map

- `src/main.ts`: UI, session creation, IndexedDB save/load, relay startup.
- `src/reverse-relay-client.ts`: browser TLS/HTTP server and relay client.
- `src/runtime-worker.ts`: browser Worker boundary.
- `src/runtime-handler.ts`: MCP methods and tools.
- `src/storage.ts`: IndexedDB helpers.
- `browser-tls-rustls/`: Rustls WebAssembly wrapper.
- `reverse-blind-relay/`: VM relay and deployment scripts.
