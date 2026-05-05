import forge from "node-forge";
import initRustls, { TlsServer as RustlsServer } from "../browser-tls-rustls/pkg/browser_tls_rustls";
import rustlsWasmUrl from "../browser-tls-rustls/pkg/browser_tls_rustls_bg.wasm?url";

import { incrementRequestCount, readText } from "./storage";
import type { RelayRequest, RuntimeReply } from "./types";

const DATA_FRAME_TYPE = 1;
const HEADER_BYTES = 5;
const DEFAULT_CONTROL_URL = "wss://control.34.16.49.200.sslip.io:8443";
const DEFAULT_PUBLIC_SUFFIX = "34.16.49.200.sslip.io";
const TLS_IDENTITY_CACHE_KEY = "browser-local-tls-identity-v1";

type ReverseRelayOptions = {
  sessionId: string;
  worker: Worker;
  onLog: (line: string) => void;
  onStatus: (status: string) => void;
  onResponse: (body: string) => void;
  onCount: () => void;
  onTlsIdentity: (identity: TlsIdentity) => void;
};

type TlsIdentity = {
  certPem: string;
  keyPem: string;
  hostname: string;
  source: "acme" | "self-signed" | "cached-acme";
  trusted: boolean;
};

type StreamState = {
  streamId: number;
  tls: RustlsServer;
  plaintext: string;
};

type TlsStep = {
  plaintext: Uint8Array;
  tls: Uint8Array;
  handshaking: boolean;
};

let rustlsInitPromise: Promise<unknown> | undefined;

function reverseRelayControlUrl() {
  const configured = import.meta.env.VITE_REVERSE_RELAY_CONTROL_URL as
    | string
    | undefined;
  return (configured || DEFAULT_CONTROL_URL).replace(/\/$/, "");
}

function reverseRelayPublicSuffix() {
  const configured = import.meta.env.VITE_REVERSE_RELAY_PUBLIC_SUFFIX as
    | string
    | undefined;
  return (configured || DEFAULT_PUBLIC_SUFFIX).replace(/^\./, "");
}

export function reverseRelayMcpUrl(sessionId: string) {
  return `https://${sessionId}.${reverseRelayPublicSuffix()}/mcp`;
}

export function reverseRelayApiUrl(sessionId: string) {
  return `https://${sessionId}.${reverseRelayPublicSuffix()}/api/process?input=hello`;
}

export function reverseRelayApiCurlCommand(sessionId: string, trustedTls = false) {
  const host = `${sessionId}.${reverseRelayPublicSuffix()}`;
  return `curl ${trustedTls ? "" : "-k "} -sS https://${host}/api/process?input=hello`.replace(
    "  ",
    " ",
  );
}

export function reverseRelayMcpCurlCommand(sessionId: string, trustedTls = false) {
  const host = `${sessionId}.${reverseRelayPublicSuffix()}`;
  return `curl ${trustedTls ? "" : "-k "} -sS https://${host}/mcp \\\n  -H 'content-type: application/json' \\\n  -H 'mcp-protocol-version: 2025-06-18' \\\n  --data '{\"jsonrpc\":\"2.0\",\"id\":\"stats-1\",\"method\":\"tools/call\",\"params\":{\"name\":\"get_text_stats\",\"arguments\":{}}}'`.replace(
    "  ",
    " ",
  );
}

export async function startReverseRelayClient(options: ReverseRelayOptions) {
  const controlUrl = reverseRelayControlUrl();
  const browserUrl = `${controlUrl}/browser/${options.sessionId}`;
  const streams = new Map<number, StreamState>();
  const pendingStreamData = new Map<number, Uint8Array[]>();
  const pending = new Map<string, (reply: RuntimeReply) => void>();

  let identity: TlsIdentity | undefined;
  let identityPromise: Promise<TlsIdentity> | undefined;
  let socket: WebSocket | undefined;
  let heartbeat: number | undefined;
  let reconnectTimer: number | undefined;
  let reconnectAttempt = 0;
  let stopped = false;

  options.worker.onmessage = (event: MessageEvent<RuntimeReply>) => {
    const reply = event.data;
    const requestId = reply.requestId;
    if (!requestId) {
      if (reply.type === "runtime-error") {
        options.onLog(`worker: ${reply.message}`);
      }
      return;
    }

    const resolve = pending.get(requestId);
    if (resolve) {
      pending.delete(requestId);
      resolve(reply);
    }
  };

  const sendText = (message: unknown) => {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    }
  };

  const sendData = (streamId: number, payloadBytes: Uint8Array) => {
    if (socket?.readyState !== WebSocket.OPEN) {
      return;
    }

    const frame = new Uint8Array(HEADER_BYTES + payloadBytes.length);
    frame[0] = DATA_FRAME_TYPE;
    writeUint32(frame, 1, streamId);
    frame.set(payloadBytes, HEADER_BYTES);
    socket.send(frame);
  };

  const closeStream = (streamId: number, reason: string) => {
    const stream = streams.get(streamId);
    stream?.tls.free();
    streams.delete(streamId);
    pendingStreamData.delete(streamId);
    sendText({ type: "stream.close", streamId, reason });
  };

  const handleTlsStep = (stream: StreamState, step: TlsStep) => {
    if (step.tls.length > 0) {
      sendData(stream.streamId, step.tls);
    }
    if (step.plaintext.length > 0) {
      stream.plaintext += new TextDecoder().decode(step.plaintext);
      void drainHttpRequests(stream).catch((error) => {
        options.onLog(error instanceof Error ? error.message : String(error));
        closeStream(stream.streamId, "handler_error");
      });
    }
  };

  const createTlsStream = async (streamId: number, tlsIdentity: TlsIdentity): Promise<StreamState> => {
    await ensureRustls();
    const stream: StreamState = {
      streamId,
      plaintext: "",
      tls: new RustlsServer(tlsIdentity.certPem, tlsIdentity.keyPem),
    };
    options.onLog(`rustls stream ${streamId} ready`);
    return stream;
  };

  const openStreamAfterIdentity = async (streamId: number) => {
    const tlsIdentity = identity ?? (await identityPromise);
    if (!tlsIdentity) {
      options.onLog(`stream ${streamId} rejected before TLS identity was ready`);
      closeStream(streamId, "tls_identity_unavailable");
      return;
    }
    const stream = await createTlsStream(streamId, tlsIdentity);
    streams.set(streamId, stream);
    options.onLog(`stream ${streamId} opened`);
    const buffered = pendingStreamData.get(streamId) ?? [];
    pendingStreamData.delete(streamId);
    for (const payload of buffered) {
      processTlsPayload(stream, payload);
    }
  };

  const handleControl = async (message: { type: string; streamId?: number; issueToken?: string }) => {
    if (message.type === "session.ready") {
      options.onStatus("Requesting TLS cert");
      identityPromise = createTlsIdentity(
        options.sessionId,
        controlUrl,
        message.issueToken ?? "",
        options.onLog,
      );
      identity = await identityPromise;
      options.onTlsIdentity(identity);
      options.onStatus("Connected");
      options.onLog(
        `reverse relay connected with ${identity.source} certificate for ${identity.hostname}`,
      );
      return;
    }

    if (message.type === "pong") {
      return;
    }

    if (message.type === "stream.open" && typeof message.streamId === "number") {
      void openStreamAfterIdentity(message.streamId).catch((error) => {
        options.onLog(error instanceof Error ? error.message : String(error));
        if (typeof message.streamId === "number") {
          closeStream(message.streamId, "tls_identity_error");
        }
      });
      return;
    }

    if (message.type === "stream.close" && typeof message.streamId === "number") {
      streams.delete(message.streamId);
      options.onLog(`stream ${message.streamId} closed`);
    }
  };

  const handleData = (data: ArrayBuffer) => {
    const frame = new Uint8Array(data);
    if (frame.length < HEADER_BYTES || frame[0] !== DATA_FRAME_TYPE) {
      return;
    }

    const streamId = readUint32(frame, 1);
    const payload = frame.slice(HEADER_BYTES);
    const stream = streams.get(streamId);
    if (!stream) {
      const buffered = pendingStreamData.get(streamId) ?? [];
      buffered.push(payload);
      pendingStreamData.set(streamId, buffered);
      return;
    }

    processTlsPayload(stream, payload);
  };

  const processTlsPayload = (stream: StreamState, payload: Uint8Array) => {
    try {
      handleTlsStep(stream, normalizeTlsStep(stream.tls.process_tls(payload)));
    } catch (error) {
      options.onLog(
        `rustls stream ${stream.streamId} error: ${error instanceof Error ? error.message : String(error)}`,
      );
      closeStream(stream.streamId, "tls_error");
    }
  };

  const shouldConnect = () =>
    !stopped && document.visibilityState === "visible";

  const clearHeartbeat = () => {
    if (heartbeat) {
      window.clearInterval(heartbeat);
      heartbeat = undefined;
    }
  };

  const scheduleReconnect = () => {
    if (!shouldConnect() || reconnectTimer) {
      return;
    }

    const delay = Math.min(1000 * 2 ** reconnectAttempt, 15_000);
    reconnectAttempt += 1;
    options.onStatus("Reconnecting");
    options.onLog(`reverse reconnect scheduled in ${delay}ms`);
    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = undefined;
      connect();
    }, delay);
  };

  const disconnect = (reason: string) => {
    clearHeartbeat();
    streams.clear();
    if (
      socket?.readyState === WebSocket.OPEN ||
      socket?.readyState === WebSocket.CONNECTING
    ) {
      socket.close(1000, reason);
    }
    socket = undefined;
  };

  const connect = () => {
    if (!shouldConnect()) {
      disconnect("hidden");
      options.onStatus("Paused");
      return;
    }

    if (
      socket?.readyState === WebSocket.OPEN ||
      socket?.readyState === WebSocket.CONNECTING
    ) {
      return;
    }

    options.onStatus(reconnectAttempt > 0 ? "Reconnecting" : "Connecting");
    socket = new WebSocket(browserUrl);
    socket.binaryType = "arraybuffer";

    socket.onopen = () => {
      reconnectAttempt = 0;
      clearHeartbeat();
      heartbeat = window.setInterval(() => sendText({ type: "ping" }), 15_000);
    };

    socket.onmessage = (event) => {
      if (typeof event.data === "string") {
        void handleControl(
          JSON.parse(event.data) as { type: string; streamId?: number; issueToken?: string },
        ).catch((error) => {
          options.onStatus("TLS cert error");
          options.onLog(error instanceof Error ? error.message : String(error));
        });
        return;
      }
      handleData(event.data as ArrayBuffer);
    };

    socket.onclose = () => {
      clearHeartbeat();
      streams.clear();
      pendingStreamData.clear();
      socket = undefined;
      if (stopped) {
        return;
      }
      if (document.visibilityState !== "visible") {
        options.onStatus("Paused");
        options.onLog("reverse relay paused while tab is hidden");
        return;
      }
      options.onStatus("Disconnected");
      options.onLog("reverse relay disconnected");
      scheduleReconnect();
    };

    socket.onerror = () => {
      options.onStatus("Connection error");
      options.onLog("reverse relay websocket error");
      scheduleReconnect();
    };
  };

  const handleVisibilityChange = () => {
    if (document.visibilityState === "visible") {
      reconnectAttempt = 0;
      connect();
      return;
    }
    disconnect("hidden");
    options.onStatus("Paused");
  };

  const dispatchRuntime = async (request: RelayRequest): Promise<RuntimeReply> =>
    new Promise((resolve) => {
      pending.set(request.requestId, resolve);
      options.worker.postMessage({ type: "handle", request });
    });

  const handleBrowserApi = async (request: ParsedHttpRequest) => {
    const input = request.url.searchParams.get("input") ?? "";
    const text = (await readText()) ?? "";
    const requestCount = await incrementRequestCount();
    const hash = await sha256Hex(input);
    return {
      input,
      result: `${input.toUpperCase()}-${hash.slice(0, 12)}`,
      textChars: text.length,
      requestCount,
      storage: "IndexedDB",
      runtime: "browser-local TLS server",
      servedFrom: "browser-tab",
      relay: "blind TCP passthrough",
      timestamp: new Date().toISOString(),
    };
  };

  const handleHttpRequest = async (request: ParsedHttpRequest) => {
    if (request.url.pathname === "/api/process") {
      const payload = await handleBrowserApi(request);
      options.onCount();
      return httpJson(200, payload);
    }

    if (request.url.pathname === "/mcp") {
      const runtimeRequest: RelayRequest = {
        type: "request",
        requestId: crypto.randomUUID(),
        method: request.method,
        path: request.url.pathname,
        query: request.url.searchParams.toString(),
        headers: request.headers,
        body: btoa(request.body),
      };
      const reply = await dispatchRuntime(runtimeRequest);
      if (reply.type === "runtime-error") {
        return httpJson(500, { error: reply.message });
      }
      options.onResponse(reply.response.body);
      options.onCount();
      return httpResponse(reply.response.status, reply.response.headers, reply.response.body);
    }

    return httpJson(404, { error: "not_found", routes: ["/api/process", "/mcp"] });
  };

  const drainHttpRequests = async (stream: StreamState) => {
    while (true) {
      const parsed = parseHttpRequest(stream.plaintext);
      if (!parsed) {
        return;
      }

      stream.plaintext = stream.plaintext.slice(parsed.consumedBytes);
      options.onLog(`${parsed.request.method} ${parsed.request.url.pathname}`);
      const response = await handleHttpRequest(parsed.request);
      const step = normalizeTlsStep(stream.tls.write_plaintext(binaryToBytes(response), true));
      if (step.tls.length > 0) {
        sendData(stream.streamId, step.tls);
      }
      closeStream(stream.streamId, "http_response_sent");
      return;
    }
  };

  document.addEventListener("visibilitychange", handleVisibilityChange);
  connect();

  return {
    close() {
      stopped = true;
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      if (reconnectTimer) {
        window.clearTimeout(reconnectTimer);
      }
      disconnect("closed");
    },
  };
}

type ParsedHttpRequest = {
  method: string;
  url: URL;
  headers: Record<string, string>;
  body: string;
};

function parseHttpRequest(buffer: string):
  | { request: ParsedHttpRequest; consumedBytes: number }
  | undefined {
  const headerEnd = buffer.indexOf("\r\n\r\n");
  if (headerEnd === -1) {
    return undefined;
  }

  const headerBlock = buffer.slice(0, headerEnd);
  const lines = headerBlock.split("\r\n");
  const [method, target] = lines[0]?.split(" ") ?? [];
  if (!method || !target) {
    return undefined;
  }

  const headers: Record<string, string> = {};
  for (const line of lines.slice(1)) {
    const separator = line.indexOf(":");
    if (separator === -1) {
      continue;
    }
    headers[line.slice(0, separator).trim().toLowerCase()] = line
      .slice(separator + 1)
      .trim();
  }

  const bodyStart = headerEnd + 4;
  const contentLength = Number(headers["content-length"] ?? "0");
  const requestEnd = bodyStart + contentLength;
  if (buffer.length < requestEnd) {
    return undefined;
  }

  return {
    consumedBytes: requestEnd,
    request: {
      method,
      url: new URL(target, "https://browser-local.invalid"),
      headers,
      body: buffer.slice(bodyStart, requestEnd),
    },
  };
}

function httpJson(status: number, payload: unknown) {
  return httpResponse(status, { "content-type": "application/json; charset=utf-8" }, JSON.stringify(payload, null, 2));
}

const HTTP_STATUS_TEXT: Record<number, string> = {
  200: "OK",
  202: "Accepted",
  400: "Bad Request",
  404: "Not Found",
  405: "Method Not Allowed",
  500: "Internal Server Error",
};

function httpResponse(status: number, headers: Record<string, string>, body: string) {
  const statusText = HTTP_STATUS_TEXT[status] ?? "Error";
  const responseHeaders = {
    "cache-control": "no-store",
    connection: "close",
    ...headers,
  };
  const bodyBytes = textToBytes(body);
  const head = [
    `HTTP/1.1 ${status} ${statusText}`,
    ...Object.entries(responseHeaders).map(([key, value]) => `${key}: ${value}`),
    `content-length: ${bodyBytes.length}`,
    "",
    "",
  ].join("\r\n");
  return head + bytesToBinary(bodyBytes);
}

function ensureRustls() {
  rustlsInitPromise ??= initRustls(rustlsWasmUrl);
  return rustlsInitPromise;
}

function normalizeTlsStep(value: unknown): TlsStep {
  const step = value as Partial<TlsStep>;
  return {
    plaintext: step.plaintext instanceof Uint8Array ? step.plaintext : new Uint8Array(),
    tls: step.tls instanceof Uint8Array ? step.tls : new Uint8Array(),
    handshaking: Boolean(step.handshaking),
  };
}

async function createTlsIdentity(
  sessionId: string,
  controlUrl: string,
  issueToken: string,
  onLog: (line: string) => void,
): Promise<TlsIdentity> {
  const hostname = `${sessionId}.${reverseRelayPublicSuffix()}`;
  const cached = readCachedTlsIdentity(hostname);
  if (cached) {
    return cached;
  }

  const keys = await new Promise<forge.pki.rsa.KeyPair>((resolve, reject) => {
    forge.pki.rsa.generateKeyPair({ bits: 2048, workers: -1 }, (error, keyPair) => {
      if (error || !keyPair) {
        reject(error ?? new Error("failed to generate keypair"));
        return;
      }
      resolve(keyPair);
    });
  });

  const keyPem = forge.pki.privateKeyToPem(keys.privateKey);
  const csrPem = createCsrPem(hostname, keys);
  const issued = await requestAcmeCertificate(
    certIssuerUrl(controlUrl),
    sessionId,
    csrPem,
    keyPem,
    issueToken,
    hostname,
    onLog,
  );
  if (issued) {
    return issued;
  }

  const cert = forge.pki.createCertificate();
  cert.publicKey = keys.publicKey;
  cert.serialNumber = Array.from(crypto.getRandomValues(new Uint8Array(12)), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
  cert.validity.notBefore = new Date(Date.now() - 60_000);
  cert.validity.notAfter = new Date(Date.now() + 24 * 60 * 60 * 1000);
  const attrs = [{ name: "commonName", value: hostname }];
  cert.setSubject(attrs);
  cert.setIssuer(attrs);
  cert.setExtensions([
    { name: "basicConstraints", cA: false },
    { name: "keyUsage", digitalSignature: true, keyEncipherment: true },
    { name: "extKeyUsage", serverAuth: true },
    {
      name: "subjectAltName",
      altNames: [{ type: 2, value: hostname }],
    },
  ]);
  cert.sign(keys.privateKey, forge.md.sha256.create());

  return {
    certPem: forge.pki.certificateToPem(cert),
    keyPem,
    hostname,
    source: "self-signed",
    trusted: false,
  };
}

function createCsrPem(hostname: string, keys: forge.pki.rsa.KeyPair) {
  const csr = forge.pki.createCertificationRequest();
  csr.publicKey = keys.publicKey;
  csr.setSubject([{ name: "commonName", value: hostname }]);
  csr.setAttributes([
    {
      name: "extensionRequest",
      extensions: [
        {
          name: "subjectAltName",
          altNames: [{ type: 2, value: hostname }],
        },
      ],
    },
  ]);
  csr.sign(keys.privateKey, forge.md.sha256.create());
  return forge.pki.certificationRequestToPem(csr);
}

async function requestAcmeCertificate(
  issuerUrl: string,
  sessionId: string,
  csrPem: string,
  keyPem: string,
  issueToken: string,
  hostname: string,
  onLog: (line: string) => void,
): Promise<TlsIdentity | undefined> {
  if (!issueToken) {
    onLog("ACME issuer token unavailable; using self-signed certificate");
    return undefined;
  }

  try {
    const response = await fetch(issuerUrl, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ sessionId, csrPem, issueToken }),
    });

    if (!response.ok) {
      const detail = await response.text();
      onLog(`ACME issuer unavailable (${response.status}); using self-signed certificate`);
      onLog(detail.slice(0, 240));
      return undefined;
    }

    const payload = (await response.json()) as { certPem?: string };
    if (!payload.certPem) {
      onLog("ACME issuer returned no certificate; using self-signed certificate");
      return undefined;
    }

    const identity: TlsIdentity = {
      certPem: payload.certPem,
      keyPem,
      hostname,
      source: "acme",
      trusted: true,
    };
    cacheTlsIdentity(identity);
    return identity;
  } catch (error) {
    onLog(error instanceof Error ? error.message : String(error));
    onLog("ACME certificate request failed; using self-signed certificate");
    return undefined;
  }
}

function certIssuerUrl(controlUrl: string) {
  const configured = import.meta.env.VITE_CERT_ISSUER_URL as string | undefined;
  if (configured) {
    return configured.replace(/\/$/, "");
  }

  const url = new URL(controlUrl);
  url.protocol = url.protocol === "wss:" ? "https:" : "http:";
  url.pathname = "/issue-cert";
  url.search = "";
  url.hash = "";
  return url.toString();
}

function readCachedTlsIdentity(hostname: string): TlsIdentity | undefined {
  try {
    const raw = localStorage.getItem(`${TLS_IDENTITY_CACHE_KEY}:${hostname}`);
    if (!raw) {
      return undefined;
    }

    const identity = JSON.parse(raw) as TlsIdentity;
    if (
      identity.hostname !== hostname ||
      !identity.certPem ||
      !identity.keyPem ||
      identity.source !== "acme"
    ) {
      return undefined;
    }

    const notAfter = firstCertificateNotAfter(identity.certPem);
    if (notAfter.getTime() - Date.now() < 24 * 60 * 60 * 1000) {
      return undefined;
    }

    return {
      ...identity,
      source: "cached-acme",
      trusted: true,
    };
  } catch {
    return undefined;
  }
}

function cacheTlsIdentity(identity: TlsIdentity) {
  if (identity.source !== "acme") {
    return;
  }
  localStorage.setItem(
    `${TLS_IDENTITY_CACHE_KEY}:${identity.hostname}`,
    JSON.stringify(identity),
  );
}

function firstCertificateNotAfter(certPem: string) {
  const match = certPem.match(/-----BEGIN CERTIFICATE-----[\s\S]+?-----END CERTIFICATE-----/);
  if (!match) {
    return new Date(0);
  }
  return forge.pki.certificateFromPem(match[0]).validity.notAfter;
}

async function sha256Hex(input: string) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(input));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function bytesToBinary(bytes: Uint8Array) {
  let out = "";
  for (const byte of bytes) {
    out += String.fromCharCode(byte);
  }
  return out;
}

function binaryToBytes(binary: string) {
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

function textToBytes(text: string) {
  return new TextEncoder().encode(text);
}

function writeUint32(bytes: Uint8Array, offset: number, value: number) {
  bytes[offset] = (value >>> 24) & 0xff;
  bytes[offset + 1] = (value >>> 16) & 0xff;
  bytes[offset + 2] = (value >>> 8) & 0xff;
  bytes[offset + 3] = value & 0xff;
}

function readUint32(bytes: Uint8Array, offset: number) {
  return (
    bytes[offset] * 0x1000000 +
    ((bytes[offset + 1] << 16) | (bytes[offset + 2] << 8) | bytes[offset + 3])
  );
}
