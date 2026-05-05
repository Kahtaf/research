import http from "node:http";
import https from "node:https";
import fs from "node:fs";
import net from "node:net";
import { URL } from "node:url";

import { WebSocketServer, type RawData, type WebSocket } from "ws";

import { decodeDataFrame, encodeDataFrame } from "./frame.js";
import { parseSniFromClientHello, sessionIdFromSni } from "./sni.js";
import type { BrowserSession, ControlMessage } from "./types.js";

const HTTP_PORT = Number(process.env.PORT ?? 8080);
const CONTROL_TLS_PORT = Number(process.env.CONTROL_TLS_PORT ?? 0);
const CONTROL_TLS_CERT_FILE = process.env.CONTROL_TLS_CERT_FILE ?? "";
const CONTROL_TLS_KEY_FILE = process.env.CONTROL_TLS_KEY_FILE ?? "";
const TCP_PORT = Number(process.env.TCP_PORT ?? 0);
const MAX_CLIENT_HELLO_BYTES = Number(process.env.MAX_CLIENT_HELLO_BYTES ?? 16_384);
const CLIENT_HELLO_TIMEOUT_MS = Number(process.env.CLIENT_HELLO_TIMEOUT_MS ?? 5_000);
const SESSION_HOST_SUFFIX = process.env.SESSION_HOST_SUFFIX ?? "";

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
  const url = new URL(req.url ?? "/", `http://${req.headers.host}`);

  if (url.pathname === "/health") {
    sendJson(res, 200, {
      ok: true,
      role: "reverse-blind-relay",
      sessions: sessions.size,
      tcpIngressEnabled: TCP_PORT > 0,
      controlTlsEnabled: CONTROL_TLS_PORT > 0,
      cloudRunNote:
        "Cloud Run can host HTTP/WebSocket control, but true normal-client blind MCP needs raw TCP ingress outside Cloud Run.",
    });
    return;
  }

  if (url.pathname === "/sessions") {
    sendJson(res, 200, { sessions: sessionStats() });
    return;
  }

  sendJson(res, 404, {
    error: "not_found",
    browserWebSocket: "/browser/:sessionId",
  });
};

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
  });
});

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
