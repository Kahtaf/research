# Plan: Automatic Login Detection & Handling During Exploration

## Context

Currently the data-agent has a separate `login` command that must be run beforehand, and the auto-mode pipeline blindly assumes auth is available via the persistent browser profile. If a site requires login during exploration, the agent either gets stuck on a login page or produces garbage results. Generated scripts also assume auth is present and fail silently with empty output when it's not.

This change makes the agent **detect login pages in real-time during exploration**, **pause and prompt the user to log in using the already-open browser**, **auto-detect when login completes**, and **resume exploration**. Generated scripts will also **verify login state before proceeding** rather than assuming it.

---

## Stage 1: Login Detection Module

**New file**: `src/browser/login-detect.ts`

Create `detectLoginPage(page, apisSeen, targetDomain)` using a scoring heuristic (following the `page-stats.ts` pattern of `page.evaluate` + Node-side pattern matching):

**DOM signals** (via `page.evaluate`):
- `input[type="password"]` exists → +40 pts
- Login/submit button text ("Sign in", "Log in", "Continue") → +10 pts
- OAuth/SSO buttons ("Sign in with Google", etc.) → +15 pts
- Small form field count (1-3 fields, distinguishes from registration) → +5 pts

**URL signals**:
- Path contains `/login`, `/signin`, `/sign-in`, `/auth`, `/sso`, `/oauth`, `/session/new`, `/accounts/login` → +25 pts
- Known SSO domains (`accounts.google.com`, `github.com/login`, `login.microsoftonline.com`) → +25 pts
- Redirect query params (`redirect`, `return_to`, `next`, `continue`) → +5 pts

**Title/heading signals**:
- Title/h1 matches "sign in", "log in", "welcome back" → +15 pts

**API signals**:
- Recent 401/403 from target domain in `apisSeen` → +20 pts

**Thresholds**: >=50 = high confidence, >=30 = medium, >=15 = low. `isLoginPage = true` when >=30.

**Returns**: `LoginDetectionResult { isLoginPage, confidence, signals: string[] }`

---

## Stage 2: Login Completion Watcher

**Same file**: `src/browser/login-detect.ts`

Create `waitForLoginCompletion(page, context, loginUrl, failedApis, timeoutMs=300_000)` that resolves when login appears complete:

**Completion signals** (poll every 2s + event listeners):
- URL navigated away from login page patterns
- `input[type="password"]` no longer in DOM
- New 200 response from an API that previously returned 401/403
- Page has substantial content (bodyTextLength > 500, interactiveElements > 5)
- For OAuth popups: `context.on('page')` to detect popup close + original page reload

**Cookie diff**: Capture cookie names before login, diff after to identify auth cookies (stored as `newCookies` for use in generated scripts).

**Returns**: `LoginCompletionResult { completed, signal, durationMs, newCookies }`

---

## Stage 3: Explorer Integration

**File**: `src/explore/explorer.ts`

Insert login detection **after the blocked-page check** (line ~177) and **before the LLM decision** (line ~180) in the agent loop. Also check **after initial navigation** (line ~137) before the loop starts.

**Flow**:
```
navigate to seed URL
→ CHECK FOR LOGIN PAGE (new)
→ if login: pause, prompt, wait for completion, navigate back to target
→ agent loop:
    snapshot → page stats → blocked check
    → CHECK FOR LOGIN PAGE (new, only if not blocked)
    → if login: pause, prompt, wait, continue loop
    → LLM decide → act → record
```

**Key details**:
- Track `loginPauseCount` — cap at 2 per session to prevent infinite loops
- Track `authSignals: AuthSignal[]` — record login URL, completion signal, new cookies, failed APIs
- After login completion, wait for network settle (longer: 1000ms quiet), then navigate back to target URL if needed
- In headless mode, skip pause — log warning "Login required but running headless. Run `data-agent login <url>` first." and treat as blocked

**CLI output during login pause**:
```
  Login required! Detected login page (high confidence)
  Signals: password field present, URL contains /login
  Please log in using the open browser window.
  Exploration will resume automatically after login.
```

---

## Stage 4: Page Stats Fix — Don't Flag Login Pages as Blocked

**File**: `src/browser/page-stats.ts`

The sparse-page heuristic (lines 141-144) currently flags pages with <3 interactive elements and <30 total as blocked. Login pages can be sparse too. Add an exclusion: if the page has a password input, it's a login page, not a blocked page.

Add to the `page.evaluate` return: `hasPasswordField: !!document.querySelector('input[type="password"]')`.

In the sparse-page check, add: `&& !stats.hasPasswordField`.

---

## Stage 5: Types & Data Flow

**File**: `src/types.ts`

Add:
```typescript
interface AuthSignal {
  loginUrl: string;
  completionSignal: string;
  newCookies: string[];
  failedApisBeforeLogin: Array<{ url: string; status: number }>;
  timestamp: number;
}
```

Update `ExploreResult` — add `authSignals: AuthSignal[]`.

Update `AnalysisResult` — add optional `authSignals?: AuthSignal[]`.

---

## Stage 6: Pass Auth Signals Through Analysis → Generation

**File**: `src/analyze/har-analyzer.ts` — in `analyze()`, pass through `exploreResult.authSignals` to the returned `AnalysisResult`.

**File**: `src/generate/script-generator.ts` — in `buildGeneratePrompt()`, if `analysis.authSignals` has entries, add an "Auth Signals" section listing login URL, auth cookie names, and APIs that required auth. This gives the LLM concrete data for generating login-state checks.

---

## Stage 7: Prompt Updates

**File**: `prompts/explore.md` — Add section:
```
## Login Page Handling
If you detect a login page (password fields, "Sign in" buttons, OAuth prompts):
- Do NOT fill in credentials or click login buttons
- Use action "wait" with reasoning explaining you see a login page
- The system will pause for user authentication automatically
```

**File**: `prompts/generate.md` — Add section after auth/stealth (new priority 8):
```
8) Login state verification:
   - After navigating, check if you're logged in before extracting data
   - Use auth signals (cookie names, test API endpoints) provided in context
   - If not logged in: console.error('ERROR: Not logged in. Run: data-agent login <url>'); process.exit(2);
   - Do NOT attempt to fill in credentials
```

---

## Stage 8: Validator Auth Detection

**File**: `src/validate/validator.ts` — Add pattern to `classifyError()`:
```typescript
if (/ERROR: Not logged in/i.test(combined) || exitCode === 2) {
  // ... auth_required classification
}
```

**File**: `src/index.ts` — Update the auth message in `runAutoMode()`:
```
Auth: Using persistent browser profile
If login is needed during exploration, you will be prompted in the browser.
```

---

## Files Modified (summary)

| File | Change |
|------|--------|
| `src/browser/login-detect.ts` | **NEW** — detection heuristics + completion watcher |
| `src/browser/page-stats.ts` | Exclude login pages from blocked-page detection |
| `src/explore/explorer.ts` | Login check after initial nav + in agent loop, pause/resume, track authSignals |
| `src/types.ts` | Add `AuthSignal`, update `ExploreResult`, `AnalysisResult` |
| `src/analyze/har-analyzer.ts` | Pass through `authSignals` |
| `src/generate/script-generator.ts` | Include auth signals in generation prompt |
| `prompts/explore.md` | Login page handling guidance for LLM |
| `prompts/generate.md` | Login state verification instructions |
| `src/validate/validator.ts` | Recognize "Not logged in" / exit code 2 |
| `src/index.ts` | Update auth status message |

## Verification

1. **Build**: `npx tsc --noEmit` — verify no type errors
2. **Manual test (auth site)**: `npx tsx src/index.ts "get my chatgpt conversations"` — verify login pause appears, login in browser works, exploration resumes
3. **Manual test (public site)**: `npx tsx src/index.ts "get hacker news top stories"` — verify no false-positive login detection
4. **Manual test (headless)**: `npx tsx src/index.ts --headless "get my github repos"` — verify headless warning
5. **Generated script test**: After successful exploration with login, run the generated `automation.ts` directly — verify it checks login state and fails clearly if not logged in
