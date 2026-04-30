# Browser-Local Compute Runtime PoC Notes

## 2026-04-30

- Created investigation folder `browser-local-compute-runtime-poc`.
- Goal: prove a mobile browser tab can host an ephemeral API endpoint where request handling and computation run locally in the browser, with a relay used only for routing.
- BrowserPod appears feasible as the preferred path: docs show `@leaningtech/browserpod`, Vite COOP/COEP headers, inner npm project copy/install, and `pod.onPortal(({ url, port }) => ...)`.
- BrowserPod requires a BrowserPod API key, so local verification without credentials needs a fallback path.
- BrowserPod docs state filesystem persistence is backed by browser IndexedDB, and Portals are routing URLs to services listening inside the browser pod.
- Fallback design: Vite mobile web app starts a dedicated Worker as the browser-local runtime, connects outbound to a relay with WebSocket, and handles `/api/process` inside the Worker using bundled npm packages plus IndexedDB state.
- Implemented Vite host app, browser Worker runtime, custom WebSocket relay, BrowserPod inner Node/Express API server, and a relay smoke test.
- `npm run build` passes.
- `npm run smoke:relay` passes; it proves the relay forwards HTTPS-style request envelopes to a connected WebSocket client and returns that client's response without local app computation.
- Desktop browser validation via local Vite + local relay:
  - Opened `http://localhost:5173/`.
  - App connected to `http://localhost:8787/`.
  - Called `curl -H "Authorization: Bearer <token>" "http://localhost:8787/portal/<session>/api/process?input=hello"`.
  - Response came from `runtime: "browser-local worker"` and included `packageUsed: "zod + lodash-es + nanoid"` plus `storage: "IndexedDB"`.
  - Reloaded the page and called again with `input=hello-again`; response returned `requestCount: 2`, proving IndexedDB persistence across reload in the same browser origin.
- BrowserPod path was not live-tested because no BrowserPod API key is available in this environment.
- Android Chrome and iOS Safari were not available in this environment; README documents expected mobile constraints and test steps.
- Added Cloudflare Worker static-assets deployment scaffold:
  - `wrangler.jsonc` deploys the Vite `dist` assets and a Worker script.
  - `cloudflare-worker/index.js` implements the WebSocket relay as a Durable Object keyed by session ID.
  - `public/_headers` keeps COOP/COEP headers for BrowserPod compatibility.
  - `npm run deploy` runs `npm run build && wrangler deploy`.
- Project-local Wrangler is installed through devDependencies; local `npx wrangler --version` reports `4.86.0`.
- User deployed to `https://browser-local-compute-runtime-poc.vana.workers.dev`, version `2251ccc2-40b2-4be6-87c0-834d60bbf789`.
- Verified deployed `/health` returns `{ "ok": true, "role": "cloudflare routing-only relay" }`.
- Verified deployed static app serves COOP/COEP headers.
- Found deployed frontend still defaulted to `https://browser-local-compute-runtime-poc.vana.workers.dev:8787/`, which prevents production tunnel connection.
- Fixed default relay URL logic: localhost uses port `8787`; deployed origins use same-origin HTTPS/WSS.
- Re-ran `npm run build` and `npm run smoke:relay`; both pass after the Cloudflare scaffold and production relay URL fix.
- Clarified documentation boundary: application computation and IndexedDB state run in the browser tab; Cloudflare hosts static assets and provides the WebSocket/HTTP routing portal only.
- Redeployed fixed Cloudflare build to `https://browser-local-compute-runtime-poc.vana.workers.dev`, version `36346451-974a-4a63-9d90-f90832d3378e`.
- Verified live bundle uses same-origin Cloudflare relay URL instead of `:8787`.
- Verified external `curl` to `/portal/<session>/api/process?input=hello` returns JSON computed by the browser worker through the Cloudflare Durable Object tunnel.
