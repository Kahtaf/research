import { customAlphabet } from "nanoid";

import "./styles.css";
import { readRequestCount, readText, writeText } from "./storage";
import {
  reverseRelayApiCurlCommand,
  reverseRelayApiUrl,
  reverseRelayMcpCurlCommand,
  reverseRelayMcpUrl,
  startReverseRelayClient,
} from "./reverse-relay-client";

const SESSION_KEY = "browser-local-mcp-session";
const SAVE_DELAY_MS = 350;
const makeSessionId = customAlphabet("abcdefghijklmnopqrstuvwxyz0123456789", 24);

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
const copyApiUrlButton = element<HTMLButtonElement>("copy-api-url");
const copyMcpUrlButton = element<HTMLButtonElement>("copy-mcp-url");
const copyApiCurlButton = element<HTMLButtonElement>("copy-api-curl");
const copyMcpCurlButton = element<HTMLButtonElement>("copy-mcp-curl");
const apiUrlAnchor = element<HTMLAnchorElement>("api-url");
const mcpUrlAnchor = element<HTMLAnchorElement>("mcp-url");
const apiCurlCommand = element<HTMLPreElement>("api-curl-command");
const mcpCurlCommand = element<HTMLPreElement>("mcp-curl-command");
const activityLog = element<HTMLPreElement>("activity-log");

let tunnel: { close: () => void } | undefined;
let saveTimer: number | undefined;
let activeMcpUrl = "";
let activeApiUrl = "";
let activeApiCurl = "";
let activeMcpCurl = "";
let activeSessionId = "";

function getSession(): Session {
  const existing = localStorage.getItem(SESSION_KEY);
  if (existing) {
    const parsed = JSON.parse(existing) as Session;
    if (/^[a-z0-9]{12,63}$/.test(parsed.sessionId)) {
      return parsed;
    }
  }

  const session = {
    sessionId: makeSessionId(),
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

async function copyText(text: string, label: string) {
  await navigator.clipboard.writeText(text);
  log(`${label} copied`);
}

function startPlainWorkerRuntime(session: Session) {
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

async function setReverseRelayDetails(session: Session) {
  activeSessionId = session.sessionId;
  const mcpUrl = reverseRelayMcpUrl(session.sessionId);
  const apiUrl = reverseRelayApiUrl(session.sessionId);
  activeMcpUrl = mcpUrl;
  activeApiUrl = apiUrl;
  apiUrlAnchor.href = apiUrl;
  apiUrlAnchor.textContent = apiUrl;
  mcpUrlAnchor.href = mcpUrl;
  mcpUrlAnchor.textContent = mcpUrl;
  updateCurlCommands(false);
  log(`API URL ${apiUrl}`);
  log(`MCP URL ${mcpUrl}`);
}

function updateCurlCommands(trustedTls: boolean) {
  activeApiCurl = reverseRelayApiCurlCommand(activeSessionId, trustedTls);
  activeMcpCurl = reverseRelayMcpCurlCommand(activeSessionId, trustedTls);
  apiCurlCommand.textContent = activeApiCurl;
  mcpCurlCommand.textContent = activeMcpCurl;
}

async function startReverseRelayMode() {
  tunnel?.close();
  const session = getSession();
  const worker = startPlainWorkerRuntime(session);

  await setReverseRelayDetails(session);
  setStatus("Generating TLS key");
  log(`session ${session.sessionId}`);

  tunnel = await startReverseRelayClient({
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
    onTlsIdentity(identity) {
      updateCurlCommands(identity.trusted);
      log(identity.trusted ? "trusted TLS certificate ready" : "self-signed TLS certificate ready");
    },
  });
}

sourceText.addEventListener("input", scheduleSave);
resetSampleButton.addEventListener("click", () => {
  sourceText.value = SAMPLE_TEXT;
  void saveSourceText(SAMPLE_TEXT);
});
copyApiUrlButton.addEventListener("click", () => {
  if (activeApiUrl) {
    void copyText(activeApiUrl, "API URL");
  }
});
copyMcpUrlButton.addEventListener("click", () => {
  if (activeMcpUrl) {
    void copyText(activeMcpUrl, "MCP URL");
  }
});
copyApiCurlButton.addEventListener("click", () => {
  if (activeApiCurl) {
    void copyText(activeApiCurl, "API curl");
  }
});
copyMcpCurlButton.addEventListener("click", () => {
  if (activeMcpCurl) {
    void copyText(activeMcpCurl, "MCP curl");
  }
});

window.addEventListener("error", (event) => {
  setStatus("Runtime error", "error");
  log(event.message);
});

void (async () => {
  await loadText();
  await refreshRequestCount();
  await startReverseRelayMode();
})().catch((error) => {
  setStatus("Tunnel failed", "error");
  log(error instanceof Error ? error.message : String(error));
});
