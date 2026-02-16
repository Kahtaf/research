/**
 * Login page detection + login completion watcher.
 *
 * Uses a composite scoring heuristic (DOM signals, URL patterns, title/heading,
 * API 401/403) to detect login pages, and a multi-signal poll+event approach
 * to detect when the user has completed login in the open browser.
 *
 * Design follows patterns from:
 * - Cypress cy.session() validate — composite validation signals
 * - agent-browser token refresh detection — URL + DOM + API poll
 * - Crawlee SessionPool — cookie diff for auth signal capture
 * - Skyvern — never expose credentials to LLM
 */

import type { Page, BrowserContext } from 'playwright';
import type { ObservedApiCall } from '../types.js';

// --- Detection Result Types ---

export interface LoginDetectionResult {
  isLoginPage: boolean;
  confidence: 'high' | 'medium' | 'low' | 'none';
  score: number;
  signals: string[];
}

export interface LoginCompletionResult {
  completed: boolean;
  signal: string;
  durationMs: number;
  newCookies: string[];
}

// --- URL Patterns ---

const LOGIN_PATH_PATTERNS = [
  /\/login/i,
  /\/signin/i,
  /\/sign-in/i,
  /\/auth\b/i,
  /\/sso/i,
  /\/oauth/i,
  /\/session\/new/i,
  /\/accounts\/login/i,
  /\/authenticate/i,
];

const SSO_DOMAINS = [
  'accounts.google.com',
  'github.com/login',
  'login.microsoftonline.com',
  'auth0.com',
  'login.live.com',
  'appleid.apple.com',
  'id.atlassian.com',
  'login.salesforce.com',
];

const REDIRECT_PARAMS = ['redirect', 'return_to', 'next', 'continue', 'redirect_uri', 'returnUrl', 'callback'];

// --- Detection ---

/**
 * Detect whether the current page is a login/authentication page.
 *
 * Uses a scoring heuristic combining DOM signals, URL patterns,
 * title/heading text, and recent API 401/403 responses.
 */
export async function detectLoginPage(
  page: Page,
  apisSeen: ObservedApiCall[],
  targetDomain?: string,
): Promise<LoginDetectionResult> {
  let score = 0;
  const signals: string[] = [];

  const currentUrl = page.url();

  // --- URL signals ---
  try {
    const parsed = new URL(currentUrl);
    const fullUrl = parsed.hostname + parsed.pathname;

    for (const pattern of LOGIN_PATH_PATTERNS) {
      if (pattern.test(parsed.pathname)) {
        score += 25;
        signals.push(`URL path matches login pattern: ${pattern}`);
        break;
      }
    }

    for (const ssoDomain of SSO_DOMAINS) {
      if (fullUrl.startsWith(ssoDomain)) {
        score += 25;
        signals.push(`Known SSO domain: ${ssoDomain}`);
        break;
      }
    }

    for (const param of REDIRECT_PARAMS) {
      if (parsed.searchParams.has(param)) {
        score += 5;
        signals.push(`Redirect param present: ${param}`);
        break;
      }
    }
  } catch { /* invalid URL, skip */ }

  // --- DOM signals ---
  const domSignals = await page.evaluate(() => {
    const passwordFields = document.querySelectorAll('input[type="password"]');
    const hasPassword = passwordFields.length > 0;

    // Login/submit button text detection
    const buttons = document.querySelectorAll('button, input[type="submit"], [role="button"]');
    const loginButtonPatterns = /^(sign\s*in|log\s*in|continue|submit|next|authenticate)$/i;
    let hasLoginButton = false;
    for (const btn of buttons) {
      const text = (btn.textContent || '').trim();
      const value = (btn as HTMLInputElement).value || '';
      if (loginButtonPatterns.test(text) || loginButtonPatterns.test(value)) {
        hasLoginButton = true;
        break;
      }
    }

    // OAuth/SSO detection — check body text to catch divs/spans, not just buttons
    const bodyText = (document.body?.innerText || '').toLowerCase();
    const oauthProviderPattern = /(sign\s*in\s*with|continue\s*with|log\s*in\s*with)\s*(google|apple|microsoft|facebook|github|email|sso)/i;
    const hasOAuthButton = oauthProviderPattern.test(bodyText);

    // Small form field count (1-3 fields = login, >3 likely registration)
    const formFields = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"])');
    const fieldCount = formFields.length;
    const isSmallForm = fieldCount >= 1 && fieldCount <= 3;

    // Title/heading check
    const title = (document.title || '').toLowerCase();
    const h1 = (document.querySelector('h1')?.textContent || '').toLowerCase();
    const headingPattern = /(sign\s*in|log\s*in|welcome\s*back|authenticate|enter\s*your\s*(password|email))/i;
    const hasLoginHeading = headingPattern.test(title) || headingPattern.test(h1);

    // Body text login phrases — catches OAuth-first pages without password fields
    const loginTextPattern = /\b(sign\s*in|log\s*in|create\s*(an?\s*)?account|sign\s*up)\b/i;
    const hasLoginBodyText = loginTextPattern.test(bodyText);

    return {
      hasPassword,
      hasLoginButton,
      hasOAuthButton,
      isSmallForm,
      hasLoginHeading,
      hasLoginBodyText,
      fieldCount,
    };
  });

  if (domSignals.hasPassword) {
    score += 40;
    signals.push('Password field present');
  }

  if (domSignals.hasLoginButton) {
    score += 10;
    signals.push('Login/submit button detected');
  }

  if (domSignals.hasOAuthButton) {
    score += 15;
    signals.push('OAuth/SSO button detected');
  }

  if (domSignals.isSmallForm) {
    score += 5;
    signals.push(`Small form (${domSignals.fieldCount} fields)`);
  }

  if (domSignals.hasLoginHeading) {
    score += 15;
    signals.push('Login-related title/heading');
  }

  if (domSignals.hasLoginBodyText) {
    score += 15;
    signals.push('Body text contains login/sign-in phrases');
  }

  // --- API signals ---
  if (targetDomain) {
    const recentFailedApis = apisSeen.filter(
      api => api.url.includes(targetDomain) &&
        (api.status === 401 || api.status === 403) &&
        Date.now() - api.timestamp < 30_000,
    );
    if (recentFailedApis.length > 0) {
      score += 20;
      signals.push(`Recent 401/403 from target domain (${recentFailedApis.length} calls)`);
    }
  }

  // --- Threshold evaluation ---
  let confidence: LoginDetectionResult['confidence'];
  if (score >= 50) confidence = 'high';
  else if (score >= 30) confidence = 'medium';
  else if (score >= 15) confidence = 'low';
  else confidence = 'none';

  return {
    isLoginPage: score >= 30,
    confidence,
    score,
    signals,
  };
}

// --- Login Completion Watcher ---

/**
 * Wait for the user to complete login in the open browser.
 *
 * Polls every 2s for completion signals:
 * - URL navigated away from login page patterns
 * - Password field no longer in DOM
 * - New 200 response from an API that previously returned 401/403
 * - Page has substantial content (body text > 500 chars, interactive > 5)
 * - OAuth popup open + close detected
 *
 * Also captures a cookie diff (before vs after) to identify auth cookies.
 */
export async function waitForLoginCompletion(
  page: Page,
  context: BrowserContext,
  loginUrl: string,
  failedApis: ObservedApiCall[],
  timeoutMs: number = 300_000,
): Promise<LoginCompletionResult> {
  const startTime = Date.now();

  // Capture cookies before login for diff
  const cookiesBefore = new Set(
    (await context.cookies()).map(c => c.name),
  );

  // Track if a failed API now returns 200
  let apiRecovered = false;
  const failedApiPaths = failedApis
    .filter(a => a.status === 401 || a.status === 403)
    .map(a => {
      try { return new URL(a.url).pathname; } catch { return ''; }
    })
    .filter(Boolean);

  const responseListener = (r: { url: () => string; status: () => number }) => {
    if (r.status() === 200 && failedApiPaths.length > 0) {
      try {
        const path = new URL(r.url()).pathname;
        if (failedApiPaths.includes(path)) {
          apiRecovered = true;
        }
      } catch { /* ignore */ }
    }
  };
  page.on('response', responseListener);

  // Watch for OAuth popup (new tab open then close)
  let oauthPopupClosed = false;
  const popupListener = (newPage: Page) => {
    newPage.on('close', () => {
      oauthPopupClosed = true;
    });
  };
  context.on('page', popupListener);

  // Parse login URL for comparison
  let loginPath = '';
  try { loginPath = new URL(loginUrl).pathname; } catch { /* ignore */ }

  const POLL_INTERVAL = 2000;

  try {
    while (Date.now() - startTime < timeoutMs) {
      await new Promise(r => setTimeout(r, POLL_INTERVAL));

      // Signal 1: API that previously failed now returns 200 (strongest)
      if (apiRecovered) {
        return await buildResult('api_recovered', startTime, cookiesBefore, context);
      }

      // Signal 2: OAuth popup was opened and closed
      if (oauthPopupClosed) {
        // Give the page a moment to process the OAuth callback
        await new Promise(r => setTimeout(r, 2000));
        return await buildResult('oauth_popup_closed', startTime, cookiesBefore, context);
      }

      // Check page state (may have been navigated/closed)
      let currentUrl: string;
      try {
        currentUrl = page.url();
      } catch {
        // Page was closed/navigated away entirely
        return await buildResult('page_navigated', startTime, cookiesBefore, context);
      }

      // Signal 3: URL navigated away from login patterns
      try {
        const currentPath = new URL(currentUrl).pathname;
        const stillOnLogin = LOGIN_PATH_PATTERNS.some(p => p.test(currentPath));
        const sameAsLoginUrl = loginPath && currentPath === loginPath;
        if (!stillOnLogin && !sameAsLoginUrl && currentPath !== loginPath) {
          // Check that the new page has some content (not just a redirect in progress)
          const hasContent = await page.evaluate(() => {
            return (document.body?.innerText || '').trim().length > 100;
          }).catch(() => false);
          if (hasContent) {
            return await buildResult('url_changed', startTime, cookiesBefore, context);
          }
        }
      } catch { /* ignore URL parse errors */ }

      // Signal 4: Password field no longer present (SPA login)
      const noPassword = await page.evaluate(() => {
        return document.querySelectorAll('input[type="password"]').length === 0;
      }).catch(() => false);

      if (noPassword) {
        // Verify the page has substantial content (not just an intermediate state)
        const pageState = await page.evaluate(() => {
          const body = document.body;
          return {
            bodyTextLength: (body?.innerText || '').trim().length,
            interactiveElements: document.querySelectorAll(
              'button, a, input, select, textarea, [role="button"], [role="link"]',
            ).length,
          };
        }).catch(() => ({ bodyTextLength: 0, interactiveElements: 0 }));

        if (pageState.bodyTextLength > 500 && pageState.interactiveElements > 5) {
          return await buildResult('password_field_gone', startTime, cookiesBefore, context);
        }
      }
    }

    // Timeout
    return {
      completed: false,
      signal: 'timeout',
      durationMs: Date.now() - startTime,
      newCookies: [],
    };
  } finally {
    page.removeListener('response', responseListener);
    context.removeListener('page', popupListener);
  }
}

/** Build a LoginCompletionResult with cookie diff. */
async function buildResult(
  signal: string,
  startTime: number,
  cookiesBefore: Set<string>,
  context: BrowserContext,
): Promise<LoginCompletionResult> {
  const cookiesAfter = (await context.cookies()).map(c => c.name);
  const newCookies = cookiesAfter.filter(name => !cookiesBefore.has(name));

  return {
    completed: true,
    signal,
    durationMs: Date.now() - startTime,
    newCookies,
  };
}
