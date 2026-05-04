#!/usr/bin/env node

const [url, browserPublicKeyToken, toolName = "get_text_stats"] = process.argv.slice(2);

if (!url || !browserPublicKeyToken) {
  console.error(
    "usage: node scripts/encrypted-mcp-request.mjs <mcp-url> <browser-public-key-token> [tool-name]",
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
  return JSON.parse(textDecoder.decode(plaintext));
}

const browserPublicJwk = decodeJsonToken(browserPublicKeyToken);
const request = {
  jsonrpc: "2.0",
  id: crypto.randomUUID(),
  method: "tools/call",
  params: {
    name: toolName,
    arguments: {},
  },
};

const { clientPrivateKey, envelope } = await encryptRequest(
  JSON.stringify(request),
  browserPublicJwk,
);

const response = await fetch(url, {
  method: "POST",
  headers: {
    accept: "application/json",
    "content-type": "application/json",
    "mcp-protocol-version": "2025-06-18",
  },
  body: JSON.stringify(envelope),
});

const responseText = await response.text();
if (!response.ok) {
  console.error(responseText);
  process.exit(1);
}

const encryptedResponse = JSON.parse(responseText);
const decrypted = await decryptResponse(
  encryptedResponse,
  clientPrivateKey,
  browserPublicJwk,
);

console.log(JSON.stringify(decrypted, null, 2));
