import { cookies } from "next/headers";
import { jwtVerify, SignJWT } from "jose";

import { SESSION_COOKIE } from "./constants";
import { requiredEnv } from "./env";

const encoder = new TextEncoder();

export type AppSession = {
  userId: string;
  googleSub: string;
  email: string;
  opensignerUserUuid: string;
};

function sessionSecret(): Uint8Array {
  return encoder.encode(requiredEnv("APP_SESSION_SECRET"));
}

export async function createSessionToken(session: AppSession): Promise<string> {
  return new SignJWT(session)
    .setProtectedHeader({ alg: "HS256", typ: "JWT" })
    .setIssuer("opensigner-poc-app")
    .setAudience("opensigner-poc-app")
    .setSubject(session.userId)
    .setIssuedAt()
    .setExpirationTime("7d")
    .sign(sessionSecret());
}

export async function verifySessionToken(
  token: string | undefined,
): Promise<AppSession | null> {
  if (!token) return null;

  try {
    const { payload } = await jwtVerify(token, sessionSecret(), {
      issuer: "opensigner-poc-app",
      audience: "opensigner-poc-app",
    });

    if (
      typeof payload.userId !== "string" ||
      typeof payload.googleSub !== "string" ||
      typeof payload.email !== "string" ||
      typeof payload.opensignerUserUuid !== "string"
    ) {
      return null;
    }

    return {
      userId: payload.userId,
      googleSub: payload.googleSub,
      email: payload.email,
      opensignerUserUuid: payload.opensignerUserUuid,
    };
  } catch {
    return null;
  }
}

export async function currentSession(): Promise<AppSession | null> {
  const cookieStore = await cookies();
  return verifySessionToken(cookieStore.get(SESSION_COOKIE)?.value);
}
