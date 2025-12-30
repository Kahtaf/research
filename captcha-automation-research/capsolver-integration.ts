/**
 * CapSolver Integration Example for CloudFlare Remote Browser
 *
 * This shows how to integrate CapSolver API with the existing
 * CloudFlare Workers + Playwright architecture for automatic captcha solving
 */

import { Page } from '@cloudflare/playwright';

interface CapSolverConfig {
  apiKey: string;
  apiUrl?: string;
}

interface CaptchaTask {
  type: 'ReCaptchaV2TaskProxyless' | 'ReCaptchaV3TaskProxyless' | 'HCaptchaTaskProxyless' | 'CloudflareTurnstileTaskProxyless';
  websiteURL: string;
  websiteKey: string;
  pageAction?: string; // For reCAPTCHA v3
}

interface CapSolverResponse {
  errorId: number;
  errorCode?: string;
  errorDescription?: string;
  taskId?: string;
  status?: 'processing' | 'ready';
  solution?: {
    gRecaptchaResponse?: string;
    token?: string;
  };
}

/**
 * CapSolver API Client
 */
class CapSolverClient {
  private apiKey: string;
  private apiUrl: string;

  constructor(config: CapSolverConfig) {
    this.apiKey = config.apiKey;
    this.apiUrl = config.apiUrl || 'https://api.capsolver.com';
  }

  /**
   * Create a captcha solving task
   */
  async createTask(task: CaptchaTask): Promise<string> {
    const response = await fetch(`${this.apiUrl}/createTask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        clientKey: this.apiKey,
        task: task,
      }),
    });

    const data: CapSolverResponse = await response.json();

    if (data.errorId !== 0) {
      throw new Error(`CapSolver error: ${data.errorDescription}`);
    }

    if (!data.taskId) {
      throw new Error('No task ID returned from CapSolver');
    }

    return data.taskId;
  }

  /**
   * Get task result (poll until ready)
   */
  async getTaskResult(taskId: string, maxAttempts = 60): Promise<string> {
    for (let i = 0; i < maxAttempts; i++) {
      const response = await fetch(`${this.apiUrl}/getTaskResult`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          clientKey: this.apiKey,
          taskId: taskId,
        }),
      });

      const data: CapSolverResponse = await response.json();

      if (data.errorId !== 0) {
        throw new Error(`CapSolver error: ${data.errorDescription}`);
      }

      if (data.status === 'ready' && data.solution) {
        const token = data.solution.gRecaptchaResponse || data.solution.token;
        if (!token) {
          throw new Error('No solution token in response');
        }
        return token;
      }

      // Wait 2 seconds before next attempt
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    throw new Error('Captcha solving timeout');
  }

  /**
   * Solve captcha (create task + wait for result)
   */
  async solve(task: CaptchaTask): Promise<string> {
    const taskId = await this.createTask(task);
    return await this.getTaskResult(taskId);
  }
}

/**
 * Helper function to solve reCAPTCHA v2
 */
export async function solveReCaptchaV2(
  page: Page,
  apiKey: string
): Promise<void> {
  const client = new CapSolverClient({ apiKey });

  // Extract site key from page
  const siteKey = await page.evaluate(() => {
    const iframe = document.querySelector('iframe[src*="google.com/recaptcha"]');
    if (iframe) {
      const src = iframe.getAttribute('src') || '';
      const match = src.match(/k=([^&]+)/);
      return match ? match[1] : null;
    }
    return null;
  });

  if (!siteKey) {
    throw new Error('reCAPTCHA site key not found');
  }

  console.log('Solving reCAPTCHA v2...');
  const token = await client.solve({
    type: 'ReCaptchaV2TaskProxyless',
    websiteURL: page.url(),
    websiteKey: siteKey,
  });

  // Inject solution into page
  await page.evaluate((token) => {
    const textarea = document.querySelector('#g-recaptcha-response') as HTMLTextAreaElement;
    if (textarea) {
      textarea.value = token;
      textarea.dispatchEvent(new Event('change'));
    }
  }, token);

  console.log('reCAPTCHA v2 solved successfully');
}

/**
 * Helper function to solve Cloudflare Turnstile
 */
export async function solveCloudflareTurnstile(
  page: Page,
  apiKey: string
): Promise<void> {
  const client = new CapSolverClient({ apiKey });

  // Extract site key from Turnstile widget
  const siteKey = await page.evaluate(() => {
    const turnstile = document.querySelector('[data-sitekey]');
    return turnstile ? turnstile.getAttribute('data-sitekey') : null;
  });

  if (!siteKey) {
    throw new Error('Cloudflare Turnstile site key not found');
  }

  console.log('Solving Cloudflare Turnstile...');
  const token = await client.solve({
    type: 'CloudflareTurnstileTaskProxyless',
    websiteURL: page.url(),
    websiteKey: siteKey,
  });

  // Inject solution into page
  await page.evaluate((token) => {
    const input = document.querySelector('input[name="cf-turnstile-response"]') as HTMLInputElement;
    if (input) {
      input.value = token;
      input.dispatchEvent(new Event('change'));
    }
  }, token);

  console.log('Cloudflare Turnstile solved successfully');
}

/**
 * Helper function to solve reCAPTCHA v3
 */
export async function solveReCaptchaV3(
  page: Page,
  apiKey: string,
  action: string = 'submit'
): Promise<void> {
  const client = new CapSolverClient({ apiKey });

  // Extract site key from page scripts
  const siteKey = await page.evaluate(() => {
    const scripts = Array.from(document.querySelectorAll('script'));
    for (const script of scripts) {
      const match = script.textContent?.match(/grecaptcha\.execute\(['"]([^'"]+)['"]/);
      if (match) return match[1];
    }
    return null;
  });

  if (!siteKey) {
    throw new Error('reCAPTCHA v3 site key not found');
  }

  console.log('Solving reCAPTCHA v3...');
  const token = await client.solve({
    type: 'ReCaptchaV3TaskProxyless',
    websiteURL: page.url(),
    websiteKey: siteKey,
    pageAction: action,
  });

  // Inject token into the page's grecaptcha callback
  await page.evaluate((token) => {
    (window as any).captchaToken = token;
  }, token);

  console.log('reCAPTCHA v3 solved successfully');
}

/**
 * Example integration with existing requestTakeover flow
 * This can be added to the BrowserSession's runScript method
 */
export async function autoSolveCaptcha(
  page: Page,
  apiKey: string
): Promise<boolean> {
  try {
    // Check for reCAPTCHA v2
    const hasReCaptchaV2 = await page.evaluate(() => {
      return !!document.querySelector('iframe[src*="google.com/recaptcha"]');
    });

    if (hasReCaptchaV2) {
      await solveReCaptchaV2(page, apiKey);
      return true;
    }

    // Check for Cloudflare Turnstile
    const hasTurnstile = await page.evaluate(() => {
      return !!document.querySelector('[data-sitekey]');
    });

    if (hasTurnstile) {
      await solveCloudflareTurnstile(page, apiKey);
      return true;
    }

    // Check for reCAPTCHA v3 (harder to detect, might need specific implementation)
    const hasReCaptchaV3 = await page.evaluate(() => {
      return !!document.querySelector('script[src*="recaptcha/api.js"]');
    });

    if (hasReCaptchaV3) {
      await solveReCaptchaV3(page, apiKey);
      return true;
    }

    return false; // No captcha detected
  } catch (error) {
    console.error('Auto-solve captcha error:', error);
    return false;
  }
}

/**
 * Example usage in Playwright script:
 *
 * // In the user's automation script:
 * await page.goto('https://example.com/form');
 * await page.fill('#email', 'user@example.com');
 *
 * // Try to auto-solve captcha
 * const solved = await autoSolveCaptcha(page, env.CAPSOLVER_API_KEY);
 *
 * if (!solved) {
 *   // Fallback to manual takeover if auto-solve fails
 *   await requestTakeover('Please solve the captcha manually');
 * }
 *
 * await page.click('#submit');
 */
