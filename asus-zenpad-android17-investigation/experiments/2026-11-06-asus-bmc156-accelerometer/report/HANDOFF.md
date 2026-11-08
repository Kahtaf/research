# Accelerometer-only future hardware input

This is a separately staged source/object/model result. It is **not integrated**, contains no bootable kernel image, and proves no physical Linux4.9/Android17 sensor operation. Parent owns the next kernel combination, full SDK37 product build, all devices and commissioning. No physical GO is given.

Local spike: `2026-11-06-asus-bmc156-accelerometer`.
Remote owned fixture: `/srv/android/asus-bmc156-accelerometer-r1`.
Read `REPORT.md`, `ABI-DECISION.md`, `CALIBRATION.md`, and `COMMISSIONING.md` before integration.

## Exact inputs and patch boundaries

`SOURCE-PINS.json` collects the exact physical source commit, SDK37 repository commits, ABI-header hashes, OEM preimages, HAL/object hashes and patch pins.

- Compiled physical r5 base Image.gz-dtb: `46895deb12ec94160ea5af0e85afa89c6de84971db126bb94c60cec1ec3ec401`.
- Physical base resolved config: `067090e03ad762344308cebd0a71274d9943e299ded6707051ebfdc075dd045f`.
- OEM driver preimage: `d3a43a00419e7c1096e1b216ae665a57a69e7af3ab0ff363240e4aed14a9a609`.
- `patches/kernel-from-physical-r5.patch` changes exactly nine files. `patches/pre-post-hashes.json` gives every exact existing preimage and final postimage; absent preimages represent four new OEM-port files.
- `patches/oem-driver-adaptation.patch` explains the source reduction from the exact ASUS OEM driver, independently of the physical-r5 integration patch. `source/oem-preimages/` preserves the original four OEM files. The header retains its original CRLF/no-final-newline bytes; use `git apply`, and verify postimages.
- `artifacts/remote/evidence/final-verification.json` pins the final config, HAL, objects, board source and preserved runtime sources. Its `source_changes` must match the local patch manifest exactly.
- `artifacts/remote/evidence/sdk-inputs.json` records frozen real SDK37 Bionic/libhardware/system headers, repository commits and library inputs. `reference-source-pins.json` covers the genuine HIDL1.0 wrapper reference files.

Do not apply this patch to `/srv/android/asus-build-continuation/kernel`, an active source/out tree, frozen R3, or `/srv/android/asus-product-integration-staging/r1`. Those were not modified here. This patch is relative to the pinned compiled physical r5 source, **not** an arbitrary parent kernel revision. Run `python3 scripts/check_preimages.py /path/to/future-owned-kernel` before applying it. A hash mismatch requires a reviewed rebase; do not use fuzzy application or copy this fixture's entire defconfig over a newer parent config. After applying, use the same verifier with `--post`.

The only resolved configuration differences are accelerometer `n→y`, BMC156_ACC `n→y`, BMA253 `y→n`, and MC3416 `y→n`. Compass, ALS, gyro, sensorhub and accelgyro remain disabled. The physical DT, charging opt-in absence and core runtime config/source hashes stay unchanged. No virtual defconfig was used.

## Future parent integration

1. Preserve the parent's build ownership/termination gates. Combine this patch only in a new parent-owned kernel candidate. Build the complete ARM64 Image/DT and run the parent's existing runtime-preservation and charging-disabled checks. This stage compiled the entire affected `sensors-1.0` subtree and its relocatable link at `-j1`; it did not launch an independent full-kernel rebuild alongside the original AOSP job.
2. Copy `source/hal/` as, for example, `device/asus/p00a/sensors/`. Include its `sensors.mk` from the future device product, and its `BoardConfig.mk` **after** existing manifest assignments. Its Soong module builds the ARM64 `sensors.mt8163.so`; use the supplied `.so` only as a compiler receipt, normally rebuild the source in the final product.
3. Merge the five lines in `ueventd.fragment.rc` into the future product's existing ueventd configuration. This fragment is intentionally not installed as a replacement for that configuration. No ueventd import was added to active or parent-owned staging files here.
4. Package the genuine SDK37 `android.hardware.sensors@1.0-service` and `@1.0-impl`, with the supplied sole `ISensors/default` declaration. The C device exposes API1.3. Require an ARM64 service process to match the only module architecture built here. Verify `ro.hardware.sensors=mt8163`; libhardware checks this property first. Do not package the old sensors blob, bmm050d, or a `/vendor/etc/sensors/hals.conf`: the latter makes the real wrapper select multihal instead.
5. Parent privately restores an existing valid `gs_cali.ini` into the reviewed layout in `CALIBRATION.md`. No restoration script, factory payload, zeroed default or NVRAM daemon is supplied. Missing calibration is explicitly unreliable operation; a malformed present file fails HAL open. Do not claim calibrated readiness merely because the service starts.
6. Run the real full product's Soong, ELF/namespace, init/ueventd, SELinux/genfs/file-context and VINTF compatibility checks. Offline schema and frozen policy merge success here do not replace these checks. Recheck coexistence with later parent source/policy changes. Declare only the accelerometer feature supplied by this stage; other sensor capabilities remain deferred.
7. Commission the real device only under the parent's existing recovery, presence and physical authorization gates. Follow `COMMISSIONING.md`. Physical gravity, sign/axis, rate, enable/flush behavior, application auto-rotation and suspend/resume all remain unproved.

## Reproduction within this owned fixture

`final_builds.py` serially runs the `-j1` subtree build, SDK37 ARM64 HAL compile/link, protocol/state tests, extracted OEM data-path tests, actual C HAL callbacks with mocked OS boundaries, extracted registration-failure tests, and the actual core enable/batch/error-recovery state function. Each runtime test is pinned to one CPU with a 1GiB address-space cap and a 30-second CPU limit. `verify_policy.py` and `merge_policy.py` generate/merge policy into owned directories, using copied frozen SDK37 policy inputs and enabled neverallow checks. `verify_final.py` checks the complete source/config delta and preserved baseline.

`create_fixture.py` and `freeze_sdk.py` are recorded one-time creation recipes and reject an existing target. Do not rerun them blindly. The existing remote fixture and SDK snapshots make repeat builds independent of active Ninja. No commands here manage or wait for the original AOSP build. `scripts/verify_bundle.py` performs local offline bundle/hash checks without SSH or devices.
