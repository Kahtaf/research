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
- Browser-local TLS server implemented with `node-forge`.
- Browser-generated private key and CSR for optional ACME certificate issuance.
- API route: `GET /api/process?input=hello`.
- Streamable HTTP MCP route: `POST /mcp`.
- MCP tools over IndexedDB-backed text.

GCP VM relay:

- Browser control WSS:
  `wss://control.34.16.49.200.sslip.io:8443/browser/<sessionId>`.
- Public TCP ingress on `34.16.49.200:443`.
- SNI routing from the public session hostname to the connected tab.
- Optional ACME issuer at `/issue-cert`.
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
response bodies. If ACME is not configured, the browser falls back to a
self-signed certificate and test clients need `curl -k`.

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

## Trusted TLS With ACME

For this PoC, the relay can issue trusted certs for the current `sslip.io`
session hostnames with HTTP-01:

```bash
SESSION_HOST_SUFFIX=34.16.49.200.sslip.io \
PUBLIC_CERT_HOST_SUFFIX=34.16.49.200.sslip.io \
ACME_CHALLENGE_MODE=http-01 \
ACME_HTTP_PORT=80 \
ACME_DIRECTORY_URL=https://acme-v02.api.letsencrypt.org/directory \
ACME_EMAIL=you@example.com \
ACME_TERMS_AGREED=true \
npm run reverse-relay:deploy:gcp-vm
```

For a production domain, use a DNS-controlled suffix and DNS-01:

```text
*.mcp.example.com -> 34.16.49.200
```

Configure and deploy the relay with:

```bash
SESSION_HOST_SUFFIX=.mcp.example.com \
PUBLIC_CERT_HOST_SUFFIX=.mcp.example.com \
ACME_CHALLENGE_MODE=dns-01 \
ACME_DIRECTORY_URL=https://acme-v02.api.letsencrypt.org/directory \
ACME_EMAIL=you@example.com \
ACME_TERMS_AGREED=true \
CLOUDFLARE_ZONE_ID=<zone-id> \
CLOUDFLARE_API_TOKEN=<dns-edit-token> \
npm run reverse-relay:deploy:gcp-vm
```

Configure and deploy the static app with matching host settings:

```bash
VITE_REVERSE_RELAY_PUBLIC_SUFFIX=mcp.example.com npm run deploy
```

Flow:

1. Browser generates a private key and CSR for `<sessionId>.mcp.example.com`.
2. Browser sends only the CSR to the relay issuer.
3. Relay completes ACME HTTP-01 on port 80 or DNS-01 using Cloudflare DNS.
4. Relay returns the signed certificate chain.
5. Browser serves TLS with the browser-local private key.

The private key stays in browser storage. The browser caches successful ACME
certificates locally and reuses them until near expiry.

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

API with trusted ACME cert:

```bash
curl -sS "https://<sessionId>.34.16.49.200.sslip.io/api/process?input=hello"
```

MCP with trusted ACME cert:

```bash
curl -sS "https://<sessionId>.34.16.49.200.sslip.io/mcp" \
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
- ACME HTTP-01 works for this `sslip.io` PoC because the hostname resolves to
  the relay VM. DNS-01 needs a DNS-controlled suffix and a DNS API token.
- The issuer can create certificates for connected browser sessions, so keep
  DNS API permissions narrow and demo-only until auth/rate limits are hardened.
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
