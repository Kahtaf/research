# Final image early Android startup

Question: What actual userspace blocker follows genuine final SYSTEM startup and the original odsign key wait?

Status: COMPLETE — one actual OS boot, declared 600 second wall limit. Guest requested `reboot,bpfloader-failed`; owned QEMU exited through `-no-reboot` after 407.95 seconds, before timeout. This is a captured boot failure, not OS success. No second OS boot was run.

## Observations

- Both namespace generations passed using actual final packaged binaries, with no candidate bind. All 39 actual APEX packages activated. Original APEX and Keystore module-hash waits completed.
- Genuine SOFTWARE Keymaster/Keystore initialized the odsign key. odsign then waited for real ART compilation: odrefresh compiled boot and service artifacts, returned 80, and odsign logged `On-device signing done.` Original `odsign.key.done=1` wait completed at guest 382.043 seconds after 277.955 seconds waiting. Public observer read both `odsign.key.done=1` and `odsign.verification.done=1`; odsign issued its own `ctl.stop`, and init killed it as recorded. No normal odsign process exit code is claimed. This run resolves its wait through actual completion; the old 180 second bound did not establish a deadlock.
- At guest 383.008 seconds real NetBpfLoad reported `tether_error_map` desired/found mismatch, `errno 22`, desired ARRAY type 2, key/value size 4, 31 entries, flags 0; found fields were -1. Loading `/apex/com.android.tethering/etc/bpf/mainline/offload.o` returned -76. Service `bpfloader` exited 38 at 403.023 seconds; genuine `reboot_on_failure` requested reboot. The precise kernel syscall deficiency is not isolated by this run. No BPF readiness was supplied: `bpf.progs_loaded` remained unset. Zygote was not reached.
- SELinux observer samples read enforce=1. Real ro.debuggable, ro.secure and ro.adb.secure read 1. No policy/trust/crypto waits were bypassed.
- Separate nonfatal errors remain: absent `/metadata` caused early aconfig missing-directory failure (exit 5), post-fs platform aconfig exited 6, mainline aconfig init exited 1; lmkd repeatedly exited 0 with missing memory-cgroup support; uprobestats requested unsupported PERFMON. Final vendor fstab has no metadata backing and the actual BOOT ramdisk was preserved apart from listed fixture adaptations. No synthetic metadata mount was added. A durable product metadata design remains a parent decision.

## Inputs and adaptations

Published receipt: `../2026-11-07-asus-radio-trigger-build-r4/evidence/delivery.json`. SYSTEM SHA256 `fff09d5ab4e0ca301786830d133106152c4c0aca15a2c49166c28827aa5e3f79`, 3753902080 bytes, inode 28131263, mode 0444. BOOT SHA256 `784d4dc565e7742ea607683d2a67d1fdb066764bddfa369895cbaaf6f048b435`, 9242624 bytes. Selected identities were identical before and after. Parent final-report hash corroborated admission; no repeated full raw hash/copy/materialization. Final BOOT ramdisk was byte-identical to the prior admitted ramdisk.

Diagnostic virtual kernel SHA256 `95a62a8bccd3085d682a89b6c74c7afd0961cebd1e3137b256229849920b549b`; config SHA256 `c2ea1277e1574da39d1d55d31bde7bda439ab624561ad3c6a6f4730e38f57834`. This is the existing virtual kernel, not the separately building physical diagnostic kernel. No other worker progress or process state was inspected.

1. Fresh thin COW over the final raw, opened read-only during actual OS boot; final COW 1835008 bytes. No old binary/APEX overlay. Core init byte-identical.
2. BOOT and vendor fstab map system to vdb and userdata to vda. Exact added file-context line: `/dev/block/vda    u:object_r:userdata_block_device:s0`. Compiled policy unchanged.
3. Added one static read-only shell-domain observer and its init rc; labels copied from actual shell/system-file inodes. Observer only reads public properties, process accounting, enforce state, and selected logcat tags. No property setters or readiness writes.
4. Existing entropy wrapper executes the original first-stage init after a fresh 64-byte entropy input. Seed values/hashes are not exported.
5. Fresh disposable 2 GiB public ext4 DATA; root/system/shell scratch labels and a 0600 shell-owned public report. Generated keys and DATA stay remote. No device/private/calibration input.

Fixture patching used a separate minimal Linux helper with a 45 second limit, completed in 1.48 seconds; it did not execute Android init. Actual OS run used two vCPUs, 2048 MiB guest RAM, no NIC/USB, no monitor, no reboot, no added RLIMIT_AS. Only owned QEMU was supervised. No VM lifecycle changes, device access, active AOSP/source/out writes, builds, integrations, or additional OS boots occurred.

## Outputs and continuation

- `run-runtime/serial.log`: complete actual boot serial.
- `evidence/public-report-compact.txt`: deduplicated public observer/odsign/odrefresh logs; full public report retained remote.
- `evidence/adaptations.json` and `evidence/cow-verification.json`: exact requested file changes, inode labels and small accounting.
- `evidence/base-unchanged-receipt.json`: before/after SYSTEM/BOOT identity and retention receipt.
- `HANDOFF.json`: machine-readable outcome.
- `scripts/`: owned preparation, run, extraction and collection scripts.

Remote owned prefix: `/srv/android/asus-final-image-startup-20261107`. COW, failed logs, DATA and private entropy-containing initramfs are preserved there. DATA and initramfs were sealed 0400 after QEMU stopped. Only compact public diagnostics and receipts were exported locally.

Parent continuation: use this offload-map failure as the next diagnostic boundary when evaluating the independently built physical kernel. No product patch is staged: this run does not justify changing userspace map requirements or weakening loader failure handling. Do not infer full boot, physical GPU/HAL functionality, cross-profile/hook support, hardware/TEE, signature/flash qualification, or success of the known netd pair from this earlier offload-object failure. The netd 26-byte/hook limitations remain unqualified here. Further runtime or product integration is a separate parent decision.
