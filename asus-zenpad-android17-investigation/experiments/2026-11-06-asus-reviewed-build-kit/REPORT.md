# Reviewed-input integration/build kit

Implemented a separate, pinned SDK37 integration/build kit locally and in `/srv/android/asus-reviewed-build-kit/r1`. All work was performed by this worker, without subagents. No active integration, next full build, device command, calibration/private-key read, cloud resource operation, arming, physical GO or goal change occurred.

The original r5 state was inspected before implementation. It was still running, with supervisor 78673 and siso 132874; no r6 artifacts existed. Subsequent bounded preflights refused the live build and observed the held real lock. They did not wait for r5 to finish. Detailed final verification is recorded in `evidence/tests-verified.json`, `tests-linux-verified.log`, `live-preflight-verified.json`, and `live-input-audit-verified.json`.

## Implementation

`scripts/integrate.py` defaults to PLAN_ONLY. It validates its kit seal before using the fixed production plan, checks actual native processes, opens the existing full-build lock without creating/truncating/replacing it, acquires it nonblockingly, and repeats process checks. Real terminal markers, coherent results, unused r6 and unused `attempt/` are mandatory. Unknown or inconsistent prior results stop. A failed r5 requires a separately supplied, explicitly parent-reviewed receipt whose exact SHA256 and underlying log/marker/image hashes must match. No state file alone launches anything.

The lock remains held across preservation, patching, product copies, launch and completed-product validation. The child inherits the very same flock FD. `check_launch.py` checks its inode, actual held state, supervisor ancestry and exclusive one-shot consumption. There is no release/reacquire gap and no detached waiter. A failed or interrupted attempt is preserved, never retried or rolled back automatically.

The exact kernel patch applies only to the original active kernel tree after terminal gates. Preflight checks all 61,976 frozen baseline files and their selected file set, all 268 changed-file preimages and compiled-fixture postimages, the patch hash, staged manifests, parent parity, config, kernel and packaging pins. The source link must resolve to `/srv/android/asus-android17/kernel-bpf-fd`. The already compiled combined fixture is read-only.

Before source writes, the kit backs up every changed existing source and records absent destinations, copies the original r5 logs, and moves existing output image inodes into its archive on the same filesystem. It does not copy a whole SYSTEM/data image for preservation. Missing output targets are then recreated by the incremental build. Preservation failures stop before source integration. A later copy or patch failure leaves the partial state and backups for parent inspection.

Integration installs the 25 reviewed radio changes, the explicitly selected combined prebuilt (26 total product differences because BoardConfig is already among those 25), matching generated defconfig, exact three Connectivity11 files and wificond. Product selection is by exact manifests; unexpected candidate files or unrelated changes fail. Postintegration and final-source receipts expose the actual bytes for parent/source-adapter binding.

`scripts/build.sh` requests the real SDK37 host tools, root/APEX modules, radio services, network components, policy tests/neverallows, then `bootimage systemimage`. Both invocations use `m -j1`. It requires the existing prior clean receipt and never runs `installclean`. It preserves secure authenticated ADB/userdebug and rejects disabling neverallow checks. It does not require runtime service-chain success before compilation.

## Updated validation

The exact one-line root-readiness patch was applied to the copied original validator text and its intermediate result matched the parent's recorded after-hash. The final validator additionally requires `com.android.adbd`, rejects disabled neverallows and takes its integration receipt explicitly. `evidence/root-validator-patch-application.json` records this derivation. No active validator was edited.

The new completed-product validator uses the kit's current receipts and the parent's pinned standalone packager. It no longer reads old hardcoded `R/evidence/active-integration.json` or runs the stale continuation scripts. Its future checks include:

- Real final ARM32 radio ELF dependency/symbol/page checks, installed init scripts with generated passwd/property contexts, full installed CIL linking with neverallows enabled, file/property contexts, and native SDK37 policy test targets. Android's valid empty product-specific file-context supplement uses `checkfc -e`; platform/vendor contexts remain mandatory. The source review is preserved.
- Actual `apexd_host` extraction and `apex-info-list.xml`, then VINTF with the real selected kernel release/config and extracted APEX metadata.
- Installed `adb_root` ELF and exact init source, genuine selected adbd APEX metadata/extracted AArch64 daemon, generated `ro.secure=1`, `ro.debuggable=1`, `ro.adb.secure=1`, and matching root-route bytes in final ext4. Actual BOOT property files are checked too. Runtime root stays unproved.
- Exact existing Google signed blobs and metadata from the pinned source manifest, both installed and read from final ext4. The manifest has 30 directly checked signed/metadata files; its two `.jar`/`.so` transformation inputs retain the existing separately-built treatment. No Google payload is replaced or downloaded by this kit.
- A full 3,753,902,080-byte raw SYSTEM output with all bytes, zero ranges and tail explicitly written, an ext4 check, source-image rehashing, and a final full raw hash.
- Actual completed BOOT packaging with synthetic mode disabled, the correct executable init/fstab, physical kernel/config, real KERNEL/ROOTFS LK wrappers, 92-byte `enforcing=1` header, actual Image size/reservations and ramdisk bounds. Unknown or wrong source BOOT/kernel/config/ramdisk inputs fail. Only an explicitly UNTESTED BOOT is emitted.

These are implemented future checks, not claims that genuine current service link outputs, final images, runtime APEX activation, hardware or the full service chain already passed. Those outputs were absent during the ongoing original build. Host tests do not substitute for the parent-owned physical qualification.

## Input pins

The sealed kit manifest hash is:

```text
9b9eea2ae274a873d99459ea4faa352dba1dd6a9ba8b5986fae0304047ee941b
```

It binds 42 internal files. `inputs/plan.json` contains all 41 exact external pins. Key bindings are:

```text
parent STAGED.json       b6dd5e14c88eb19ece0187ac586ecea8186c45a238c5fbc21a94ef97f4426bca
parent scoped parity     c41c57757ec3e37eed57655f0876ad5efefd2dcd44c4eb5f8a809518badb1696
actual kernel contract   2e21015ca5cba34033f16a1453ed7c6a593952aee6bf78e49b3f061bbd5e28cd
combined source receipt  b207be8fcb6739202fae31f54a987f2d11834d43f618edd2a47c6cc33fe2ebe4
source baseline receipt  e219c0e87d2cfca252088e06839dbf9cedaa794b3832e3829cf5c96021717315
source patch             3ee1f9835330e1a589c0e93a73fc65ebdb57ffd9b48a8bbbd32a7bc98e0f3f8b
physical kernel          46895deb12ec94160ea5af0e85afa89c6de84971db126bb94c60cec1ec3ec401
physical config          067090e03ad762344308cebd0a71274d9943e299ded6707051ebfdc075dd045f
root readiness patch     3684dee7f2730e63bf20dfa8b8107d4745943c306f29bf028e3fcf275fc3d71e
packager entry point     b527e9e473b6f24155e91c23ef1f16877ab04f37bcc37422ecd0f18bd0c01129
```

The kernel is exactly 7,705,525 bytes. All eight full-BOOT packaging inputs are independently pinned in the staging manifest and kit plan. The parent scoped parity supplement records 290 independently checked source files, 134 options and 84 exported payloads. The old immutable manifests continue to say parity false; this kit does not rewrite them or turn scoped acceptance into full-service-chain acceptance.

## Behavioral evidence and limits

The Linux suite contains 21 meaningful tests, using small filesystem/native-process fixtures under one CPU affinity and a 1 GiB address-space limit. No compiler, Ninja engine, Soong invocation or full target build runs in the suite. It covers live native-process and real flock refusal before mutation, missing/mutated preimages/parity/artifacts, exact manifest selection, unknown/incoherent prior results, hash-bound failed-prior review, preservation, uninterrupted lock ownership during integration and launch, one-shot launch, partial integration and build failure stopping, source-image drift, wrong/synthetic BOOT rejection, root-route/security failures, explicit zero materialization, and absence of cleaning/unbounded build commands.

The production audit independently rehashed the 61,976 baseline files, checked the exact source set and 268 compiled postimages, 25 radio changes and three Connectivity files. It compared all 299 possible write destinations and the full active product manifest before and after. The final live refusal, actual held lock, absent attempt and absent r6 artifacts are timestamped in the final evidence. Earlier iterations and their original seals/logs were preserved instead of rewriting history.

The full integration/build has deliberately not been executed. The actual full product, final validators against its genuine outputs, combined-kernel execution, full service chain, runtime root, Google behavior and hardware remain unproved. There is no flash-ready publication or physical authorization.

Continue with the exact commands in `HANDOFF.md`. Existing parent staging, old spikes and nested repositories were preserved. This spike contains only code, small fixtures, source/metadata receipts and QA evidence; no SYSTEM/data copy, private calibration or private-key material was collected.
