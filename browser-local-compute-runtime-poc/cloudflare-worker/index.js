const REQUEST_TIMEOUT_MS = 30_000;
const MAX_BODY_BYTES = 1_048_576;
const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX = 30;

function json(status, payload) {
  return new Response(JSON.stringify(payload, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function cors(response) {
  const next = new Response(response.body, response);
  next.headers.set("access-control-allow-origin", "*");
  next.headers.set("access-control-allow-methods", "GET,POST,OPTIONS");
  next.headers.set(
    "access-control-allow-headers",
    "accept,content-type,mcp-protocol-version,mcp-session-id",
  );
  return next;
}

function getSessionId(pathname, prefix) {
  const escaped = prefix.replaceAll("/", "\\/");
  const match = pathname.match(new RegExp(`^${escaped}([^/]+)(?:/.*)?$`));
  return match?.[1] ?? "";
}

function encodeBody(arrayBuffer) {
  if (!arrayBuffer.byteLength) {
    return "";
  }

  const bytes = new Uint8Array(arrayBuffer);
  let binary = "";
  for (let index = 0; index < bytes.length; index += 1) {
    binary += String.fromCharCode(bytes[index]);
  }
  return btoa(binary);
}

export class BrowserRelay {
  constructor(state) {
    this.state = state;
    this.browserSocket = undefined;
    this.pending = new Map();
    this.rateLimitBuckets = new Map();
  }

  async fetch(request) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return cors(new Response(null, { status: 204 }));
    }

    if (url.pathname.startsWith("/ws/")) {
      return this.connectBrowser(request);
    }

    if (url.pathname.startsWith("/portal/")) {
      return this.forwardToBrowser(request);
    }

    return json(404, { error: "not_found" });
  }

  connectBrowser(request) {
    if (request.headers.get("upgrade") !== "websocket") {
      return json(426, { error: "websocket_upgrade_required" });
    }

    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);

    server.accept();

    if (this.browserSocket) {
      this.browserSocket.close(1012, "session replaced");
    }

    this.browserSocket = server;

    server.addEventListener("message", (event) => {
      this.handleBrowserMessage(String(event.data));
    });

    server.addEventListener("close", () => {
      if (this.browserSocket === server) {
        this.browserSocket = undefined;
      }
      this.rejectPending("browser_runtime_disconnected");
    });

    server.addEventListener("error", () => {
      if (this.browserSocket === server) {
        this.browserSocket = undefined;
      }
      this.rejectPending("browser_runtime_error");
    });

    return new Response(null, { status: 101, webSocket: client });
  }

  async forwardToBrowser(request) {
    if (!this.browserSocket || this.browserSocket.readyState !== 1) {
      return cors(
        json(503, {
          error: "browser_session_unavailable",
          detail: "The mobile browser tab is not connected.",
        }),
      );
    }

    if (this.isRateLimited(request)) {
      return cors(
        json(429, {
          error: "rate_limited",
          windowMs: RATE_LIMIT_WINDOW_MS,
          max: RATE_LIMIT_MAX,
        }),
      );
    }

    const url = new URL(request.url);
    const portalMatch = url.pathname.match(/^\/portal\/[^/]+(\/.*)$/);
    const path = portalMatch?.[1] ?? "/";
    const requestId = crypto.randomUUID();
    const bodyBuffer = await request.arrayBuffer();

    if (bodyBuffer.byteLength > MAX_BODY_BYTES) {
      return cors(json(413, { error: "request_body_too_large" }));
    }

    const responsePromise = this.waitForBrowserResponse(requestId);

    this.browserSocket.send(
      JSON.stringify({
        type: "request",
        requestId,
        method: request.method,
        path,
        query: url.searchParams.toString(),
        headers: Object.fromEntries(request.headers.entries()),
        body: encodeBody(bodyBuffer),
      }),
    );

    try {
      const browserResponse = await responsePromise;
      return cors(
        new Response(browserResponse.body, {
          status: browserResponse.status,
          headers: browserResponse.headers,
        }),
      );
    } catch (error) {
      return cors(
        json(502, {
          error: "relay_forward_failed",
          detail: error instanceof Error ? error.message : String(error),
        }),
      );
    }
  }

  waitForBrowserResponse(requestId) {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.pending.delete(requestId);
        reject(new Error("browser runtime timed out"));
      }, REQUEST_TIMEOUT_MS);

      this.pending.set(requestId, (response) => {
        clearTimeout(timeout);
        resolve(response);
      });
    });
  }

  handleBrowserMessage(rawMessage) {
    let message;
    try {
      message = JSON.parse(rawMessage);
    } catch {
      return;
    }

    if (message.type === "ping") {
      this.browserSocket?.send(JSON.stringify({ type: "pong" }));
      return;
    }

    if (message.type !== "response" || typeof message.requestId !== "string") {
      return;
    }

    const resolve = this.pending.get(message.requestId);
    if (!resolve) {
      return;
    }

    this.pending.delete(message.requestId);
    resolve(message);
  }

  rejectPending(error) {
    for (const resolve of this.pending.values()) {
      resolve({
        status: 503,
        headers: { "content-type": "application/json; charset=utf-8" },
        body: JSON.stringify({ error }),
      });
    }
    this.pending.clear();
  }

  isRateLimited(request) {
    const forwarded = request.headers.get("cf-connecting-ip") ?? "unknown";
    const now = Date.now();
    const bucket =
      this.rateLimitBuckets.get(forwarded) ?? { startedAt: now, count: 0 };

    if (now - bucket.startedAt > RATE_LIMIT_WINDOW_MS) {
      bucket.startedAt = now;
      bucket.count = 0;
    }

    bucket.count += 1;
    this.rateLimitBuckets.set(forwarded, bucket);
    return bucket.count > RATE_LIMIT_MAX;
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return json(200, {
        ok: true,
        role: "cloudflare routing-only relay",
      });
    }

    if (url.pathname.startsWith("/ws/")) {
      const sessionId = getSessionId(url.pathname, "/ws/");
      const id = env.BROWSER_RELAY.idFromName(sessionId);
      return env.BROWSER_RELAY.get(id).fetch(request);
    }

    if (url.pathname.startsWith("/portal/")) {
      const sessionId = getSessionId(url.pathname, "/portal/");
      const id = env.BROWSER_RELAY.idFromName(sessionId);
      return env.BROWSER_RELAY.get(id).fetch(request);
    }

    return env.ASSETS.fetch(request);
  },
};
