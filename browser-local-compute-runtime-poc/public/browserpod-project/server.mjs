import fs from "node:fs";

import express from "express";
import lodash from "lodash";
import { nanoid } from "nanoid";
import { z } from "zod";

const { countBy, sortBy, words } = lodash;
const PORT = 3000;
const STATE_PATH = "/project/state.json";
const CONFIG_PATH = "/project/config.json";

const config = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
const inputSchema = z
  .string()
  .trim()
  .min(1)
  .max(256)
  .regex(/^[\p{L}\p{N}\s._:-]+$/u, "input contains unsupported characters");

function readState() {
  try {
    return JSON.parse(fs.readFileSync(STATE_PATH, "utf8"));
  } catch {
    return { requestCount: 0, history: [] };
  }
}

function writeState(state) {
  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2));
}

function authorize(req, res, next) {
  if (req.headers.authorization !== `Bearer ${config.token}`) {
    res.status(401).json({
      error: "unauthorized",
      runtime: "BrowserPod Node.js",
      servedFrom: "mobile-browser-tab",
    });
    return;
  }
  next();
}

const app = express();

app.get("/health", (_req, res) => {
  res.json({
    ok: true,
    runtime: "BrowserPod Node.js",
    storage: "BrowserPod filesystem backed by browser IndexedDB",
  });
});

app.get("/api/process", authorize, (req, res) => {
  const parsed = inputSchema.safeParse(String(req.query.input ?? ""));

  if (!parsed.success) {
    res.status(400).json({
      error: "invalid_input",
      issues: parsed.error.issues.map((issue) => issue.message),
    });
    return;
  }

  const input = parsed.data;
  const tokens = words(input.toLowerCase());
  const sortedTokens = sortBy(tokens);
  const frequency = countBy(tokens);
  const result = `${input.toUpperCase()}-${nanoid(10)}`;
  const timestamp = new Date().toISOString();
  const state = readState();

  state.requestCount += 1;
  state.history = [{ input, result, at: timestamp }, ...state.history].slice(
    0,
    20,
  );
  writeState(state);

  res.setHeader("cache-control", "no-store");
  res.json({
    input,
    result,
    packageUsed: "zod + lodash + nanoid",
    requestCount: state.requestCount,
    storage: "BrowserPod filesystem backed by IndexedDB",
    runtime: "browser-local BrowserPod Node.js",
    servedFrom: "mobile-browser-tab",
    sessionId: config.sessionId,
    processing: {
      sortedTokens,
      frequency,
      tokenCount: tokens.length,
    },
    browserProof: {
      processVersion: process.version,
      platform: process.platform,
      pid: process.pid,
    },
    timestamp,
  });
});

app.listen(PORT, () => {
  console.log(`BrowserPod local API listening on ${PORT}`);
});
