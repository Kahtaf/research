# Firstboot r7 parity: final handoff

**The r7 physical-configuration parity milestone passes within the virtual fixture boundary. The full Android service chain is blocked by missing genuine build outputs.** This final report supersedes the unfinished r7/r11 claims in the earlier firstboot DRAFT; that draft and all previous evidence remain untouched.

The isolated fixture is `/srv/android/asus-firstboot-parity-continuation`. All new runtime work used one QEMU CPU, 1024 MiB and no network interface, sequentially. Only small static test probes were compiled. No kernel rebuild, Ninja, installclean, active-source/output mutation, cloud lifecycle operation, physical device operation or calibration/key-content access occurred. No physical GO is given or inferred from elapsed time. The parent retains shared integration and all device/ADB/USB/root/flashing ownership.

At 19:27 UTC the original r7 status was returncode 0, and its Image/config hashes matched the saved receipts. There was no running firstboot job; prior boot-r11 and qualification-r3 did not exist. The completed kernel was reused. Prior capture-r1 remains the inherited accepted capture identified by `06dace070ff5e9ef11a48ae70fc718b1c42e00e11884ee619c5cdb06f5aa79c8`; this continuation did not rehash all 119 entries or rerun its earlier tests.

Actual r7 Image SHA256 is `95a62a8bccd3085d682a89b6c74c7afd0961cebd1e3137b256229849920b549b`; resolved config SHA256 is `c2ea1277e1574da39d1d55d31bde7bda439ab624561ad3c6a6f4730e38f57834`. The retained kernel command, successful status and terminal compilation log are in `artifacts/frozen-r3/evidence/kernel-r7-*` and `kernel-build-r7-compile.log`.

Actual run handles, all terminal:

- `run-cpuset-r3`: launcher PID1178409, 19:28:00–19:28:03 UTC. Thirteen cpuset/blkio assertions pass, including v2-mode mount, inherited effective masks, attachment to an empty child, clearing masks and cleanup.
- `run-locks-r1`: PID1178686, 19:28:03–19:28:04 UTC. Five POSIX lock assertions pass: acquisition, another process denied under contention, release and acquisition after release.
- `run-policy-r4`: PID1178727, 19:28:04–19:28:05 UTC. The actual 872537-byte compiled product policy loads at policy version30; enforcement is1 both before and after loading.
- `run-boot-r11`: PID1178799, 19:28:05–19:28:12 UTC. Genuine first-stage/SELinux/second-stage init, ueventd and property service run. SetupCgroups succeeds, UID0/PID groups exist, and the observer reads ueventd's actual PID from its cgroup.procs.
- `run-locks-r2`: additional r6 negative control, completed with the identical lock-probe ELF. Parent acquisition, unlock and acquisition after release fail with errno13, giving three failures as expected. QEMU exits0 even in this negative control; exit status alone is never treated as a pass.

Every run has `command.json`, `status.json` and raw `serial.log` under `artifacts/frozen-r3/`. Every QEMU run exited0 without timeout. The 37 final assertions are independently recorded in `evidence/qualification-final.json` within that export; `evidence/parity-run.json` records the four positive launch handles and timestamps. `runtime-input-hashes.json` pins run scripts, probe ELFs, initramfs and consumed Android inputs. Guest ueventd is the normal `/system/bin/init` symlink: its host-side absolute target does not resolve, but its guest execution and SID are directly observed.

Actual domains are `u:r:init:s0`, `u:r:ueventd:s0` and observer `u:r:shell:s0`, with enforcement1. Genuine ueventd completes coldboot; init expands `ro.cold_boot_done=true`. Both property sockets are created. The allowed non-readiness diagnostic property round-trips through the real service. The forbidden persistent property receives `PROP_ERROR_PERMISSION_DENIED (0x18)` and remains unset. Shell's denied access to protected paths/properties is retained, not mistaken for absence.

The unchanged SDK37 cgroups.json is `ab2ed667ff45958843fb0c6ee953a5512def0ae87470c4358aa9576a6a4b2e22`. Preserved prior negatives include old cpuset-v2-mode ENOENT and boot-r8's mandatory cpuset mount failure. No permissive/allowall policy, readiness setter, skipped crypto wait, fake service or trust substitution was introduced. The observer is diagnostic instrumentation inherited from boot-r10, not a replacement Android service.

The genuine fatal next gate is still `Cannot find '/system/bin/apexd'`, followed by normal `bootstrap-apexd-failed` shutdown. There is no boot-complete claim. MEMCG remains absent and optional-controller warnings remain visible. CPU hotplug, mandatory-lock semantics, HIDL registration, Keymaster operations, keystore crypto, APEX trust/verity/activation, final linker namespaces and authenticated adbd are untested here. Kernel standalone lock/cpuset probes do not establish Android-domain crypto access. This run uses real compiled SDK37 components but does not establish complete Android17 OS/version-property readiness.

Combined physical r5 correspondence is **scoped and verified**, not whole-kernel equivalence. Image `46895deb12ec94160ea5af0e85afa89c6de84971db126bb94c60cec1ec3ec401` is 7705525 bytes; physical config is `067090e03ad762344308cebd0a71274d9943e299ded6707051ebfdc075dd045f`. All 288 previously pinned firstboot source postimages still match. The expanded 290-file comparison, including fs/locks.c and include/linux/fs.h, byte-matches the combined source. All 134 selected config values match, explicitly including FILE_LOCKING=y, MANDATORY_FILE_LOCKING=y, CPUSETS=y and BLK_CGROUP=y. Full receipts are `combined-parity.json` and `prior-source-pins.json`.

There are 950 whole-config differences. The virtual GIC adaptation and physical board differences remain; network/radio integration is outside this runtime result. The combined physical kernel was not executed. Do not copy the virtual config onto hardware. The physical patch set remains BLK_CGROUP plus the cpuset-v2 semantics/cached-flag source patch; FILE_LOCKING parity restores existing physical settings in the virtual fixture. The combined owner's immutable manifest still says firstboot parity false; this supplemental receipt allows the parent to reconcile that gate deliberately without rewriting the old receipt.

Service availability was inspected at 2026-11-06T19:28:53.214727+00:00. Genuine stripped and unstripped outputs for all five requested services remain absent, as do their installed product paths. The captured final link edges still lack 22 inputs for apexd, 7 for hwservicemanager, 75 for keystore2, 5 for servicemanager and 3 for software Keymaster. Counts include TOCs. The Keymaster blockers are service.o and vendor-CFI libkeymaster4.so plus its TOC. Exact variants, link targets and every missing file are in [MISSING-TARGETS.md](MISSING-TARGETS.md), backed by `services-current.json`, `service-output-alternatives.json` and the tested read-only readiness command (exit2).

The previously frozen genuine linkerconfig and signed adbd APEX remain available as intermediate artifacts; their manifest is retained in `late-outputs-prior-manifest.json`. Their absence at installed product paths does not mean the intermediate artifacts are absent. They do not replace the missing service chain. No optional service-chain launch was attempted without prerequisites. Networking patch12 and its security-hook gaps remain with their owner; the immutable networking handoff was not modified and no bpf.progs_loaded value was fabricated.

At the final 19:29:58 UTC build observation, original supervisor78673 and siso132874 were alive, with the full-build log at approximately58% (93641/160828). This is a timestamped observation, not a promise of present status. No competing build or waiter was started. Parent integration must first establish original r5 termination independently.

The next builder command is read-only and reproducible:

```sh
python3 /srv/android/asus-firstboot-parity-continuation/source/continuation/check_service_ready.py
```

It prints the exact current missing paths and exits2 while any captured service link output/input is absent; exit0 means only that these link prerequisites exist. After original r5 terminates and genuine prerequisites appear, the parent should capture them and their dynamic dependency closure into a new numbered input revision, retain the real policy/init triggers and signed APEXes, and resume ordinary crypto/APEX/adbd sequencing. Do not replay `prepare.py` or rebuild r7. Existing run directories intentionally reject duplicate launches; the prior missing-apexd run must remain preserved.

Local export r3 contains 84 verified payload files in a 159947-byte archive, SHA256 `673323b4027cbb64b0dca34003e0e1bfb94eccc60ae5731e2122e0d22168d16a`. Only small source/evidence records were downloaded; no SYSTEM/data image was copied or rollback image rehashed. The first export remains preserved. Export r2 failed a local integrity assertion because its manifest included its own previous revision; r3 excludes that self-reference and every payload hash passes. The rejected r2 archive and diagnostic remain preserved. This packaging correction did not alter runtime evidence.

Google Play/Services, root, debloat, physical boot and working hardware remain outside this qualification. No factory-calibration or rollback artifact was modified.
