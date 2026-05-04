# Browser-Local MCP Text Server PoC

Proof of concept for an ephemeral MCP server whose request handling and text
tools run inside the user's browser tab. The hosted app stores pasted text in
IndexedDB, opens an outbound WebSocket to a routing-only relay, and exposes a
public Streamable HTTP MCP URL while the tab stays active.

This version does not use BrowserPod and does not use bearer-token auth. The
browser tab generates a local P-256 ECDH keypair and accepts only encrypted MCP
request envelopes at `/mcp`, so the relay sees ciphertext rather than MCP JSON.

## Deployed App

```text
https://browser-local-compute-runtime-poc.vana.workers.dev
Current Version ID: 140d4420-b70f-4d9f-b497-ed26431c7e56
```

Open the deployed URL on desktop or mobile. The app displays an MCP URL shaped
like:

```text
https://browser-local-compute-runtime-poc.vana.workers.dev/portal/<sessionId>/mcp
```

The current local implementation also displays a browser public key and
fingerprint. External clients need both the MCP URL and browser public key to
construct encrypted request envelopes. Do not paste sensitive text into this
temporary demo; it is encrypted from the relay, but it is not authenticated.

## Architecture

Runs locally in the browser:

- Minimal web UI and browser `Worker` runtime.
- Browser-local ECDH private key generation and MCP JSON-RPC request handling
  behind encrypted envelopes at `/mcp`.
- `zod` validation for MCP tool arguments.
- Text persistence in IndexedDB.
- Tool execution and response construction.

Runs on Cloudflare:

- Static hosting for the web app.
- WebSocket acceptor at `/ws/:sessionId`.
- Public HTTPS routing at `/portal/:sessionId/*`.
- Durable Object session affinity for the active browser tab.
- Rate limiting, body-size limiting, and request timeout.

Cloudflare does not read IndexedDB and does not perform the MCP text processing.
In the blind-relay version, it only forwards encrypted request/response
envelopes to and from the connected browser tab.

The browser WebSocket connection is visibility-aware. When the tab becomes
hidden, the client closes the tunnel and marks the runtime paused. When the tab
becomes visible again, it reconnects automatically and keeps retrying with
bounded backoff while visible.

## Blind Relay Encryption

The browser tab generates a fresh P-256 ECDH keypair on page load. The private
key stays in the browser Worker. The UI displays:

- MCP URL: `/portal/<sessionId>/mcp`.
- Browser public key token.
- Browser public key fingerprint.
- A copyable encrypted curl request.
- A local encryption proxy command for normal MCP clients.

Plaintext `POST /mcp` requests are rejected with:

```json
{
  "error": "encrypted_envelope_required"
}
```

Cloudflare can still observe metadata such as IP addresses, session IDs, timing,
and ciphertext sizes. It should not see MCP method names, tool arguments,
textarea content, or MCP response data.

## MCP Tools

The browser-local MCP endpoint is:

```text
POST /portal/<sessionId>/mcp
```

`POST` bodies must be encrypted envelopes. The decrypted payload is the normal
MCP JSON-RPC message.

Supported JSON-RPC methods:

- `initialize`: returns server info and `tools` capability.
- `notifications/initialized`: accepted with HTTP `202`.
- `tools/list`: lists available tools.
- `tools/call`: runs a tool against IndexedDB-backed textarea content.

Tools:

- `get_text`: returns text by `offset` and `maxChars`.
- `search_text`: returns snippets for a literal case-insensitive query.
- `get_text_stats`: returns `charCount`, `byteEstimate`, `lineCount`, and
  `wordCount`.

Output limits:

- Default `maxChars`: `20000`.
- Hard maximum `maxChars`: `100000`.
- `get_text` includes `truncated`, `nextOffset`, and `totalChars` metadata.

## Local Setup

```bash
npm install
npm run build
```

Start the relay:

```bash
npm run relay
```

Start the web app:

```bash
npm run dev
```

Open:

```text
http://localhost:5173/
```

For mobile LAN testing, open Vite's network URL on the phone and make sure the
phone can reach the relay host.

## Deployment

Login once:

```bash
npx wrangler login
```

Deploy:

```bash
npm run deploy
```

The deploy script runs `npm run build && wrangler deploy`.

On the Cloudflare deployment, the browser connects to the same origin:

```text
wss://browser-local-compute-runtime-poc.vana.workers.dev/ws/<sessionId>
```

External callers use:

```text
https://browser-local-compute-runtime-poc.vana.workers.dev/portal/<sessionId>/mcp
```

The app also shows a copyable `curl` command that sends an encrypted
`get_text_stats` envelope against the active MCP URL. The curl response is also
encrypted; use `npm run encrypted:mcp` or the local proxy below when you need to
decrypt and inspect the JSON-RPC response.

## Codex MCP Config

Standard MCP clients do not speak this encrypted envelope format directly. Run
the local encryption proxy shown in the app, then point Codex at the local proxy:

```toml
[mcp_servers.browser_text]
url = "http://localhost:3333/mcp"
startup_timeout_sec = 20
tool_timeout_sec = 60
```

The proxy receives plaintext MCP from Codex locally, encrypts it to the browser
public key, sends ciphertext through Cloudflare, decrypts the browser response,
and returns plaintext MCP to Codex. The browser tab must remain foregrounded and
connected.

Manual encrypted request:

```bash
npm run encrypted:mcp -- "<mcp-url>" "<browser-public-key-token>"
```

## Smoke Tests

```bash
npm run build
npm run smoke:relay
npm run smoke:mcp
```

`smoke:relay` verifies unauthenticated `/portal/:sessionId/mcp` routing through
the local WebSocket relay. `smoke:mcp` verifies the MCP JSON-RPC wire shape for
`initialize`, `tools/list`, `get_text`, `search_text`, and `get_text_stats`.

Wrangler blind relay check:

```bash
npm run build
npx wrangler dev --local --port 8788
WRANGLER_BASE_URL=http://localhost:8788 npm run smoke:wrangler-blind
```

The smoke test connects a mock browser WebSocket to the local Wrangler Worker,
sends an encrypted MCP request containing a secret marker, verifies the body
forwarded by the Worker does not contain the marker, MCP method, or tool name,
then decrypts the request only in the mock browser and returns an encrypted
response. Wrangler logs should show only route/status metadata such as
`POST /portal/<sessionId>/mcp 200 OK`.

## Demo Script

1. Open the deployed app on a mobile browser:

   ```text
   https://browser-local-compute-runtime-poc.vana.workers.dev
   ```

2. Paste or edit text in the textarea. It auto-saves to IndexedDB.

3. Wait until the status reads `Connected`.

4. Copy the displayed MCP URL.

5. Add the MCP config to Codex.

6. Ask Codex to call `get_text`, `search_text`, or `get_text_stats`.

7. Keep the mobile browser tab open while testing.

8. Refresh or reopen the app to confirm the textarea content persists.

## Security Notes

- This refactor intentionally removes bearer-token auth for a temporary demo.
- The random session URL is unguessable, but anyone who has it can query the
  text while the tab is open if they also have the browser public key or proxy
  command.
- Cloudflare sees encrypted envelopes only for `POST /mcp`, not MCP JSON.
- This is honest-but-curious relay protection only. A malicious static host
  could still serve modified JavaScript; production needs bundle integrity or a
  separately trusted app distribution path.
- Do not paste private or sensitive data.
- The relay still rate-limits requests and rejects bodies over 1 MiB.
- The browser worker exposes only MCP text tools, not arbitrary code execution.

## Browser Limitations

- Availability is foreground-tab only in practice. Mobile browsers may pause
  timers, Workers, WebSockets, and IndexedDB work when the user locks the phone,
  switches apps, or leaves the tab in the background.
- This app closes the WebSocket when the tab is hidden and reconnects when it
  becomes visible again. Mobile OS background suspension can still prevent
  immediate reconnect until the browser is foregrounded.
- iOS Safari is especially aggressive about suspending background tabs.
- Browser storage is local but not permanent. IndexedDB can be evicted under
  storage pressure or private-browsing constraints.
- Large text is feasible, but hundreds of MB can become memory- and UI-heavy on
  mobile. The tools page large reads with `offset` and `maxChars`.
- HTTPS is required for the deployed tunnel and modern browser APIs.
- Cross-origin isolation headers are still set by the deployment, though this
  Worker-only refactor no longer depends on BrowserPod.

## Files

- `src/main.ts`: UI orchestration, IndexedDB loading/saving, and tunnel startup.
- `src/runtime-worker.ts`: browser-local Worker runtime boundary.
- `src/runtime-handler.ts`: MCP handler and tool implementations.
- `src/crypto-envelope.ts`: browser-compatible ECDH/AES-GCM envelope helpers.
- `src/storage.ts`: IndexedDB text and request counter storage.
- `src/tunnel-client.ts`: browser outbound WebSocket client.
- `relay/server.mjs`: local routing-only relay.
- `cloudflare-worker/index.js`: Cloudflare Worker and Durable Object relay.
- `scripts/relay-smoke.mjs`: unauthenticated relay smoke test.
- `scripts/mcp-smoke.mjs`: MCP JSON-RPC smoke test.
- `scripts/wrangler-blind-smoke.mjs`: Wrangler local Worker blind-relay smoke
  test.
- `scripts/encrypted-mcp-request.mjs`: one-shot encrypted MCP verifier.
- `scripts/encrypted-mcp-proxy.mjs`: local MCP encryption proxy for clients.
