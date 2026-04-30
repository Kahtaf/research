import { nanoid } from "nanoid";

import "./styles.css";
import { readRequestCount, readText, writeText } from "./storage";
import { publicMcpUrl, startTunnelClient } from "./tunnel-client";

const SESSION_KEY = "browser-local-mcp-session";
const SAVE_DELAY_MS = 350;

const SAMPLE_TEXT = `Spotify export sample

Recently played tracks:
- The Strokes - Reptilia
- Yeah Yeah Yeahs - Maps
- Arctic Monkeys - Do I Wanna Know?
- The White Stripes - Seven Nation Army
- Fleetwood Mac - The Chain
- Phoebe Bridgers - Motion Sickness
- Radiohead - Weird Fishes / Arpeggi
- Tame Impala - Let It Happen

Notes:
The user tends to replay guitar-driven rock and alternative tracks in the evening. The strongest repeated artists in this sample are The Strokes, Arctic Monkeys, Radiohead, and Fleetwood Mac. Newer indie tracks appear next to older classic rock tracks, suggesting the taste is rock-centered but not limited to one decade.

Potential memory:
The user appears to like rock and alternative music, especially guitar-driven tracks.`;

type Session = {
  sessionId: string;
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
const requestCount = element<HTMLElement>("request-count");
const saveState = element<HTMLElement>("save-state");
const sourceText = element<HTMLTextAreaElement>("source-text");
const resetSampleButton = element<HTMLButtonElement>("reset-sample");
const copyUrlButton = element<HTMLButtonElement>("copy-url");
const copyConfigButton = element<HTMLButtonElement>("copy-config");
const copyCurlButton = element<HTMLButtonElement>("copy-curl");
const mcpUrlAnchor = element<HTMLAnchorElement>("mcp-url");
const codexConfig = element<HTMLPreElement>("codex-config");
const curlCommand = element<HTMLPreElement>("curl-command");
const activityLog = element<HTMLPreElement>("activity-log");

let tunnel: { close: () => void } | undefined;
let saveTimer: number | undefined;
let activeMcpUrl = "";

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
  activityLog.textContent += `[${at}] ${line}\n`;
  activityLog.scrollTop = activityLog.scrollHeight;
}

function setMcpUrl(url: string) {
  activeMcpUrl = url;
  mcpUrlAnchor.href = url;
  mcpUrlAnchor.textContent = url;
  codexConfig.textContent = `[mcp_servers.browser_text]
url = "${url}"
startup_timeout_sec = 20
tool_timeout_sec = 60`;
  curlCommand.textContent = `curl -sS '${url}' \\
  -H 'content-type: application/json' \\
  -H 'mcp-protocol-version: 2025-06-18' \\
  --data '{"jsonrpc":"2.0","id":"verify-1","method":"tools/call","params":{"name":"get_text_stats","arguments":{}}}'`;
}

async function copyText(text: string, label: string) {
  await navigator.clipboard.writeText(text);
  log(`${label} copied`);
}

function startWorkerRuntime(session: Session) {
  const worker = new Worker(new URL("./runtime-worker.ts", import.meta.url), {
    type: "module",
  });

  worker.postMessage({
    type: "init",
    sessionId: session.sessionId,
  });

  return worker;
}

async function saveSourceText(text: string) {
  saveState.textContent = "Saving";
  await writeText(text);
  saveState.textContent = "Saved";
}

function scheduleSave() {
  saveState.textContent = "Unsaved";
  if (saveTimer) {
    window.clearTimeout(saveTimer);
  }
  saveTimer = window.setTimeout(() => {
    void saveSourceText(sourceText.value).catch((error) => {
      saveState.textContent = "Error";
      log(error instanceof Error ? error.message : String(error));
    });
  }, SAVE_DELAY_MS);
}

async function loadText() {
  const stored = await readText();
  const initial = stored ?? SAMPLE_TEXT;
  sourceText.value = initial;
  if (stored === undefined) {
    await writeText(initial);
  }
  saveState.textContent = "Saved";
}

async function refreshRequestCount() {
  requestCount.textContent = String(await readRequestCount());
}

async function startTunnelMode() {
  tunnel?.close();
  const session = getSession();
  const relayHttpUrl = getDefaultRelayUrl();
  const worker = startWorkerRuntime(session);
  const url = publicMcpUrl(relayHttpUrl, session.sessionId);

  setMcpUrl(url);
  setStatus("Connecting");
  log(`session ${session.sessionId}`);

  tunnel = startTunnelClient({
    relayHttpUrl,
    sessionId: session.sessionId,
    worker,
    onLog: log,
    onStatus(status) {
      setStatus(status, status === "Connected" ? "ready" : "booting");
    },
    onResponse(body) {
      if (body) {
        log(`response ${body.length} bytes`);
      }
    },
    onCount() {
      void refreshRequestCount();
    },
  });
}

sourceText.addEventListener("input", scheduleSave);
resetSampleButton.addEventListener("click", () => {
  sourceText.value = SAMPLE_TEXT;
  void saveSourceText(SAMPLE_TEXT);
});
copyUrlButton.addEventListener("click", () => {
  if (activeMcpUrl) {
    void copyText(activeMcpUrl, "MCP URL");
  }
});
copyConfigButton.addEventListener("click", () => {
  if (codexConfig.textContent) {
    void copyText(codexConfig.textContent, "Codex config");
  }
});
copyCurlButton.addEventListener("click", () => {
  if (curlCommand.textContent) {
    void copyText(curlCommand.textContent, "curl command");
  }
});

window.addEventListener("error", (event) => {
  setStatus("Runtime error", "error");
  log(event.message);
});

void (async () => {
  await loadText();
  await refreshRequestCount();
  await startTunnelMode();
})().catch((error) => {
  setStatus("Tunnel failed", "error");
  log(error instanceof Error ? error.message : String(error));
});
