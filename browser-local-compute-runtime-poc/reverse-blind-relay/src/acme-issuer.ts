import fs from "node:fs/promises";
import path from "node:path";

import * as acme from "acme-client";
import type { Authorization } from "acme-client";

type IssueOptions = {
  sessionId: string;
  csrPem: string;
  issueToken: string;
  expectedIssueToken: string;
  hostSuffix: string;
};

type CloudflareRecord = {
  id: string;
  name: string;
  content: string;
};

const SESSION_ID_PATTERN = /^[a-z0-9][a-z0-9-]{2,62}$/;
const httpChallenges = new Map<string, string>();

export function isAcmeIssuerConfigured(): boolean {
  if (!process.env.ACME_DIRECTORY_URL || !process.env.ACME_EMAIL) {
    return false;
  }

  if (challengeMode() === "dns-01") {
    return Boolean(process.env.CLOUDFLARE_API_TOKEN && process.env.CLOUDFLARE_ZONE_ID);
  }

  return true;
}

export function getHttpChallengeResponse(token: string): string | undefined {
  return httpChallenges.get(token);
}

export async function issueCertificate(options: IssueOptions): Promise<string> {
  assertIssuerConfig();

  if (!SESSION_ID_PATTERN.test(options.sessionId)) {
    throw new Error("invalid_session_id");
  }

  if (!options.expectedIssueToken || options.issueToken !== options.expectedIssueToken) {
    throw new Error("invalid_issue_token");
  }

  const hostSuffix = normalizeSuffix(options.hostSuffix);
  if (!hostSuffix) {
    throw new Error("missing_public_host_suffix");
  }

  const hostname = `${options.sessionId}.${hostSuffix}`;
  assertCsrMatchesHostname(options.csrPem, hostname);

  const client = new acme.Client({
    directoryUrl: requiredEnv("ACME_DIRECTORY_URL"),
    accountKey: await getAccountKey(),
    externalAccountBinding: externalAccountBinding(),
  });

  const certPem = await client.auto({
    csr: options.csrPem,
    email: requiredEnv("ACME_EMAIL"),
    termsOfServiceAgreed: process.env.ACME_TERMS_AGREED === "true",
    challengePriority: [challengeMode()],
    skipChallengeVerification: process.env.ACME_SKIP_CHALLENGE_VERIFICATION === "true",
    challengeCreateFn: async (authz, challenge, keyAuthorization) => {
      if (challenge.type === "http-01") {
        createHttpChallenge(challenge.token, keyAuthorization);
        return;
      }
      await createDnsChallenge(authz, keyAuthorization);
      await sleep(Number(process.env.ACME_DNS_PROPAGATION_MS ?? 5_000));
    },
    challengeRemoveFn: async (authz, challenge, keyAuthorization) => {
      if (challenge.type === "http-01") {
        removeHttpChallenge(challenge.token);
        return;
      }
      await removeDnsChallenge(authz, keyAuthorization);
    },
  });

  return certPem;
}

function assertIssuerConfig(): void {
  if (!isAcmeIssuerConfigured()) {
    throw new Error(
      challengeMode() === "dns-01"
        ? "ACME issuer is not configured. Set ACME_DIRECTORY_URL, ACME_EMAIL, CLOUDFLARE_API_TOKEN, and CLOUDFLARE_ZONE_ID."
        : "ACME issuer is not configured. Set ACME_DIRECTORY_URL and ACME_EMAIL.",
    );
  }
}

function assertCsrMatchesHostname(csrPem: string, hostname: string): void {
  const domains = acme.crypto.readCsrDomains(csrPem);
  const names = new Set([domains.commonName, ...domains.altNames].filter(Boolean));

  if (!names.has(hostname)) {
    throw new Error(`csr_hostname_mismatch:${hostname}`);
  }

  for (const name of names) {
    if (name !== hostname) {
      throw new Error(`csr_extra_hostname:${name}`);
    }
  }
}

async function getAccountKey(): Promise<string> {
  const keyFile = process.env.ACME_ACCOUNT_KEY_FILE
    ? process.env.ACME_ACCOUNT_KEY_FILE
    : path.join(process.cwd(), "acme-account-key.pem");

  try {
    return await fs.readFile(keyFile, "utf8");
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
      throw error;
    }
  }

  const key = await acme.crypto.createPrivateRsaKey(4096);
  await fs.writeFile(keyFile, key, { mode: 0o600 });
  return key.toString("utf8");
}

function externalAccountBinding() {
  const kid = process.env.ACME_EAB_KID;
  const hmacKey = process.env.ACME_EAB_HMAC_KEY;
  return kid && hmacKey ? { kid, hmacKey } : undefined;
}

async function createDnsChallenge(
  authz: Authorization,
  keyAuthorization: string,
): Promise<void> {
  const name = `_acme-challenge.${authz.identifier.value}`;
  await cloudflareRequest("/dns_records", {
    method: "POST",
    body: JSON.stringify({
      type: "TXT",
      name,
      content: keyAuthorization,
      ttl: 60,
      proxied: false,
      comment: "browser-local-compute-runtime-poc ACME DNS-01",
    }),
  });
}

async function removeDnsChallenge(
  authz: Authorization,
  keyAuthorization: string,
): Promise<void> {
  const name = `_acme-challenge.${authz.identifier.value}`;
  const records = await listCloudflareTxtRecords(name);
  await Promise.all(
    records
      .filter((record) => record.content === keyAuthorization)
      .map((record) => cloudflareRequest(`/dns_records/${record.id}`, { method: "DELETE" })),
  );
}

function createHttpChallenge(token: string, keyAuthorization: string): void {
  httpChallenges.set(token, keyAuthorization);
}

function removeHttpChallenge(token: string): void {
  httpChallenges.delete(token);
}

async function listCloudflareTxtRecords(name: string): Promise<CloudflareRecord[]> {
  const result = await cloudflareRequest(
    `/dns_records?type=TXT&name=${encodeURIComponent(name)}`,
  );
  return result as CloudflareRecord[];
}

async function cloudflareRequest(
  pathAndQuery: string,
  init: RequestInit = {},
): Promise<unknown> {
  const response = await fetch(
    `https://api.cloudflare.com/client/v4/zones/${requiredEnv("CLOUDFLARE_ZONE_ID")}${pathAndQuery}`,
    {
      ...init,
      headers: {
        authorization: `Bearer ${requiredEnv("CLOUDFLARE_API_TOKEN")}`,
        "content-type": "application/json",
        ...init.headers,
      },
    },
  );
  const payload = (await response.json()) as {
    success?: boolean;
    result?: unknown;
    errors?: Array<{ message?: string }>;
  };

  if (!response.ok || payload.success === false) {
    const detail = payload.errors?.map((error) => error.message).join("; ");
    throw new Error(`cloudflare_dns_error:${response.status}:${detail ?? "unknown"}`);
  }

  return payload.result;
}

function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`missing_env:${name}`);
  }
  return value;
}

function normalizeSuffix(suffix: string): string {
  return suffix.replace(/^\./, "").replace(/\.$/, "").toLowerCase();
}

function challengeMode(): "http-01" | "dns-01" {
  return process.env.ACME_CHALLENGE_MODE === "dns-01" ? "dns-01" : "http-01";
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}
