import { NextResponse } from "next/server";

import { allowedOrigins } from "./env";

const allowedMethods = "GET,POST,PUT,DELETE,OPTIONS";
const allowedHeaders =
  "Content-Type, Authorization, X-Auth-Provider, X-Token-Type, X-Request-ID, X-Cookie-Field";

export function corsHeaders(request: Request): HeadersInit {
  const origin = request.headers.get("origin") || "";
  const requestedHeaders = request.headers.get("access-control-request-headers");
  const headers: Record<string, string> = {
    "Access-Control-Allow-Methods": allowedMethods,
    "Access-Control-Allow-Headers": requestedHeaders || allowedHeaders,
    "Access-Control-Allow-Credentials": "true",
    Vary: "Origin, Access-Control-Request-Headers",
  };

  if (allowedOrigins().includes(origin)) {
    headers["Access-Control-Allow-Origin"] = origin;
  }

  return headers;
}

export function jsonResponse(
  request: Request,
  body: unknown,
  init: ResponseInit = {},
): NextResponse {
  return NextResponse.json(body, {
    ...init,
    headers: {
      ...corsHeaders(request),
      ...init.headers,
    },
  });
}

export function optionsResponse(request: Request): NextResponse {
  return new NextResponse(null, {
    status: 204,
    headers: corsHeaders(request),
  });
}
