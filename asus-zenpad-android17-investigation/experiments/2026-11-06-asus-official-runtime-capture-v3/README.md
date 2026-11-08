# Official runtime capture preparation v3

Question: can the bounded official-runtime capture preparation use the exact SDK37 product and system_ext property install paths, while retaining v2's qualification and provenance boundary?

Status: prepared and self-reviewed; **58/58 genuine Linux offline fixture tests passed**, zero failures/errors. No real output availability, selection, verification, or capture is asserted. Owned VM revision: `/srv/android/asus-official-runtime-capture/preparation-v3`. The prior `preparation-v2` remains untouched.

Important outputs: `source/`, `inputs/selector.json`, `inputs/profile-r8.json`, `tests/test_capture.py`, `tool-pins.json`, and `evidence/` receipts. Large graphs, ELFs and fixture work remain on the VM.

Continuation: read the final report and exact pins before executing anything. A parent must independently establish a genuinely successful, qualified terminal r8 with matching source bindings before selecting actual outputs. The default CLI prints only a static plan. No device, build, process lifecycle, cloud lifecycle, or physical GO action is part of this preparation.

## Primary-source premise correction

The prior premise that product and system_ext install their properties directly below their partition roots was incorrect. The parent exact native graph receipt `evidence/exact-seven-producers-r3.json` records:

- `system/build.prop` from `out/soong/.intermediates/build/soong/system-build.prop/android_common/build.prop` (graph line 458381).
- `system/system_ext/etc/build.prop` from `out/soong/.intermediates/build/soong/system_ext-build.prop/android_common/build.prop` (line 458407).
- `system/product/etc/build.prop` from `out/soong/.intermediates/build/soong/product-build.prop/android_common/build.prop` (line 458268).

All install targets are relative to `out/target/product/p00a/`. Genuine init's `PropertyLoadBootDefaults` states that `/<part>/etc/build.prop` is canonical since S and handles system specially at `/system/build.prop`; product/system_ext legacy fallback is restricted through SDK30. Its quoted source is preserved in the parent receipt. A fresh public-source read is also preserved in `evidence/public-init-premise.json`: source SHA256 `5c3c53b56705328e1d482c897df6e8ab129c4998efab620595aec717464df4be`, lines 1149–1233. SDK37 therefore requires the exact graph targets above. This is a source/graph premise correction, not evidence that the outputs currently exist or qualify.

The selector, property validation loop, mandatory contract and synthetic fixtures use these exact paths. The contract refuses the obsolete product/system_ext paths, including when added alongside the canonical paths. Mandatory SDK37 properties and generated-byte provenance remain required. The signed packages, complete policy/CIL/mapping/context groups, source and generator bindings, finite resource ceilings, symlink/private exclusions and success-only terminal gates are retained.

## r8 identity

The profile binds kit seal `f55aedf8ac9d2a513e3663230db0b9d802e72b5df512fc0db6b3714331a7efa4`, supervisor `1580911`, native child `1581077`, and original lock inode `15018964`. Parent launch and observation hashes are recorded in `inputs/fixed-r8-metadata.json`. The single permitted VM read at `2026-11-06T23:29:56.273946+00:00` corroborated both immutable metadata files; `evidence/r8-identity-once.json` records their exact hashes. These establish identity only. No failed r7/r8 terminal, missing completion, disabled validation, synthetic property value or placeholder PID is accepted.

## Parent commands

Run the default plan without inspecting source/out:

```sh
python3 -B /srv/android/asus-official-runtime-capture/preparation-v3/source/capture.py
```

Only after independent successful terminal qualification and review of this sealed revision:

```sh
python3 -B /srv/android/asus-official-runtime-capture/preparation-v3/source/capture.py select --name select-r8-001
sha256sum /srv/android/asus-official-runtime-capture/snapshots/select-r8-001/selection.json
```

Review selection and COMPLETE, then pin the actual selection hash externally. Substitute it for `SELECTION_SHA256` below; it is never a made-up value or an approval flag:

```sh
python3 -B /srv/android/asus-official-runtime-capture/preparation-v3/source/capture.py verify --name verify-r8-001 --selection /srv/android/asus-official-runtime-capture/snapshots/select-r8-001/selection.json --selection-sha256 SELECTION_SHA256
python3 -B /srv/android/asus-official-runtime-capture/preparation-v3/source/capture.py copy --mode PARENT_EXECUTE --name capture-r8-001 --selection /srv/android/asus-official-runtime-capture/snapshots/select-r8-001/selection.json --selection-sha256 SELECTION_SHA256
```

Use unused destination names. Each action is exclusive and preserves failures; there is no resume, wait, fallback or force flag. The original lock and live-native exclusion remain mandatory. The parent SSH wrapper is `../2026-11-06-asus-product-input-build-kit/scripts/remote.py`: import `run(script)`, then invoke exact argument vectors with checked subprocess calls; it has no command-forwarding CLI.

Only a completed select receipt can feed verify/copy. Require the final complete group/source recheck. A future runtime worker must validate all hashes and use the complete new coherent policy set, unchanged signed package bytes and genuine source/generator provenance. Host `/apex` symlinks do not prove extraction, payload architecture, trust, activation or namespace resolution. These require separate future qualification; no readiness properties may be fabricated.

## Scope and limits

The v2 limits remain: 8,192 selected files/edges; 256 MiB ordinary files; 3 GiB total including hash-only provenance; up to 2 GiB terminal log; 512 MiB per graph/2 GiB total graphs; 2 MiB graph blocks; 3 GiB SQLite index; 20,000 entries per enumerated directory; 16 MiB graph evidence; 64 MiB JSON receipts/journal. Linux preparation and tests use one CPU and a 1 GiB address-space limit; QA has a 120 CPU-second ceiling.

No actual source/out writes, AOSP/Ninja/guest builds, active-job observation, process or cloud lifecycle actions, device/ADB/root access, private calibration/keys, or actual output operations are authorized here. r7 and targeted runtime r1/r2 failures are preserved; no targeted r3 is launched. Runtime readiness, full OS/service-chain qualification and physical GO remain unproved.

## Offline validation and final review

`evidence/linux-offline-tests.json` and `linux-offline-tests.log` are genuine VM receipts: 58 tests, zero failures/errors, one CPU (affinity CPU0), 1,073,741,824-byte address-space ceiling, 120 CPU-second limit, 17.768 seconds elapsed and 25,044 KiB maximum RSS. All fixtures live under this preparation's `tests/tmp`; no actual AOSP output or original lock was accessed. These timings describe this fixture run only.

`evidence/linux-qa-execution.json` binds every tested candidate file; no file changed during tests. The final executable code, selector, profile and fixtures are identical to that tested candidate. Only this README, metadata corroboration and the resulting seal changed afterward. `evidence/local-review.json` and `minimal-v2-v3.diff` record the narrow review against v2. `gates.py`, `safeio.py`, `graph.py`, `packages.py`, `elf.py`, `run_tests.py`, the manifest schema and public-source inventory remain byte-identical to v2. The uploader creates only the fresh v3 directory and refuses an existing prefix.

Do not rerun the one-time corroboration script or treat launch identity as a build-result check. Preserve the exact tool seal from `HANDOFF.json` externally. This revision is ready for parent review, without claiming parent approval, terminal success, output availability, runtime acceptance or physical GO.
