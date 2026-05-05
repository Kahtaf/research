# Reverse Blind Relay

This is a separate relay prototype for the browser-local MCP demo. It is meant
to replace the Cloudflare `/portal/:sessionId/mcp` relay path with an
Embrowse-style byte relay where the public relay does not parse HTTP or MCP.

## What It Does

- Browser tab opens an outbound WebSocket:

  ```text
  /browser/:sessionId
  ```

- Public client connections are represented as opaque streams and forwarded to
  that browser WebSocket.
- Stream bytes are framed as binary WebSocket messages. The relay can log
  stream open/close and byte counts, but it does not parse HTTP, MCP JSON, or
  browser-local text.
- Optional raw TCP ingress can accept TLS ClientHello, route by SNI, and forward
  the encrypted TLS stream to the browser.

## Recommended Target: VM Or TCP Load Balancer

A regular VM is the better deployment target for the real blind MCP relay.

The reason is straightforward: a normal MCP client expects a normal HTTPS URL,
and the relay must not terminate that HTTPS. The relay needs to accept raw TCP on
`443`, peek only at TLS SNI to find the browser session, and forward the opaque
TLS stream to the browser tab.

On a VM, run:

```bash
PORT=8080 TCP_PORT=443 SESSION_HOST_SUFFIX=.mcp.example.com npm start
```

Then route DNS like:

```text
*.mcp.example.com -> VM public IP
```

The browser session id is the left-most label. For example, a TLS ClientHello
for `abc123.mcp.example.com` routes to browser WebSocket session `abc123`.

## Current GCP VM

The relay is currently deployed on a cheap GCP VM:

```text
project: corsali-development
zone: us-central1-a
name: browser-local-reverse-relay
machine: e2-micro
disk: 10GB pd-standard
external IP: 34.16.49.200
service: browser-local-reverse-relay.service
control WSS: wss://control.34.16.49.200.sslip.io:8443/browser/<sessionId>
```

Health check:

```bash
curl http://34.16.49.200:8080/health
```

Raw TCP ingress is listening on `443`. Until a browser session is registered,
TLS clients connect and then get closed after SNI routing fails.

Browser control WebSocket health:

```bash
curl https://control.34.16.49.200.sslip.io:8443/health
```

Deploy or update the VM:

```bash
npm run reverse-relay:deploy:gcp-vm
```

The deploy script uses these defaults, which can be overridden:

```bash
PROJECT=corsali-development
ZONE=us-central1-a
INSTANCE=browser-local-reverse-relay
MACHINE_TYPE=e2-micro
TCP_PORT=443
HTTP_PORT=8080
CONTROL_TLS_PORT=8443
SESSION_HOST_SUFFIX=
```

The hosted HTTPS browser app must use the secure browser-control WebSocket:

```text
wss://control.34.16.49.200.sslip.io:8443/browser/<sessionId>
```

TLS terminates at the relay only for this browser-control WebSocket. MCP client
traffic still uses raw TCP passthrough on `443`, where TLS terminates in the
browser runtime once that piece exists.

## Cloud Run Boundary

Cloud Run can run this service for the HTTP/WebSocket control plane and the
custom WebSocket ingress:

```text
wss://<cloud-run-host>/browser/:sessionId
wss://<cloud-run-host>/connect/:sessionId
```

That is useful for testing relay session management and opaque byte forwarding.

It is not enough for normal MCP clients. Cloud Run terminates public HTTPS
before the request reaches the container, and Cloud Run does not expose raw TCP
listeners. For a normal URL like:

```text
https://<session>.mcp.example.com/mcp
```

the real blind relay needs raw TCP ingress on a VM or equivalent TCP load
balancer target. The relay then peeks only at TLS SNI for routing and forwards
opaque TLS bytes to the browser, where TLS and MCP terminate.

## Local Development

```bash
cd reverse-blind-relay
npm install
npm run build
npm run smoke
```

Run HTTP/WebSocket mode:

```bash
npm run dev
```

Run with local raw TCP ingress enabled:

```bash
PORT=8080 TCP_PORT=9443 SESSION_HOST_SUFFIX=.mcp.local npm run dev
```

With `SESSION_HOST_SUFFIX=.mcp.local`, a TLS ClientHello for
`abc.mcp.local` routes to browser session `abc`.

## Protocol

Browser registration:

```text
GET /browser/:sessionId
Upgrade: websocket
```

Custom client stream, useful on Cloud Run:

```text
GET /connect/:sessionId
Upgrade: websocket
```

Control frames are JSON text messages:

```json
{ "type": "stream.open", "streamId": 1, "sessionId": "abc", "sni": "abc.mcp.local" }
{ "type": "stream.close", "streamId": 1, "reason": "tcp_closed" }
```

Data frames are binary messages:

```text
byte 0      frame type, currently 1
bytes 1-4  uint32 stream id, big endian
bytes 5..  opaque stream bytes
```

## Cloud Run Deployment

Build and deploy from this folder:

```bash
gcloud run deploy browser-local-reverse-blind-relay \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --timeout 3600 \
  --no-cpu-throttling \
  --min-instances 1
```

For Artifact Registry builds:

```bash
docker build --platform=linux/amd64 -t us-docker.pkg.dev/<project>/<repo>/browser-local-reverse-blind-relay:latest .
docker push us-docker.pkg.dev/<project>/<repo>/browser-local-reverse-blind-relay:latest
gcloud run deploy browser-local-reverse-blind-relay \
  --image us-docker.pkg.dev/<project>/<repo>/browser-local-reverse-blind-relay:latest \
  --region us-central1 \
  --allow-unauthenticated \
  --timeout 3600 \
  --no-cpu-throttling \
  --min-instances 1
```

## Next Browser-Side Work

The current browser app still expects HTTP request metadata from the old
Cloudflare relay. To use this relay for normal MCP:

1. Add a browser WebSocket client for `/browser/:sessionId`.
2. Add a browser-local TLS server implementation in WASM or a VM-like runtime.
3. Parse HTTP inside the browser after TLS decrypts.
4. Dispatch `/mcp` to the existing MCP text handler.
5. Add a certificate flow where the browser owns the private key and gets a
   CA-trusted certificate for `<session>.mcp.example.com`.
