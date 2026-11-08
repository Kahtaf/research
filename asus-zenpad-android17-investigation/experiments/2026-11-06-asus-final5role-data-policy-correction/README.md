# Future final5role DATA policy correction

Question: can the exact Android 7 stock-kernel rescue policy gain only daemon DATA open/read/write/getattr/ioctl and BLKGETSIZE64 while retaining every other policy boundary?

Status: **implemented and reproduced offline; UNQUALIFIED-future5role-policy; integration held**. This is not SDK 37 product policy. No image was produced or deployed.

The actual policy is [artifacts/UNQUALIFIED-future5role-policy](artifacts/UNQUALIFIED-future5role-policy), 390,437 bytes, SHA256 `3d982859fdbf06336d6274e7e700ca64a2551effd769a8cb119b4fed97388815`.

Important outputs:

- [REPORT.md](REPORT.md): implementation, audit proof, actual binary evidence, limitations and preservation.
- [INTEGRATION.md](INTEGRATION.md): exact patch preimages, mandatory frozen-reference audit argument and parent continuation.
- [patches/three-file-policy-correction.patch](patches/three-file-policy-correction.patch): copied builder/audit/test correction; [offline test support](patches/offline-xperm-test-support.patch) adds one host-only query source.
- [evidence/final-policy-audit.json](evidence/final-policy-audit.json), [effective-policy.json](evidence/effective-policy.json), [effective-xperms.json](evidence/effective-xperms.json), [policy-checks.json](evidence/policy-checks.json): 218 checks, original 72/29 scope retained, 144-row comparison and exact ioctl-key sets.
- [evidence/negative-fixtures.json](evidence/negative-fixtures.json): 19 valid bad-policy fixtures rejected.
- [evidence/clean-reproduction.json](evidence/clean-reproduction.json), [preservation.json](evidence/preservation.json), [resources.json](evidence/resources.json), [toolchain.json](evidence/toolchain.json): clean host rebuild, 154 originals preserved, bounded-resource facts and toolchain pins.
- `baseline/`, `inputs/`, `SOURCE_PINS.json`, `ARTIFACTS.json`, `OUTPUT_PINS.json`, `HANDOFF.json`: preimages, pinned public inputs and delivered identities. Expected failures, resource-limit rejections and initial overlapping QA receipts are retained under `evidence/`.

Continuation: parent starts with fresh independent review and follows INTEGRATION.md in a new owned fork. Creation/build scripts are single-use and refuse existing output directories/files; do not build over this completed spike. Read-only integrity verification is `python3 -B scripts/verify_delivery.py`. Actual install SYSTEM/BOOT admissions, terminal manifest gates, future core/helper/image assembly and every physical action remain parent work. The frozen two-role 5a61… / 3f99… / 16f6… artifacts stay exact. No phase-proof optimization, target daemon/helper build, deployment/flag change, final helper compatibility, source-writer requalification, actual SELinux application or flash GO is claimed.
