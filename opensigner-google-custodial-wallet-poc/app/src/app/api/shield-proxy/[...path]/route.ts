import { NextResponse } from "next/server";

import { corsHeaders, optionsResponse } from "@/lib/cors";
import { requiredEnv } from "@/lib/env";

export const runtime = "nodejs";

type Context = { params: Promise<{ path: string[] }> };

const forwardedHeaders = [
  "authorization",
  "content-type",
  "x-auth-provider",
  "x-token-type",
  "x-cookie-field",
  "x-encryption-part",
  "x-encryption-session",
  "x-api-key",
  "x-openfort-flow-name",
  "x-openfort-user-id",
  "x-openfort-chain-id",
  "traceparent",
];

export async function OPTIONS(request: Request) {
  return optionsResponse(request);
}

export async function GET(request: Request, context: Context) {
  return proxyShield(request, context);
}

export async function POST(request: Request, context: Context) {
  return proxyShield(request, context);
}

async function proxyShield(request: Request, context: Context) {
  const { path } = await context.params;
  const shieldUrl = new URL(requiredEnv("SHIELD_URL"));
  shieldUrl.pathname = [shieldUrl.pathname.replace(/\/$/, ""), ...path].join("/");
  shieldUrl.search = new URL(request.url).search;

  const headers = new Headers();
  for (const name of forwardedHeaders) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  const response = await fetch(shieldUrl, {
    method: request.method,
    headers,
    body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.text(),
  });

  const responseHeaders = new Headers(corsHeaders(request));
  const contentType = response.headers.get("content-type");
  if (contentType) responseHeaders.set("content-type", contentType);

  return new NextResponse(await response.text(), {
    status: response.status,
    headers: responseHeaders,
  });
}
