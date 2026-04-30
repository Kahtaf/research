This proof-of-concept demonstrates an ephemeral API server architecture where request handling and computation occur entirely within a mobile browser tab. By establishing an outbound WebSocket tunnel to a routing layer on Cloudflare, the system bypasses traditional browser networking limitations to serve public HTTP requests locally. The implementation leverages standard npm packages like Zod and Lodash for data processing while persisting application state across sessions via IndexedDB. Developers can choose between a specialized BrowserPod environment for running Node.js servers or a lightweight Web Worker fallback for broad compatibility.

*   Successfully routes public HTTP requests to local browser compute using a Cloudflare Durable Object relay.
*   Maintains state persistence across page refreshes by utilizing browser-native IndexedDB storage.
*   Supports dual execution paths: a full Node/Express environment and a portable Web Worker-based runtime.

**Key Tools:**
*   [BrowserPod](https://browserpod.io)
*   [Cloudflare Workers](https://workers.cloudflare.com)
