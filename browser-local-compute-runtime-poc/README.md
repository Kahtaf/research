# Browser-Local Compute Runtime PoC

Proof of concept for an ephemeral API server whose request handler runs in a
mobile browser tab. The browser connects outbound to a routing layer, receives an
internet request, computes locally with npm packages, persists state in browser
storage, and returns JSON.

## Result

This repo contains two compatible paths:

1. **BrowserPod Portal path**: boots BrowserPod in the page, copies an inner
   Node/Express npm project into the pod, installs dependencies, starts the API
   server inside BrowserPod, and exposes it with a BrowserPod Portal URL.
2. **Fallback tunnel path**: starts a browser `Worker` runtime, connects outbound
   to `relay/server.mjs` over WebSocket, and handles `/api/process` locally in
   the worker. The relay only authenticates, rate-limits, and forwards request
   envelopes.

The fallback path is the locally validated implementation because BrowserPod
requires an API key.

Current Cloudflare deployment:

```text
https://browser-local-compute-runtime-poc.vana.workers.dev
Version ID: 36346451-974a-4a63-9d90-f90832d3378e
```

The deployment above was verified for `/health`, static COOP/COEP headers, and
the Cloudflare Durable Object tunnel path. The hosted app now defaults to
same-origin `wss://.../ws/:sessionId` and `https://.../portal/:sessionId/...`
instead of the local development `:8787` relay.

## Compute Boundary

This PoC is browser-local compute with a cloud-hosted tunnel.

Runs locally in the browser tab:

- `/api/process` request handler.
- Input validation with `zod`.
- Tokenization, sorting, and frequency aggregation with `lodash-es`.
- ID/result generation with `nanoid`.
- Browser state persistence with IndexedDB.
- Final JSON response construction.

Runs on Cloudflare:

- Static asset hosting for the web app.
- WebSocket acceptor at `/ws/:sessionId`.
- Public HTTP routing at `/portal/:sessionId/*`.
- Durable Object session affinity for the active browser tab.
- Relay-layer bearer token check and rate limiting.

Cloudflare is required because browsers cannot directly accept inbound TCP/HTTP
connections from the public internet. The Cloudflare Worker/Durable Object is a
portal and routing layer only; it must not perform the application computation
or read/write the browser's local IndexedDB state.

## Files

- `src/main.ts`: host app orchestration and UI.
- `src/runtime-worker.ts`: browser-local runtime boundary for fallback mode.
- `src/runtime-handler.ts`: local API handler using `zod`, `lodash-es`, and
  `nanoid`.
- `src/storage.ts`: IndexedDB counter/history persistence.
- `src/tunnel-client.ts`: browser WebSocket tunnel client.
- `src/browserpod.ts`: BrowserPod boot, file copy, npm install, server launch,
  and Portal URL capture.
- `public/browserpod-project/server.mjs`: Node/Express API server intended to
  run inside BrowserPod.
- `relay/server.mjs`: routing-only relay for fallback mode.
- `scripts/relay-smoke.mjs`: relay-only smoke test.
- `cloudflare-worker/index.js`: Cloudflare Durable Object relay and static asset
  Worker.
- `wrangler.jsonc`: Cloudflare deployment config.

## API Contract

Route:

```text
GET /api/process?input=hello
Authorization: Bearer <session-token>
```

Fallback public relay URL:

```text
https://<relay-host>/portal/<unguessable-session-id>/api/process?input=hello
```

Example response:

```json
{
  "input": "hello",
  "result": "HELLO-EU9383UlbK",
  "packageUsed": "zod + lodash-es + nanoid",
  "requestCount": 1,
  "storage": "IndexedDB",
  "runtime": "browser-local worker",
  "servedFrom": "mobile-browser-tab",
  "timestamp": "2026-04-30T16:39:35.150Z"
}
```

## Setup

```bash
npm install
npm run build
```

Start the fallback relay:

```bash
npm run relay
```

Start the hosted web app:

```bash
npm run dev
```

Open the app on desktop or mobile:

```text
http://<host-lan-ip>:5173/
```

For same-device desktop testing, `http://localhost:5173/` is enough. For mobile,
use the LAN URL printed by Vite and ensure the phone can reach the relay host.

## Cloudflare Deploy

This project can deploy as a single Cloudflare Worker:

- Vite static assets are served from `dist`.
- `/ws/:sessionId` accepts the browser tab's outbound WebSocket.
- `/portal/:sessionId/*` forwards external HTTP requests to the active browser
  tab through a Durable Object.

Login once:

```bash
npx wrangler login
```

Deploy:

```bash
npm run deploy
```

The deploy script runs:

```bash
npm run build && wrangler deploy
```

In local development, the app defaults the relay URL to
`http://localhost:8787/`. On a deployed HTTPS origin, it defaults to the same
origin, so the browser connects to `wss://<worker-host>/ws/:sessionId` and curls
use `https://<worker-host>/portal/:sessionId/...`.

## Demo Script

1. Start the relay:

   ```bash
   npm run relay
   ```

2. Start the web app:

   ```bash
   npm run dev
   ```

3. Open the Vite URL on mobile Chrome or Safari.

4. Wait until the status reads `Tunnel connected`.

5. Copy the displayed `curl` command.

6. From another device or shell, call the public URL:

   ```bash
   curl -H "Authorization: Bearer <token>" \
     "https://<relay-host>/portal/<session-id>/api/process?input=hello"
   ```

7. Confirm the JSON contains:

   - `runtime: "browser-local worker"` or `runtime: "browser-local BrowserPod Node.js"`
   - `servedFrom: "mobile-browser-tab"`
   - `packageUsed`
   - `storage`
   - incrementing `requestCount`

8. Refresh the browser tab and call the URL again. The fallback path should keep
   the same session ID/token via `localStorage`, reconnect the tunnel, and return
   a higher `requestCount` from IndexedDB.

## BrowserPod Mode

BrowserPod is the preferred path when you have a BrowserPod API key.

1. Serve the app with COOP/COEP headers. This Vite config already sends:

   ```text
   Cross-Origin-Opener-Policy: same-origin
   Cross-Origin-Embedder-Policy: require-corp
   ```

2. Open the app.

3. Paste a BrowserPod API key into `BrowserPod API key`.

4. Click `Start BrowserPod`.

5. Wait for the Portal URL and call it with the bearer token shown in the curl
   command.

The inner BrowserPod server persists `state.json` in the BrowserPod filesystem.
BrowserPod documents that this filesystem is backed by browser IndexedDB for the
same origin.

## Public Hosting Notes

For a real internet demo of the fallback path with a separate Node relay:

- Host the Vite app over HTTPS.
- Host `relay/server.mjs` over public HTTPS/WSS.
- Set `VITE_RELAY_HTTP_URL=https://<relay-host>` when building the app.
- Set `PUBLIC_BASE_URL=https://<relay-host>` on the relay if it sits behind a
  proxy.
- Keep the relay generic. It must not import the app handler or perform
  application computation.

The Cloudflare Worker deployment does not need a separate relay host; the
Durable Object relay is deployed with the static app.

## Security Controls

- Public API URLs include a random `sessionId`.
- Requests require `Authorization: Bearer <token>`.
- The browser worker also checks the bearer token, not just the relay.
- The relay rate-limits each session/IP pair with `RATE_LIMIT_MAX` per
  `RATE_LIMIT_WINDOW_MS`.
- The worker exposes only `GET /api/process`, not arbitrary code execution.
- The API is ephemeral and reachable only while the browser tab is active and
  connected.

## Validation

Completed locally on April 30, 2026:

```bash
npm run build
npm run smoke:relay
```

Desktop browser validation:

- Loaded `http://localhost:5173/`.
- Observed `Tunnel connected`.
- Called the relay URL with `curl`.
- Received JSON generated by the browser worker using `zod + lodash-es + nanoid`.
- Refreshed the page and called again.
- Received `requestCount: 2`, confirming IndexedDB persistence across reload.

Cloudflare deployment validation on April 30, 2026:

- `https://browser-local-compute-runtime-poc.vana.workers.dev/health` returns
  `ok: true`.
- Static app response includes:
  - `Cross-Origin-Opener-Policy: same-origin`
  - `Cross-Origin-Embedder-Policy: require-corp`
- The deployed app connects to the Cloudflare Durable Object tunnel on the same
  origin and successfully returns `/api/process` responses computed by the
  browser worker.

Not completed:

- BrowserPod Portal live test, because no BrowserPod API key was available.
- Android Chrome device test.
- iOS Safari device test.

## Mobile Limitations

- Browsers cannot accept inbound TCP from the internet; a Portal or outbound
  WebSocket relay is required.
- iOS Safari and Android Chrome can suspend background tabs, breaking the
  ephemeral API until the tab is foregrounded again.
- iOS may be more aggressive about memory pressure and storage eviction.
- BrowserPod needs `SharedArrayBuffer`, which requires cross-origin isolation
  headers and HTTPS outside localhost.
- The fallback worker path does not need `SharedArrayBuffer`, but production
  browser APIs still require secure contexts for reliable mobile behavior.
- WebSocket connectivity depends on captive portals, VPNs, corporate proxies,
  and mobile network policies.
- Browser storage is origin-scoped. Changing hostnames or ports creates a
  separate IndexedDB/localStorage namespace.

## References

- [BrowserPod overview](https://browserpod.io/docs/overview)
- [BrowserPod Portals](https://browserpod.io/docs/understanding-browserpod/portals)
- [BrowserPod filesystem](https://browserpod.io/docs/understanding-browserpod/filesystem)
- [BrowserPod cross-origin isolation](https://browserpod.io/docs/understanding-browserpod/cross-origin-isolation)
- [BrowserPod Express tutorial](https://browserpod.io/docs/getting-started/expressjs)
