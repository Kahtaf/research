/**
 * iCloud Notes Connector
 *
 * Authenticates with Apple ID (handling cross-origin auth iframe via CDP keyboard),
 * handles 2FA, then captures CloudKit API responses to extract all notes.
 */

// ── Helpers ──────────────────────────────────────────────────────────

function decodeBase64(value) {
  if (!value) return null;
  try {
    return atob(value);
  } catch {
    return null;
  }
}

function timestampToISO(ts) {
  if (!ts) return null;
  return new Date(ts).toISOString();
}

async function tryDecompress(bytes, format) {
  const ds = new DecompressionStream(format);
  const writer = ds.writable.getWriter();
  const reader = ds.readable.getReader();

  const chunks = [];
  const readAll = (async () => {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
    }
  })();

  writer.write(bytes);
  writer.close();
  await readAll;

  const decompressed = new Uint8Array(
    chunks.reduce((acc, c) => acc + c.length, 0),
  );
  let offset = 0;
  for (const chunk of chunks) {
    decompressed.set(chunk, offset);
    offset += chunk.length;
  }
  return decompressed;
}

function extractCleanText(decompressedBytes) {
  const decoder = new TextDecoder("utf-8", { fatal: false });
  const fullText = decoder.decode(decompressedBytes);

  const textRuns = [];
  const runRe = /[\x20-\x7E\u00A0-\uFFFF]{4,}/g;
  let match;
  while ((match = runRe.exec(fullText)) !== null) {
    const run = match[0];
    const cleanCount = (run.match(/[a-zA-Z0-9 .,;:!?'"()\-\n\r\t\u2018\u2019\u201C\u201D\u2026\u2013\u2014]/g) || []).length;
    if (cleanCount / run.length > 0.6) {
      textRuns.push(run);
    }
  }

  return textRuns.length > 0 ? textRuns.join("\n") : null;
}

async function extractTextFromProtobuf(base64Data) {
  try {
    const binary = atob(base64Data);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }

    const formats = ["gzip", "deflate", "deflate-raw"];
    for (const format of formats) {
      try {
        const decompressed = await tryDecompress(bytes, format);
        const text = extractCleanText(decompressed);
        if (text) return text;
      } catch {
        continue;
      }
    }

    return null;
  } catch {
    return null;
  }
}

const checkLogin = async () => {
  try {
    const result = await page.evaluate(`
      (async () => {
        try {
          const resp = await fetch('https://setup.icloud.com/setup/ws/1/validate', {
            method: 'POST',
            credentials: 'include'
          });
          if (!resp.ok) return null;
          const data = await resp.json();
          return data?.dsInfo?.fullName || null;
        } catch { return null; }
      })()
    `);
    return result;
  } catch { return null; }
};

// ── Phase 1: Set up network capture ──────────────────────────────────

await page.setData('status', 'Setting up...');

await page.captureNetwork({
  urlPattern: 'ckdatabasews\\.icloud\\.com.*com\\.apple\\.notes',
  key: 'notes-api',
  accumulate: true
});

// ── Phase 2: Navigate and check login ────────────────────────────────

await page.setData('status', 'Launching iCloud...');
await page.goto('https://www.icloud.com/notes');
await page.sleep(5000);

let fullName = await checkLogin();
let isLoggedIn = !!fullName;

// ── Phase 3: Login flow ──────────────────────────────────────────────

if (!isLoggedIn) {
  let attempts = 0;
  const maxAttempts = 3;
  let lastError = null;
  let credentials = null;

  while (!isLoggedIn && attempts < maxAttempts) {
    attempts++;

    // Navigate to iCloud (reload on retry)
    if (attempts > 1) {
      await page.goto('https://www.icloud.com/');
      await page.sleep(3000);
    }

    // Step 1: Click "Sign In" button first to load the auth iframe
    await page.setData('status', 'Opening sign in...');
    try {
      await page.evaluate(`
        (() => {
          const btns = Array.from(document.querySelectorAll('button, a, [role="button"]'));
          const signIn = btns.find(el => /^Sign\\s*In$/i.test((el.textContent || '').trim()));
          if (signIn) { signIn.click(); return true; }
          return false;
        })()
      `);
    } catch (e) {
      lastError = 'Could not find Sign In button. Retrying...';
      continue;
    }

    // Wait for the auth iframe to fully load
    await page.sleep(4000);

    // Verify the iframe appeared
    const hasIframe = await page.evaluate(`
      !!document.getElementById('aid-auth-widget-iFrame')
    `);
    if (!hasIframe) {
      lastError = 'Login form did not load. Retrying...';
      continue;
    }

    // Step 2: NOW ask for credentials (the browser is showing the Apple login form)
    if (!credentials || lastError) {
      credentials = await page.getInput({
        title: 'Sign in to iCloud',
        description: lastError || 'Enter your Apple ID to access your notes',
        schema: {
          type: 'object',
          required: ['appleId', 'password'],
          properties: {
            appleId: { type: 'string', title: 'Apple ID' },
            password: { type: 'string', title: 'Password' }
          }
        },
        uiSchema: {
          appleId: { 'ui:placeholder': 'email@example.com', 'ui:autofocus': true },
          password: { 'ui:widget': 'password', 'ui:placeholder': 'Password' }
        },
        submitLabel: 'Sign In',
        error: lastError
      });
    }

    // Step 3: Use frame_fill to directly fill the email input inside the cross-origin iframe
    const APPLE_FRAME = 'idmsa.apple.com';
    await page.setData('status', 'Entering credentials...');

    try {
      // Wait for the email input to appear in the Apple auth iframe
      await page.frame_waitForSelector(APPLE_FRAME, 'input#account_name_text_field, input[type="email"], input[name="account_name"]', { timeout: 10000 });

      // Fill the email field directly
      await page.frame_fill(APPLE_FRAME, 'input#account_name_text_field, input[type="email"], input[name="account_name"]', credentials.appleId);
      await page.sleep(500);

      // Click the Continue/Sign In button to submit email
      try {
        await page.frame_click(APPLE_FRAME, '#sign-in, button[type="submit"], .si-button', { timeout: 5000 });
      } catch (e) {
        // Fallback: press Enter
        await page.keyboard_press('Enter');
      }
      await page.sleep(4000);

      // Wait for password field to appear
      await page.frame_waitForSelector(APPLE_FRAME, 'input#password_text_field, input[type="password"], input[name="password"]', { timeout: 10000 });

      // Fill the password field
      await page.frame_fill(APPLE_FRAME, 'input#password_text_field, input[type="password"], input[name="password"]', credentials.password);
      await page.sleep(500);

      // Click Sign In button to submit password
      try {
        await page.frame_click(APPLE_FRAME, '#sign-in, button[type="submit"], .si-button', { timeout: 5000 });
      } catch (e) {
        await page.keyboard_press('Enter');
      }

      await page.setData('status', 'Authenticating...');
      await page.sleep(10000);
    } catch (e) {
      lastError = `Login form error: ${e.message || String(e)}`;
      continue;
    }

    // Check if login succeeded
    fullName = await checkLogin();
    if (fullName) {
      isLoggedIn = true;
      break;
    }

    // Check if 2FA is needed by looking for the verification code input IN the iframe
    let needs2FA = false;
    try {
      const twoFACheck = await page.frame_evaluate(APPLE_FRAME, `
        (() => {
          const text = document.body?.innerText || '';
          const hasCodeInput = !!document.querySelector('input[name="security_code"], input.form-textbox-input, input[id*="code"], input[type="tel"]');
          return hasCodeInput || text.includes('Two-Factor') || text.includes('verification code') || text.includes('Verification Code') || text.includes('Enter the code');
        })()
      `);
      needs2FA = !!twoFACheck;
    } catch (e) {
      // Frame might have navigated away - check if iframe is still present
      const stillHasIframe = await page.evaluate(`!!document.getElementById('aid-auth-widget-iFrame')`);
      needs2FA = stillHasIframe;
    }

    if (needs2FA) {
      await page.setData('status', 'Two-factor authentication required');

      const otpResult = await page.getInput({
        title: 'Two-Factor Authentication',
        description: 'Enter the verification code sent to your trusted device or phone',
        schema: {
          type: 'object',
          required: ['code'],
          properties: {
            code: { type: 'string', title: 'Verification Code', minLength: 6, maxLength: 8 }
          }
        },
        uiSchema: {
          code: { 'ui:placeholder': '000000', 'ui:autofocus': true }
        },
        submitLabel: 'Verify'
      });

      await page.setData('status', 'Verifying code...');

      // Fill the verification code directly in the iframe
      try {
        await page.frame_fill(APPLE_FRAME, 'input[name="security_code"], input.form-textbox-input, input[id*="code"], input[type="tel"]', otpResult.code);
        await page.sleep(1000);

        // Click the continue/verify button
        try {
          await page.frame_click(APPLE_FRAME, 'button[type="submit"], .si-button, button.button-primary', { timeout: 5000 });
        } catch (e) {
          await page.keyboard_press('Enter');
        }
      } catch (e) {
        // Fallback to keyboard typing
        await page.keyboard_type(otpResult.code, { delay: 50 });
        await page.sleep(500);
        await page.keyboard_press('Enter');
      }

      await page.sleep(8000);

      // Handle "Trust This Browser?" prompt
      try {
        const trustCheck = await page.frame_evaluate(APPLE_FRAME, `
          document.body?.innerText?.includes('Trust') || false
        `);
        if (trustCheck) {
          try {
            await page.frame_click(APPLE_FRAME, 'button.button-primary, button[type="submit"]', { timeout: 5000 });
          } catch (e) {
            await page.keyboard_press('Enter');
          }
          await page.sleep(5000);
        }
      } catch (e) { }

      // Check login status
      fullName = await checkLogin();
      if (fullName) {
        isLoggedIn = true;
        break;
      }
    }

    // Check for error messages
    const errorCheck = await page.evaluate(`
      (() => {
        const text = document.body.innerText || '';
        if (text.includes('incorrect') || text.includes('Incorrect')) return 'Incorrect Apple ID or password.';
        if (text.includes('locked') || text.includes('disabled')) return 'This Apple ID has been locked or disabled.';
        return null;
      })()
    `);

    lastError = errorCheck || 'Sign in failed. Please check your credentials.';
  }

  // Fallback: manual login via browser takeover
  if (!isLoggedIn) {
    await page.setData('status', 'Please sign in manually in the browser below.');
    await page.promptUser(
      'Automatic sign-in failed. Please sign in to your Apple ID manually, including any 2FA. The process will continue automatically once you are signed in.',
      async () => {
        const name = await checkLogin();
        return !!name;
      },
      5000
    );
    fullName = await checkLogin();
    isLoggedIn = !!fullName;
  }
}

if (!isLoggedIn) {
  await page.setData('error', 'Login failed');
  return { success: false, error: 'Could not sign in to iCloud' };
}

await page.setData('status', `Signed in as ${fullName}`);

// ── Phase 4: Navigate to Notes and capture API data ──────────────────

await page.setData('status', 'Loading Notes...');
await page.goto('https://www.icloud.com/notes');
await page.sleep(8000);

// Poll for captured API responses (up to 120s)
await page.setData('status', 'Waiting for Notes data...');
let apiCaptured = null;
const pollStart = Date.now();
while (Date.now() - pollStart < 120000) {
  apiCaptured = await page.getCapturedResponse('notes-api');
  if (apiCaptured && (Array.isArray(apiCaptured) ? apiCaptured.length > 0 : true)) break;
  await page.sleep(2000);
}

if (!apiCaptured || (Array.isArray(apiCaptured) ? apiCaptured.length === 0 : false)) {
  // Try reloading Notes page
  await page.setData('status', 'Reloading Notes...');
  await page.goto('https://www.icloud.com/notes');
  await page.sleep(8000);

  const retryStart = Date.now();
  while (Date.now() - retryStart < 60000) {
    apiCaptured = await page.getCapturedResponse('notes-api');
    if (apiCaptured && (Array.isArray(apiCaptured) ? apiCaptured.length > 0 : true)) break;
    await page.sleep(2000);
  }
}

if (!apiCaptured || (Array.isArray(apiCaptured) ? apiCaptured.length === 0 : false)) {
  await page.setData('error', 'Timed out waiting for Notes API response');
  return { success: false, error: 'Timed out waiting for Notes API response' };
}

// Wait for additional API calls to settle
await page.sleep(5000);
const allCaptured = await page.getCapturedResponse('notes-api') || apiCaptured;

// Normalize to array
const capturedArray = Array.isArray(allCaptured) ? allCaptured : [allCaptured];

// ── Phase 5: Parse CloudKit records ──────────────────────────────────

await page.setData('status', 'Processing notes...');

const recordMap = {};
const folderMap = {};
const noteRefSet = new Set();

for (const captured of capturedArray) {
  let data;
  try {
    data = typeof captured.data === 'string'
      ? JSON.parse(captured.data)
      : captured.data;
  } catch {
    continue;
  }

  const records = data?.records || [];
  for (const record of records) {
    const name = record.recordName;
    const type = record.recordType;
    const fields = record.fields || {};

    if (type === 'Folder') {
      const title = decodeBase64(fields.TitleEncrypted?.value);
      folderMap[name] = title || name;
    }

    if (type === 'Note') {
      const existing = recordMap[name];
      if (!existing || fields.TextDataEncrypted) {
        recordMap[name] = record;
      }
      noteRefSet.add(name);
    }

    if (type === 'SearchIndexes' || type === 'pinned') {
      const noteRef = fields.Note?.value?.recordName;
      if (noteRef) {
        noteRefSet.add(noteRef);
        if (!recordMap[noteRef]) {
          recordMap[noteRef] = {
            recordName: noteRef,
            recordType: 'Note',
            fields,
            created: record.created,
            modified: record.modified,
            _fromSearchIndex: true
          };
        }
      }
    }
  }
}

// ── Phase 6: Build notes list ────────────────────────────────────────

const notes = [];
const parseErrors = [];

for (const noteRecordName of noteRefSet) {
  const record = recordMap[noteRecordName];
  if (!record) continue;

  try {
    const fields = record.fields || {};
    const deleted = fields.Deleted?.value === 1;
    if (deleted) continue;

    const title = decodeBase64(fields.TitleEncrypted?.value);
    const snippet = decodeBase64(fields.SnippetEncrypted?.value);
    const folderRef = fields.Folder?.value?.recordName
      || (fields.Folders?.value || [])[0]?.recordName;

    let textContent = null;
    const textDataRaw = fields.TextDataEncrypted?.value || null;
    if (textDataRaw) {
      textContent = await extractTextFromProtobuf(textDataRaw);
    }

    notes.push({
      recordName: noteRecordName,
      title,
      snippet,
      folder: folderMap[folderRef] || folderRef || null,
      isPinned: !!(fields.IsPinned?.value),
      createdDate: timestampToISO(
        fields.CreationDate?.value || record.created?.timestamp
      ),
      modifiedDate: timestampToISO(
        fields.ModificationDate?.value || record.modified?.timestamp
      ),
      hasAttachments: (fields.Attachments?.value || []).length > 0,
      textContent
    });
  } catch (err) {
    parseErrors.push({
      recordName: noteRecordName,
      error: err instanceof Error ? err.message : String(err)
    });
  }
}

// ── Phase 7: DOM scraping fallback for missing content ───────────────

const notesNeedingContent = notes.filter(n => !n.textContent);

if (notesNeedingContent.length > 0) {
  await page.setData('status', `Fetching note contents... (0/${notesNeedingContent.length})`);

  for (let i = 0; i < notesNeedingContent.length; i++) {
    const note = notesNeedingContent[i];
    await page.setData('status', `Fetching note contents... (${i + 1}/${notesNeedingContent.length})`);

    try {
      // The Notes app is inside a same-origin iframe, so we access it via
      // document.querySelector('iframe').contentDocument
      const titleToFind = (note.title || '').replace(/[\\'"]/g, '');
      const clicked = await page.evaluate(`
        (() => {
          const iframe = document.querySelector('iframe');
          const doc = iframe ? (iframe.contentDocument || iframe.contentWindow?.document) : document;
          if (!doc) return false;

          // Find and click the note in the sidebar
          const groups = doc.querySelectorAll('[role="group"], [role="row"], [role="gridcell"], tr');
          for (const group of groups) {
            const text = group.textContent || '';
            if (text.includes(${JSON.stringify(titleToFind)})) {
              const btn = group.querySelector('button, [role="button"]') || group;
              btn.click();
              return true;
            }
          }
          return false;
        })()
      `);

      if (!clicked) continue;
      await page.sleep(2000);

      // Read the editor content from the iframe
      const content = await page.evaluate(`
        (() => {
          const iframe = document.querySelector('iframe');
          const doc = iframe ? (iframe.contentDocument || iframe.contentWindow?.document) : document;
          if (!doc) return null;

          const selectors = [
            '[contenteditable="true"]',
            '[role="textbox"]',
            '.note-content',
            '.editor',
            '.ProseMirror'
          ];
          for (const sel of selectors) {
            const el = doc.querySelector(sel);
            if (el && el.innerText?.trim()) {
              return el.innerText.trim();
            }
          }
          const main = doc.querySelector('[role="main"]') || doc.querySelector('main');
          if (main) return main.innerText?.trim() || null;
          return null;
        })()
      `);

      if (content) {
        note.textContent = content;
      }
    } catch {
      // Non-fatal
    }
  }
}

// ── Phase 8: Return results ──────────────────────────────────────────

const folders = Object.entries(folderMap).map(([recordName, title]) => ({
  recordName,
  title
}));

const result = {
  notes,
  folders,
  userName: fullName,
  parseErrors: parseErrors.length > 0 ? parseErrors : undefined,
  exportSummary: {
    count: notes.length,
    label: notes.length === 1 ? 'note' : 'notes',
    details: `${notes.length} notes from iCloud Notes`
  },
  platform: 'icloud',
  timestamp: new Date().toISOString()
};

await page.setData('result', result);
await page.setData('status', `iCloud Notes - ${notes.length} notes captured`);
return { success: true, data: result };
