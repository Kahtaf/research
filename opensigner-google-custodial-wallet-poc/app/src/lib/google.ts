import { OAuth2Client } from "google-auth-library";

import { appUrl, requiredEnv } from "./env";

export type GoogleIdentity = {
  sub: string;
  email: string;
};

function redirectUri(): string {
  return `${appUrl()}/api/auth/google/callback`;
}

export function googleAuthUrl(state: string): string {
  const url = new URL("https://accounts.google.com/o/oauth2/v2/auth");
  url.searchParams.set("client_id", requiredEnv("GOOGLE_CLIENT_ID"));
  url.searchParams.set("redirect_uri", redirectUri());
  url.searchParams.set("response_type", "code");
  url.searchParams.set("scope", "openid email profile");
  url.searchParams.set("state", state);
  url.searchParams.set("prompt", "select_account");
  return url.toString();
}

export async function exchangeGoogleCode(code: string): Promise<GoogleIdentity> {
  const response = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      code,
      client_id: requiredEnv("GOOGLE_CLIENT_ID"),
      client_secret: requiredEnv("GOOGLE_CLIENT_SECRET"),
      redirect_uri: redirectUri(),
      grant_type: "authorization_code",
    }),
  });

  if (!response.ok) {
    throw new Error("Google token exchange failed");
  }

  const tokenSet = (await response.json()) as { id_token?: string };
  if (!tokenSet.id_token) {
    throw new Error("Google did not return an id token");
  }

  const client = new OAuth2Client(requiredEnv("GOOGLE_CLIENT_ID"));
  const ticket = await client.verifyIdToken({
    idToken: tokenSet.id_token,
    audience: requiredEnv("GOOGLE_CLIENT_ID"),
  });

  const payload = ticket.getPayload();
  if (!payload?.sub || !payload.email) {
    throw new Error("Google identity is missing sub or email");
  }

  return { sub: payload.sub, email: payload.email };
}
