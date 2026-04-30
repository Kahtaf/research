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
