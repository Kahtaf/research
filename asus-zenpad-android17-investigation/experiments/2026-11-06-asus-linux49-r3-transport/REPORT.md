# R3 exact recovery transport — implementation handoff

Implemented and verified offline. The corrected R3 image is the only accepted candidate in the new transport and observer. The historical R2 install CLI still refuses execution. Both final fresh-process replays passed **60 tests** with zero failures/errors and zero actual subprocess calls. No device, USB, ADB, root helper, SSH, builder machine, cloud resource, calibration, private key or full SYSTEM/data image was accessed by an execution command. Local pinned helper/binary and two stock recovery files were read only for verification. Physical boot remains unproved; `hardware_ready` remains false.

## Exact artifact and reproduction

Candidate: `../2026-11-06-asus-linux49-probe-initrd-fix/artifacts/probe-r3/UNTESTED-combined-linux49-ram-probe-r3.img`, 8,880,128 bytes.

- Image SHA256: `45551fec6af489bef6813131fb3854eddcfe95d3ca3fa640fea7a37dfd21b630`.
- Zero-padded 16,740,352-byte p10 SHA256: `01d7bbb4d8951875f753fde2c1f7fb486dec1e42bd502b6b93a5296245fe9bf3`.
- Combined-r1 compiled input: `d4094bcff6c763af7f1c01ccd3d612a988f96de13f78b492b808cc76c0ac929f`.
- Header page: `4b58f4a3032eb2814c54bafbe0c95337822dbdf0d940ff822ea8540e8e1687d8`.
- Packaged DT: `e629e636c1e5ef5dc2c80bcab5fd8de7b1c6d962c4036ef3b9945afa86a01246`.
- Ramdisk gzip: `7d7ed3b6ad1d477afd970181d433e64ad09398da19bfeb1f0f8f58901edcd4df`.

[`source/reproduce.py`](source/reproduce.py) verifies and invokes the parent's exact pinned metadata builder, redirecting its outputs exclusively into this spike. It does not rebuild a kernel. The reproduced image **and manifest are byte-identical** to the parent's originals. [`evidence/reproduction/receipt.json`](evidence/reproduction/receipt.json) records the result. The rebuilt image is in `evidence/reproduction/artifacts/probe-r3/`.

The reproduction re-parses the image, cpio and DT using the pinned metadata helpers. All 22 cpio entries match the inherited exact mode/uid/gid/length/hash profile. The complete wrapped ramdisk and compressed Image are unchanged from R2. Only `/chosen/bootargs`, `/chosen/linux,initrd-start`, and `/chosen/linux,initrd-end` differ from the original compiled DT. The corrected range is `0x44000000..0x4411f7b0`; length is 1,177,520 bytes. The header is exactly 95 bytes and carries `initrd=0x44000000,0x11f7b0`, within the traced LK 99-byte copy limit.

This is reproduction with the pinned builder, not an independent CPU emulation or physical test. The parent's exact LK semantic evidence was read; its assumptions, including no extra runtime initrd token and the secure-monitor stop boundary, remain applicable. The unchanged original manifest's `transport_profile_ready=false` is historical metadata, preserved for byte identity. This delivery supplies the separate transport implementation without rewriting that manifest.

## Implementation and review receipts

[`profile.json`](profile.json) is derived from the old profile plus the parent's R3 manifest. It preserves the original control identity, p10 geometry, compressed kernel and per-cpio provenance. It adds explicit builder/manifest/old-profile provenance and the relocated initrd range. `physical_execution_authorized=false`, `physical_boot_proven=false`, and `hardware_ready=false` are retained.

- Profile SHA256: `1729116fe9f302052d84589805b8ea665c2317e5a3a734675baabe320fc7ceca`.
- New observer SHA256: `01ce966e7fc269e69d7468d824646cb1b123c20c01708e5b5aebc3e2bb849dd8`.
- Code-bundle SHA256: `f9aa8238d9d5d09c5d82d8ad8fb5c557a5d245fae819f93194208ac12608a32e`.

The bundle digest hashes the compact sorted JSON file mapping in [`evidence/code-receipt.json`](evidence/code-receipt.json). The adapter, engine, profile and new observer are included. [`evidence/source-freeze.json`](evidence/source-freeze.json) additionally freezes all implementation/reproduction/test files. [`evidence/implementation.diff`](evidence/implementation.diff) and its separate engine/adapter/observer/profile diffs are the concrete review inputs. Unmodified original small sources are retained in `evidence/reference/`.

The engine differs from the previous transport only in `BASE`, now `/data/local/tmp/asus-linux49-r3-transport`. The original shared mutation lock, stock-only validator, helper/root pins, fixed Wi-Fi endpoint, device/alias/node/geometry guards, bounded p10 writer, inverse logic and uncertainty stops are byte-for-byte unchanged. A regression gives the unchanged stock-only validator the **actual R3 image** and proves rejection for its non-stock kernel.

The new adapter removes the R2 quarantine only in its own exact R3 entry. It retains the default PLAN_ONLY behavior, source/profile review hashes, truthful supervision/fallback gates, fresh canonical same-run UUID pin, 180-second freshness checked again at candidate dispatch, topology binding, current `adb -t` guarded inventories, exact stock fingerprint/SDK24/secure-ADB/Enforcing checks, and separately verified Wi-Fi `IP_REDACTED:5555` identity. Full staged bytes and full p10 readbacks remain mandatory. There is no image, target, endpoint, force, retry or resume override.

The new observer retains USB serial `P00A49PROBE`, product `p00a_diagnostic`, model `P00A_RAM_diagnostic`, device `p00a`, state `recovery`, and marker `ASUS RAM-only diagnostic combined-linux49-r1`. It accepts only the corrected initrd token, rejects missing/wrong/duplicate tokens, and pins the complete image/padding/header/DT/ramdisk. The parent's observer with SHA `75b1d96686a484e0eb5cfd73ec62976c394de1895e14ea45c83ea745d15f07ec` remains unchanged and historical.

The new observer's standalone `finalize --execute` is refused. Its internal byte assessor is used only after the adapter validates a same-run post-return root-read and Wi-Fi-pull journal. This prevents a parent-facing alternate CLI from accepting a copied stock backup as capture evidence. The finalizer still verifies command hashes/status, exact guarded full-p10 read, fixed Wi-Fi pull, captured bytes, chronology, original install/pin linkage and current stock health. Host journals are auditable evidence, not hardware signatures.

## R2 quarantine and source preservation

[`evidence/r2-quarantine.json`](evidence/r2-quarantine.json) records the original R2 CLI returning code 2 with `R2 INSTALL QUARANTINED`, even with its current code/profile digests and every attestation flag supplied in a process-blocked offline test. It refuses before lock or transport access. The old published `6bfe...` bundle remains intentionally stale. The original R2 adapter, quarantine notices, observer and image were not edited.

The new entry also rejects the actual R2 image and old profile/pin. A real product-r3 compiled input is rejected; every compiled input except the exact combined-r1 hash is forbidden, including product-r4. No product-r4 physical or artifact test is claimed. There is no generic bypass. “R2 uninstallable” here means neither supported exact-candidate CLI permits its installation; arbitrary privileged programs outside these tools are not controlled by a Python guard.

[`evidence/input-receipts.json`](evidence/input-receipts.json) records the inputs before work; [`evidence/source-preservation.json`](evidence/source-preservation.json) confirms their hashes afterward. The original failed parent replay and subsequent successful replay are included in that preservation check. Existing nested repositories and all original artifacts remain in place.

## Tests and limitations

The final suite contains **32 inherited transport methods, 15 observer methods, and 13 R3 regression methods**. The two final runs use identical implementation and test source hashes:

- [`evidence/final-replay-1/receipt.json`](evidence/final-replay-1/receipt.json): 60/60, 6.806 seconds.
- [`evidence/final-replay-2/receipt.json`](evidence/final-replay-2/receipt.json): 60/60, 7.317 seconds.

Each starts in a fresh Python process and installs an audit hook before importing implementation/tests. Actual subprocess, shell/exec/fork/spawn and network operations are prohibited. The process count is zero and neither run recorded a blocked operation. Typed fake fixtures inject the exact adapter's engine/observer modules, avoiding duplicate fixture imports. Test receipts record test-source hashes, state errors, error events, command counts, pin ages, CLI results, platform/Python versions, and complete failure tracebacks if any occur. Temporary 16-MiB emulation files are removed per test. The delivery uses about 9.3 MiB on disk before final documentation.

Coverage includes complete emulated install → report → stock return → inverse → journal-linked finalization; all p10 geometry fields; USB identity/topology changes; secure-ADB/SELinux/stock identity; full staging and readback corruption; one inverse or already-stock no-write; failed/ambiguous inverse; no commands after transport uncertainty; stale and staging-expired pins; missing attestations/hashes; shared lock contention; replay refusal; helper mutation; reader/journal/capture tampering; copied-backup rejection; bad/missing reports; optional unavailable measurements; unverified directory listings; R2 quarantine; exact R3 provenance and token regressions.

The earlier parent R2 run with **15 failures and 1 error across 32 tests** is preserved unchanged, as is its later 32-method successful replay. The historical failure cause remains unresolved. The new failures did not recur, but these results do not retroactively explain or relabel the earlier run. New scenario errors are retained so a recurrence is diagnosable. The preliminary new 59-test pass is also retained; one additional real product-kernel rejection and better CLI state capture yielded the final 60-test frozen suite.

Four outcomes remain distinct: `report_collected`, `diagnostic_requirements_passed`, `stock_returned`, and `stock_recovery_readback_verified`. All acceptance shown by tests is fabricated offline fixture evidence. No actual report, physical stock return, stock partition readback or hardware readiness is asserted by this handoff. Optional measurement errors remain unavailable, directory listings remain unverified, and `hardware_ready` is always false.

## Parent continuation

Use [`COMMANDS.md`](COMMANDS.md) for concrete offline review/replay and individual guarded parent commands. Review and freeze the exact code/profile/observer before a run. The first physical 4.9 test still requires actual nearby fallback and current supervision; the expected 23:03 UTC return time does not establish either. This report is not a physical approval or mode-entry instruction.

The parent owns all device/ADB/root/flashing and manual boot/return actions. No tool here enters recovery, reboots, changes BCB/para, touches other partitions, discovers/reconnects transports or enables Wi-Fi. Candidate/stock transfer uses the fixed authenticated Wi-Fi endpoint while USB remains healthy. At most one candidate attempt and one stock inverse are permitted per run. Uncertain execution stops without automatic cleanup, inverse or retries; preserve evidence for parent assessment.

After actual observed stock return, use a fresh same-run stock pin and the genuine restore/readback phase, then the adapter finalizer. A stock boot alone or a copied backup cannot satisfy restoration. Full Android 17 OS work and the separate whole-BOOT packager correction are outside this spike.
