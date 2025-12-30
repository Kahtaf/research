# Captcha Solving Service Comparison

## Overview
Comparison of the two main recommended API-based captcha solving services for CloudFlare Workers integration.

## Feature Comparison

| Feature | 2Captcha | CapSolver |
|---------|----------|-----------|
| **Pricing Model** | Pay-per-solve | Pay-per-solve |
| **reCAPTCHA v2** | ✅ Supported | ✅ Supported |
| **reCAPTCHA v3** | ✅ Supported | ✅ Supported |
| **hCaptcha** | ✅ Supported | ✅ Supported |
| **Cloudflare Turnstile** | ✅ Supported | ✅ Supported |
| **Image Captcha** | ✅ Supported | ✅ Supported |
| **API Type** | REST API | REST API |
| **JavaScript SDK** | ✅ Available | ✅ Available |
| **CloudFlare Workers Compatible** | ✅ Yes (REST API) | ✅ Yes (REST API) |
| **Response Time** | ~10-30 seconds | ~10-30 seconds |
| **Success Rate** | ~95% | ~95% |

## Pricing Comparison (Approximate)

### 2Captcha
- reCAPTCHA v2: $2.99 per 1000 solves
- reCAPTCHA v3: $2.99 per 1000 solves
- hCaptcha: $2.99 per 1000 solves
- Cloudflare Turnstile: $2.99 per 1000 solves
- Image Captcha: $0.50 per 1000 solves

### CapSolver
- reCAPTCHA v2: $0.80 per 1000 solves
- reCAPTCHA v3: $0.80 per 1000 solves
- hCaptcha: $0.80 per 1000 solves
- Cloudflare Turnstile: $2.50 per 1000 solves
- Image Captcha: $0.40 per 1000 solves

**Note:** CapSolver appears to be more cost-effective, especially for reCAPTCHA.

## API Structure Comparison

### 2Captcha API Flow
```
1. Submit captcha: GET https://2captcha.com/in.php?key=API_KEY&method=...
2. Get result: GET https://2captcha.com/res.php?key=API_KEY&action=get&id=TASK_ID
```

### CapSolver API Flow
```
1. Create task: POST https://api.capsolver.com/createTask
2. Get result: POST https://api.capsolver.com/getTaskResult
```

CapSolver uses POST requests with JSON bodies, which is more modern and easier to work with.

## Integration Complexity

Both services are similar in complexity:
1. Extract captcha parameters from page
2. Submit to API
3. Poll for result (2-30 seconds)
4. Inject solution into page

## Reliability & Support

### 2Captcha
- Established since 2013
- Large community
- 24/7 support
- Extensive documentation

### CapSolver
- Newer service (2021)
- AI-powered solving
- Modern API design
- Good documentation
- 24/7 support

## Recommendation

**For CloudFlare Workers Project: Use CapSolver**

Reasons:
1. **Lower cost** - Significantly cheaper for reCAPTCHA ($0.80 vs $2.99 per 1000)
2. **Modern API** - POST with JSON is cleaner than GET with query params
3. **AI-powered** - Better success rates on complex captchas
4. **Better TypeScript support** - Easier to type with JSON structure

**Alternative: Use 2Captcha if:**
- Budget is not a concern
- You want the most established service with longest track record
- You need support for more exotic captcha types

## Implementation Notes

Both services:
- Are compatible with CloudFlare Workers
- Work well with @cloudflare/playwright
- Can be used as a fallback before `requestTakeover()`
- Support all major captcha types needed for modern web automation
- Have similar integration patterns

The choice ultimately comes down to cost optimization (CapSolver) vs. maximum reliability/establishment (2Captcha).
