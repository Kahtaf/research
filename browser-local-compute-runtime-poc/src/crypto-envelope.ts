export type EncryptedEnvelope = {
  version: 1;
  encoding: "json";
  clientPublicKey: JsonWebKey;
  iv: string;
  ciphertext: string;
};

const textEncoder = new TextEncoder();
const textDecoder = new TextDecoder();

export function base64UrlEncode(bytes: Uint8Array) {
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary)
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replaceAll("=", "");
}

export function base64UrlDecode(value: string) {
  const padded = value.replaceAll("-", "+").replaceAll("_", "/").padEnd(
    Math.ceil(value.length / 4) * 4,
    "=",
  );
  const binary = atob(padded);
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

export function encodeJsonToken(value: unknown) {
  return base64UrlEncode(textEncoder.encode(JSON.stringify(value)));
}

export function decodeJsonToken<T>(value: string) {
  return JSON.parse(textDecoder.decode(base64UrlDecode(value))) as T;
}

export async function generateBrowserKeyPair() {
  return crypto.subtle.generateKey(
    {
      name: "ECDH",
      namedCurve: "P-256",
    },
    false,
    ["deriveKey"],
  ) as Promise<CryptoKeyPair>;
}

export async function exportPublicJwk(publicKey: CryptoKey) {
  return crypto.subtle.exportKey("jwk", publicKey);
}

export async function publicKeyFingerprint(publicJwk: JsonWebKey) {
  const fingerprintInput = JSON.stringify({
    crv: publicJwk.crv,
    kty: publicJwk.kty,
    x: publicJwk.x,
    y: publicJwk.y,
  });
  const digest = new Uint8Array(
    await crypto.subtle.digest("SHA-256", textEncoder.encode(fingerprintInput)),
  );
  return Array.from(digest.slice(0, 12), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join(":");
}

async function importEcdhPublicKey(publicJwk: JsonWebKey) {
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

async function deriveAesKey(privateKey: CryptoKey, publicJwk: JsonWebKey) {
  const publicKey = await importEcdhPublicKey(publicJwk);
  return crypto.subtle.deriveKey(
    {
      name: "ECDH",
      public: publicKey,
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

export async function encryptForRecipient(
  plaintext: string,
  recipientPublicJwk: JsonWebKey,
) {
  const clientKeyPair = await generateBrowserKeyPair();
  const clientPublicKey = await exportPublicJwk(clientKeyPair.publicKey);
  const aesKey = await deriveAesKey(clientKeyPair.privateKey, recipientPublicJwk);
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
    clientPublicKey,
    iv: base64UrlEncode(iv),
    ciphertext: base64UrlEncode(ciphertext),
  } satisfies EncryptedEnvelope;
}

export async function decryptFromClient(
  envelope: EncryptedEnvelope,
  browserPrivateKey: CryptoKey,
) {
  const aesKey = await deriveAesKey(browserPrivateKey, envelope.clientPublicKey);
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

export async function encryptToClient(
  plaintext: string,
  clientPublicJwk: JsonWebKey,
  browserPrivateKey: CryptoKey,
) {
  const aesKey = await deriveAesKey(browserPrivateKey, clientPublicJwk);
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
    iv: base64UrlEncode(iv),
    ciphertext: base64UrlEncode(ciphertext),
  };
}
