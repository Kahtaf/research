import { spawn } from "node:child_process";
import net from "node:net";
import { once } from "node:events";
import { setTimeout as delay } from "node:timers/promises";

import WebSocket from "ws";

const port = 19080 + Math.floor(Math.random() * 1000);
const sessionId = "smoke-session";
const base = `http://127.0.0.1:${port}`;

const server = spawn(process.execPath, ["dist/index.js"], {
  env: {
    ...process.env,
    PORT: String(port),
  },
  stdio: ["ignore", "pipe", "pipe"],
});

let output = "";
server.stdout.on("data", (chunk) => {
  output += chunk.toString();
});
server.stderr.on("data", (chunk) => {
  output += chunk.toString();
});

try {
  await waitForHealth(`${base}/health`);

  const browser = new WebSocket(`ws://127.0.0.1:${port}/browser/${sessionId}`);
  const [openMessage] = await once(browser, "message");
  const ready = JSON.parse(openMessage.toString());
  assert(ready.type === "session.ready", "browser did not receive session.ready");

  const client = new WebSocket(`ws://127.0.0.1:${port}/connect/${sessionId}`);
  await once(client, "open");

  const [streamOpenRaw] = await once(browser, "message");
  const streamOpen = JSON.parse(streamOpenRaw.toString());
  assert(streamOpen.type === "stream.open", "browser did not receive stream.open");
  assert(typeof streamOpen.streamId === "number", "stream id missing");

  const clientPayload = Buffer.from("opaque-client-bytes");
  client.send(clientPayload);

  const [browserDataRaw] = await once(browser, "message");
  const browserData = Buffer.from(browserDataRaw);
  assert(browserData.readUInt8(0) === 1, "data frame type mismatch");
  assert(browserData.readUInt32BE(1) === streamOpen.streamId, "stream id mismatch");
  assert(
    browserData.subarray(5).equals(clientPayload),
    "browser did not receive client payload",
  );

  const response = Buffer.from("opaque-browser-bytes");
  const frame = Buffer.alloc(5 + response.length);
  frame.writeUInt8(1, 0);
  frame.writeUInt32BE(streamOpen.streamId, 1);
  response.copy(frame, 5);
  browser.send(frame);

  const [clientDataRaw] = await once(client, "message");
  assert(Buffer.from(clientDataRaw).equals(response), "client did not receive browser payload");

  client.close();
  browser.close();

  console.log("reverse blind relay smoke passed");
} finally {
  server.kill("SIGTERM");
}

async function waitForHealth(url) {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        return;
      }
    } catch {
      // keep waiting
    }
    await delay(100);
  }

  throw new Error(`server did not become healthy\n${output}`);
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}
