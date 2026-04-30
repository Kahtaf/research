import { nanoid } from "nanoid";

import "./styles.css";
import { startBrowserPod } from "./browserpod";
import { publicApiUrl, startTunnelClient } from "./tunnel-client";

const SESSION_KEY = "browser-local-api-session";

type Session = {
  sessionId: string;
  token: string;
};

function element<T extends HTMLElement>(id: string) {
  const node = document.getElementById(id);
  if (!node) {
    throw new Error(`missing #${id}`);
  }
  return node as T;
}

const statusDot = element<HTMLSpanElement>("status-dot");
const statusText = element<HTMLSpanElement>("status-text");
const modeLabel = element<HTMLElement>("mode-label");
const requestCount = element<HTMLElement>("request-count");
const relayInput = element<HTMLInputElement>("relay-url");
const browserPodKey = element<HTMLInputElement>("browserpod-key");
const startTunnelButton = element<HTMLButtonElement>("start-tunnel");
const startBrowserPodButton = element<HTMLButtonElement>("start-browserpod");
const copyCurlButton = element<HTMLButtonElement>("copy-curl");
const publicUrlAnchor = element<HTMLAnchorElement>("public-url");
const curlCommand = element<HTMLPreElement>("curl-command");
const lastResponse = element<HTMLPreElement>("last-response");
const terminal = element<HTMLPreElement>("terminal");

let activePublicUrl = "";
let activeToken = "";
let tunnel: { close: () => void } | undefined;

function getDefaultRelayUrl() {
  const envRelay = import.meta.env.VITE_RELAY_HTTP_URL as string | undefined;
  if (envRelay) {
    return envRelay;
  }

  const url = new URL(window.location.href);
  const isLocalDevHost =
    url.hostname === "localhost" ||
    url.hostname === "127.0.0.1" ||
    url.hostname === "[::1]";

  if (isLocalDevHost) {
    url.port = "8787";
  }

  url.pathname = "/";
  url.search = "";
  url.hash = "";
  return url.toString();
}

function getSession(): Session {
  const existing = localStorage.getItem(SESSION_KEY);
  if (existing) {
    return JSON.parse(existing) as Session;
  }

  const session = {
    sessionId: nanoid(24),
    token: nanoid(32),
  };
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  return session;
}

function setStatus(text: string, state: "booting" | "ready" | "error" = "booting") {
  statusText.textContent = text;
  statusDot.dataset.state = state;
}

function log(line: string) {
  const at = new Date().toLocaleTimeString();
  terminal.textContent += `[${at}] ${line}\n`;
  terminal.scrollTop = terminal.scrollHeight;
}

function setPublicUrl(url: string, token: string) {
  activePublicUrl = url;
  activeToken = token;
  publicUrlAnchor.href = url;
  publicUrlAnchor.textContent = url;
  curlCommand.textContent = `curl -H "Authorization: Bearer ${token}" "${url}"`;
}

async function copyCurl() {
  if (!curlCommand.textContent) {
    return;
  }
  await navigator.clipboard.writeText(curlCommand.textContent);
  log("curl command copied");
}

function startWorkerRuntime(session: Session) {
  const worker = new Worker(new URL("./runtime-worker.ts", import.meta.url), {
    type: "module",
  });

  worker.postMessage({
    type: "init",
    token: session.token,
    sessionId: session.sessionId,
  });

  return worker;
}

async function startTunnelMode() {
  tunnel?.close();
  const session = getSession();
  const relayHttpUrl = relayInput.value.trim();
  const worker = startWorkerRuntime(session);
  const publicUrl = publicApiUrl(relayHttpUrl, session.sessionId);

  modeLabel.textContent = "Tunnel worker";
  setPublicUrl(publicUrl, session.token);
  setStatus("Connecting tunnel");
  log(`session ${session.sessionId}`);

  tunnel = startTunnelClient({
    relayHttpUrl,
    sessionId: session.sessionId,
    token: session.token,
    worker,
    onLog: log,
    onStatus(status) {
      setStatus(status, status.includes("connected") ? "ready" : "booting");
    },
    onResponse(body) {
      lastResponse.textContent = body;
    },
    onCount(count) {
      requestCount.textContent = String(count);
    },
  });
}

async function startBrowserPodMode() {
  const apiKey = browserPodKey.value.trim();
  if (!apiKey) {
    setStatus("BrowserPod key required", "error");
    log("BrowserPod mode needs a BrowserPod API key");
    return;
  }

  const session = getSession();
  modeLabel.textContent = "BrowserPod Portal";
  setStatus("Booting BrowserPod");

  await startBrowserPod({
    apiKey,
    token: session.token,
    sessionId: session.sessionId,
    terminal,
    onLog: log,
    onPortal(url) {
      setPublicUrl(url, session.token);
      setStatus("Portal ready", "ready");
    },
  });
}

relayInput.value = getDefaultRelayUrl();
browserPodKey.value =
  (import.meta.env.VITE_BROWSERPOD_API_KEY as string | undefined) ?? "";

copyCurlButton.addEventListener("click", () => void copyCurl());
startTunnelButton.addEventListener("click", () => void startTunnelMode());
startBrowserPodButton.addEventListener("click", () => void startBrowserPodMode());

window.addEventListener("error", (event) => {
  setStatus("Runtime error", "error");
  log(event.message);
});

void startTunnelMode().catch((error) => {
  setStatus("Tunnel failed", "error");
  log(error instanceof Error ? error.message : String(error));
});

export { activePublicUrl, activeToken };
