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

For a real internet demo of the fallback path:

- Host the Vite app over HTTPS.
- Host `relay/server.mjs` over public HTTPS/WSS.
- Set `VITE_RELAY_HTTP_URL=https://<relay-host>` when building the app.
- Set `PUBLIC_BASE_URL=https://<relay-host>` on the relay if it sits behind a
  proxy.
- Keep the relay generic. It must not import the app handler or perform
  application computation.

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
