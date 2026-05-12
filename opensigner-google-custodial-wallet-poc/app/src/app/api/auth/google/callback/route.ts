import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { OAUTH_STATE_COOKIE, SESSION_COOKIE } from "@/lib/constants";
import { appUrl, secureCookies } from "@/lib/env";
import { exchangeGoogleCode } from "@/lib/google";
import { findOrCreateUser } from "@/lib/repos";
import { createSessionToken } from "@/lib/session";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const cookieStore = await cookies();
  const expectedState = cookieStore.get(OAUTH_STATE_COOKIE)?.value;

  if (!code || !state || !expectedState || state !== expectedState) {
    return NextResponse.redirect(`${appUrl()}/?error=oauth_state`);
  }

  try {
    const identity = await exchangeGoogleCode(code);
    const user = await findOrCreateUser(identity.sub, identity.email);
    const sessionToken = await createSessionToken({
      userId: user.id,
      googleSub: user.google_sub,
      email: user.google_email,
      opensignerUserUuid: user.opensigner_user_uuid,
    });

    const response = NextResponse.redirect(appUrl());
    response.cookies.set(SESSION_COOKIE, sessionToken, {
      httpOnly: true,
      sameSite: "lax",
      secure: secureCookies(),
      maxAge: 7 * 24 * 60 * 60,
      path: "/",
    });
    response.cookies.delete(OAUTH_STATE_COOKIE);
    return response;
  } catch {
    return NextResponse.redirect(`${appUrl()}/?error=oauth_callback`);
  }
}
