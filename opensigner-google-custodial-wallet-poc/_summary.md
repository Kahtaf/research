OpenSigner Google Custodial Wallet POC demonstrates a seamless integration between Google OAuth and self-hosted embedded wallet infrastructure. By leveraging a multi-service architecture on Google Cloud Run, the system manages private keys through a three-share split involving a browser-side iframe, encrypted hot storage, and a recovery Shield. The implementation ensures that full private keys never touch the database in plaintext, maintaining a secure yet operator-controlled custodial environment for signing and signature verification.

* Implements a complete "Sign-in to Sign-message" flow using Next.js, Cloud Run, and Cloud SQL.
* Secures wallet shares through AES-256-GCM encryption and server-side Shield session management.
* Supports controlled private-key export by reconstructing keys in browser memory only after strict identity verification.
* Utilizes a fully self-hosted configuration where the application operator maintains authority over all recovery materials.

**Key Links:**
* OpenSigner Documentation: https://www.opensigner.dev
* POC Deployment: https://opensigner-poc-app-khacypbkia-uc.a.run.app
