import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";

import { WebSocket } from "ws";

const port = 9876;
const sessionId = "smoke-session";
const relay = spawn(process.execPath, ["relay/server.mjs"], {
  cwd: new URL("..", import.meta.url),
  env: {
    ...process.env,
    PORT: String(port),
    RATE_LIMIT_MAX: "10",
  },
  stdio: ["ignore", "pipe", "pipe"],
});

relay.stdout.on("data", (chunk) => process.stdout.write(chunk));
relay.stderr.on("data", (chunk) => process.stderr.write(chunk));

await delay(500);

const socket = new WebSocket(`ws://127.0.0.1:${port}/ws/${sessionId}`);

await new Promise((resolve, reject) => {
  socket.once("open", resolve);
  socket.once("error", reject);
});

socket.on("message", (data) => {
  const message = JSON.parse(String(data));
  if (message.type !== "request") {
    return;
  }

  socket.send(
    JSON.stringify({
      type: "response",
      requestId: message.requestId,
      status: 200,
      headers: {
        "content-type": "application/json; charset=utf-8",
        "x-smoke": "browser-runtime",
      },
      body: JSON.stringify({
        ok: true,
        path: message.path,
        query: message.query,
        computedBy: "mock-browser-websocket-client",
      }),
    }),
  );
});

const response = await fetch(
  `http://127.0.0.1:${port}/portal/${sessionId}/mcp`,
);

if (!response.ok) {
  throw new Error(`unexpected relay smoke status ${response.status}`);
}

const payload = await response.json();
if (payload.computedBy !== "mock-browser-websocket-client") {
  throw new Error("relay response did not come from websocket client");
}

console.log("relay smoke passed");
socket.close();
relay.kill("SIGTERM");
