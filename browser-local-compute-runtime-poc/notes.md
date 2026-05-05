# Browser-Local MCP Server PoC Notes

## Objective

Prove that a mobile browser tab can host an ephemeral public API and MCP server
without moving application compute or stored user text to a backend.

Success criteria:

- Public requests reach an active browser tab.
- The browser handles API and MCP logic locally.
- Browser-local storage persists textarea content and request counts.
- The relay forwards traffic without seeing HTTP paths, MCP method names, tool
  arguments, text content, or response bodies.
- Standard MCP clients can connect without disabling TLS verification.

## Current Design

The hosted Cloudflare app boots a browser runtime and registers a session with a
GCP VM relay over WSS. Public clients connect to:

```text
https://<sessionId>.34.16.49.200.sslip.io
```

The relay accepts raw TCP on port `443`, peeks at TLS SNI to find the browser
session, and forwards opaque TLS bytes over the browser control WebSocket. TLS
terminates inside the browser tab using Rustls compiled to WebAssembly.

The browser runtime exposes:

- `GET /api/process?input=hello`
- `POST /mcp`

MCP tools:

- `get_text`
- `search_text`
- `get_text_stats`

State is stored in IndexedDB.

## Key Decisions

- BrowserPod was not used in the final PoC because the fallback WebSocket relay
  and browser Worker path was enough to prove the end-to-end behavior.
- Cloudflare is now only the static app host. API/MCP traffic goes through the
  blind VM relay.
- The relay uses SNI routing instead of terminating HTTPS. This keeps HTTP and
  MCP payloads opaque to the relay.
- The browser generates and stores the TLS private key locally. The relay sees a
  CSR, not the private key.
- Rustls WASM terminates TLS in the browser so stricter clients such as Claude
  Code can validate the certificate chain normally.
- The current demo is unauthenticated. The random session URL is the only access
  barrier.

## Validation

Latest deployed static app:

```text
https://browser-local-compute-runtime-poc.vana.workers.dev
version: 8193bebc-04f6-4949-976d-3360046611dc
```

Verified locally:

- `npm run build`
- `npm run reverse-relay:build`
- `npx fallow dead-code`

Fallow result:

- No dead files.
- No dead exports.
- Health score: `93 A`.
- Remaining warnings are complexity in live TLS, relay, parser, and MCP
  dispatcher paths.

Verified against the deployed browser tab:

- API request returned JSON with `runtime: "browser-local TLS server"`,
  `storage: "IndexedDB"`, and `relay: "blind TCP passthrough"`.
- MCP `tools/list` returned `get_text`, `search_text`, and `get_text_stats`.
- Claude Code connected through `.claude/.mcp.json` and called
  `get_text_stats`, receiving IndexedDB-backed browser-local stats.

Current live session used for Claude verification:

```text
https://uq32uggkc6f9h4sqtm22f6ld.34.16.49.200.sslip.io/mcp
```

This URL changes when the browser session changes.

## Open Risks

- Mobile browser backgrounding can pause the server.
- IndexedDB storage can be evicted by the browser.
- No authentication exists in this demo.
- Per-session ACME certificates will not scale cleanly under public CA rate
  limits.
- Static app integrity is unresolved. A malicious static host could alter the
  browser runtime.
- The relay is payload-blind, not metadata-blind.

## Useful Commands

```bash
npm run build
npm run reverse-relay:build
npx fallow dead-code
npm run deploy
```

Claude verification:

```bash
claude --strict-mcp-config --mcp-config .claude/.mcp.json \
  --permission-mode bypassPermissions \
  -p 'Use the browser-local-poc MCP server to call get_text_stats.'
```
