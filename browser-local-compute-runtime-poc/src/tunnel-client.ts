import type {
  RelayRequest,
  RelayResponse,
  RuntimeReply,
} from "./types";

type TunnelClientOptions = {
  relayHttpUrl: string;
  sessionId: string;
  token: string;
  worker: Worker;
  onLog: (line: string) => void;
  onStatus: (status: string) => void;
  onResponse: (body: string) => void;
  onCount: (count: number) => void;
};

function websocketUrl(relayHttpUrl: string, sessionId: string, token: string) {
  const url = new URL(relayHttpUrl);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `/ws/${sessionId}`;
  url.searchParams.set("token", token);
  return url.toString();
}

export function publicApiUrl(relayHttpUrl: string, sessionId: string) {
  const url = new URL(relayHttpUrl);
  url.pathname = `/portal/${sessionId}/api/process`;
  url.search = "?input=hello";
  return url.toString();
}

export function startTunnelClient(options: TunnelClientOptions) {
  let socket: WebSocket | undefined;
  let heartbeat: number | undefined;
  const pending = new Map<string, (reply: RuntimeReply) => void>();

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

  const sendResponse = (response: RelayResponse) => {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(response));
    }
  };

  const handleRequest = async (request: RelayRequest) => {
    options.onLog(`${request.method} ${request.path}?${request.query}`);

    const reply = await new Promise<RuntimeReply>((resolve) => {
      pending.set(request.requestId, resolve);
      options.worker.postMessage({ type: "handle", request });
    });

    if (reply.type === "runtime-error") {
      sendResponse({
        type: "response",
        requestId: request.requestId,
        status: 500,
        headers: { "content-type": "application/json; charset=utf-8" },
        body: JSON.stringify({ error: reply.message }, null, 2),
      });
      return;
    }

    sendResponse({
      type: "response",
      requestId: request.requestId,
      ...reply.response,
    });

    options.onResponse(reply.response.body);

    try {
      const parsed = JSON.parse(reply.response.body) as { requestCount?: number };
      if (typeof parsed.requestCount === "number") {
        options.onCount(parsed.requestCount);
      }
    } catch {
      // Non-JSON responses are not expected for this PoC.
    }
  };

  const connect = () => {
    socket = new WebSocket(
      websocketUrl(options.relayHttpUrl, options.sessionId, options.token),
    );

    socket.onopen = () => {
      options.onStatus("Tunnel connected");
      options.onLog("relay websocket connected");
      heartbeat = window.setInterval(() => {
        if (socket?.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: "ping" }));
        }
      }, 15_000);
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(String(event.data)) as RelayRequest | { type: string };
      if (isRelayRequest(message)) {
        void handleRequest(message);
      }
    };

    socket.onclose = () => {
      if (heartbeat) {
        window.clearInterval(heartbeat);
      }
      options.onStatus("Tunnel disconnected");
      options.onLog("relay websocket disconnected");
    };

    socket.onerror = () => {
      options.onStatus("Tunnel error");
      options.onLog("relay websocket error");
    };
  };

  connect();

  return {
    close() {
      if (heartbeat) {
        window.clearInterval(heartbeat);
      }
      socket?.close();
    },
  };
}

function isRelayRequest(message: RelayRequest | { type: string }): message is RelayRequest {
  return (
    message.type === "request" &&
    typeof (message as RelayRequest).requestId === "string" &&
    typeof (message as RelayRequest).method === "string" &&
    typeof (message as RelayRequest).path === "string"
  );
}
