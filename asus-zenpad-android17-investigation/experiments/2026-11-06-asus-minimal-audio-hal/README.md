# P00A minimal audio HAL — future hardware input

Question: can a source-built minimal speaker/microphone C HAL use the MT8163 kernel through genuine Android17/SDK37 HIDL audio wrappers without importing Android7 framework libraries?

**Status: bounded implementation complete; hardware route activation blocked.** Real ARM64 SDK37 HAL and tinyalsa v2 ELFs compile/link.58 injected transport assertions and28 native HAL contract assertions pass. Production routes stay unqualified and return `-ENODEV`; no physical audio or boot claim. The stock/internal amplifier versus combined-kernel AW8737S discrepancy and exact microphone mode/source require parent qualification.

Important outputs:

- [Parent handoff](report/HANDOFF.md): exact future integration/commissioning steps, limitations and unsupported features.
- [Route ledger](report/ROUTE-LEDGER.md): public stock/kernel card/PCM, GPIO/modes, enums/gains, rates/formats, micbias and copy callback findings.
- [Calibration contract](report/CALIBRATION.md): public LID65 payload interpretation and explicit no-default/no-private-data boundary.
- `src/`, `Android.bp`, `staging/`: actual C implementation and guarded future product/BoardConfig/VINTF/policy/volumes/effects/init references. No SELinux rule delta.
- `evidence/remote/`: actual ELF, compiler/link input, header dependency and test receipts. Full-product neverallow validation is incomplete (bounded secilc timeout); init, VINTF fragment and audio XSD checks pass.
- `bundle/p00a-audio-stage.tar.gz`, `bundle/SHA256SUMS`: small review bundle. `staging-additions.patch` is additive only; `patch-preimages.json` requires absent destinations under a future `device/asus/p00a/audio` directory. Nothing was integrated.

Continuation: parent reads the handoff, reconciles the amplifier and microphone facts, and creates a new qualified route revision. Do not flip the gate as a shortcut. Parent owns active build integration, all device/root/ADB/USB/flashing and physical gates. Never apply to frozen core product r1 or mutate the active source/out/kernel. Factory payloads stay private/local.

Reproduce local checks: `python3 scripts/verify_local.py`. Builder compile recipe: `scripts/compile_remote.py`; it reuses captured genuine SDK37 compile flags and only writes the separately owned `/srv/android/asus-minimal-audio-hal-20261106` fixture. Compiler processes run serially, on one CPU with1GiB AS. Re-run builder work only under the parent's resource coordination. The evidence Bionic files were genuine vendor link stubs, not runtime replacements; no Bionic payload is included in the bundle.
