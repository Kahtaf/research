# E2E File Sharing Survey - Working Notes

## Hypothetical product
- Sender's browser tab acts as ephemeral HTTP server via outbound WebSocket to Cloudflare relay
- Relay exposes public URL, routes ciphertext only
- E2E from sender browser to recipient browser
- Never persisted; sender tab IS the server
- Tab close = transfer dies

## Findings summary (one-liner each)

- **timvisee/send**: server-stored encrypted blob, key in URL fragment, ~5.6k stars, MPL-2.0. Sender CAN go offline. Closest in spirit to Firefox Send. NOT sender-online.
- **FilePizza**: WebRTC P2P, sender MUST stay online (tab open), 9.5k stars, BSD-3. Closest match to our model in browser-only space.
- **PairDrop / Snapdrop**: WebRTC P2P, both peers online, signaling via WebSocket, room-based. Built for LAN airdrop UX. Both peers online.
- **OnionShare**: Native app, runs onion service locally, sender stays online, but Tor not browser. Conceptually identical "your computer is the server" pattern.
- **wormhole.app (Socket Inc.)**: Server-stored encrypted (10GB, 24h), AES-128-GCM, key in URL fragment. Not P2P at all. Not sender-online.
- **Magic Wormhole**: CLI tool, PAKE codes, transit relay, sender online. Not browser.
- **croc**: CLI tool, PAKE codes, relay, AES-256, sender online. Not browser.
- **WebWormhole (saljam)**: WebRTC, PAKE in browser, sender online. Closest "magic wormhole in browser". Less active.
- **ToffeeShare**: WebRTC, no size limit, sender stays online, free SaaS. Closed source. Closest commercial analog.
- **Reep.io**: WebRTC, sender online. Old but works.
- **ShareDrop (cowbell)**: WebRTC P2P, Firebase signaling, room URL or LAN. Both peers online.
- **Send Anywhere (Estmob)**: hybrid P2P + cloud relay, 6-digit codes, closed source proprietary.
- **JustBeamIt**: WebRTC, sender online, transfer starts only when recipient hits link.
- **drop.lol**: WebRTC + TURN relay, sender online.
- **blymp.io**: WebRTC + WebSockets browser app.
- **Gokapi**: self-hosted Firefox Send replacement, server-stored, AWS S3 backend.
- **1time.io**: AES-256-GCM Firefox Send replacement, self-hostable.

## Architecture buckets

### A. Sender-stays-online, browser-only, WebRTC (closest to our model)
FilePizza, ToffeeShare, WebWormhole, Reep.io, JustBeamIt, drop.lol, blymp.io,
ShareDrop (P2P browser cousin)

### B. Sender-stays-online, native app (same conceptual model)
OnionShare (Tor onion), Magic Wormhole CLI, croc CLI

### C. Server-stored, encrypted at rest, key in URL fragment
timvisee/send, wormhole.app, Gokapi, 1time.io

### D. Local network only / discovery
Snapdrop, PairDrop, ShareDrop (LAN room), AirDrop

## Differentiator analysis for our PoC

What's unique about our architecture:
1. Sender tab as HTTP server with PUBLIC URL — not a WebRTC handshake to a peer
2. The relay is just a Cloudflare worker, not Firebase/STUN/TURN
3. Recipient does NOT need a special webapp — they just hit a URL

Closest precedent: OnionShare (your computer IS the server, public URL),
but ours runs in a browser tab, no Tor, public clearnet URL.

Compared to FilePizza/ToffeeShare: those still use WebRTC to negotiate a
peer connection. The recipient runs a webapp. Ours has the sender act
as an actual addressable HTTP origin via tunnel.

Comparable pattern: like running `ngrok http :8080` BUT inside a browser
tab. That's the genuinely novel piece — browser-tab-as-tunneled-origin.

## Saturation conclusion
Browser-based ephemeral E2E file transfer is well-saturated.
- If you want server-stored + key-in-URL: use Wormhole.app or self-host timvisee/send.
- If you want sender-online WebRTC P2P: use FilePizza or ToffeeShare.
- The genuinely empty quadrant: tab-as-tunneled-HTTP-origin so the recipient
  uses NO app at all (just curl or a browser opening a URL).
  This is OnionShare-without-Tor-and-without-installing-anything. Plausible niche.
