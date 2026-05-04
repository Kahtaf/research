#!/usr/bin/env node

import http from "node:http";

const args = new Map();
for (let index = 2; index < process.argv.length; index += 2) {
  args.set(process.argv[index], process.argv[index + 1]);
}

const remoteUrl = args.get("--url") ?? process.env.BROWSER_MCP_URL;
const browserPublicKeyToken =
  args.get("--browser-public-key") ?? process.env.BROWSER_PUBLIC_KEY;
const port = Number(args.get("--port") ?? process.env.PORT ?? 3333);

if (!remoteUrl || !browserPublicKeyToken) {
  console.error(
    "usage: node scripts/encrypted-mcp-proxy.mjs --url <browser-mcp-url> --browser-public-key <token> [--port 3333]",
  );
  process.exit(1);
}

const textEncoder = new TextEncoder();
const textDecoder = new TextDecoder();

function base64UrlEncode(bytes) {
  return Buffer.from(bytes).toString("base64url");
}

function base64UrlDecode(value) {
  return Uint8Array.from(Buffer.from(value, "base64url"));
}

function decodeJsonToken(value) {
  return JSON.parse(textDecoder.decode(base64UrlDecode(value)));
}

async function generateKeyPair() {
  return crypto.subtle.generateKey(
    {
      name: "ECDH",
      namedCurve: "P-256",
    },
    false,
    ["deriveKey"],
  );
}

async function importPublicKey(publicJwk) {
  return crypto.subtle.importKey(
    "jwk",
    publicJwk,
    {
      name: "ECDH",
      namedCurve: "P-256",
    },
    false,
    [],
  );
}

async function deriveAesKey(privateKey, publicJwk) {
  return crypto.subtle.deriveKey(
    {
      name: "ECDH",
      public: await importPublicKey(publicJwk),
    },
    privateKey,
    {
      name: "AES-GCM",
      length: 256,
    },
    false,
    ["encrypt", "decrypt"],
  );
}

async function encryptRequest(plaintext, browserPublicJwk) {
  const clientKeyPair = await generateKeyPair();
  const clientPublicKey = await crypto.subtle.exportKey("jwk", clientKeyPair.publicKey);
  const aesKey = await deriveAesKey(clientKeyPair.privateKey, browserPublicJwk);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = new Uint8Array(
    await crypto.subtle.encrypt(
      {
        name: "AES-GCM",
        iv,
      },
      aesKey,
      textEncoder.encode(plaintext),
    ),
  );

  return {
    clientPrivateKey: clientKeyPair.privateKey,
    envelope: {
      version: 1,
      encoding: "json",
      clientPublicKey,
      iv: base64UrlEncode(iv),
      ciphertext: base64UrlEncode(ciphertext),
    },
  };
}

async function decryptResponse(responseEnvelope, clientPrivateKey, browserPublicJwk) {
  const aesKey = await deriveAesKey(clientPrivateKey, browserPublicJwk);
  const plaintext = await crypto.subtle.decrypt(
    {
      name: "AES-GCM",
      iv: base64UrlDecode(responseEnvelope.iv),
    },
    aesKey,
    base64UrlDecode(responseEnvelope.ciphertext),
  );
  return textDecoder.decode(plaintext);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

function writeCorsHeaders(res) {
  res.setHeader("access-control-allow-origin", "*");
  res.setHeader("access-control-allow-methods", "GET,POST,OPTIONS");
  res.setHeader(
    "access-control-allow-headers",
    "accept,content-type,mcp-protocol-version,mcp-session-id",
  );
}

const browserPublicJwk = decodeJsonToken(browserPublicKeyToken);

const server = http.createServer(async (req, res) => {
  writeCorsHeaders(res);

  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.url === "/health") {
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ ok: true, role: "local encrypted MCP proxy" }));
    return;
  }

  if (req.url !== "/mcp") {
    res.writeHead(404, { "content-type": "application/json" });
    res.end(JSON.stringify({ error: "not_found", expected: "/mcp" }));
    return;
  }

  if (req.method === "GET") {
    res.writeHead(200, { "content-type": "application/json" });
    res.end(
      JSON.stringify({
        name: "local-browser-mcp-encryption-proxy",
        upstream: remoteUrl,
      }),
    );
    return;
  }

  if (req.method !== "POST") {
    res.writeHead(405, { "content-type": "application/json", allow: "GET, POST" });
    res.end(JSON.stringify({ error: "method_not_allowed" }));
    return;
  }

  try {
    const plaintextRequest = await readBody(req);
    const { clientPrivateKey, envelope } = await encryptRequest(
      plaintextRequest,
      browserPublicJwk,
    );
    const upstream = await fetch(remoteUrl, {
      method: "POST",
      headers: {
        accept: "application/json",
        "content-type": "application/json",
        "mcp-protocol-version": req.headers["mcp-protocol-version"] ?? "2025-06-18",
      },
      body: JSON.stringify(envelope),
    });

    const upstreamText = await upstream.text();
    if (upstream.status === 202 || upstreamText.length === 0) {
      res.writeHead(upstream.status);
      res.end();
      return;
    }

    if (!upstream.ok) {
      res.writeHead(upstream.status, { "content-type": "application/json" });
      res.end(upstreamText);
      return;
    }

    const decryptedResponse = await decryptResponse(
      JSON.parse(upstreamText),
      clientPrivateKey,
      browserPublicJwk,
    );

    res.writeHead(200, {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    });
    res.end(decryptedResponse);
  } catch (error) {
    res.writeHead(502, { "content-type": "application/json" });
    res.end(
      JSON.stringify({
        error: "proxy_failed",
        detail: error instanceof Error ? error.message : String(error),
      }),
    );
  }
});

server.listen(port, () => {
  console.log(
    JSON.stringify({
      event: "encrypted_mcp_proxy_listening",
      port,
      url: `http://localhost:${port}/mcp`,
      upstream: remoteUrl,
    }),
  );
});
