export function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required`);
  }
  return value;
}

export function appUrl(): string {
  return process.env.APP_URL || "http://localhost:3000";
}

export function secureCookies(): boolean {
  return appUrl().startsWith("https://") || process.env.NODE_ENV === "production";
}

export function allowedOrigins(): string[] {
  const configured = process.env.ALLOWED_ORIGINS || appUrl();
  return configured
    .split(",")
    .map((origin) => origin.trim())
    .filter(Boolean);
}
