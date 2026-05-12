# OpenSigner POC Notes

## Purpose

This folder contains a self-contained POC for a custodial OpenSigner wallet flow:

```text
Google login -> internal app user -> OpenSigner user UUID -> embedded wallet -> sign -> verify -> audit
```

The POC is scoped to browser-present signing through the OpenSigner iframe. Backend signing without user presence is intentionally out of scope.

## Custody Position

OpenSigner is normally positioned as non-custodial key-management infrastructure. This POC uses a custodial deployment shape:

- The app controls Hot Storage.
- The app controls Shield/cold storage.
- The app controls the developer encryption part.
- Automatic recovery is enabled.

That means the operator has technical custody and can reconstruct wallet material. The application UI says: `This POC uses a custodial wallet managed by the application.`

## Service Layout

- `app/`: Next.js app, auth API, wallet metadata API, signing audit API, Shield proxy, and minimal Hot Storage.
- `services/iframe/`: static OpenSigner iframe Cloud Run service.
- `services/shield/`: OpenSigner Shield Cloud Run wrapper.
- `scripts/`: GCP setup and Cloud Run deploy helpers.
- `app/migrations/001_initial.sql`: Cloud SQL schema for app data and Hot Storage data.

## User And Token Flow

1. The user signs in with Google.
2. The callback validates the Google identity token.
3. `users.google_sub` maps Google identity to an internal user.
4. Each user gets one `opensigner_user_uuid`.
5. The app session cookie stores only the internal user/session claims.
6. `/api/me` issues a short-lived OpenSigner JWT for storage services.
7. Hot Storage and Shield validate the internal JWT rather than Google tokens.

## Wallet Creation

The OpenSigner iframe creates the wallet after login:

1. The app creates a Shield encryption session server-side.
2. The iframe generates an EVM private key in the browser.
3. The iframe splits the key into device, hot, and recovery shares.
4. Hot Storage persists the hot share encrypted with AES-256-GCM.
5. Shield persists the recovery share.
6. The app stores wallet metadata in `wallets`.

The database stores shares and references, not plaintext private keys.

## Signing

Signing happens through the iframe:

1. The app asks the iframe to recover/reconstruct the wallet.
2. The iframe fetches the hot share and recovery share.
3. The iframe reconstructs the private key in memory.
4. The iframe signs `Hello from OpenSigner POC`.
5. The app verifies the signature with `ethers.verifyMessage`.
6. The app writes a signing audit row with hashes and verification result.

## Private-Key Export

Private-key export is for POC inspection only.

The export flow:

1. The app calls the iframe `export` method.
2. The iframe reconstructs the key in memory.
3. The iframe calls `POST /v1/devices/exported`.
4. Hot Storage returns `201` only if the wallet address belongs to the authenticated OpenSigner user.
5. The app derives the address from the returned private key.
6. The derived address must match the wallet address before copying.
7. The UI shows only a masked preview.
8. After a successful copy, the app clears the private key from React state.

If clipboard user activation expires while export is in progress, the app keeps the private key in memory and prompts for a second click to copy immediately.

## Database Notes

Cloud SQL for MySQL is the only database provider.

App database:

- `users`
- `wallets`
- `signing_audit_logs`
- `hot_signers`
- `hot_accounts`
- `hot_devices`

Shield database:

- Managed by the Shield service.
- Backed by MySQL in Cloud SQL.

The hot share is encrypted before insertion into `hot_devices.encrypted_share`.

## Security Checks

Current implemented controls:

- No Google token is passed to Hot Storage or Shield.
- OpenSigner storage JWTs expire after 15 minutes.
- Hot shares are encrypted at rest.
- Private keys are not stored in Cloud SQL.
- Full private keys, shares, secrets, and tokens are redacted from debug output.
- CORS only emits `Access-Control-Allow-Origin` for configured origins.
- The iframe connection uses a fixed allowed origin.
- Production secrets are expected from Google Secret Manager.

Remaining POC caveats:

- This is not a hardened production wallet service.
- The operator is custodial by design.
- Direct deployed Google OAuth requires the deployed callback URI to be added to the OAuth client.
- Private-key export should not be enabled in a production custodial wallet without a deliberate policy and audit trail.

## Verified State

Verified locally and on Cloud Run:

- Lint and build pass.
- Google-to-internal-user mapping works locally.
- Wallet creation works through the iframe.
- Hot Storage stores encrypted hot-share data.
- Shield stores recovery data in Cloud SQL.
- Message signing works.
- Server-side signature verification works.
- Signing audit rows are written.
- Private-key export/copy works and verifies the derived address first.

Latest deployed app revision verified:

```text
opensigner-poc-app-00004-tx9
```

## 2026-05-12 Deployed Signing Recovery Debug

The deployed app reproduced `NoSecretFoundError: No secret found for the given auth options` during signing after Google login. Cloud Run and Cloud SQL checks showed that the hot share and Shield recovery share existed for the wallet. Shield logged a failed share read because the app proxy did not forward the encryption headers required by Shield.

Fixes applied:

- Forward `X-Encryption-Part` and `X-Encryption-Session` through the app Shield proxy.
- Include `device`, `deviceId`, and `deviceID` aliases in Hot Storage recovery responses for iframe compatibility.
- Use Shield custom authentication provider value `custom` for the iframe recovery request.
- Reuse the configured iframe for private-key export and run recovery before export.
- Force the iframe to flush local OpenSigner state before recovery for signing/export after refresh.
- Use the iframe `configure` path plus a real `/v1/devices/register` implementation for refreshed-page recovery.
- Add the `/v2/accounts/signer` lookup required by the iframe configure path.
- Add the GitHub button beside the custodial wallet notice.

Validation:

- `npm run lint` passed.
- `npm run build` passed.
- Deployed app revision `opensigner-poc-app-00013-rfm` is ready and serving traffic.
- Headed browser flow on Cloud Run created wallet `0x98Fdf902a608b01e3A095e7dCF21C136B41fC5c3`.
- Message signing returned a signature and wrote verified audit rows.
- Private-key export returned a verified key preview. Clipboard copy was blocked in the automated browser context, but the app kept the exported key available behind the "Copy Exported Key" button.
- Refresh-specific retest created wallet `0xf074093f3a3c48A808e43B5Ea1f81880C89fb35e`; refreshing the page and then exporting/copying the private key succeeded.
