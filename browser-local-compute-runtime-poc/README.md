# Browser-Local MCP Text Server PoC

Proof of concept for an ephemeral MCP server whose request handling and text
tools run inside the user's browser tab. The hosted app stores pasted text in
IndexedDB, opens an outbound WebSocket to a routing-only relay, and exposes a
public Streamable HTTP MCP URL while the tab stays active.

This version does not use BrowserPod and does not use bearer-token auth. The
random `sessionId` in the URL is the only access barrier for this temporary
demo.

## Deployed App

```text
https://browser-local-compute-runtime-poc.vana.workers.dev
Current Version ID: 7ec78151-6d30-4810-87c7-5009a02ce758
```

Open the deployed URL on desktop or mobile. The app displays an MCP URL shaped
like:

```text
https://browser-local-compute-runtime-poc.vana.workers.dev/portal/<sessionId>/mcp
```

Anyone with that URL can query the browser-local text while the tab is open. Do
not paste sensitive text into this unauthenticated demo.

## Architecture

Runs locally in the browser:

- Minimal web UI and browser `Worker` runtime.
- MCP JSON-RPC request handling at `/mcp`.
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
It only forwards request envelopes to the connected browser tab and returns the
browser's response.

## MCP Tools

The browser-local MCP endpoint is:

```text
POST /portal/<sessionId>/mcp
```

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

The app also shows a copyable `curl` command that calls `get_text_stats`
against the active MCP URL. Run it from another terminal to verify the public
Cloudflare route reaches the browser tab and the browser Worker reads local
IndexedDB state.

## Codex MCP Config

Copy the config shown in the app:

```toml
[mcp_servers.browser_text]
url = "https://browser-local-compute-runtime-poc.vana.workers.dev/portal/<sessionId>/mcp"
startup_timeout_sec = 20
tool_timeout_sec = 60
```

Then ask Codex to read, search, or summarize the browser text. The browser tab
must remain foregrounded and connected.

## Smoke Tests

```bash
npm run build
npm run smoke:relay
npm run smoke:mcp
```

`smoke:relay` verifies unauthenticated `/portal/:sessionId/mcp` routing through
the local WebSocket relay. `smoke:mcp` verifies the MCP JSON-RPC wire shape for
`initialize`, `tools/list`, `get_text`, `search_text`, and `get_text_stats`.

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
  text while the tab is open.
- Do not paste private or sensitive data.
- The relay still rate-limits requests and rejects bodies over 1 MiB.
- The browser worker exposes only MCP text tools, not arbitrary code execution.

## Browser Limitations

- Availability is foreground-tab only in practice. Mobile browsers may pause
  timers, Workers, WebSockets, and IndexedDB work when the user locks the phone,
  switches apps, or leaves the tab in the background.
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
- `src/storage.ts`: IndexedDB text and request counter storage.
- `src/tunnel-client.ts`: browser outbound WebSocket client.
- `relay/server.mjs`: local routing-only relay.
- `cloudflare-worker/index.js`: Cloudflare Worker and Durable Object relay.
- `scripts/relay-smoke.mjs`: unauthenticated relay smoke test.
- `scripts/mcp-smoke.mjs`: MCP JSON-RPC smoke test.
