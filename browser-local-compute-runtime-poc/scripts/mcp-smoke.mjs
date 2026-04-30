import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";

import { WebSocket } from "ws";

const port = 9877;
const sessionId = "mcp-smoke-session";
const sampleText =
  "Spotify export: Queens of the Stone Age, The Strokes, Wet Leg, and IDLES have frequent plays. Rock, indie rock, and post-punk show up repeatedly.";

const relay = spawn(process.execPath, ["relay/server.mjs"], {
  cwd: new URL("..", import.meta.url),
  env: {
    ...process.env,
    PORT: String(port),
    RATE_LIMIT_MAX: "20",
  },
  stdio: ["ignore", "pipe", "pipe"],
});

relay.stdout.on("data", (chunk) => process.stdout.write(chunk));
relay.stderr.on("data", (chunk) => process.stderr.write(chunk));

function fail(error) {
  socket?.close();
  relay.kill("SIGTERM");
  throw error;
}

await delay(500);

let socket = new WebSocket(`ws://127.0.0.1:${port}/ws/${sessionId}`);

await new Promise((resolve, reject) => {
  socket.once("open", resolve);
  socket.once("error", reject);
});

socket.on("message", (data) => {
  const message = JSON.parse(String(data));
  if (message.type !== "request") {
    return;
  }

  const body = message.body
    ? JSON.parse(Buffer.from(message.body, "base64").toString("utf8"))
    : {};
  const response = handleRpc(body);

  socket.send(
    JSON.stringify({
      type: "response",
      requestId: message.requestId,
      status: response.status,
      headers: {
        "content-type": "application/json; charset=utf-8",
        "x-runtime": "mock-browser-local-mcp",
      },
      body: JSON.stringify(response.body),
    }),
  );
});

function textToolResult(payload) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(payload),
      },
    ],
  };
}

function handleRpc(request) {
  if (request.method === "initialize") {
    return {
      status: 200,
      body: {
        jsonrpc: "2.0",
        id: request.id,
        result: {
          protocolVersion: "2025-03-26",
          serverInfo: { name: "browser-text-mcp-smoke", version: "0.0.0" },
          capabilities: { tools: {} },
        },
      },
    };
  }

  if (request.method === "tools/list") {
    return {
      status: 200,
      body: {
        jsonrpc: "2.0",
        id: request.id,
        result: {
          tools: [
            { name: "get_text" },
            { name: "search_text" },
            { name: "get_text_stats" },
          ],
        },
      },
    };
  }

  if (request.method === "tools/call") {
    const { name, arguments: args = {} } = request.params ?? {};

    if (name === "get_text") {
      const offset = Number(args.offset ?? 0);
      const maxChars = Number(args.maxChars ?? 20_000);
      const text = sampleText.slice(offset, offset + maxChars);
      return {
        status: 200,
        body: {
          jsonrpc: "2.0",
          id: request.id,
          result: textToolResult({
            text,
            totalChars: sampleText.length,
            truncated: offset + text.length < sampleText.length,
          }),
        },
      };
    }

    if (name === "search_text") {
      const query = String(args.query ?? "").toLowerCase();
      return {
        status: 200,
        body: {
          jsonrpc: "2.0",
          id: request.id,
          result: textToolResult({
            query,
            results: sampleText.toLowerCase().includes(query)
              ? [{ index: sampleText.toLowerCase().indexOf(query), snippet: sampleText }]
              : [],
          }),
        },
      };
    }

    if (name === "get_text_stats") {
      return {
        status: 200,
        body: {
          jsonrpc: "2.0",
          id: request.id,
          result: textToolResult({
            totalChars: sampleText.length,
            wordCount: sampleText.trim().split(/\s+/).length,
            runtime: "browser-local",
          }),
        },
      };
    }
  }

  return {
    status: 200,
    body: {
      jsonrpc: "2.0",
      id: request.id ?? null,
      error: { code: -32601, message: "Method not found" },
    },
  };
}

async function rpc(method, params) {
  const response = await fetch(
    `http://127.0.0.1:${port}/portal/${sessionId}/mcp`,
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: crypto.randomUUID(),
        method,
        params,
      }),
    },
  );

  if (!response.ok) {
    fail(new Error(`unexpected ${method} status ${response.status}`));
  }

  return response.json();
}

try {
  const initialized = await rpc("initialize", {
    protocolVersion: "2025-03-26",
    capabilities: {},
    clientInfo: { name: "mcp-smoke", version: "0.0.0" },
  });
  if (initialized.result?.serverInfo?.name !== "browser-text-mcp-smoke") {
    fail(new Error("initialize did not return expected server info"));
  }

  const listed = await rpc("tools/list");
  const toolNames = listed.result?.tools?.map((tool) => tool.name) ?? [];
  for (const name of ["get_text", "search_text", "get_text_stats"]) {
    if (!toolNames.includes(name)) {
      fail(new Error(`tools/list missing ${name}`));
    }
  }

  const text = await rpc("tools/call", {
    name: "get_text",
    arguments: { offset: 0, maxChars: 80 },
  });
  if (!text.result?.content?.[0]?.text?.includes("Spotify export")) {
    fail(new Error("get_text did not return sample text"));
  }

  const search = await rpc("tools/call", {
    name: "search_text",
    arguments: { query: "rock" },
  });
  if (!search.result?.content?.[0]?.text?.includes("rock")) {
    fail(new Error("search_text did not return expected query result"));
  }

  const stats = await rpc("tools/call", {
    name: "get_text_stats",
    arguments: {},
  });
  if (!stats.result?.content?.[0]?.text?.includes("wordCount")) {
    fail(new Error("get_text_stats did not return stats"));
  }

  console.log("mcp smoke passed");
  socket.close();
  relay.kill("SIGTERM");
} catch (error) {
  fail(error);
}
