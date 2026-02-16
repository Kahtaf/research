/**
 * Explorer — AI agent loop for autonomous site exploration.
 *
 * Launches a browser, navigates to a site, and uses an LLM to decide
 * what actions to take. Records all API traffic via HAR and tracks
 * observed API calls for pattern detection.
 *
 * Inspired by Skyvern's agent_step() loop: plan → act → observe → record → evaluate.
 */

import { launchProfile } from '../browser/stealth.js';
import { readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { getEnhancedSnapshot, getSnapshotStats } from '../browser/snapshot.js';
import { waitForNetworkSettle } from '../browser/network-settle.js';
import { getPageStats, formatPageStats } from '../browser/page-stats.js';
import { initArtifactBundle, recordPageStats, appendRunLog } from '../browser/artifacts.js';
import { detectLoginPage, waitForLoginCompletion } from '../browser/login-detect.js';
import type {
  ActionWithIntent,
  AuthSignal,
  ExploreDecision,
  ExploreResult,
  LlmProvider,
  ObservedApiCall,
} from '../types.js';

const MAX_STEPS = 30;

interface ExploreOptions {
  task: string;
  url: string;
  llm: LlmProvider;
  chromePath?: string;
  headless?: boolean;
  sessionsDir: string;
}

/** Check if a response looks like an API response (JSON, non-trivial). */
function isApiResponse(url: string, status: number, contentType: string | null): boolean {
  // Skip static assets
  if (/\.(css|js|png|jpg|gif|svg|woff|ico|map)(\?|$)/i.test(url)) return false;

  // Skip common tracking/analytics
  const skipDomains = [
    'google-analytics.com', 'googletagmanager.com', 'facebook.com',
    'sentry.io', 'mixpanel.com', 'segment.io', 'hotjar.com',
    'cdn.jsdelivr.net', 'unpkg.com', 'cdnjs.cloudflare.com',
  ];
  try {
    const hostname = new URL(url).hostname;
    if (skipDomains.some(d => hostname.includes(d))) return false;
  } catch { return false; }

  // Must have a reasonable status
  if (status < 200 || status >= 600) return false;

  // Prefer JSON responses but also capture other API-like responses
  const ct = contentType?.toLowerCase() ?? '';
  if (ct.includes('json')) return true;
  if (ct.includes('text/html')) return false;
  if (ct.includes('text/css')) return false;
  if (ct.includes('javascript')) return false;

  // API-like paths
  if (url.includes('/api/') || url.includes('/graphql') || url.includes('/v1/') || url.includes('/v2/')) {
    return true;
  }

  return false;
}

/**
 * Load the explore system prompt from prompts/explore.md
 */
function loadExplorePrompt(): string {
  try {
    // Try relative to the package root
    const promptPath = resolve(import.meta.dirname, '../../prompts/explore.md');
    return readFileSync(promptPath, 'utf-8');
  } catch {
    // Fallback inline prompt
    return 'You are a web exploration agent. Respond with JSON actions.';
  }
}

const MAX_LOGIN_PAUSES = 2;
const LOGIN_TIMEOUT_MS = 300_000; // 5 minutes

/**
 * Handle a detected login page: pause for user login, wait for completion.
 *
 * Returns an AuthSignal if login completed, or null if it timed out / was skipped.
 */
async function handleLoginPause(
  page: import('playwright').Page,
  context: import('playwright').BrowserContext,
  detection: import('../browser/login-detect.js').LoginDetectionResult,
  apisSeen: ObservedApiCall[],
  headless: boolean,
  sessionDir: string,
): Promise<AuthSignal | null> {
  const loginUrl = page.url();

  // In headless mode, we can't pause for user login
  if (headless) {
    console.log(`  Login required but running headless. Run \`data-agent login <url>\` first.`);
    appendRunLog(sessionDir, `Login detected (headless) — aborting: ${loginUrl}`);
    return null;
  }

  console.log(`  Login required! Detected login page (${detection.confidence} confidence)`);
  console.log(`  Signals: ${detection.signals.join(', ')}`);
  console.log('  Please log in using the open browser window.');
  console.log('  Exploration will resume automatically after login.\n');

  appendRunLog(sessionDir, `Login pause: ${loginUrl} — signals: ${detection.signals.join(', ')}`);

  // Gather failed APIs for completion detection
  const failedApis = apisSeen.filter(a => a.status === 401 || a.status === 403);

  const completion = await waitForLoginCompletion(
    page, context, loginUrl, failedApis, LOGIN_TIMEOUT_MS,
  );

  if (!completion.completed) {
    console.log('  Login timed out. Run `data-agent login <url>` to log in first, then retry.');
    appendRunLog(sessionDir, `Login timeout after ${LOGIN_TIMEOUT_MS / 1000}s`);
    return null;
  }

  console.log(`  Login completed! (signal: ${completion.signal}, ${(completion.durationMs / 1000).toFixed(1)}s)`);
  if (completion.newCookies.length > 0) {
    console.log(`  New auth cookies: ${completion.newCookies.join(', ')}`);
  }
  appendRunLog(sessionDir, `Login complete: signal=${completion.signal} newCookies=[${completion.newCookies.join(',')}]`);

  return {
    loginUrl,
    completionSignal: completion.signal,
    newCookies: completion.newCookies,
    failedApisBeforeLogin: failedApis.map(a => ({ url: a.url, status: a.status })),
    timestamp: Date.now(),
  };
}

/**
 * Run the explore agent loop.
 *
 * Launches browser → navigates → agent loop (snapshot → LLM → act → record) → close.
 */
export async function explore(options: ExploreOptions): Promise<ExploreResult> {
  const { task, url, llm, chromePath, headless = false, sessionsDir } = options;

  // Create session directory with artifact bundle
  const sessionId = `session-${Date.now()}`;
  const sessionDir = join(sessionsDir, sessionId);
  initArtifactBundle(sessionDir);

  const harPath = join(sessionDir, 'recording.har');

  console.log(`  Session: ${sessionDir}`);
  console.log(`  HAR: ${harPath}`);
  appendRunLog(sessionDir, `Explore started: task="${task}" url="${url}"`);

  // Launch browser with persistent profile
  const { context, page, close } = await launchProfile({
    headless,
    chromePath,
    recordHar: { path: harPath, mode: 'full' },
  });

  const actions: ActionWithIntent[] = [];
  const apisSeen: ObservedApiCall[] = [];
  const authSignals: AuthSignal[] = [];
  let loginPauseCount = 0;

  // Track all API responses
  page.on('response', (r) => {
    const respUrl = r.url();
    const status = r.status();
    const contentType = r.headers()['content-type'] ?? null;

    if (isApiResponse(respUrl, status, contentType)) {
      apisSeen.push({
        url: respUrl,
        method: r.request().method(),
        status,
        contentType: contentType ?? undefined,
        timestamp: Date.now(),
      });
    }
  });

  // Navigate to starting URL
  // Use network-settle instead of waitForLoadState('networkidle')
  // Adapted from Stagehand's waitForDomNetworkQuiet():
  // @see https://github.com/browserbase/stagehand/blob/main/packages/core/lib/v3/handlers/handlerUtils/actHandlerUtils.ts L537–L679
  console.log(`  Navigating to ${url}...`);
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30_000 });
  await waitForNetworkSettle(page, { quietMs: 500, timeoutMs: 5000 });

  // Check for login page after initial navigation
  let targetDomain: string | undefined;
  try { targetDomain = new URL(url).hostname; } catch { /* ignore */ }

  const initialLoginCheck = await detectLoginPage(page, apisSeen, targetDomain);
  if (initialLoginCheck.isLoginPage && loginPauseCount < MAX_LOGIN_PAUSES) {
    loginPauseCount++;
    const signal = await handleLoginPause(page, context, initialLoginCheck, apisSeen, headless, sessionDir);
    if (signal) {
      authSignals.push(signal);
      // Wait for network to settle after login, then navigate back to target
      await waitForNetworkSettle(page, { quietMs: 1000, timeoutMs: 8000 });
      const currentUrl = page.url();
      if (!currentUrl.includes(targetDomain ?? '')) {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30_000 });
        await waitForNetworkSettle(page, { quietMs: 500, timeoutMs: 5000 });
      }
    } else {
      // Login failed/timed out or headless — abort exploration
      await close();
      return { harPath, actions, apisSeen, sessionDir, authSignals };
    }
  }

  const systemPrompt = loadExplorePrompt();

  /** Count consecutive blocked-page detections for early bail. */
  let consecutiveBlocked = 0;

  // Agent loop
  for (let step = 0; step < MAX_STEPS; step++) {
    try {
      // 1. OBSERVE: Take compact accessibility snapshot
      const { tree: snapshot, refs: refMap } = await getEnhancedSnapshot(page, {
        interactive: true,
        cursor: true,
        compact: true,
      });

      const snapshotStats = getSnapshotStats(snapshot, refMap);

      // Collect page stats for blocked-page detection
      // Inspired by browser-use _extract_page_statistics():
      // @see https://github.com/browser-use/browser-use/blob/main/browser_use/agent/prompts.py
      const pageStats = await getPageStats(page);
      recordPageStats(sessionDir, step, pageStats);

      const statsStr = formatPageStats(pageStats);
      console.log(`  Step ${step + 1}: snapshot ${snapshotStats.refs} refs, ~${snapshotStats.tokens} tokens ${statsStr}`);

      // Blocked-page early bail
      if (pageStats.isLikelyBlocked) {
        consecutiveBlocked++;
        appendRunLog(sessionDir, `Step ${step + 1}: blocked detection — ${pageStats.blockReason}`);
        if (consecutiveBlocked >= 2) {
          console.log(`  Blocked page detected (${consecutiveBlocked}x consecutive): ${pageStats.blockReason}`);
          console.log('  Stopping exploration — site appears to be blocking automation.');
          appendRunLog(sessionDir, 'Exploration stopped: consecutive blocked page detections');
          break;
        }
      } else {
        consecutiveBlocked = 0;
      }

      // Login page detection (only if not already blocked)
      if (!pageStats.isLikelyBlocked && loginPauseCount < MAX_LOGIN_PAUSES) {
        const loginCheck = await detectLoginPage(page, apisSeen, targetDomain);
        if (loginCheck.isLoginPage) {
          loginPauseCount++;
          const signal = await handleLoginPause(page, context, loginCheck, apisSeen, headless, sessionDir);
          if (signal) {
            authSignals.push(signal);
            await waitForNetworkSettle(page, { quietMs: 1000, timeoutMs: 8000 });
            // Navigate back to target if we ended up somewhere else
            const currentUrl = page.url();
            if (targetDomain && !currentUrl.includes(targetDomain)) {
              await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30_000 });
              await waitForNetworkSettle(page, { quietMs: 500, timeoutMs: 5000 });
            }
            continue; // re-snapshot after login
          } else {
            // Login failed/timed out or headless — abort
            appendRunLog(sessionDir, 'Exploration stopped: login required but could not complete');
            break;
          }
        }
      }

      // 2. PLAN: Ask LLM what to do next
      const userPrompt = buildExplorePrompt(task, snapshot, actions, apisSeen, statsStr);
      const decision = await llm.generateJson<ExploreDecision>(systemPrompt, userPrompt);

      console.log(`    Action: ${decision.done ? 'DONE' : decision.action} — ${decision.reasoning.slice(0, 80)}`);

      if (decision.done) break;

      // 3. ACT: Execute the decision
      if (decision.action === 'click' && decision.ref) {
        const refData = refMap[decision.ref];
        if (refData) {
          const locator = buildLocator(page, refData);
          await locator.click({ timeout: 10_000 }).catch((err: Error) => {
            console.log(`    Click failed: ${err.message.slice(0, 60)}`);
          });
        } else {
          console.log(`    Ref ${decision.ref} not found in snapshot`);
        }
      } else if (decision.action === 'type' && decision.ref && decision.text) {
        const refData = refMap[decision.ref];
        if (refData) {
          const locator = buildLocator(page, refData);
          await locator.fill(decision.text, { timeout: 10_000 }).catch((err: Error) => {
            console.log(`    Type failed: ${err.message.slice(0, 60)}`);
          });
        }
      } else if (decision.action === 'scroll') {
        await page.evaluate(() => window.scrollBy(0, 500));
      } else if (decision.action === 'navigate' && decision.url) {
        await page.goto(decision.url, { waitUntil: 'domcontentloaded', timeout: 30_000 });
      } else if (decision.action === 'wait') {
        await page.waitForTimeout(2000);
      } else if (decision.action === 'press' && decision.key) {
        await page.keyboard.press(decision.key);
      }

      // Wait for network to settle after action (Stagehand pattern)
      await waitForNetworkSettle(page, { quietMs: 500, timeoutMs: 5000 });

      // 4. RECORD: Store action with intent metadata
      actions.push({
        step,
        action: decision.action ?? 'wait',
        ref: decision.ref,
        text: decision.text,
        url: decision.url,
        key: decision.key,
        reasoning: decision.reasoning,
        intention: decision.intention,
        confidence: decision.confidence,
        timestamp: Date.now(),
      });
    } catch (err) {
      console.log(`    Step ${step + 1} error: ${err instanceof Error ? err.message.slice(0, 80) : String(err)}`);
    }
  }

  // Close browser and save HAR
  await close();

  // Save session metadata
  const sessionMeta = {
    id: sessionId,
    task,
    url,
    actions,
    apisSeen,
    authSignals,
    createdAt: new Date().toISOString(),
  };
  writeFileSync(join(sessionDir, 'session.json'), JSON.stringify(sessionMeta, null, 2));

  appendRunLog(sessionDir, `Explore complete: ${actions.length} actions, ${apisSeen.length} APIs observed`);
  console.log(`  Explore complete: ${actions.length} actions, ${apisSeen.length} APIs observed`);

  return { harPath, actions, apisSeen, sessionDir, authSignals };
}

/**
 * Build the user prompt for an explore step.
 */
function buildExplorePrompt(
  task: string,
  snapshot: string,
  actions: ActionWithIntent[],
  apisSeen: ObservedApiCall[],
  pageStatsStr?: string,
): string {
  const parts: string[] = [];

  parts.push(`## Task\n${task}\n`);

  // Inject page stats for LLM context (browser-use pattern)
  if (pageStatsStr) {
    parts.push(`## Page Statistics\n${pageStatsStr}\n`);
  }

  parts.push(`## Current Page Snapshot\n${snapshot}\n`);

  if (actions.length > 0) {
    parts.push('## Actions Taken So Far');
    for (const a of actions.slice(-10)) {
      parts.push(`${a.step + 1}. ${a.action}${a.ref ? ` @${a.ref}` : ''}${a.text ? ` "${a.text}"` : ''} — ${a.intention}`);
    }
    parts.push('');
  }

  if (apisSeen.length > 0) {
    parts.push('## API Calls Observed');
    // Deduplicate by URL pattern
    const seen = new Map<string, { method: string; status: number; count: number }>();
    for (const api of apisSeen) {
      const key = `${api.method} ${api.url.split('?')[0]}`;
      const existing = seen.get(key);
      if (existing) {
        existing.count++;
      } else {
        seen.set(key, { method: api.method, status: api.status, count: 1 });
      }
    }
    for (const [pattern, info] of seen) {
      parts.push(`- ${pattern} (${info.status}) x${info.count}`);
    }
    parts.push('');
  }

  parts.push(`Step ${actions.length + 1}: What should I do next? Respond with JSON.`);

  return parts.join('\n');
}

/**
 * Build a Playwright locator from ref data.
 */
function buildLocator(page: import('playwright').Page, refData: { selector: string; role: string; name?: string; nth?: number }) {
  // For cursor-interactive elements, use CSS selector directly
  if (refData.role === 'clickable' || refData.role === 'focusable') {
    return page.locator(refData.selector);
  }

  // For ARIA elements, use getByRole
  const roleOptions: { name?: string; exact?: boolean } = {};
  if (refData.name) {
    roleOptions.name = refData.name;
    roleOptions.exact = true;
  }

  let locator = page.getByRole(refData.role as any, roleOptions);

  if (refData.nth !== undefined) {
    locator = locator.nth(refData.nth);
  }

  return locator;
}
