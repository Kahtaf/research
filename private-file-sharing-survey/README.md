# Private / E2E File Sharing Landscape Survey

**Date:** 2026-05-01
**Purpose:** Compare a hypothetical "browser-tab-as-public-HTTP-origin via Cloudflare relay tunnel" file-sharing PoC against the existing landscape.

## Hypothetical product (recap)

Sender opens a webpage; the tab acts as an ephemeral HTTP server via outbound WebSocket to a Cloudflare relay that exposes a public URL. Recipient just hits that URL. Bytes are E2E-encrypted in-browser; the relay routes ciphertext only. The "server" is the sender's tab — close the tab, transfer dies. Files never persisted anywhere.

Sorted **closest-to-our-model first**.

---

## A. Sender-online, browser-only, no third-party storage (closest match)

### 1. OnionShare — `onionshare/onionshare`
- **URL**: https://github.com/onionshare/onionshare · https://onionshare.org
- **Architecture**: Sender's machine runs a Tor onion service; recipient hits a `.onion` URL. No relay storage. Native desktop app (Electron-ish, Python).
- **Encryption**: Tor-native E2E to the onion address (public-key derived). Optional shared password.
- **Persistence**: None. Bytes live on sender's disk; never copied to a third party.
- **Sender online**: Yes. Closing the app kills the share.
- **Max size**: Disk-bound only.
- **License/activity**: GPL-3.0, ~7k stars, active (releases through 2026).
- **Operator can see**: No third-party operator. Tor relays see only onion-routed ciphertext.
- **Differentiator**: The canonical "your computer is the server" model — but requires Tor on both ends.

### 2. FilePizza — `kern/filepizza`
- **URL**: https://github.com/kern/filepizza · https://file.pizza
- **Architecture**: WebRTC P2P browser-to-browser. Server is signaling-only (WebSocket).
- **Encryption**: WebRTC DTLS-SRTP transport. Optional password gate.
- **Persistence**: None — never touches disk on the server. Bytes flow peer-to-peer.
- **Sender online**: Yes — sender's tab must stay open. Multiple downloads supported while tab open.
- **Max size**: No hard cap; browser memory / connection-bound.
- **License/activity**: BSD-3, ~9.9k stars (Feb 2026), actively maintained.
- **Operator can see**: Signaling metadata (IPs, session token, file name unless modified). No file bytes.
- **Differentiator**: The reference "stay-online browser P2P" tool. Requires recipient to load the FilePizza webapp.

### 3. ToffeeShare — toffeeshare.com
- **URL**: https://toffeeshare.com (closed source)
- **Architecture**: WebRTC P2P browser-to-browser, signaling via the site.
- **Encryption**: DTLS 1.3 (WebRTC native). No app-layer E2E layer published.
- **Persistence**: None. Streamed P2P.
- **Sender online**: Yes — closing the tab terminates the transfer.
- **Max size**: Advertised "no limit"; bound by connection.
- **License/activity**: Proprietary SaaS, free tier.
- **Operator can see**: Signaling metadata; no file bytes if NAT traversal succeeds (TURN fallback would expose ciphertext bytes).
- **Differentiator**: The polished commercial FilePizza analog with no size cap.

### 4. WebWormhole — `saljam/webwormhole`
- **URL**: https://github.com/saljam/webwormhole · https://webwormhole.io
- **Architecture**: WebRTC P2P with PAKE (SPAKE2) handshake derived from a short code. Browser app + Go signaling server.
- **Encryption**: PAKE-derived key on top of DTLS — true E2E independent of TURN.
- **Persistence**: None.
- **Sender online**: Yes. Both peers must be present for the handshake.
- **Max size**: Browser-bound.
- **License/activity**: BSD-3, ~4k stars, low recent activity (still functional).
- **Operator can see**: Signaling metadata + ciphertext if TURN-relayed; PAKE key never leaves either client.
- **Differentiator**: Magic Wormhole's PAKE UX, in the browser.

### 5. Reep.io — reep.io
- **URL**: https://reep.io (closed source)
- **Architecture**: WebRTC P2P, browser-to-browser, signaling SaaS.
- **Encryption**: WebRTC DTLS.
- **Persistence**: None.
- **Sender online**: Yes.
- **Max size**: No documented limit.
- **License/activity**: Proprietary, long-running but minimal updates.
- **Operator can see**: Signaling metadata; no file bytes (assuming P2P succeeds).
- **Differentiator**: Pre-FilePizza-era SaaS, still works.

### 6. JustBeamIt, drop.lol, blymp.io, ShareDrop (`cowbell/sharedrop`)
- All WebRTC P2P, sender stays online, transfer initiated when recipient hits a generated URL or joins a room. ShareDrop ~9k stars, Apache-2.0, Firebase signaling, LAN+room model.
- **Operator can see**: Signaling only; no bytes (modulo TURN).
- **Differentiator**: Variations on the FilePizza pattern with different UX (room codes, LAN discovery, drag-and-drop UI).

### 7. PairDrop — `schlagmichdoch/PairDrop`, Snapdrop — `RobinLinus/snapdrop`
- **URL**: https://github.com/schlagmichdoch/PairDrop · pairdrop.net · https://github.com/RobinLinus/snapdrop
- **Architecture**: WebRTC P2P with WebSocket signaling. Auto-pairing within same public IP (LAN-style) plus pairing-code/room link for cross-network.
- **Encryption**: WebRTC DTLS.
- **Persistence**: None.
- **Sender online**: Yes (both peers).
- **Max size**: Browser-bound.
- **License/activity**: GPL-3.0; PairDrop ~7k stars and active; Snapdrop ~18k stars but maintenance moved to PairDrop.
- **Operator can see**: Signaling metadata; no bytes.
- **Differentiator**: AirDrop-style UX in a browser.

---

## B. Sender-online, native CLI (same conceptual model, not browser)

### 8. Magic Wormhole — `magic-wormhole/magic-wormhole`
- **URL**: https://github.com/magic-wormhole/magic-wormhole
- **Architecture**: PAKE handshake via mailbox server, then transit relay (or direct connection) for bulk bytes. Python CLI.
- **Encryption**: SPAKE2-derived NaCl SecretBox; mailbox/transit see only ciphertext.
- **Persistence**: None on relays — they buffer in memory only.
- **Sender online**: Yes.
- **Max size**: Unlimited.
- **License/activity**: MIT, ~20k stars, active.
- **Operator can see**: Mailbox sees connection metadata + handshake nonces; transit sees ciphertext bytes + IPs.
- **Differentiator**: The PAKE-code UX standard. Inspired most others in this list.

### 9. croc — `schollz/croc`
- **URL**: https://github.com/schollz/croc
- **Architecture**: PAKE handshake via relay, AES-256-GCM bulk transfer. Go CLI.
- **Encryption**: PAKE-derived AES-256-GCM E2E.
- **Persistence**: None on relay (memory buffer).
- **Sender online**: Yes.
- **Max size**: Unlimited.
- **License/activity**: MIT, ~30k stars, very active.
- **Operator can see**: Ciphertext + IPs.
- **Differentiator**: Single static binary, cross-platform, resumable.

---

## C. Server-stored, encrypted-at-rest, key-in-URL-fragment (sender CAN go offline)

### 10. timvisee/send — `timvisee/send`
- **URL**: https://github.com/timvisee/send · https://send.vis.ee
- **Architecture**: Browser uploads ciphertext to Node server; recipient downloads ciphertext + decrypts in browser. Self-hostable.
- **Encryption**: AES-128-GCM, key derived in browser, embedded in URL fragment (`#key=...`) — never sent to server.
- **Persistence**: Server stores ciphertext until first download or TTL (default 24h, configurable). S3-compatible backends.
- **Sender online**: **No**. Sender uploads and walks away.
- **Max size**: Configurable (default 1 GB; instances offer up to 20 GB).
- **License/activity**: MPL-2.0, ~5.6k stars, active in 2026 (mirror of GitLab repo). Companion CLI `ffsend` v0.2.77 (Feb 2026).
- **Operator can see**: Ciphertext, file size, upload/download IPs, expiry — never the key or plaintext.
- **Differentiator**: The community-maintained Firefox Send. Async (sender offline) + true E2E.

### 11. Wormhole.app — Socket Inc.
- **URL**: https://wormhole.app (proprietary; uses open-source `wormhole-crypto` on npm)
- **Architecture**: Hybrid — files <=5 GB encrypted-at-rest on Cloudflare-fronted servers for 24h; files >5 GB use WebRTC P2P (sender must stay online for those).
- **Encryption**: AES-128-GCM in-browser, key in URL fragment. Streaming encryption.
- **Persistence**: Encrypted blob on server for 24h, then deleted.
- **Sender online**: No (for <=5 GB), Yes (for >5 GB P2P mode).
- **Max size**: 10 GB upload, but only first 5 GB stored; >5 GB P2P only.
- **License/activity**: SaaS proprietary; crypto lib MIT.
- **Operator can see**: Ciphertext, IPs, ciphertext size; never the key or plaintext.
- **Differentiator**: Most polished UX in the Send-replacement category, sender can disconnect.

### 12. Gokapi, 1time.io, Lufi, PrivateBin's file mode
- Self-hosted Send-style encrypted blob stores. Various server backends (S3, local FS). All key-in-fragment, sender-can-leave, server-stored ciphertext. Maturity varies; Gokapi (~1.5k stars, MIT) is the most active.

---

## D. Mozilla Send (historical baseline)

### 13. Mozilla Send (discontinued)
- **URL**: https://github.com/mozilla/send (archived 2020)
- Defined the "key-in-URL-fragment + server-stored ciphertext + auto-expiry" pattern. Discontinued after abuse concerns. timvisee/send is the canonical successor.

---

## E. Closed-source SaaS, hybrid relay+cloud

### 14. Send Anywhere — sendanywhere.com (Estmob)
- **Architecture**: 6-digit code; hybrid direct-P2P or cloud-relay fallback.
- **Encryption**: Claims E2E for direct mode; cloud-relay mode uses TLS only.
- **Persistence**: Direct: none. Link/email: stored on Estmob servers ~48h.
- **Sender online**: Required for direct/key-code mode; not required for link mode.
- **License/activity**: Proprietary, freemium.
- **Operator can see**: In link mode, ciphertext at minimum, possibly plaintext (no public crypto spec). In direct-code mode, signaling metadata only.
- **Differentiator**: Mobile-first, large user base, but opaque crypto.

---

## Relay leak audit: what the current PoC's relay actually sees

Before claiming "E2E by construction," it is worth auditing what the routing layer can observe today. Reviewing `browser-local-compute-runtime-poc/cloudflare-worker/index.js` and `relay/server.mjs`, every `/portal/<sessionId>/*` request is serialized inside the relay as:

```json
{
  "type": "request",
  "requestId": "...",
  "method": "POST",
  "path": "/upload",
  "query": "...",
  "headers": { /* every caller header, verbatim */ },
  "body": "<base64 of raw bytes>"
}
```

That JSON is built **inside** the Cloudflare Worker (or Node relay) — TLS terminates at the relay, not at the browser tab. So the relay sees in plaintext:

- The full HTTP request body (base64 is encoding, not encryption).
- The full HTTP response body the browser sends back.
- Every caller HTTP header, including `Cookie`, `Authorization`, `Content-Disposition` (filename), `Content-Type`.
- Caller IP (`cf-connecting-ip` / `x-forwarded-for`).
- Session ID (links sender and recipient to each other).
- Timing and byte counts.

**As written, the PoC is not E2E-encrypted.** It is "trust the relay operator with everything." Anyone with access to the Worker, Durable Object inspector, Cloudflare observability/logs, or upstream taps inside CF's edge sees content, filenames, and both IPs.

### What it would take to make it actually E2E

1. Encrypt in the sender's tab before the request leaves the browser (WebCrypto AES-GCM or libsodium sealed box). The relay forwards ciphertext.
2. Put the symmetric key in the **URL fragment** (`https://.../portal/<id>#k=<base64key>`). Browsers do not include the fragment in HTTP requests by spec, so the relay never sees it. Same trick Mozilla Send / Wormhole.app / timvisee/send use.
3. Encrypt metadata (filename, content-type, size) into a dedicated header blob — otherwise it leaks via HTTP headers.
4. Tighten the relay code to forward only an allowlisted minimal header set rather than `Object.fromEntries(request.headers.entries())`.

### Irreducible metadata leak even after E2E

Even with full E2E payload encryption, the relay still observes:

- Sender + recipient IP addresses.
- Session ID (proves the two parties communicated).
- Ciphertext length (file size, ±padding).
- Timing and request count.
- TLS fingerprint, User-Agent, Accept (unless stripped).

This is the same threat model as Wormhole.app / Send / Magic Wormhole's transit relay: trust the server with routing metadata, not with content. To eliminate IP correlation you'd need Tor (the OnionShare model) or a trusted mixnet — different product, different tradeoffs.

---

## Synthesis: where does our PoC actually fit?

The space is **largely saturated**, but there is one structurally distinct gap. Every browser-based "sender-stays-online" tool above (FilePizza, ToffeeShare, WebWormhole, ShareDrop, PairDrop, Reep) requires the **recipient to load a JavaScript webapp** so a WebRTC peer connection can be negotiated. Every "no-app-on-recipient" tool (timvisee/send, Wormhole.app) requires the **server to hold ciphertext at rest**. OnionShare gives you tab-as-server-with-public-URL semantics but mandates Tor on both sides.

Our PoC's actual novelty is the **tab-as-tunneled-HTTP-origin** pattern: the sender's tab is reachable at a clearnet `https://` URL via an outbound WebSocket tunnel, so the recipient just runs `curl -O` (or any HTTP client, embedded device, script). That combination — sender-stays-online + nothing-stored-server-side + recipient-needs-no-app + clearnet URL — is genuinely uncovered. It is OnionShare-without-Tor with the addressable-by-any-HTTP-client property. The downside is exactly what makes the niche small: most users want the opposite (sender disconnects, recipient has a webapp). If you want a turnkey fix today, ship FilePizza/PairDrop or self-host timvisee/send. If the use case is delivering bytes to non-browser HTTP clients without ever persisting them, the PoC fills a real gap.

## Sources

- [FilePizza GitHub](https://github.com/kern/filepizza)
- [ToffeeShare overview](https://www.notionblogs.com/blog/what-is-toffeeshare-and-how-does-it-work/)
- [timvisee/send GitHub](https://github.com/timvisee/send)
- [ffsend releases (Feb 2026)](https://github.com/timvisee/ffsend/releases)
- [Wormhole.app FAQ](https://wormhole.app/faq)
- [Wormhole.app security](https://wormhole.app/security)
- [wormhole-crypto on npm](https://socket.dev/npm/package/wormhole-crypto)
- [Magic Wormhole GitHub](https://github.com/magic-wormhole/magic-wormhole)
- [croc GitHub](https://github.com/schollz/croc)
- [OnionShare](https://onionshare.org)
- [WebWormhole](https://github.com/saljam/webwormhole)
- [PairDrop](https://github.com/schlagmichdoch/PairDrop)
- [Snapdrop](https://github.com/RobinLinus/snapdrop)
- [ShareDrop](https://github.com/cowbell/sharedrop)
