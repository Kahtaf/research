import {
  exportJWK,
  importPKCS8,
  importSPKI,
  jwtVerify,
  SignJWT,
  type JWK,
} from "jose";

import { requiredEnv } from "./env";

const encoder = new TextEncoder();
const issuer = "opensigner-poc-auth";
const audience = "opensigner-storage";

function normalizePem(value: string): string {
  return value.replace(/\\n/g, "\n");
}

async function signingKey() {
  const privateKey = process.env.OPENSIGNER_JWT_PRIVATE_KEY;
  if (privateKey) {
    return {
      alg: "RS256" as const,
      key: await importPKCS8(normalizePem(privateKey), "RS256"),
    };
  }

  return {
    alg: "HS256" as const,
    key: encoder.encode(requiredEnv("OPENSIGNER_JWT_HS_SECRET")),
  };
}

export async function createOpenSignerToken(userUuid: string): Promise<string> {
  const key = await signingKey();
  return new SignJWT({ user_id: userUuid })
    .setProtectedHeader({
      alg: key.alg,
      typ: "JWT",
      kid: process.env.OPENSIGNER_JWT_KEY_ID || "opensigner-poc-key",
    })
    .setIssuer(issuer)
    .setAudience(audience)
    .setSubject(userUuid)
    .setIssuedAt()
    .setExpirationTime("15m")
    .sign(key.key);
}

export async function verifyOpenSignerToken(token: string): Promise<string | null> {
  try {
    const publicKey = process.env.OPENSIGNER_JWT_PUBLIC_KEY;
    if (publicKey) {
      const { payload } = await jwtVerify(
        token,
        await importSPKI(normalizePem(publicKey), "RS256"),
        { issuer, audience },
      );
      return typeof payload.sub === "string" ? payload.sub : null;
    }

    const privateKey = process.env.OPENSIGNER_JWT_PRIVATE_KEY;
    if (privateKey) {
      const { payload } = await jwtVerify(
        token,
        await importPKCS8(normalizePem(privateKey), "RS256"),
        { issuer, audience },
      );
      return typeof payload.sub === "string" ? payload.sub : null;
    }

    const { payload } = await jwtVerify(
      token,
      encoder.encode(requiredEnv("OPENSIGNER_JWT_HS_SECRET")),
      { issuer, audience },
    );
    return typeof payload.sub === "string" ? payload.sub : null;
  } catch {
    return null;
  }
}

export async function publicJwks(): Promise<{ keys: JWK[] }> {
  const explicitJwk = process.env.OPENSIGNER_JWT_PUBLIC_JWK;
  if (explicitJwk) {
    return { keys: [JSON.parse(explicitJwk) as JWK] };
  }

  const publicKey = process.env.OPENSIGNER_JWT_PUBLIC_KEY;
  if (!publicKey) {
    return { keys: [] };
  }

  const jwk = await exportJWK(await importSPKI(normalizePem(publicKey), "RS256"));
  jwk.alg = "RS256";
  jwk.use = "sig";
  jwk.kid = process.env.OPENSIGNER_JWT_KEY_ID || "opensigner-poc-key";
  return { keys: [jwk] };
}

export function bearerToken(request: Request): string | null {
  const value = request.headers.get("authorization");
  if (!value?.startsWith("Bearer ")) return null;
  return value.slice("Bearer ".length);
}
