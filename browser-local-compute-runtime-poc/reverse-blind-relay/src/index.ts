import http from "node:http";
import https from "node:https";
import fs from "node:fs";
import net from "node:net";
import { randomUUID } from "node:crypto";
import { URL } from "node:url";

import { WebSocketServer, type RawData, type WebSocket } from "ws";

import {
  getHttpChallengeResponse,
  isAcmeIssuerConfigured,
  issueCertificate,
} from "./acme-issuer.js";
import { decodeDataFrame, encodeDataFrame } from "./frame.js";
import { parseSniFromClientHello, sessionIdFromSni } from "./sni.js";
import type { BrowserSession, ControlMessage } from "./types.js";

const HTTP_PORT = Number(process.env.PORT ?? 8080);
const ACME_HTTP_PORT = Number(process.env.ACME_HTTP_PORT ?? 0);
const CONTROL_TLS_PORT = Number(process.env.CONTROL_TLS_PORT ?? 0);
const CONTROL_TLS_CERT_FILE = process.env.CONTROL_TLS_CERT_FILE ?? "";
const CONTROL_TLS_KEY_FILE = process.env.CONTROL_TLS_KEY_FILE ?? "";
const TCP_PORT = Number(process.env.TCP_PORT ?? 0);
const MAX_CLIENT_HELLO_BYTES = Number(process.env.MAX_CLIENT_HELLO_BYTES ?? 16_384);
const CLIENT_HELLO_TIMEOUT_MS = Number(process.env.CLIENT_HELLO_TIMEOUT_MS ?? 5_000);
const SESSION_HOST_SUFFIX = process.env.SESSION_HOST_SUFFIX ?? "";
const PUBLIC_CERT_HOST_SUFFIX = process.env.PUBLIC_CERT_HOST_SUFFIX ?? SESSION_HOST_SUFFIX;
const MAX_ISSUE_BODY_BYTES = Number(process.env.MAX_ISSUE_BODY_BYTES ?? 16_384);

const sessions = new Map<string, BrowserSession>();
let nextStreamId = 1;

function log(event: string, fields: Record<string, unknown> = {}): void {
  console.log(JSON.stringify({ event, ...fields }));
}

function sendJson(
  res: http.ServerResponse,
  status: number,
  payload: Record<string, unknown>,
): void {
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
  });
  res.end(JSON.stringify(payload, null, 2));
}

function sendCorsJson(
  res: http.ServerResponse,
  status: number,
  payload: Record<string, unknown>,
): void {
  res.writeHead(status, {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "POST,OPTIONS",
    "access-control-allow-headers": "content-type",
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
  });
  res.end(JSON.stringify(payload, null, 2));
}

function sendControl(session: BrowserSession, message: ControlMessage): void {
  if (session.socket.readyState === session.socket.OPEN) {
    session.socket.send(JSON.stringify(message));
  }
}

function sendData(session: BrowserSession, streamId: number, payload: Buffer): void {
  if (session.socket.readyState === session.socket.OPEN) {
    session.socket.send(encodeDataFrame(streamId, payload));
  }
}

function closeStream(session: BrowserSession, streamId: number, reason: string): void {
  const socket = session.streams.get(streamId);
  if (!socket) {
    return;
  }

  session.streams.delete(streamId);
  socket.destroy();
  sendControl(session, { type: "stream.close", streamId, reason });
}

function closeAllStreams(session: BrowserSession, reason: string): void {
  for (const streamId of session.streams.keys()) {
    closeStream(session, streamId, reason);
  }
}

function sessionStats(): Array<Record<string, unknown>> {
  return Array.from(sessions.values()).map((session) => ({
    sessionId: session.sessionId,
    streams: session.streams.size,
    connectedForMs: Date.now() - session.connectedAt,
  }));
}

const requestHandler: http.RequestListener = (req, res) => {
  void handleRequest(req, res).catch((error: unknown) => {
    log("request_error", { error: error instanceof Error ? error.message : String(error) });
    if (!res.headersSent) {
      sendJson(res, 500, { error: "internal_error" });
    } else {
      res.destroy();
    }
  });
};

async function handleRequest(req: http.IncomingMessage, res: http.ServerResponse): Promise<void> {
  const url = new URL(req.url ?? "/", `http://${req.headers.host}`);

  if (url.pathname === "/health") {
    sendJson(res, 200, {
      ok: true,
      role: "reverse-blind-relay",
      sessions: sessions.size,
      tcpIngressEnabled: TCP_PORT > 0,
      controlTlsEnabled: CONTROL_TLS_PORT > 0,
      acmeIssuerEnabled: isAcmeIssuerConfigured(),
      cloudRunNote:
        "Cloud Run can host HTTP/WebSocket control, but true normal-client blind MCP needs raw TCP ingress outside Cloud Run.",
    });
    return;
  }

  const challenge = url.pathname.match(/^\/\.well-known\/acme-challenge\/([^/]+)$/);
  if (challenge) {
    const keyAuthorization = getHttpChallengeResponse(challenge[1]);
    if (!keyAuthorization) {
      sendJson(res, 404, { error: "challenge_not_found" });
      return;
    }

    res.writeHead(200, {
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "no-store",
    });
    res.end(keyAuthorization);
    return;
  }

  if (url.pathname === "/sessions") {
    sendJson(res, 200, { sessions: sessionStats() });
    return;
  }

  if (url.pathname === "/issue-cert") {
    await handleIssueCert(req, res);
    return;
  }

  sendJson(res, 404, {
    error: "not_found",
    browserWebSocket: "/browser/:sessionId",
  });
}

const httpServer = http.createServer(requestHandler);

const browserWss = new WebSocketServer({ noServer: true });
const clientWss = new WebSocketServer({ noServer: true });

browserWss.on("connection", (socket: WebSocket, req: http.IncomingMessage, context: { sessionId: string }) => {
  const { sessionId } = context;
  const existing = sessions.get(sessionId);
  if (existing) {
    closeAllStreams(existing, "session_replaced");
    existing.socket.close(1012, "session replaced");
  }

  const session: BrowserSession = {
    sessionId,
    socket,
    streams: new Map(),
    connectedAt: Date.now(),
    issueToken: randomUUID(),
  };
  sessions.set(sessionId, session);

  log("browser_connected", {
    sessionId,
    remoteAddress: req.socket.remoteAddress,
  });

  socket.on("message", (raw) => handleBrowserMessage(session, raw));
  socket.on("close", () => {
    if (sessions.get(sessionId) === session) {
      sessions.delete(sessionId);
    }
    closeAllStreams(session, "browser_disconnected");
    log("browser_disconnected", { sessionId });
  });
  socket.on("error", () => {
    closeAllStreams(session, "browser_socket_error");
  });

  sendControl(session, {
    type: "session.ready",
    sessionId,
    issueToken: session.issueToken,
  });
});

async function handleIssueCert(
  req: http.IncomingMessage,
  res: http.ServerResponse,
): Promise<void> {
  if (req.method === "OPTIONS") {
    sendCorsJson(res, 204, {});
    return;
  }

  if (req.method !== "POST") {
    sendCorsJson(res, 405, { error: "method_not_allowed", allowed: ["POST"] });
    return;
  }

  if (!isAcmeIssuerConfigured()) {
    sendCorsJson(res, 503, {
      error: "acme_issuer_not_configured",
      requiredEnv: [
        "ACME_DIRECTORY_URL",
        "ACME_EMAIL",
        "CLOUDFLARE_API_TOKEN",
        "CLOUDFLARE_ZONE_ID",
      ],
    });
    return;
  }

  const body = await readJsonBody(req, MAX_ISSUE_BODY_BYTES);
  const sessionId = typeof body.sessionId === "string" ? body.sessionId : "";
  const csrPem = typeof body.csrPem === "string" ? body.csrPem : "";
  const issueToken = typeof body.issueToken === "string" ? body.issueToken : "";
  const session = sessions.get(sessionId);

  if (!session) {
    sendCorsJson(res, 409, { error: "browser_session_required" });
    return;
  }

  try {
    const certPem = await issueCertificate({
      sessionId,
      csrPem,
      issueToken,
      expectedIssueToken: session.issueToken,
      hostSuffix: PUBLIC_CERT_HOST_SUFFIX,
    });
    sendCorsJson(res, 200, {
      certPem,
      hostname: `${sessionId}.${PUBLIC_CERT_HOST_SUFFIX.replace(/^\./, "")}`,
    });
    log("acme_cert_issued", { sessionId });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    log("acme_issue_failed", { sessionId, error: message });
    sendCorsJson(res, 400, { error: "acme_issue_failed", detail: message });
  }
}

clientWss.on("connection", (clientSocket: WebSocket, req: http.IncomingMessage, context: { sessionId: string }) => {
  const session = sessions.get(context.sessionId);
  if (!session) {
    clientSocket.close(1011, "browser session unavailable");
    return;
  }

  const streamId = allocateStreamId();
  const stream = new WebSocketBackedSocket(clientSocket);
  session.streams.set(streamId, stream);

  log("ws_client_stream_open", {
    sessionId: session.sessionId,
    streamId,
    remoteAddress: req.socket.remoteAddress,
  });

  sendControl(session, {
    type: "stream.open",
    streamId,
    sessionId: session.sessionId,
    remoteAddress: req.socket.remoteAddress,
  });

  clientSocket.on("message", (raw) => {
    const payload = Buffer.isBuffer(raw) ? raw : Buffer.from(raw as ArrayBuffer);
    sendData(session, streamId, payload);
  });
  clientSocket.on("close", () => closeStream(session, streamId, "ws_client_closed"));
  clientSocket.on("error", () => closeStream(session, streamId, "ws_client_error"));
});

function handleUpgrade(
  req: http.IncomingMessage,
  socket: net.Socket,
  head: Buffer,
): void {
  const url = new URL(req.url ?? "/", `http://${req.headers.host}`);
  const browserMatch = url.pathname.match(/^\/browser\/([^/]+)$/);
  const clientMatch = url.pathname.match(/^\/connect\/([^/]+)$/);

  if (browserMatch) {
    browserWss.handleUpgrade(req, socket, head, (ws) => {
      browserWss.emit("connection", ws, req, { sessionId: browserMatch[1] });
    });
    return;
  }

  if (clientMatch) {
    clientWss.handleUpgrade(req, socket, head, (ws) => {
      clientWss.emit("connection", ws, req, { sessionId: clientMatch[1] });
    });
    return;
  }

  socket.destroy();
}

httpServer.on("upgrade", handleUpgrade);

httpServer.listen(HTTP_PORT, () => {
  log("http_listening", {
    port: HTTP_PORT,
    browserWebSocket: "/browser/:sessionId",
    customClientWebSocket: "/connect/:sessionId",
  });
});

if (ACME_HTTP_PORT > 0 && ACME_HTTP_PORT !== HTTP_PORT) {
  http.createServer(requestHandler).listen(ACME_HTTP_PORT, () => {
    log("acme_http_listening", {
      port: ACME_HTTP_PORT,
      challengePath: "/.well-known/acme-challenge/:token",
    });
  });
}

if (CONTROL_TLS_PORT > 0) {
  if (!CONTROL_TLS_CERT_FILE || !CONTROL_TLS_KEY_FILE) {
    throw new Error(
      "CONTROL_TLS_CERT_FILE and CONTROL_TLS_KEY_FILE are required when CONTROL_TLS_PORT is set",
    );
  }

  const httpsServer = https.createServer(
    {
      cert: fs.readFileSync(CONTROL_TLS_CERT_FILE),
      key: fs.readFileSync(CONTROL_TLS_KEY_FILE),
    },
    requestHandler,
  );

  httpsServer.on("upgrade", handleUpgrade);
  httpsServer.listen(CONTROL_TLS_PORT, () => {
    log("control_tls_listening", {
      port: CONTROL_TLS_PORT,
      browserWebSocket: "/browser/:sessionId",
      customClientWebSocket: "/connect/:sessionId",
    });
  });
}

if (TCP_PORT > 0) {
  const tcpServer = net.createServer((socket) => {
    handleTcpIngress(socket).catch((error: unknown) => {
      log("tcp_ingress_error", {
        error: error instanceof Error ? error.message : String(error),
      });
      socket.destroy();
    });
  });

  tcpServer.listen(TCP_PORT, () => {
    log("tcp_listening", {
      port: TCP_PORT,
      sessionHostSuffix: SESSION_HOST_SUFFIX || "(full SNI is session id)",
    });
  });
}

async function handleTcpIngress(socket: net.Socket): Promise<void> {
  const firstBytes = await readClientHello(socket);
  const sni = parseSniFromClientHello(firstBytes);

  if (!sni) {
    log("tcp_rejected", { reason: "missing_sni", remoteAddress: socket.remoteAddress });
    socket.destroy();
    return;
  }

  const sessionId = sessionIdFromSni(sni, SESSION_HOST_SUFFIX);
  const session = sessions.get(sessionId);

  if (!session) {
    log("tcp_rejected", {
      reason: "session_unavailable",
      sni,
      sessionId,
      remoteAddress: socket.remoteAddress,
    });
    socket.destroy();
    return;
  }

  const streamId = allocateStreamId();
  session.streams.set(streamId, socket);

  log("tcp_stream_open", {
    sessionId,
    streamId,
    sni,
    remoteAddress: socket.remoteAddress,
  });

  sendControl(session, {
    type: "stream.open",
    streamId,
    sessionId,
    sni,
    remoteAddress: socket.remoteAddress,
  });
  sendData(session, streamId, firstBytes);

  socket.on("data", (chunk: Buffer | string) => {
    sendData(session, streamId, Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  });
  socket.on("close", () => {
    if (session.streams.get(streamId) === socket) {
      session.streams.delete(streamId);
      sendControl(session, { type: "stream.close", streamId, reason: "tcp_closed" });
      log("tcp_stream_closed", { sessionId, streamId });
    }
  });
  socket.on("error", () => closeStream(session, streamId, "tcp_error"));
}

function handleBrowserMessage(session: BrowserSession, raw: RawData): void {
  if (typeof raw !== "string") {
    const buffer = Array.isArray(raw)
      ? Buffer.concat(raw)
      : Buffer.isBuffer(raw)
        ? raw
        : Buffer.from(raw as ArrayBuffer);
    const frame = decodeDataFrame(buffer);
    if (!frame) {
      return;
    }

    const stream = session.streams.get(frame.streamId);
    if (stream && !stream.destroyed) {
      stream.write(frame.payload);
    }
    return;
  }

  let message: ControlMessage;
  try {
    message = JSON.parse(String(raw)) as ControlMessage;
  } catch {
    return;
  }

  if (message.type === "ping") {
    sendControl(session, { type: "pong" });
    return;
  }

  if (
    (message.type === "stream.close" || message.type === "stream.error") &&
    typeof message.streamId === "number"
  ) {
    closeStream(session, message.streamId, message.type);
  }
}

function allocateStreamId(): number {
  const streamId = nextStreamId;
  nextStreamId += 1;
  if (nextStreamId >= 0xffff_fffe) {
    nextStreamId = 1;
  }
  return streamId;
}

function readJsonBody(
  req: http.IncomingMessage,
  maxBytes: number,
): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    let totalBytes = 0;

    req.on("data", (chunk: Buffer | string) => {
      const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
      totalBytes += buffer.byteLength;
      if (totalBytes > maxBytes) {
        reject(new Error("request_body_too_large"));
        req.destroy();
        return;
      }
      chunks.push(buffer);
    });
    req.on("end", () => {
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString("utf8")) as Record<string, unknown>);
      } catch {
        reject(new Error("invalid_json"));
      }
    });
    req.on("error", reject);
  });
}

function readClientHello(socket: net.Socket): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    let totalBytes = 0;

    const timer = setTimeout(() => {
      cleanup();
      reject(new Error("timed out waiting for TLS ClientHello"));
    }, CLIENT_HELLO_TIMEOUT_MS);

    const cleanup = (): void => {
      clearTimeout(timer);
      socket.off("data", onData);
      socket.off("error", onError);
      socket.off("close", onClose);
    };

    const onData = (chunk: Buffer): void => {
      chunks.push(chunk);
      totalBytes += chunk.length;

      const buffered = Buffer.concat(chunks, totalBytes);
      if (buffered.length >= 5) {
        const recordLength = buffered.readUInt16BE(3);
        if (buffered.length >= 5 + recordLength) {
          cleanup();
          resolve(buffered);
          return;
        }
      }

      if (totalBytes > MAX_CLIENT_HELLO_BYTES) {
        cleanup();
        reject(new Error("ClientHello exceeded maximum buffer"));
      }
    };

    const onError = (error: Error): void => {
      cleanup();
      reject(error);
    };

    const onClose = (): void => {
      cleanup();
      reject(new Error("socket closed before ClientHello"));
    };

    socket.on("data", onData);
    socket.on("error", onError);
    socket.on("close", onClose);
  });
}

class WebSocketBackedSocket extends net.Socket {
  constructor(private readonly ws: WebSocket) {
    super({ readable: false, writable: true });
  }

  override write(
    buffer: Uint8Array | string,
    cb?: (err?: Error | null) => void,
  ): boolean;
  override write(
    str: Uint8Array | string,
    encoding?: BufferEncoding,
    cb?: (err?: Error | null) => void,
  ): boolean;
  override write(
    chunk: Uint8Array | string,
    encodingOrCallback?: BufferEncoding | ((err?: Error | null) => void),
    callback?: (err?: Error | null) => void,
  ): boolean {
    const cb = typeof encodingOrCallback === "function" ? encodingOrCallback : callback;
    if (this.ws.readyState !== this.ws.OPEN) {
      cb?.(new Error("websocket is not open"));
      return false;
    }

    this.ws.send(chunk, cb);
    return true;
  }

  override destroy(error?: Error): this {
    if (this.ws.readyState === this.ws.OPEN || this.ws.readyState === this.ws.CONNECTING) {
      this.ws.close(error ? 1011 : 1000, error?.message);
    }
    return super.destroy(error);
  }
}
