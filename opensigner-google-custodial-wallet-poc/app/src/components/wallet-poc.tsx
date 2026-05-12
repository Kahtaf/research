"use client";

import { connect, WindowMessenger, type RemoteProxy } from "penpal";
import { Wallet as EthersWallet } from "ethers";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { DEMO_MESSAGE } from "@/lib/constants";

type Wallet = {
  id: string;
  address: string;
  opensignerAccountUuid: string | null;
  custodyModel: string;
  recoveryMethod: string;
};

type MeResponse =
  | { authenticated: false; signInUrl: string }
  | {
      authenticated: true;
      email: string;
      opensignerUserUuid: string;
      openSignerToken: string;
      wallet: Wallet | null;
      walletDefaults: { custodyModel: string; recoveryMethod: string };
      config: {
        iframeUrl: string;
        hotStorageUrl: string;
        shieldUrl: string;
        shieldApiKey: string;
        chainId: number;
      };
    };

type OpenSignerRemote = {
  create(request: Record<string, unknown>): Promise<Record<string, unknown>>;
  recover(request: Record<string, unknown>): Promise<Record<string, unknown>>;
  sign(request: Record<string, unknown>): Promise<Record<string, unknown>>;
  export(request: Record<string, unknown>): Promise<unknown>;
};

type Status = "idle" | "loading" | "ready" | "error";

function asString(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function extractSignature(value: unknown): string | null {
  if (!value || typeof value !== "object") return null;
  const queue: unknown[] = [value];
  while (queue.length) {
    const item = queue.shift();
    if (!item || typeof item !== "object") continue;
    for (const [key, nested] of Object.entries(item)) {
      if (
        key.toLowerCase().includes("signature") &&
        typeof nested === "string" &&
        nested.startsWith("0x")
      ) {
        return nested;
      }
      if (nested && typeof nested === "object") queue.push(nested);
    }
  }
  return null;
}

function walletAddressFromCreate(result: Record<string, unknown>): string | null {
  return asString(result.address) || asString(result.ownerAddress);
}

function privateKeyPreview(privateKey: string): string {
  if (privateKey.length <= 14) return `${privateKey.length} chars`;
  return `${privateKey.slice(0, 6)}...${privateKey.slice(-6)} (${privateKey.length} chars)`;
}

function privateKeyFromExport(result: unknown): string | null {
  if (typeof result === "string" && result.length > 0) return result;
  if (result instanceof ArrayBuffer) return bytesToPrivateKey(new Uint8Array(result));
  if (result instanceof Uint8Array) return bytesToPrivateKey(result);
  if (!result || typeof result !== "object") return null;
  if (
    Array.isArray((result as Record<string, unknown>).data) &&
    (result as Record<string, unknown>).type === "Buffer"
  ) {
    return bytesToPrivateKey(
      Uint8Array.from((result as { data: number[] }).data),
    );
  }
  return (
    asString((result as Record<string, unknown>).privateKey) ||
    asString((result as Record<string, unknown>).secret) ||
    asString((result as Record<string, unknown>).key)
  );
}

function bytesToPrivateKey(bytes: Uint8Array): string | null {
  if (bytes.length !== 32) return null;
  return `0x${Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("")}`;
}

function describeExportResult(result: unknown): Record<string, unknown> {
  if (result === null) return { resultType: "null" };
  if (result === undefined) return { resultType: "undefined" };
  if (typeof result !== "object") return { resultType: typeof result };
  return {
    resultType: typeof result,
    constructorName: result.constructor?.name,
    isArray: Array.isArray(result),
    isArrayBuffer: result instanceof ArrayBuffer,
    isUint8Array: result instanceof Uint8Array,
    byteLength:
      result instanceof ArrayBuffer || result instanceof Uint8Array
        ? result.byteLength
        : undefined,
    keys: Object.keys(result).slice(0, 12),
    error: asString((result as Record<string, unknown>).error),
    success: (result as Record<string, unknown>).success,
    action: asString((result as Record<string, unknown>).action),
    dataLength: Array.isArray((result as Record<string, unknown>).data)
      ? (result as { data: unknown[] }).data.length
      : undefined,
  };
}

function safeDebugValue(value: unknown, depth = 0): unknown {
  if (depth > 6) return "[truncated]";
  if (Array.isArray(value)) {
    return value.map((item) => safeDebugValue(item, depth + 1));
  }
  if (!value || typeof value !== "object") return value;

  const redactedKeys = new Set([
    "accesstoken",
    "authorization",
    "encryptionkey",
    "encryptionpart",
    "key",
    "privatekey",
    "publishablekey",
    "secret",
    "share",
    "shieldapikey",
    "token",
  ]);

  return Object.fromEntries(
    Object.entries(value).map(([key, nested]) => [
      key,
      redactedKeys.has(key.toLowerCase())
        ? "[redacted]"
        : safeDebugValue(nested, depth + 1),
    ]),
  );
}

function safeDebugJson(value: unknown): string {
  return JSON.stringify(safeDebugValue(value), null, 2);
}

async function writeClipboard(value: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(value);
    return;
  } catch {
    const textarea = document.createElement("textarea");
    textarea.value = value;
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    const copied = document.execCommand("copy");
    textarea.remove();
    if (!copied) throw new Error("Could not copy private key to clipboard.");
  }
}

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export function WalletPoc() {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [status, setStatus] = useState<Status>("loading");
  const [message, setMessage] = useState<string>("");
  const [signature, setSignature] = useState<string>("");
  const [verification, setVerification] = useState<string>("");
  const [privateKeyExport, setPrivateKeyExport] = useState<string>("");
  const [exportedPrivateKey, setExportedPrivateKey] = useState<string>("");
  const [rawResult, setRawResult] = useState<string>("");
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const remoteRef = useRef<RemoteProxy<OpenSignerRemote> | null>(null);

  const authenticated = me?.authenticated === true;
  const config = authenticated ? me.config : null;

  const hotStorageUrl = useMemo(() => {
    if (!config) return "";
    return config.hotStorageUrl || window.location.origin;
  }, [config]);

  const refresh = useCallback(async () => {
    setStatus("loading");
    const response = await fetch("/api/me", { cache: "no-store" });
    const nextMe = (await response.json()) as MeResponse;
    setMe(nextMe);
    setWallet(nextMe.authenticated ? nextMe.wallet : null);
    setStatus("ready");
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadInitialSession() {
      try {
        const response = await fetch("/api/me", { cache: "no-store" });
        const nextMe = (await response.json()) as MeResponse;
        if (cancelled) return;
        setMe(nextMe);
        setWallet(nextMe.authenticated ? nextMe.wallet : null);
        setStatus("ready");
      } catch {
        if (cancelled) return;
        setStatus("error");
        setMessage("Unable to load session state.");
      }
    }
    void loadInitialSession();
    return () => {
      cancelled = true;
    };
  }, []);

  const connectIframe = useCallback(async (forceReload = false) => {
    if (!authenticated || !config?.iframeUrl) {
      throw new Error("OpenSigner iframe URL is not configured.");
    }
    if (!forceReload && remoteRef.current) return remoteRef.current;
    if (forceReload) remoteRef.current = null;

    const iframe = iframeRef.current;
    if (!iframe?.contentWindow) {
      throw new Error("OpenSigner iframe did not load.");
    }

    const iframeUrl = new URL(config.iframeUrl);
    iframeUrl.searchParams.set("reload", String(Date.now()));
    await new Promise<void>((resolve, reject) => {
      const timeout = window.setTimeout(() => {
        reject(new Error("OpenSigner iframe did not finish loading."));
      }, 7000);
      iframe.onload = () => {
        window.clearTimeout(timeout);
        resolve();
      };
      iframe.onerror = () => {
        window.clearTimeout(timeout);
        reject(new Error("OpenSigner iframe failed to load."));
      };
      iframe.src = iframeUrl.toString();
    });

    if (!iframe.contentWindow) {
      throw new Error("OpenSigner iframe did not load.");
    }

    const origin = iframeUrl.origin;
    const messenger = new WindowMessenger({
      remoteWindow: iframe.contentWindow,
      allowedOrigins: [origin],
    });
    const connection = connect<OpenSignerRemote>({
      messenger,
      timeout: 20000,
      methods: {},
    });
    remoteRef.current = await connection.promise;
    return remoteRef.current;
  }, [authenticated, config]);

  const createEncryptionSession = useCallback(async () => {
    const response = await fetch("/api/shield/encryption-session", {
      method: "POST",
    });
    if (!response.ok) {
      throw new Error("Could not create Shield encryption session.");
    }
    const body = (await response.json()) as { sessionId?: string };
    if (!body.sessionId) throw new Error("Shield did not return a session.");
    return body.sessionId;
  }, []);

  const baseIframeRequest = useCallback(
    async () => {
      if (!authenticated || !config) throw new Error("Not signed in.");
      const encryptionSession = await createEncryptionSession();
      return {
        uuid: crypto.randomUUID(),
        publishableKey: me.openSignerToken,
        accessToken: me.openSignerToken,
        playerID: me.opensignerUserUuid,
        thirdPartyProvider: null,
        thirdPartyTokenType: "jwt",
        encryptionKey: null,
        encryptionPart: null,
        encryptionSession,
        openfortURL: hotStorageUrl,
        shieldURL: config.shieldUrl,
        shieldAPIKey: config.shieldApiKey,
        recovery: {
          auth: "custom",
          token: me.openSignerToken,
          authProvider: "authservice",
          tokenType: "jwt",
          encryptionSession,
        },
      };
    },
    [authenticated, config, createEncryptionSession, hotStorageUrl, me],
  );

  const createWallet = useCallback(async () => {
    if (!authenticated || !config) return;
    setMessage("Creating custodial embedded wallet through OpenSigner iframe...");
    setVerification("");
    setExportedPrivateKey("");
    setPrivateKeyExport("");
    const iframe = await connectIframe(true);
    const base = await baseIframeRequest();
    const result = await iframe.create({
      ...base,
      accountType: "Externally Owned Account",
      chainType: "EVM",
      chainId: config.chainId,
      userEntropy: null,
      projectEntropy: null,
    });
    setRawResult(safeDebugJson(result));

    const address = walletAddressFromCreate(result);
    if (!address) throw new Error("OpenSigner did not return a wallet address.");

    const saved = await fetch("/api/wallets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        address,
        opensignerAccountUuid: asString(result.account),
      }),
    });
    if (!saved.ok) throw new Error("Could not store wallet metadata.");
    const nextWallet = (await saved.json()) as Wallet;
    setWallet(nextWallet);
    setMessage("Wallet ready.");
  }, [authenticated, baseIframeRequest, config, connectIframe]);

  const recoverWallet = useCallback(
    async (iframe: RemoteProxy<OpenSignerRemote>) => {
      if (!wallet?.opensignerAccountUuid) return;
      const base = await baseIframeRequest();
      const recoverResult = await iframe.recover({
        ...base,
        account: wallet.opensignerAccountUuid,
        passkey: null,
      });
      setRawResult(safeDebugJson(recoverResult));
      if (recoverResult.success === false) {
        throw new Error(asString(recoverResult.error) || "OpenSigner recovery failed.");
      }
      await delay(750);
    },
    [baseIframeRequest, wallet],
  );

  const signMessage = useCallback(async () => {
    if (!authenticated || !wallet || !config) return;
    setMessage("Signing fixed message in the OpenSigner iframe...");
    setVerification("");
    setSignature("");

    const iframe = await connectIframe(false);
    await recoverWallet(iframe);

    const result = await iframe.sign({
      uuid: crypto.randomUUID(),
      message: new TextEncoder().encode(DEMO_MESSAGE),
      requestConfiguration: {
        token: me.openSignerToken,
        thirdPartyProvider: null,
        thirdPartyTokenType: "jwt",
        publishableKey: me.openSignerToken,
        openfortURL: hotStorageUrl,
      },
    });
    setRawResult(safeDebugJson(result));

    const nextSignature = extractSignature(result);
    if (!nextSignature) {
      setMessage("Signed, but the response shape did not include a signature field.");
      return;
    }

    setSignature(nextSignature);
    const verificationResponse = await fetch("/api/signing-audits", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        walletId: wallet.id,
        walletAddress: wallet.address,
        message: DEMO_MESSAGE,
        signature: nextSignature,
      }),
    });
    const body = (await verificationResponse.json()) as { verified?: boolean };
    setVerification(body.verified ? "Verified" : "Not verified");
    setMessage("Signature captured and audit record written.");
  }, [authenticated, config, connectIframe, hotStorageUrl, me, recoverWallet, wallet]);

  const copyPrivateKey = useCallback(async () => {
    if (!authenticated || !wallet || !config) return;
    if (exportedPrivateKey) {
      await writeClipboard(exportedPrivateKey);
      setPrivateKeyExport(`Copied ${privateKeyPreview(exportedPrivateKey)}`);
      setExportedPrivateKey("");
      setMessage("Private key copied to clipboard and verified against wallet address.");
      return;
    }

    setMessage("Exporting private key in the OpenSigner iframe...");
    setPrivateKeyExport("");

    const iframe = await connectIframe(true);
    const exportRequest = () => iframe.export({
      uuid: crypto.randomUUID(),
      requestConfiguration: {
        token: me.openSignerToken,
        thirdPartyProvider: null,
        thirdPartyTokenType: "jwt",
        publishableKey: me.openSignerToken,
        openfortURL: hotStorageUrl,
      },
    });
    let result: unknown;
    try {
      result = await exportRequest();
    } catch {
      await recoverWallet(iframe);
      result = await exportRequest();
    }
    const privateKey = privateKeyFromExport(result);
    if (!privateKey) {
      setRawResult(JSON.stringify(describeExportResult(result), null, 2));
      throw new Error("OpenSigner did not return a private key.");
    }
    const exportedAddress = new EthersWallet(privateKey).address;
    if (exportedAddress.toLowerCase() !== wallet.address.toLowerCase()) {
      throw new Error("Exported private key does not match the wallet address.");
    }

    setExportedPrivateKey(privateKey);
    setPrivateKeyExport(`Exported ${privateKeyPreview(privateKey)}`);
    setRawResult(JSON.stringify({ exported: true, copied: true }, null, 2));
    try {
      await writeClipboard(privateKey);
      setPrivateKeyExport(`Copied ${privateKeyPreview(privateKey)}`);
      setExportedPrivateKey("");
      setMessage("Private key copied to clipboard and verified against wallet address.");
    } catch {
      setRawResult(JSON.stringify({ exported: true, copied: false }, null, 2));
      setMessage(
        "Private key exported and verified. Click Copy Exported Key to copy it.",
      );
    }
  }, [
    authenticated,
    config,
    connectIframe,
    exportedPrivateKey,
    hotStorageUrl,
    me,
    recoverWallet,
    wallet,
  ]);

  async function run(action: () => Promise<void>) {
    setStatus("loading");
    try {
      await action();
      setStatus("ready");
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "Operation failed.");
    }
  }

  if (status === "loading" && !me) {
    return <main className="min-h-screen p-6 text-sm">Loading...</main>;
  }

  return (
    <main className="min-h-screen px-5 py-8 md:px-10">
      <section className="mx-auto grid max-w-5xl gap-6">
        <header className="border-b-2 border-black pb-5">
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-stone-600">
            OpenSigner POC
          </p>
          <h1 className="mt-2 max-w-3xl text-4xl font-semibold leading-tight md:text-6xl">
            Google sign-in to custodial embedded wallet signing.
          </h1>
        </header>

        <div className="border-2 border-black bg-[#fffdf6] p-5 shadow-[6px_6px_0_#181818]">
          <strong>This POC uses a custodial wallet managed by the application.</strong>
        </div>

        {!authenticated ? (
          <div className="grid gap-5 border-2 border-black bg-white p-6 md:grid-cols-[1fr_auto] md:items-center">
            <div>
              <h2 className="text-2xl font-semibold">Sign in</h2>
              <p className="mt-2 max-w-xl text-stone-700">
                Continue with Google to create an internal user and OpenSigner user UUID.
              </p>
            </div>
            <a
              href={me?.authenticated === false ? me.signInUrl : "/api/auth/google"}
              className="inline-flex h-12 items-center justify-center border-2 border-black bg-black px-5 text-sm font-semibold text-white hover:bg-stone-800"
            >
              Continue with Google
            </a>
          </div>
        ) : (
          <>
            {config?.iframeUrl ? (
              <iframe
                ref={iframeRef}
                src={config.iframeUrl}
                title="OpenSigner iframe"
                className="hidden"
                sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
              />
            ) : null}

            <section className="grid gap-4 border-2 border-black bg-white p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-mono text-xs uppercase tracking-[0.16em] text-stone-500">
                    Logged in Google email
                  </p>
                  <p className="mt-1 text-lg font-semibold">{me.email}</p>
                </div>
                <button
                  className="h-10 border-2 border-black px-4 text-sm font-semibold hover:bg-stone-100"
                  onClick={() => run(async () => {
                    await fetch("/api/auth/logout", { method: "POST" });
                    await refresh();
                  })}
                >
                  Sign out
                </button>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <Info label="Wallet type" value="Custodial embedded wallet" />
                <Info label="Recovery method" value="automatic" />
                <Info label="Wallet address" value={wallet?.address || "Not created"} wide />
                <Info label="Fixed message" value={DEMO_MESSAGE} wide />
              </div>

              <div className="flex flex-wrap gap-3">
                <button
                  disabled={status === "loading" || !config?.iframeUrl || Boolean(wallet)}
                  onClick={() => run(createWallet)}
                  className="h-11 border-2 border-black bg-[#d8ff5f] px-4 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {wallet ? "Wallet Created" : "Create Wallet"}
                </button>
                <button
                  disabled={status === "loading" || !wallet || !config?.iframeUrl}
                  onClick={() => run(signMessage)}
                  className="h-11 border-2 border-black bg-black px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Sign Message
                </button>
                <button
                  disabled={status === "loading" || !wallet || !config?.iframeUrl}
                  onClick={() => run(copyPrivateKey)}
                  className="h-11 border-2 border-black bg-white px-4 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {exportedPrivateKey ? "Copy Exported Key" : "Export / Copy Private Key"}
                </button>
              </div>
            </section>

            <section className="grid gap-4 border-2 border-black bg-[#fffdf6] p-5">
              <Info label="Status" value={message || "Ready"} wide />
              <Info label="Signature output" value={signature || "No signature yet"} wide mono />
              <Info label="Verification result" value={verification || "Not run"} />
              <Info label="Private key export" value={privateKeyExport || "Not exported"} />
              <details className="border-t border-stone-300 pt-3">
                <summary className="cursor-pointer text-sm font-semibold">
                  Raw OpenSigner response
                </summary>
                <pre className="mt-3 max-h-72 overflow-auto bg-black p-4 text-xs text-white">
                  {rawResult || "{}"}
                </pre>
              </details>
            </section>
          </>
        )}
      </section>
    </main>
  );
}

function Info({
  label,
  value,
  wide,
  mono,
}: {
  label: string;
  value: string;
  wide?: boolean;
  mono?: boolean;
}) {
  return (
    <div className={wide ? "md:col-span-2" : undefined}>
      <p className="font-mono text-xs uppercase tracking-[0.16em] text-stone-500">
        {label}
      </p>
      <p
        className={`mt-1 break-words text-sm ${mono ? "font-mono" : "font-semibold"}`}
      >
        {value}
      </p>
    </div>
  );
}
