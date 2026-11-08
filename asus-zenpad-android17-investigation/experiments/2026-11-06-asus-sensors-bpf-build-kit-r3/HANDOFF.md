# r3 implementation handoff

Status: r3 implementation complete, sealed and tested; **parent review is required before any active integration or build**. All 40 tests and the full real input audit passed against the final seal. The actual preflight at 2026-11-06 22:13:43 UTC refused absent explicit r5 failure acceptance (exit 20). No native build, attempt, parent-review file or r6 marker existed at that observation. No r6 build was launched.

## Exact candidate and kit

- Builder kit: `/srv/android/asus-reviewed-build-kit/r3`
- Immutable candidate: `/srv/android/asus-product-integration-staging/r3`
- Kit `inputs/kit-pins.json` SHA256: `a00ea8d7c944d45e3035296c81b31a369f13bde830f88a7165b0d7542960717c` (90 files)
- STAGED.json SHA256: `c168e1b13ad76b669655c071017f3ba038b06b1fc2b619df969aade441f7e17d`
- Combined original-baseline patch SHA256: `e5b162f002753df8c8f3ba7e58939de38b2b5cab6361f51de7f68a1fb20dc893`
- Physical BMC156 kernel image SHA256: `e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1`
- Kernel config SHA256: `10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`

The staging already composed before this continuation was preserved. Do not rerun composition, substitute the separate audio experiment's kernel, or overwrite r1/r2/r3 staging. The source receipt retains the original 61,976-file baseline and exactly 276 postimages, including the nine-file r5-relative BMC change with one overlap. The complete compiled tree has 62,228 files.

## Parent's concrete launch command

Run on the builder only after the parent's targeted service build has genuinely stopped and released the **original** `/srv/android/asus-device-product/logs/full-product-build.lock`. There is no lock waiter. A live process or held lock is a refusal, not a reason to kill or replace a job.

First inspect the failed-result description under that lock:

```sh
python3 -B /srv/android/asus-reviewed-build-kit/r3/scripts/integrate.py --describe-prior
```

The parent must author `/srv/android/asus-reviewed-build-kit/r3/parent-review/r5-failure.json` from the returned `result.review_template`. The file's top-level keys must be `reviewed_by_parent`, `reason`, and `prior`. Only the parent may set `reviewed_by_parent` to true and provide the actual review reason. Preserve the exact `prior` object, including every r5 log/result hash and existing image hash. This kit supplies no acceptance. The r5 exit remains 1, finished at `2026-11-06T21:15:32+00:00`; its log SHA256 remains `4f317efdc2a8583190ca275084ccf976632573fe32a5c57e274d04d10e7570b2`.

After that review, the complete foreground command is:

```sh
set -euo pipefail
cd /srv/android/asus-reviewed-build-kit/r3
printf '%s  %s\n' a00ea8d7c944d45e3035296c81b31a369f13bde830f88a7165b0d7542960717c inputs/kit-pins.json | sha256sum --check
python3 -B scripts/integrate.py --mode PARENT_EXECUTE \
  --prior-failure-review /srv/android/asus-reviewed-build-kit/r3/parent-review/r5-failure.json \
  --prior-failure-review-sha256 "$(sha256sum parent-review/r5-failure.json | cut -d ' ' -f 1)"
```

The JSON hash must be the file the parent actually reviewed. `PLAN_ONLY` is the default and can be run with the same review arguments for a read-only eligibility check; a passed check is not a reserved build slot. The active command repeats all checks under the original flock.

The supervisor exclusively claims `attempt/` and unused revision r6, preserves preimages and r5 logs/images, applies and checks all selected sources, and keeps the same open-file-description flock continuously through integration, child build, and final validation. The child independently verifies inherited lock identity and consumes its launch once. The real build uses `m -j8` for required native/host tools, then `m -j8 bootimage systemimage`. `NINJA_ARGS=-v` retains actual compiler/linker commands. There is no installclean command, automatic retry, detached launcher, or supervisor waiting for an earlier build.

Any failed/partial attempt is retained. Do not remove `attempt/`, consume r6 again, overwrite result markers, or retry automatically.

## Implemented validation

- Exact 12-source sensor origin, genuine SDK37 HIDL service/implementation selected with `:64`, and byte-exact r2 suffix composition for device.mk, BoardConfig.mk, and ueventd.
- Exact one-file platform BPF patch12 and one-line vold `<algorithm>` fix, with preimage, preservation, apply, integrated-postimage and final-product hooks.
- Complete 201-file qualified BPF supplement integrity and authoritative object selection; fixture ELFs are never installation inputs.
- Final native compiler/linker/Ninja-log and source provenance, ELF64 architecture, unstripped/installed build-ID and byte identity, installed init/permission/VINTF sensor files, and SYSTEM extraction checks.
- All 26 selected BPF objects covered across platform/vendor and extracted APEX containers, including the previously missing vendor filter object. Changed/new compiled outputs require fresh r6 command/execution evidence. Qualified unchanged platform objects remain byte-exact.
- Google 32-payload coverage: 30 signed/metadata files remain byte-exact to release in installed tree and SYSTEM. JNI has independent release-source/allocated-code/data and ELF checks. The JAR has independent release bytecode or dexpreopt companion checks and final SYSTEM checks.
- Authenticated userdebug adb_root/adbd selection remains enforced. Final policy neverallows, contexts, init, APEX, VINTF, image integrity and corrected physical-kernel/LK packaging are mandatory before completion.

## Remaining gates

The real r3 Soong graph, new sensor compile/link, product boot/system build, final compiler/payload validator, installed policy/context/APEX/VINTF checks, and full physical boot/service behavior have **not** run. The bounded host check uses a mechanical translation of the exact macro-free sensor TE/genfs additions with existing real split CIL; it is not a new Soong policy product. Both init checks, candidate CIL with neverallows, and actual checkfc passed; a deliberate neverallow failed as expected. Native `property_info_checker` and `checkvintf` were unavailable at that check and are requested by the future build.

BPF's real property-service/runtime success, physical BMC156 calibration/restoration and operation, Google runtime, authenticated root runtime, audio/camera routes, and device commissioning remain parent-owned gates. No device/ADB/root/flash/private calibration/key-content/cloud lifecycle operations occurred here. No whole-kernel or physical GO is granted. The parent's separate targeted service build and separate audio-kernel task remain independent.

See REPORT.md, `inputs/kit-pins.json`, `evidence/`, and `ARTIFACTS.sha256` for exact results and preserved failures. Continue from these files; do not restart composition.
