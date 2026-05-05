# Browser-Local MCP Text Server PoC

Minimal proof of concept for an API and MCP server that runs in an active
browser tab. Cloudflare hosts the static app. A GCP VM relay forwards opaque TCP
streams by SNI. TLS terminates in the browser tab, and the browser handles HTTP,
MCP tools, computation, and IndexedDB storage.

Deployed app:

```text
https://browser-local-compute-runtime-poc.vana.workers.dev
```

Source:

```text
https://github.com/Kahtaf/research/tree/main/browser-local-compute-runtime-poc
```

## What Runs Where

Browser tab:

- Minimal UI.
- Browser Worker runtime.
- Self-signed TLS server implemented with `node-forge`.
- API route: `GET /api/process?input=hello`.
- Streamable HTTP MCP route: `POST /mcp`.
- MCP tools over IndexedDB-backed text.

GCP VM relay:

- Browser control WSS:
  `wss://control.34.16.49.200.sslip.io:8443/browser/<sessionId>`.
- Public TCP ingress on `34.16.49.200:443`.
- SNI routing from `<sessionId>.34.16.49.200.sslip.io` to the connected tab.
- Opaque byte forwarding only.

Cloudflare:

- Static web app hosting.
- No API/MCP relay logic in the current path.

## Architecture

```text
Hosted app
  │ boots
  ▼
Browser tab ── WSS control ──► Blind relay VM
  ▲                              │
  │ TLS, HTTP, MCP, IndexedDB     │ SNI only
  └──────── opaque TCP/TLS ◄──────┘
                 ▲
                 │ HTTPS
           API or MCP client
```

The relay can see source IPs, SNI/session ids, timing, and byte counts. It
should not see HTTP paths, MCP methods, tool arguments, textarea content, or
response bodies. The current certificate is self-signed, so test clients need
`curl -k` or equivalent trust handling.

## MCP Tools

Endpoint:

```text
https://<sessionId>.34.16.49.200.sslip.io/mcp
```

Methods:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `tools/call`

Tools:

- `get_text`: read text by `offset` and `maxChars`.
- `search_text`: return snippets for a literal query.
- `get_text_stats`: return character, byte, line, and word counts.

`get_text` defaults to `20000` chars and has a hard maximum of `100000` chars.

## Local Development

Install and build:

```bash
npm install
npm run build
```

Start the browser app:

```bash
npm run dev
```

Start the relay locally:

```bash
npm run reverse-relay:dev
```

Relay smoke test:

```bash
npm run reverse-relay:smoke
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

The deploy script runs `npm run build && wrangler deploy`.

## Manual Verification

Open the deployed app, wait for `Connected`, then copy the displayed session
URLs.

API:

```bash
curl -k -sS "https://<sessionId>.34.16.49.200.sslip.io/api/process?input=hello"
```

MCP:

```bash
curl -k -sS "https://<sessionId>.34.16.49.200.sslip.io/mcp" \
  -H 'content-type: application/json' \
  -H 'mcp-protocol-version: 2025-06-18' \
  --data '{"jsonrpc":"2.0","id":"stats-1","method":"tools/call","params":{"name":"get_text_stats","arguments":{}}}'
```

Codex MCP config:

```toml
[mcp_servers.browser_text]
url = "https://<sessionId>.34.16.49.200.sslip.io/mcp"
startup_timeout_sec = 20
tool_timeout_sec = 60
```

## Limitations

- The server is available only while the browser tab is open and connected.
- Mobile browsers may pause tabs, Workers, WebSockets, and IndexedDB access in
  the background.
- IndexedDB can be evicted by the browser under storage pressure.
- Self-signed TLS is acceptable for this PoC but not for a normal MCP client
  integration. Production needs CA-trusted per-session certificates while
  keeping private keys browser-local.
- A malicious static host could serve modified JavaScript. Production needs a
  stronger app integrity story.
- There is no auth in this demo. Anyone with the session URL can query the tab.

## Files

- `src/main.ts`: UI, session creation, IndexedDB save/load, relay startup.
- `src/reverse-relay-client.ts`: browser TLS server, HTTP parser, relay client.
- `src/runtime-worker.ts`: Worker boundary for MCP handling.
- `src/runtime-handler.ts`: MCP methods and tools.
- `src/storage.ts`: IndexedDB helpers.
- `reverse-blind-relay/`: VM relay and deployment scripts.
