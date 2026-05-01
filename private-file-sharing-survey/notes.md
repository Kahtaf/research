# Private File Sharing Survey — Notes

## 2026-05-01

Investigation kicked off from a question on the `browser-local-compute-runtime-poc` project: if we used its tab-as-API architecture for ephemeral private file sharing, what other projects already exist in this space, and does the relay actually see decrypted traffic / PII?

### Audit of current PoC relay (cloudflare-worker/index.js, relay/server.mjs)

What the Cloudflare Worker / local relay sees in plaintext per request:

- HTTP method, path, query string (forwarded as JSON fields).
- All HTTP request headers (`Object.fromEntries(request.headers.entries())`).
- Full HTTP request body, base64-encoded (`encodeBody(arrayBuffer)`). Base64 is encoding, not encryption.
- All HTTP response headers, status, and body from the browser.
- Caller IP (`cf-connecting-ip` / `x-forwarded-for`) used for rate limiting.
- Session ID (path-derived).
- WebSocket frames between browser and relay are over TLS to Cloudflare; CF terminates TLS and sees plaintext frames.

So the current relay is **plaintext from CF's perspective**. The "dumb routing" property means CF does not *use* the data, but it absolutely can *read* it. Anyone with access to relay logs, the Worker, the Durable Object, Cloudflare observability, or upstream network taps inside the CF edge sees the full request and response bodies.

To turn this into a real private-file-sharing primitive, encryption has to happen end-to-end *inside* the browser tabs, with the relay seeing only ciphertext + minimal routing metadata. The session ID and IP are still visible regardless — that is structural metadata leakage no matter what is encrypted.

This is the same threat model as Send / Wormhole / Magic Wormhole: trust-the-server-with-routing, not-with-content.

### What a properly E2E version would change

- Sender derives a symmetric key in the browser (libsodium / WebCrypto AES-GCM) and never sends it to the relay.
- Key is communicated out-of-band — typically as a URL fragment (`#key=...`), which by spec is *not* sent to the server in HTTP requests.
- Sender encrypts the file in the browser, POSTs ciphertext through the relay.
- Recipient's tab decrypts in the browser using the fragment key.
- Filename and content-type need to be encrypted as part of a metadata blob — otherwise they leak through HTTP headers.
- IP, timing, session-id, and ciphertext size are still visible to the relay. Padding can mask size.

### Non-encrypted residual PII the relay sees even after E2E

- Sender IP address.
- Recipient IP address.
- Session ID (links sender/recipient pair to each other).
- Approximate file size (ciphertext length, modulo padding).
- Timing / number of requests.
- TLS fingerprint, User-Agent, Accept headers (forwarded by the current code).

If the current PoC is to be used for private file sharing, the relay code should also be tightened to *not forward* raw client headers — only the minimum subset needed to deliver the bytes.

## Survey pass — verifying tools

Confirmed via WebSearch (May 2026):

- **FilePizza**: ~9.9k stars, BSD-3, sender browser tab must stay open, WebRTC P2P, optional password. Active.
- **ToffeeShare**: P2P WebRTC, DTLS for transport encryption, no published max size, sender stays online — closing tab kills transfer. Closed source SaaS.
- **timvisee/send**: actively maintained 2026 fork of Firefox Send. ffsend CLI v0.2.77 released Feb 2026. Server-stored encrypted blob, key in URL fragment. Sender does NOT need to stay online. Self-hostable.
- **wormhole.app** (Socket Inc.): files <=5 GB stored encrypted on their servers for 24h, files >5 GB go P2P browser-to-browser. AES-128-GCM, key in URL fragment. Cloudflare CDN. Source library `wormhole-crypto` published on npm.

Architecture buckets settled:

- **A. Sender-online, browser, WebRTC**: FilePizza, ToffeeShare, WebWormhole, Reep.io, JustBeamIt, drop.lol, blymp.io, ShareDrop. Closest to our PoC's "sender-tab-is-the-server" property.
- **B. Sender-online, native**: OnionShare (Tor), Magic Wormhole, croc.
- **C. Server-stored, encrypted, key-in-URL**: timvisee/send, wormhole.app, Gokapi, 1time.io.
- **D. LAN airdrop**: Snapdrop, PairDrop.

### What's structurally novel about the PoC

The closest peer concept is **OnionShare** (your computer hosts a server, recipient hits a URL, no third-party storage). OnionShare needs Tor on both sides. WebRTC tools (FilePizza/ToffeeShare) need both peers in a webapp at the same time — the recipient cannot just `curl` the URL.

Our model: browser tab is an addressable HTTP origin on the public internet via outbound WebSocket tunnel to a Cloudflare relay. Recipient hits a plain URL — no WebRTC dance, no app to install, just GET. That is the gap: **OnionShare-without-Tor, recipient-app-free**. It is a niche but real.

### Saturation conclusion

Browser-based ephemeral E2E file transfer is well-saturated.
- Server-stored + key-in-URL: use Wormhole.app or self-host timvisee/send.
- Sender-online WebRTC P2P: use FilePizza or ToffeeShare.
- The empty quadrant: tab-as-tunneled-HTTP-origin so recipient uses NO app at all, just a URL hit by curl/browser. Plausible niche, useful for delivering to people who can't run JS (CLI tools, scripts, embedded clients).

## Final report
See README.md.
