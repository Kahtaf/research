# Reverse Blind Relay

Raw TCP relay for the browser-local MCP PoC. It lets normal HTTPS clients reach
a server running inside a browser tab while keeping HTTP and MCP payloads opaque
to the relay.

## Role

The relay:

- Accepts browser sessions over WebSocket:
  `GET /browser/:sessionId`.
- Accepts public TCP on `443`.
- Peeks only at TLS SNI to map a public connection to a browser session.
- Forwards framed opaque bytes between the TCP socket and browser WebSocket.
- Issues ACME certificates for browser-generated CSRs when configured.

The relay does not parse HTTP, MCP JSON, tool arguments, textarea content, or
browser responses.

## Current VM

```text
project: corsali-development
zone: us-central1-a
name: browser-local-reverse-relay
machine: e2-micro
disk: 10GB pd-standard
external IP: 34.16.49.200
service: browser-local-reverse-relay.service
```

Endpoints:

```text
control WSS: wss://control.34.16.49.200.sslip.io:8443/browser/<sessionId>
public HTTPS: https://<sessionId>.34.16.49.200.sslip.io
health:      http://34.16.49.200:8080/health
```

## Protocol

Browser registration:

```text
GET /browser/:sessionId
Upgrade: websocket
```

Control frames are JSON text messages:

```json
{ "type": "stream.open", "streamId": 1, "sessionId": "abc", "sni": "abc.example.com" }
{ "type": "stream.close", "streamId": 1, "reason": "tcp_closed" }
```

Data frames are binary WebSocket messages:

```text
byte 0      frame type, currently 1
bytes 1-4  uint32 stream id, big endian
bytes 5..  opaque stream bytes
```

## ACME Issuer

Endpoint:

```text
POST /issue-cert
```

Request:

```json
{
  "sessionId": "abc123",
  "issueToken": "<session-ready-token>",
  "csrPem": "-----BEGIN CERTIFICATE REQUEST-----..."
}
```

The relay validates that:

- The browser session is connected.
- The issue token matches the active session.
- The CSR contains only the expected session hostname.

The browser keeps the TLS private key. The relay sees only the CSR and the
issued certificate chain.

## Environment

VM defaults used by the deploy script:

```bash
PROJECT=corsali-development
ZONE=us-central1-a
INSTANCE=browser-local-reverse-relay
MACHINE_TYPE=e2-micro
TCP_PORT=443
HTTP_PORT=8080
CONTROL_TLS_PORT=8443
SESSION_HOST_SUFFIX=34.16.49.200.sslip.io
PUBLIC_CERT_HOST_SUFFIX=34.16.49.200.sslip.io
ACME_CHALLENGE_MODE=http-01
ACME_HTTP_PORT=80
ACME_DIRECTORY_URL=https://acme-v02.api.letsencrypt.org/directory
ACME_EMAIL=<email>
ACME_TERMS_AGREED=true
```

Production-style DNS setup:

```text
*.mcp.example.com -> VM public IP
```

Production-style DNS-01 env:

```bash
SESSION_HOST_SUFFIX=.mcp.example.com
PUBLIC_CERT_HOST_SUFFIX=.mcp.example.com
ACME_CHALLENGE_MODE=dns-01
CLOUDFLARE_ZONE_ID=<zone-id>
CLOUDFLARE_API_TOKEN=<dns-edit-token>
```

## Commands

Install and build:

```bash
npm install
npm run build
```

Run locally:

```bash
npm run dev
```

Run local smoke test:

```bash
npm run smoke
```

Deploy the VM from the project root:

```bash
npm run reverse-relay:deploy:gcp-vm
```

## Why Not Cloud Run For The Final Relay

Cloud Run is useful for HTTP and WebSocket control-plane testing, but it
terminates public HTTPS before traffic reaches the container and does not expose
raw TCP listeners. A normal MCP client needs a normal HTTPS URL whose TLS
session terminates in the browser. That requires raw TCP ingress on a VM or
equivalent TCP load balancer target.
