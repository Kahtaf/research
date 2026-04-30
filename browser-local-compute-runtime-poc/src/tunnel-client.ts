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

  const connect = () => {
    socket = new WebSocket(websocketUrl(options.relayHttpUrl, options.sessionId));

    socket.onopen = () => {
      options.onStatus("Connected");
      options.onLog("tunnel connected");
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
      if (heartbeat) {
        window.clearInterval(heartbeat);
      }
      options.onStatus("Disconnected");
      options.onLog("tunnel disconnected");
    };

    socket.onerror = () => {
      options.onStatus("Connection error");
      options.onLog("tunnel websocket error");
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
