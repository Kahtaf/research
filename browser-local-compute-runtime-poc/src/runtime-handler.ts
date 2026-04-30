import { z } from "zod";

import { incrementRequestCount, readText } from "./storage";
import type { RelayRequest } from "./types";

const DEFAULT_MAX_CHARS = 20_000;
const HARD_MAX_CHARS = 100_000;
const MAX_SEARCH_RESULTS = 20;

type RuntimeConfig = {
  sessionId: string;
};

const getTextArgsSchema = z.object({
  offset: z.number().int().min(0).default(0),
  maxChars: z.number().int().min(1).max(HARD_MAX_CHARS).default(DEFAULT_MAX_CHARS),
});

const searchTextArgsSchema = z.object({
  query: z.string().trim().min(1).max(512),
  maxResults: z.number().int().min(1).max(MAX_SEARCH_RESULTS).default(10),
  contextChars: z.number().int().min(20).max(2_000).default(240),
});

const tools = [
  {
    name: "get_text",
    description:
      "Read text currently stored in the browser tab. Use offset and maxChars to page through large text.",
    inputSchema: {
      type: "object",
      properties: {
        offset: {
          type: "integer",
          minimum: 0,
          default: 0,
          description: "Zero-based character offset.",
        },
        maxChars: {
          type: "integer",
          minimum: 1,
          maximum: HARD_MAX_CHARS,
          default: DEFAULT_MAX_CHARS,
          description: "Maximum number of characters to return.",
        },
      },
      additionalProperties: false,
    },
  },
  {
    name: "search_text",
    description: "Search the browser-local text and return matching snippets.",
    inputSchema: {
      type: "object",
      properties: {
        query: {
          type: "string",
          minLength: 1,
          maxLength: 512,
          description: "Case-insensitive literal search query.",
        },
        maxResults: {
          type: "integer",
          minimum: 1,
          maximum: MAX_SEARCH_RESULTS,
          default: 10,
        },
        contextChars: {
          type: "integer",
          minimum: 20,
          maximum: 2000,
          default: 240,
          description: "Characters of context to include around each match.",
        },
      },
      required: ["query"],
      additionalProperties: false,
    },
  },
  {
    name: "get_text_stats",
    description:
      "Return basic size and tokenization stats for the browser-local text.",
    inputSchema: {
      type: "object",
      properties: {},
      additionalProperties: false,
    },
  },
];

function json(status: number, payload: unknown, extraHeaders = {}) {
  return {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      ...extraHeaders,
    },
    body: payload === undefined ? "" : JSON.stringify(payload, null, 2),
  };
}

function decodeBody(body: string) {
  if (!body) {
    return "";
  }

  const binary = atob(body);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

function textContent(payload: unknown) {
  return {
    content: [
      {
        type: "text",
        text:
          typeof payload === "string"
            ? payload
            : JSON.stringify(payload, null, 2),
      },
    ],
  };
}

function jsonRpcResult(id: string | number | null, result: unknown) {
  return {
    jsonrpc: "2.0",
    id,
    result,
  };
}

function jsonRpcError(
  id: string | number | null,
  code: number,
  message: string,
  data?: unknown,
) {
  return {
    jsonrpc: "2.0",
    id,
    error: {
      code,
      message,
      ...(data === undefined ? {} : { data }),
    },
  };
}

function getTextSlice(text: string, offset: number, maxChars: number) {
  const end = Math.min(offset + maxChars, text.length);
  const value = text.slice(offset, end);
  return {
    text: value,
    offset,
    returnedChars: value.length,
    totalChars: text.length,
    truncated: end < text.length,
    nextOffset: end < text.length ? end : null,
  };
}

function searchText(text: string, query: string, maxResults: number, contextChars: number) {
  const lowerText = text.toLowerCase();
  const lowerQuery = query.toLowerCase();
  const results = [];
  let index = lowerText.indexOf(lowerQuery);

  while (index !== -1 && results.length < maxResults) {
    const start = Math.max(0, index - contextChars);
    const end = Math.min(text.length, index + query.length + contextChars);
    results.push({
      offset: index,
      snippet: text.slice(start, end),
    });
    index = lowerText.indexOf(lowerQuery, index + lowerQuery.length);
  }

  return {
    query,
    totalChars: text.length,
    resultCount: results.length,
    results,
  };
}

function getTextStats(text: string) {
  const words = text.trim().length === 0 ? [] : text.trim().split(/\s+/);
  return {
    charCount: text.length,
    byteEstimate: new TextEncoder().encode(text).byteLength,
    lineCount: text.length === 0 ? 0 : text.split(/\r\n|\r|\n/).length,
    wordCount: words.length,
  };
}

async function handleMcpMessage(message: Record<string, unknown>, config: RuntimeConfig) {
  const id = (message.id as string | number | null | undefined) ?? null;
  const method = message.method;

  if (typeof method !== "string") {
    return jsonRpcError(id, -32600, "Invalid Request");
  }

  if (method === "initialize") {
    return jsonRpcResult(id, {
      protocolVersion: "2025-06-18",
      capabilities: {
        tools: {},
      },
      serverInfo: {
        name: "browser-local-text-mcp",
        version: "0.1.0",
      },
      instructions:
        "Use tools to read text stored in the user's active browser tab. The server is available only while that tab is open and connected.",
    });
  }

  if (method === "tools/list") {
    return jsonRpcResult(id, { tools });
  }

  if (method === "tools/call") {
    const requestCount = await incrementRequestCount();
    const params = message.params as
      | { name?: string; arguments?: Record<string, unknown> }
      | undefined;
    const name = params?.name;
    const args = params?.arguments ?? {};
    const text = (await readText()) ?? "";

    if (name === "get_text") {
      const parsed = getTextArgsSchema.safeParse(args);
      if (!parsed.success) {
        return jsonRpcError(id, -32602, "Invalid get_text arguments", parsed.error.issues);
      }
      return jsonRpcResult(
        id,
        textContent({
          ...getTextSlice(text, parsed.data.offset, parsed.data.maxChars),
          requestCount,
          sessionId: config.sessionId,
          runtime: "browser-local worker",
        }),
      );
    }

    if (name === "search_text") {
      const parsed = searchTextArgsSchema.safeParse(args);
      if (!parsed.success) {
        return jsonRpcError(id, -32602, "Invalid search_text arguments", parsed.error.issues);
      }
      return jsonRpcResult(
        id,
        textContent({
          ...searchText(
            text,
            parsed.data.query,
            parsed.data.maxResults,
            parsed.data.contextChars,
          ),
          requestCount,
          sessionId: config.sessionId,
          runtime: "browser-local worker",
        }),
      );
    }

    if (name === "get_text_stats") {
      return jsonRpcResult(
        id,
        textContent({
          ...getTextStats(text),
          requestCount,
          sessionId: config.sessionId,
          runtime: "browser-local worker",
          storage: "IndexedDB",
        }),
      );
    }

    return jsonRpcError(id, -32602, `Unknown tool: ${String(name)}`);
  }

  return jsonRpcError(id, -32601, `Method not found: ${method}`);
}

export async function handleRuntimeRequest(
  request: RelayRequest,
  config: RuntimeConfig,
) {
  if (request.path !== "/mcp") {
    return json(404, {
      error: "not_found",
      allowedRoute: "POST /mcp",
    });
  }

  if (request.method === "GET") {
    return json(200, {
      name: "browser-local-text-mcp",
      transport: "streamable-http",
      tools: tools.map((tool) => tool.name),
      runtime: "browser-local worker",
    });
  }

  if (request.method !== "POST") {
    return json(
      405,
      { error: "method_not_allowed", allowed: ["GET", "POST"] },
      { allow: "GET, POST" },
    );
  }

  let message: Record<string, unknown>;
  try {
    message = JSON.parse(decodeBody(request.body)) as Record<string, unknown>;
  } catch {
    return json(400, jsonRpcError(null, -32700, "Parse error"));
  }

  if (message.id === undefined && typeof message.method === "string") {
    return {
      status: 202,
      headers: {
        "cache-control": "no-store",
      },
      body: "",
    };
  }

  return json(200, await handleMcpMessage(message, config));
}
