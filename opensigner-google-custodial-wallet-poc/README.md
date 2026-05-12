# OpenSigner Google Custodial Wallet POC

This is a proof of concept for a single OpenSigner flow:

```text
Google sign-in -> internal user -> custodial embedded wallet -> sign message -> verify signature
```

The app is intentionally custodial. It uses OpenSigner in a fully self-hosted automatic-recovery configuration where the application operator controls Hot Storage, Shield/cold storage, and the developer encryption part. The browser iframe still reconstructs the private key only during signing or export.

## Status

- Next.js app, API routes, and minimal Hot Storage run in one Cloud Run service.
- OpenSigner iframe runs as a separate Cloud Run static service.
- OpenSigner Shield runs as a separate Cloud Run service.
- Cloud SQL for MySQL stores app data, hot-share data, and Shield data.
- The deployed app URL is `https://opensigner-poc-app-khacypbkia-uc.a.run.app`.
- The latest verified app revision is `opensigner-poc-app-00004-tx9`.

Direct deployed Google OAuth still requires this authorized redirect URI on the Google OAuth client:

```text
https://opensigner-poc-app-khacypbkia-uc.a.run.app/api/auth/google/callback
```

## Architecture

### Next.js App And API

The app in `app/` owns the user-facing POC and the internal API surface:

- Google OAuth start and callback.
- Internal user lookup/creation.
- Session cookie creation.
- Short-lived OpenSigner storage JWT issuance.
- Wallet metadata storage.
- Signing audit logging and signature verification.
- Minimal MySQL-backed Hot Storage endpoints.
- Same-origin Shield proxy for browser calls that need strict CORS.

The frontend loads the OpenSigner iframe with:

- OpenSigner user UUID.
- Short-lived internal storage JWT.
- Hot Storage URL.
- Shield proxy URL.
- Shield API key.
- Chain ID.

### OpenSigner iframe

The iframe is the browser-side signing surface. For this POC it:

- Generates the private key in the browser.
- Splits the key into shares.
- Stores shares through Hot Storage and Shield.
- Recovers shares when needed.
- Reconstructs the private key in iframe memory.
- Signs `Hello from OpenSigner POC`.
- Exports/copies the private key only after deriving and checking the wallet address.

The full private key is not stored in Cloud SQL. During export, the app keeps it only in browser memory long enough to copy it. The UI shows only a masked preview.

### Hot Storage

The POC implements only the OpenSigner storage endpoints needed for the demo:

- `GET /v2/accounts`
- `POST /v2/devices/create`
- `POST /v2/devices/recover`
- `POST /v2/devices/register`
- `POST /v1/devices/init`
- `POST /v1/devices/register`
- `GET /v1/devices/primary`
- `GET /v1/devices/{deviceId}`
- `POST /v1/devices/exported`

Hot shares are encrypted before being stored in MySQL with AES-256-GCM using `SHARE_ENCRYPTION_KEY`.

### Shield / Cold Storage

Shield stores the recovery/cold share in a Cloud SQL MySQL database. The app creates Shield encryption sessions server-side so the developer encryption part is not exposed to the browser.

### Cloud SQL

Cloud SQL for MySQL is the only database provider. App tables live in `opensigner_poc`; Shield tables live in `opensigner_shield`.

## Key And Custody Model

The wallet is created by the OpenSigner iframe after login:

1. The app maps the Google identity to an internal user and OpenSigner user UUID.
2. The app issues a short-lived OpenSigner-compatible JWT.
3. The iframe generates an EVM private key.
4. The iframe splits the private key into device, hot, and recovery shares.
5. The hot share is sent to Hot Storage and stored encrypted in Cloud SQL.
6. The recovery share is stored by Shield in Cloud SQL.
7. The iframe keeps its browser-side state for recovery/signing.
8. The app stores wallet metadata, not the private key.

This is custodial because the operator controls the storage services and recovery material. The UI labels the wallet as `Custodial embedded wallet`.

## Private-Key Export

The `Export / Copy Private Key` button calls OpenSigner iframe `export`.

The app verifies the exported key before copying:

1. The iframe reconstructs the key from shares in browser memory.
2. The iframe calls `POST /v1/devices/exported`; the POC returns `201` when the wallet belongs to the authenticated OpenSigner user.
3. The iframe returns the private key to the app.
4. The app derives the EVM address with `ethers.Wallet`.
5. The derived address must match the stored wallet address.
6. The app copies the private key and clears it from React state after a successful copy.

If browser clipboard user activation expires during export, the app keeps the exported key in memory and asks the user to click `Copy Exported Key`. The second click copies immediately.

## Data Model

Minimum app tables are defined in `app/migrations/001_initial.sql`:

- `users`: internal ID, Google subject/email, OpenSigner user UUID, login timestamps.
- `wallets`: wallet metadata, OpenSigner account reference, custody model, recovery method.
- `signing_audit_logs`: wallet, message hash, signature hash, verification result.
- `hot_signers`: signer references.
- `hot_accounts`: OpenSigner user/account mapping.
- `hot_devices`: encrypted hot shares.

There is no plaintext private-key column.

## Secrets

Production secrets are expected in Google Secret Manager:

- `opensigner-app-session-secret`
- `opensigner-google-client-secret`
- `opensigner-mysql-username`
- `opensigner-mysql-password`
- `opensigner-mysql-database`
- `opensigner-shield-mysql-database`
- `opensigner-jwt-private-key`
- `opensigner-jwt-public-key`
- `opensigner-hot-share-key`
- `opensigner-shield-api-secret`
- `opensigner-developer-encryption-part`

Browser-visible values such as `GOOGLE_CLIENT_ID`, Shield API key, iframe URL, and public service URLs are configured as Cloud Run environment variables.

## Local Development

```bash
cd app
cp .env.example .env.local
openssl rand -base64 32
openssl rand -hex 32
```

Fill `.env.local` with Google OAuth credentials, MySQL credentials, Shield values, and OpenSigner iframe URLs.

For local MySQL parity:

```bash
cd ..
docker compose -f docker-compose.local.yml up -d
cd app
DB_SSL_REJECT_UNAUTHORIZED=false npm run db:migrate
npm run dev
```

Useful app checks:

```bash
cd app
npm run lint
npm run build
```

## Cloud Run Deployment

Initial GCP setup:

```bash
./scripts/setup-gcp.sh
```

Deploy all services:

```bash
PROJECT_ID=corsali-development \
GOOGLE_CLIENT_ID=... \
SHIELD_API_KEY=... \
./scripts/deploy-cloud-run.sh
```

The script builds and deploys:

- `opensigner-poc-app`
- `opensigner-poc-iframe`
- `opensigner-poc-shield`

Cloud SQL defaults:

- Instance: `opensigner-poc-mysql`
- Connection name: `corsali-development:us-central1:opensigner-poc-mysql`
- App database: `opensigner_poc`
- Shield database: `opensigner_shield`
- App MySQL user: `opensigner_app`

## Verification

Latest verification covered:

- `npm run lint`
- `npm run build`
- Local browser flow with wallet creation, signing, verification, private-key export, and copy.
- Deployed browser flow with wallet creation, private-key export/copy, signing, and verification.
- Cloud SQL rows for wallet metadata, encrypted hot-share storage, and verified signing audit.
- `POST /v1/devices/exported` returning the OpenSigner-required `201`.

The deployed verification used a temporary app session because the Google OAuth redirect URI still needs to be registered.

## Security Boundaries

- Google tokens are never passed directly to OpenSigner storage services.
- Storage services accept the internal OpenSigner JWT only.
- OpenSigner JWTs are short-lived.
- Hot shares are encrypted at rest.
- Shield secrets and developer encryption material stay server-side.
- Private keys are not written to Cloud SQL.
- Full private keys and key shares are redacted from debug output.
- CORS is restricted by `ALLOWED_ORIGINS`.
- The iframe messenger uses the configured iframe origin as the allowed origin.

## Source References

- OpenSigner iframe docs: https://www.opensigner.dev/components/iframe
- OpenSigner auth docs: https://www.opensigner.dev/components/auth
- OpenSigner hot storage docs: https://www.opensigner.dev/components/hot-storage
- OpenSigner Shield docs: https://www.opensigner.dev/components/shield
- OpenSigner signing docs: https://www.opensigner.dev/actions/operation
- OpenSigner deployment/custody docs: https://www.opensigner.dev/security/deployment-scenarios
