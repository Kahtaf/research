import { randomBytes } from "node:crypto";
import { NextResponse } from "next/server";

import { OAUTH_STATE_COOKIE } from "@/lib/constants";
import { googleAuthUrl } from "@/lib/google";
import { secureCookies } from "@/lib/env";

export const runtime = "nodejs";

export async function GET() {
  const state = randomBytes(24).toString("base64url");
  const response = NextResponse.redirect(googleAuthUrl(state));
  response.cookies.set(OAUTH_STATE_COOKIE, state, {
    httpOnly: true,
    sameSite: "lax",
    secure: secureCookies(),
    maxAge: 10 * 60,
    path: "/",
  });
  return response;
}
