# BMC156 complete physical kernel fixture

Question: Can the exact compiled physical r5 source plus the completed BMC156 port build a complete ARM64 Image.gz-dtb while preserving every inherited prerequisite?

Status: completed full compile exit 0 and source/config/DT/header/layout preservation checks. Physical behavior and product integration remain untested.

Important outputs:

- [Complete Image.gz-dtb](artifacts/Image.gz-dtb), SHA256 `e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1`.
- [Report](report/REPORT.md), [parent handoff](report/HANDOFF.md), [exact pins](report/SOURCE-PINS.json), and [minimal future product delta](parent-delta.json).
- Exact nine-file source patch and four-option resolved config diff in `patches/`; complete r5 source manifest and full build log in `evidence/`.

Continuation: run `python3 -B scripts/verify_bundle.py` locally. The existing owned VM BUILD FIXTURE is `/srv/android/asus-bmc156-full-kernel-r1`; inspect completed status receipts before any action. Do not rerun one-time reconstruction/launch/export scripts. Large source, objects, vmlinux and raw Image stay on the VM. Read the handoff before a future parent-owned integration. Original fixtures, active builds, sealed r2 and frozen R3 remain untouched. No hardware actions are authorized by this artifact.
