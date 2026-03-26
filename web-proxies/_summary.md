Operating entirely within the browser tab, modern web proxies leverage Service Workers and WebAssembly to bypass network restrictions without requiring administrative privileges or software installation. These systems, such as [Scramjet](https://github.com/MercuryWorkshop/scramjet) and the [Titanium Network](https://github.com/titaniumnetwork-dev) ecosystem, intercept network requests to rewrite HTML, JavaScript, and CSS in real-time. This research highlights the technical shift from slow, AST-based transformations to high-performance "Byte Span" rewriting and the implementation of the Wisp protocol for multiplexed transport. While highly effective for accessing content on locked-down devices like Chromebooks, these tools face significant hurdles from modern bot detection systems and inherent man-in-the-middle security risks.

**Key Findings:**
* **Architecture:** Modern proxies use Service Workers to act as a client-side proxy, avoiding the need for system-wide configuration.
* **Performance:** Scramjet's WASM-powered engine provides 2-3x faster rewriting speeds compared to legacy JavaScript-based parsers.
* **Transport:** The Wisp protocol enables complex features like WebSocket and UDP tunneling over a single connection.
* **Limitations:** Significant site breakage occurs with Google Sign-in (BotGuard) and Cloudflare protected sites due to sophisticated proxy detection.
