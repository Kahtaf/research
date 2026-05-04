import type { RelayRequest, RelayResponse, RuntimeReply } from "./types";

type TunnelClientOptions = {
  relayHttpUrl: string;
  sessionId: string;
  worker: Worker;
  onLog: (line: string) => void;
  onStatus: (status: string) => void;
  onResponse: (body: string) => void;
  onCount: () => void;
};

function websocketUrl(relayHttpUrl: string, sessionId: string) {
  const url = new URL(relayHttpUrl);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `/ws/${sessionId}`;
  url.search = "";
  return url.toString();
}

export function publicMcpUrl(relayHttpUrl: string, sessionId: string) {
  const url = new URL(relayHttpUrl);
  url.pathname = `/portal/${sessionId}/mcp`;
  url.search = "";
  return url.toString();
}

export function startTunnelClient(options: TunnelClientOptions) {
  let socket: WebSocket | undefined;
  let heartbeat: number | undefined;
  let reconnectTimer: number | undefined;
  let reconnectAttempt = 0;
  let stopped = false;
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
    options.onLog(`${request.method} ${request.path}`);

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
    options.onCount();
  };

  const clearHeartbeat = () => {
    if (heartbeat) {
      window.clearInterval(heartbeat);
      heartbeat = undefined;
    }
  };

  const clearReconnect = () => {
    if (reconnectTimer) {
      window.clearTimeout(reconnectTimer);
      reconnectTimer = undefined;
    }
  };

  const shouldConnect = () =>
    !stopped && document.visibilityState === "visible";

  const scheduleReconnect = () => {
    if (!shouldConnect() || reconnectTimer) {
      return;
    }

    const delay = Math.min(1000 * 2 ** reconnectAttempt, 15_000);
    reconnectAttempt += 1;
    options.onStatus("Reconnecting");
    options.onLog(`reconnect scheduled in ${delay}ms`);
    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = undefined;
      connect();
    }, delay);
  };

  const disconnectForHiddenTab = () => {
    clearReconnect();
    clearHeartbeat();

    if (
      socket?.readyState === WebSocket.OPEN ||
      socket?.readyState === WebSocket.CONNECTING
    ) {
      socket.close(1000, "tab hidden");
    }

    socket = undefined;
    options.onStatus("Paused");
    options.onLog("tab hidden; tunnel paused");
  };

  const connect = () => {
    if (!shouldConnect()) {
      disconnectForHiddenTab();
      return;
    }

    if (
      socket?.readyState === WebSocket.OPEN ||
      socket?.readyState === WebSocket.CONNECTING
    ) {
      return;
    }

    clearReconnect();
    options.onStatus(reconnectAttempt > 0 ? "Reconnecting" : "Connecting");
    socket = new WebSocket(websocketUrl(options.relayHttpUrl, options.sessionId));

    socket.onopen = () => {
      reconnectAttempt = 0;
      options.onStatus("Connected");
      options.onLog("tunnel connected");
      clearHeartbeat();
      heartbeat = window.setInterval(() => {
        if (socket?.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: "ping" }));
        }
      }, 15_000);
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(String(event.data)) as
        | RelayRequest
        | { type: string };
      if (isRelayRequest(message)) {
        void handleRequest(message);
      }
    };

    socket.onclose = () => {
      clearHeartbeat();
      socket = undefined;

      if (stopped) {
        return;
      }

      if (document.visibilityState !== "visible") {
        options.onStatus("Paused");
        options.onLog("tunnel paused while tab is hidden");
        return;
      }

      options.onStatus("Disconnected");
      options.onLog("tunnel disconnected");
      scheduleReconnect();
    };

    socket.onerror = () => {
      options.onStatus("Connection error");
      options.onLog("tunnel websocket error");
      scheduleReconnect();
    };
  };

  const handleVisibilityChange = () => {
    if (document.visibilityState === "visible") {
      options.onLog("tab visible; tunnel connecting");
      reconnectAttempt = 0;
      connect();
      return;
    }

    disconnectForHiddenTab();
  };

  document.addEventListener("visibilitychange", handleVisibilityChange);
  connect();

  return {
    close() {
      stopped = true;
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      clearReconnect();
      clearHeartbeat();
      socket?.close();
      socket = undefined;
    },
  };
}

function isRelayRequest(
  message: RelayRequest | { type: string },
): message is RelayRequest {
  return (
    message.type === "request" &&
    typeof (message as RelayRequest).requestId === "string" &&
    typeof (message as RelayRequest).method === "string" &&
    typeof (message as RelayRequest).path === "string"
  );
}
