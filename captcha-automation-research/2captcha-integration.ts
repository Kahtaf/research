/**
 * 2Captcha Integration Example for CloudFlare Remote Browser
 *
 * Alternative implementation using 2Captcha API
 * Similar to CapSolver but with 2Captcha's API structure
 */

import { Page } from '@cloudflare/playwright';

interface TwoCaptchaConfig {
  apiKey: string;
  apiUrl?: string;
}

interface CaptchaRequest {
  method: string;
  googlekey?: string;
  sitekey?: string;
  pageurl: string;
  action?: string;
  json?: number;
}

/**
 * 2Captcha API Client
 */
class TwoCaptchaClient {
  private apiKey: string;
  private apiUrl: string;

  constructor(config: TwoCaptchaConfig) {
    this.apiKey = config.apiKey;
    this.apiUrl = config.apiUrl || 'https://2captcha.com';
  }

  /**
   * Submit a captcha solving request
   */
  async submitCaptcha(params: CaptchaRequest): Promise<string> {
    const url = new URL(`${this.apiUrl}/in.php`);
    url.searchParams.append('key', this.apiKey);
    url.searchParams.append('json', '1');

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.append(key, String(value));
      }
    });

    const response = await fetch(url.toString());
    const data = await response.json();

    if (data.status !== 1) {
      throw new Error(`2Captcha error: ${data.request}`);
    }

    return data.request; // Task ID
  }

  /**
   * Get captcha result (poll until ready)
   */
  async getResult(taskId: string, maxAttempts = 60): Promise<string> {
    for (let i = 0; i < maxAttempts; i++) {
      const url = new URL(`${this.apiUrl}/res.php`);
      url.searchParams.append('key', this.apiKey);
      url.searchParams.append('action', 'get');
      url.searchParams.append('id', taskId);
      url.searchParams.append('json', '1');

      const response = await fetch(url.toString());
      const data = await response.json();

      if (data.status === 1) {
        return data.request; // The solution token
      }

      if (data.request !== 'CAPCHA_NOT_READY') {
        throw new Error(`2Captcha error: ${data.request}`);
      }

      // Wait 2 seconds before next attempt
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    throw new Error('Captcha solving timeout');
  }

  /**
   * Solve captcha (submit + wait for result)
   */
  async solve(params: CaptchaRequest): Promise<string> {
    const taskId = await this.submitCaptcha(params);
    return await this.getResult(taskId);
  }
}

/**
 * Solve reCAPTCHA v2 using 2Captcha
 */
export async function solveReCaptchaV2With2Captcha(
  page: Page,
  apiKey: string
): Promise<void> {
  const client = new TwoCaptchaClient({ apiKey });

  // Extract site key
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

  console.log('Solving reCAPTCHA v2 with 2Captcha...');
  const token = await client.solve({
    method: 'userrecaptcha',
    googlekey: siteKey,
    pageurl: page.url(),
  });

  // Inject solution
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
 * Solve Cloudflare Turnstile using 2Captcha
 */
export async function solveTurnstileWith2Captcha(
  page: Page,
  apiKey: string
): Promise<void> {
  const client = new TwoCaptchaClient({ apiKey });

  // Extract site key
  const siteKey = await page.evaluate(() => {
    const turnstile = document.querySelector('[data-sitekey]');
    return turnstile ? turnstile.getAttribute('data-sitekey') : null;
  });

  if (!siteKey) {
    throw new Error('Cloudflare Turnstile site key not found');
  }

  console.log('Solving Cloudflare Turnstile with 2Captcha...');
  const token = await client.solve({
    method: 'turnstile',
    sitekey: siteKey,
    pageurl: page.url(),
  });

  // Inject solution
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
 * Universal auto-solve function using 2Captcha
 */
export async function autoSolveWith2Captcha(
  page: Page,
  apiKey: string
): Promise<boolean> {
  try {
    // Check for reCAPTCHA v2
    const hasReCaptchaV2 = await page.evaluate(() => {
      return !!document.querySelector('iframe[src*="google.com/recaptcha"]');
    });

    if (hasReCaptchaV2) {
      await solveReCaptchaV2With2Captcha(page, apiKey);
      return true;
    }

    // Check for Cloudflare Turnstile
    const hasTurnstile = await page.evaluate(() => {
      return !!document.querySelector('[data-sitekey]');
    });

    if (hasTurnstile) {
      await solveTurnstileWith2Captcha(page, apiKey);
      return true;
    }

    return false;
  } catch (error) {
    console.error('2Captcha auto-solve error:', error);
    return false;
  }
}
