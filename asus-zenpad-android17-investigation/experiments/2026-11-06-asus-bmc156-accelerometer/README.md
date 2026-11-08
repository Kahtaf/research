# BMC156 accelerometer-only SDK37 staging

Question: Can the fitted OEM BMC156 accelerometer be ported to the pinned physical Linux4.9 r5 kernel and served through a matched minimal SDK37 sensors HAL?

Status: Source, affected-kernel-object compilation, SDK37 ARM64 HAL compile/link, boundary tests and future packaging completed. Isolated staging only; no complete kernel Image, active integration, Android HAL execution or physical hardware qualification.

Important outputs:

- [Report](report/REPORT.md), [ABI decision](report/ABI-DECISION.md), [parent handoff](report/HANDOFF.md).
- [Source pins](report/SOURCE-PINS.json) and [compact bundle](artifacts/bmc156-accelerometer-staging.tar.gz).
- [Kernel patch](patches/kernel-from-physical-r5.patch) and [exact pre/post hashes](patches/pre-post-hashes.json).
- [HAL source and packaging](source/hal/), [calibration contract](report/CALIBRATION.md), [commissioning metadata](report/COMMISSIONING.md).
- `artifacts/remote/` contains the bounded compiler/policy/test/preservation receipts and objects; `evidence/` contains source-interface receipts and local patch verification.
- `scripts/verify_bundle.py` runs local offline hash checks; `scripts/check_preimages.py KERNEL` checks a future parent's exact source preimages without modifying them.

Continuation: Parent owns all source combination, full kernel/product builds, private restoration and device/root/USB/flashing/physical commissioning. This is a future hardware input; do not apply it to active r5, its pinned physical source, frozen R3 or product-integration-staging/r1. Charging remains disabled. Read the handoff before integration; do not transplant the entire defconfig over newer parent changes.
