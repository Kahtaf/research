import { WebSocket } from "ws";

const baseUrl = process.env.WRANGLER_BASE_URL ?? "http://localhost:8788";
const sessionId = `blind-smoke-${Date.now()}`;
const marker = `cloudflare-must-not-see-${crypto.randomUUID()}`;
const textEncoder = new TextEncoder();
const textDecoder = new TextDecoder();

function base64UrlEncode(bytes) {
  return Buffer.from(bytes).toString("base64url");
}

function base64UrlDecode(value) {
  return Uint8Array.from(Buffer.from(value, "base64url"));
}

function relayBase64Decode(value) {
  return Buffer.from(value, "base64").toString("utf8");
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

async function encrypt(plaintext, privateKey, publicJwk, includeClientPublicKey) {
  const aesKey = await deriveAesKey(privateKey, publicJwk);
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
    version: 1,
    encoding: "json",
    ...(includeClientPublicKey ? { clientPublicKey: includeClientPublicKey } : {}),
    iv: base64UrlEncode(iv),
    ciphertext: base64UrlEncode(ciphertext),
  };
}

async function decrypt(envelope, privateKey, publicJwk) {
  const aesKey = await deriveAesKey(privateKey, publicJwk);
  const plaintext = await crypto.subtle.decrypt(
    {
      name: "AES-GCM",
      iv: base64UrlDecode(envelope.iv),
    },
    aesKey,
    base64UrlDecode(envelope.ciphertext),
  );
  return textDecoder.decode(plaintext);
}

function websocketUrl(url) {
  const next = new URL(url);
  next.protocol = next.protocol === "https:" ? "wss:" : "ws:";
  next.pathname = `/ws/${sessionId}`;
  next.search = "";
  return next.toString();
}

function portalUrl(url) {
  const next = new URL(url);
  next.pathname = `/portal/${sessionId}/mcp`;
  next.search = "";
  return next.toString();
}

const browserKeyPair = await generateKeyPair();
const clientKeyPair = await generateKeyPair();
const browserPublicJwk = await crypto.subtle.exportKey("jwk", browserKeyPair.publicKey);
const clientPublicJwk = await crypto.subtle.exportKey("jwk", clientKeyPair.publicKey);

const socket = new WebSocket(websocketUrl(baseUrl));
await new Promise((resolve, reject) => {
  socket.once("open", resolve);
  socket.once("error", reject);
});

let forwardedBodyWasOpaque = false;

socket.on("message", async (data) => {
  const message = JSON.parse(String(data));
  if (message.type !== "request") {
    return;
  }

  const forwardedBody = relayBase64Decode(message.body);
  if (
    forwardedBody.includes(marker) ||
    forwardedBody.includes("tools/call") ||
    forwardedBody.includes("get_text_stats")
  ) {
    socket.send(
      JSON.stringify({
        type: "response",
        requestId: message.requestId,
        status: 500,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ error: "relay_saw_plaintext" }),
      }),
    );
    return;
  }

  forwardedBodyWasOpaque = true;
  const requestEnvelope = JSON.parse(forwardedBody);
  const decryptedRequest = await decrypt(
    requestEnvelope,
    browserKeyPair.privateKey,
    requestEnvelope.clientPublicKey,
  );

  if (!decryptedRequest.includes(marker)) {
    socket.send(
      JSON.stringify({
        type: "response",
        requestId: message.requestId,
        status: 500,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ error: "browser_could_not_decrypt_marker" }),
      }),
    );
    return;
  }

  const responsePayload = JSON.stringify({
    jsonrpc: "2.0",
    id: "blind-smoke",
    result: {
      blindRelay: true,
      markerReturned: marker,
    },
  });
  const responseEnvelope = await encrypt(
    responsePayload,
    browserKeyPair.privateKey,
    requestEnvelope.clientPublicKey,
  );

  socket.send(
    JSON.stringify({
      type: "response",
      requestId: message.requestId,
      status: 200,
      headers: {
        "content-type": "application/json; charset=utf-8",
        "x-browser-local-encrypted": "1",
      },
      body: JSON.stringify(responseEnvelope),
    }),
  );
});

const requestPayload = JSON.stringify({
  jsonrpc: "2.0",
  id: "blind-smoke",
  method: "tools/call",
  params: {
    name: "get_text_stats",
    arguments: {
      marker,
    },
  },
});
const requestEnvelope = await encrypt(
  requestPayload,
  clientKeyPair.privateKey,
  browserPublicJwk,
  clientPublicJwk,
);

const response = await fetch(portalUrl(baseUrl), {
  method: "POST",
  headers: {
    "content-type": "application/json",
    "mcp-protocol-version": "2025-06-18",
  },
  body: JSON.stringify(requestEnvelope),
});

const encryptedResponse = await response.json();
if (!response.ok) {
  throw new Error(JSON.stringify(encryptedResponse));
}

const decryptedResponse = await decrypt(
  encryptedResponse,
  clientKeyPair.privateKey,
  browserPublicJwk,
);
const payload = JSON.parse(decryptedResponse);

if (!forwardedBodyWasOpaque) {
  throw new Error("relay did not forward an opaque body");
}

if (payload.result?.blindRelay !== true || payload.result?.markerReturned !== marker) {
  throw new Error("encrypted response did not round trip");
}

console.log(
  JSON.stringify(
    {
      ok: true,
      wranglerBaseUrl: baseUrl,
      sessionId,
      relaySawOnlyEnvelope: forwardedBodyWasOpaque,
      plaintextMarkerLength: marker.length,
      decryptedResponse: payload,
    },
    null,
    2,
  ),
);

socket.close();
