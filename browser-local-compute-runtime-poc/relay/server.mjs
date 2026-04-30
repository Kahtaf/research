import http from "node:http";
import { randomUUID } from "node:crypto";
import { URL } from "node:url";

import { WebSocketServer } from "ws";

const PORT = Number(process.env.PORT ?? 8787);
const REQUEST_TIMEOUT_MS = Number(process.env.REQUEST_TIMEOUT_MS ?? 30_000);
const MAX_BODY_BYTES = Number(process.env.MAX_BODY_BYTES ?? 1_048_576);
const RATE_LIMIT_WINDOW_MS = Number(process.env.RATE_LIMIT_WINDOW_MS ?? 60_000);
const RATE_LIMIT_MAX = Number(process.env.RATE_LIMIT_MAX ?? 30);
const PUBLIC_BASE_URL = process.env.PUBLIC_BASE_URL;

const sessions = new Map();
const rateLimitBuckets = new Map();

function sendJson(res, status, payload) {
  const body = JSON.stringify(payload, null, 2);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
    "access-control-allow-origin": "*",
  });
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let total = 0;

    req.on("data", (chunk) => {
      total += chunk.length;
      if (total > MAX_BODY_BYTES) {
        reject(new Error("request body too large"));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });

    req.on("end", () => resolve(Buffer.concat(chunks).toString("base64")));
    req.on("error", reject);
  });
}

function rateLimitKey(req, sessionId) {
  const forwarded = req.headers["x-forwarded-for"];
  const ip = Array.isArray(forwarded)
    ? forwarded[0]
    : forwarded?.split(",")[0]?.trim() || req.socket.remoteAddress || "unknown";
  return `${sessionId}:${ip}`;
}

function isRateLimited(req, sessionId) {
  const key = rateLimitKey(req, sessionId);
  const now = Date.now();
  const bucket = rateLimitBuckets.get(key) ?? { startedAt: now, count: 0 };

  if (now - bucket.startedAt > RATE_LIMIT_WINDOW_MS) {
    bucket.startedAt = now;
    bucket.count = 0;
  }

  bucket.count += 1;
  rateLimitBuckets.set(key, bucket);
  return bucket.count > RATE_LIMIT_MAX;
}

function waitForBrowserResponse(session, requestId) {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      session.pending.delete(requestId);
      reject(new Error("browser runtime timed out"));
    }, REQUEST_TIMEOUT_MS);

    session.pending.set(requestId, (response) => {
      clearTimeout(timeout);
      resolve(response);
    });
  });
}

function visiblePublicUrl(req, sessionId) {
  const base = PUBLIC_BASE_URL ?? `http://${req.headers.host}`;
  const url = new URL(`/portal/${sessionId}/api/process?input=hello`, base);
  return url.toString();
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url ?? "/", `http://${req.headers.host}`);

  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "access-control-allow-origin": "*",
      "access-control-allow-methods": "GET,POST,OPTIONS",
      "access-control-allow-headers": "authorization,content-type",
      "access-control-max-age": "600",
    });
    res.end();
    return;
  }

  if (url.pathname === "/health") {
    sendJson(res, 200, {
      ok: true,
      sessions: sessions.size,
      role: "routing-only relay",
    });
    return;
  }

  const match = url.pathname.match(/^\/portal\/([^/]+)(\/.*)$/);
  if (!match) {
    sendJson(res, 404, {
      error: "not_found",
      expected: "/portal/:sessionId/api/process?input=hello",
    });
    return;
  }

  const [, sessionId, path] = match;
  const session = sessions.get(sessionId);

  if (!session || session.socket.readyState !== session.socket.OPEN) {
    sendJson(res, 503, {
      error: "browser_session_unavailable",
      detail: "The mobile browser tab is not connected.",
    });
    return;
  }

  const expectedAuthorization = `Bearer ${session.token}`;
  if (req.headers.authorization !== expectedAuthorization) {
    sendJson(res, 401, { error: "unauthorized" });
    return;
  }

  if (isRateLimited(req, sessionId)) {
    sendJson(res, 429, {
      error: "rate_limited",
      windowMs: RATE_LIMIT_WINDOW_MS,
      max: RATE_LIMIT_MAX,
    });
    return;
  }

  try {
    const requestId = randomUUID();
    const body = await readBody(req);
    const responsePromise = waitForBrowserResponse(session, requestId);

    session.socket.send(
      JSON.stringify({
        type: "request",
        requestId,
        method: req.method,
        path,
        query: url.searchParams.toString(),
        headers: Object.fromEntries(
          Object.entries(req.headers).map(([key, value]) => [
            key.toLowerCase(),
            Array.isArray(value) ? value.join(",") : String(value ?? ""),
          ]),
        ),
        body,
      }),
    );

    const browserResponse = await responsePromise;
    res.writeHead(browserResponse.status, browserResponse.headers);
    res.end(browserResponse.body);
  } catch (error) {
    sendJson(res, 502, {
      error: "relay_forward_failed",
      detail: error instanceof Error ? error.message : String(error),
    });
  }
});

const wss = new WebSocketServer({ noServer: true });

wss.on("connection", (socket, req, { sessionId, token }) => {
  const existing = sessions.get(sessionId);
  if (existing) {
    existing.socket.close(1012, "session replaced");
  }

  const session = {
    token,
    socket,
    pending: new Map(),
  };
  sessions.set(sessionId, session);

  console.log(
    JSON.stringify({
      event: "session_connected",
      sessionId,
      publicUrl: visiblePublicUrl(req, sessionId),
    }),
  );

  socket.on("message", (data) => {
    let message;
    try {
      message = JSON.parse(String(data));
    } catch {
      return;
    }

    if (message.type === "ping") {
      socket.send(JSON.stringify({ type: "pong" }));
      return;
    }

    if (message.type === "response" && typeof message.requestId === "string") {
      const resolve = session.pending.get(message.requestId);
      if (resolve) {
        session.pending.delete(message.requestId);
        resolve(message);
      }
    }
  });

  socket.on("close", () => {
    if (sessions.get(sessionId)?.socket === socket) {
      sessions.delete(sessionId);
    }
    for (const resolve of session.pending.values()) {
      resolve({
        status: 503,
        headers: { "content-type": "application/json; charset=utf-8" },
        body: JSON.stringify({ error: "browser_runtime_disconnected" }),
      });
    }
    session.pending.clear();
    console.log(JSON.stringify({ event: "session_disconnected", sessionId }));
  });
});

server.on("upgrade", (req, socket, head) => {
  const url = new URL(req.url ?? "/", `http://${req.headers.host}`);
  const match = url.pathname.match(/^\/ws\/([^/]+)$/);

  if (!match) {
    socket.destroy();
    return;
  }

  const sessionId = match[1];
  const token = url.searchParams.get("token");

  if (!token || token.length < 16) {
    socket.destroy();
    return;
  }

  wss.handleUpgrade(req, socket, head, (ws) => {
    wss.emit("connection", ws, req, { sessionId, token });
  });
});

server.listen(PORT, () => {
  console.log(
    JSON.stringify({
      event: "relay_listening",
      port: PORT,
      role: "routing-only relay",
    }),
  );
});
