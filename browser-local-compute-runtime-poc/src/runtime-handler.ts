import { countBy, sortBy, words } from "lodash-es";
import { nanoid } from "nanoid";
import { z } from "zod";

import { recordRequest } from "./storage";
import type { RelayRequest } from "./types";

const inputSchema = z
  .string()
  .trim()
  .min(1)
  .max(256)
  .regex(/^[\p{L}\p{N}\s._:-]+$/u, "input contains unsupported characters");

type RuntimeConfig = {
  token: string;
  sessionId: string;
};

function json(status: number, payload: unknown) {
  return {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
    body: JSON.stringify(payload, null, 2),
  };
}

function authorize(request: RelayRequest, token: string) {
  const authorization =
    request.headers.authorization ?? request.headers.Authorization ?? "";
  return authorization === `Bearer ${token}`;
}

export async function handleRuntimeRequest(
  request: RelayRequest,
  config: RuntimeConfig,
) {
  if (!authorize(request, config.token)) {
    return json(401, {
      error: "unauthorized",
      runtime: "browser-local",
      servedFrom: "mobile-browser-tab",
    });
  }

  if (request.method !== "GET" || request.path !== "/api/process") {
    return json(404, {
      error: "not_found",
      allowedRoute: "GET /api/process?input=hello",
    });
  }

  const params = new URLSearchParams(request.query);
  const parsed = inputSchema.safeParse(params.get("input") ?? "");

  if (!parsed.success) {
    return json(400, {
      error: "invalid_input",
      issues: parsed.error.issues.map((issue) => issue.message),
    });
  }

  const input = parsed.data;
  const tokens = words(input.toLowerCase());
  const sortedTokens = sortBy(tokens);
  const frequency = countBy(tokens);
  const id = nanoid(10);
  const result = `${input.toUpperCase()}-${id}`;
  const timestamp = new Date().toISOString();
  const state = await recordRequest(input, result, timestamp);

  return json(200, {
    input,
    result,
    packageUsed: "zod + lodash-es + nanoid",
    requestCount: state.requestCount,
    storage: "IndexedDB",
    runtime: "browser-local worker",
    servedFrom: "mobile-browser-tab",
    sessionId: config.sessionId,
    processing: {
      sortedTokens,
      frequency,
      tokenCount: tokens.length,
    },
    browserProof: {
      userAgent: navigator.userAgent,
      workerScope:
        globalThis.constructor?.name ?? "DedicatedWorkerGlobalScope",
      crossOriginIsolated: globalThis.crossOriginIsolated,
    },
    timestamp,
  });
}
