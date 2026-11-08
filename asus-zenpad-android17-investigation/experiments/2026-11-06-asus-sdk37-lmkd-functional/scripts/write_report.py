from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent.parent;F=P/'artifacts/frozen';q=json.loads((F/'evidence/qualification.json').read_text());assert q['default_low_ram_functional_pass_with_staged_label_fix'];assert json.loads((P/'evidence/export-verification.json').read_text())['verified'];assert json.loads((P/'evidence/elf-runtime-closure.json').read_text())['verified']
report='''# SDK37 lmkd / PSI / zRAM functional qualification

Genuine SDK37 lmkd starts, registers real PSI monitors and handles controlled memory pressure at approximately the stock available RAM, **with one staged zRAM file-context correction**. Four accepted default-policy pressure/recovery cycles preserve a protected foreground surrogate and evict eligible background work. This is a native memory-subsystem result, not proof that the complete Android17 + Google + root product fits or is usable.

A concrete pre-boot configuration blocker was found: the current platform/default zRAM label is `ram_device`, but SDK37 toolbox/mkswap and init swapon require `swap_block_device` for this `swapon_all` route. Under the unchanged compiled enforcing policy, mkswap fails with Permission denied. Adding only `/dev/block/zram0 u:object_r:swap_block_device:s0` to the fixture's vendor file contexts fixes it. The candidate is in [candidate/vendor-file-contexts.additions](../candidate/vendor-file-contexts.additions). It has **not** been applied to active product sources, policy, out, a sealed kit or hardware.

The separate protected-incompressible overload failed and was explicitly aborted: repeated zRAM swap write errors, no useful recovery, and no completed promotion to an eligible victim pool. That failure is retained, not counted as a daemon-directed eviction. It shows why compressed swap cannot substitute for sufficient RAM when the irreducible/protected working set is too large. It does not invalidate the four eligible-background cycles or establish acceptable full-OS memory headroom.

**Genuine inputs and provenance.** The original r5 full build failed; no full images are inferred. The parent's later targeted native build finished at 22:11:20 UTC with exit 0. This worker ran no Ninja, installclean or Android module replay. The accepted installed ELF is 99,760 bytes, ELF64 little-endian AArch64, SHA256 `ff975915ad8d1f2882cf297c6fa312e144166d87b1251bf880eb6e890a34353d`. Source HEAD is `c3601e823bd07c9c190f67e2f9bc7486e4978328`; lmkd.cpp is `63b6821d591e11536148ab71fd905665575c7679bfbde61b0bacb674cfa20678`.

The frozen runtime closure contains 15 actual ARM64 ELFs totaling 6,147,560 bytes, including linker64 and genuine bionic implementations. A local independent ELF parser verifies hashes, architecture, SONAME and every DT_NEEDED edge; `ld-android.so` is supplied by linker64. See [elf-runtime-closure.json](../evidence/elf-runtime-closure.json), [native manifest](../artifacts/frozen/inputs/native-r3/manifest.json), saved link response files, source manifest and parent build receipts. Final runs consume owned copies; no active-out inputs remain in their runtime dependency closure.

Actual stock MemTotal was 2,000,192 KiB. Accepted guests have 2,001,792 KiB (0.080% higher), using QEMU `-m 1996`, one Cortex-A53 vCPU, one host CPU affinity, single-thread TCG and a 64 MiB translation cache. Every accepted pressure run has a 300-second wall limit, 240-second CPU limit and 3 GiB address-space cap. The filesystem is a small owned 96 MiB ext4 image, built from selected genuine firstboot components; there is no SYSTEM/data image copy or host raw block access. Source/helper compilations are serial, one CPU and 1 GiB capped. Runtime wall/CPU times are resource receipts, not tablet speed measurements.

**Kernel correspondence.** The old verified r7 virtual kernel had PSI, ZSMALLOC and zRAM disabled. A real 2 GiB negative boot confirmed absent PSI/zRAM paths; genuine lmkd subsequently logged ENOENT and exited. Reusing r7 for a positive memory result would have been invalid.

An owned source/config copy was built with the BMC memory settings. Its Image is 5,922,824 bytes, SHA256 `c59e030cdfc3e752eeddbbf62d091ae9760c94d5fbf780a22824e004ec872080`; config SHA256 is `0426746d90db074dd026ae5d383e1cde27d587020699d5dc9af4faac0b54489f`. All 210 selected memory, scheduler, cgroup, zRAM and pidfd source files byte-match the new physical BMC source. The 72 selected config entries and exact delta are recorded in [final-config-parity.json](../artifacts/frozen/evidence/final-config-parity.json), [final-source-parity.json](../artifacts/frozen/evidence/final-source-parity.json), and [config-delta.txt](../artifacts/frozen/kernel-memory-r1/config-delta.txt). PSI/ZRAM/ZSMALLOC/SWAP are enabled, MEMCG disabled; lz4, compaction, CMA, VM counters, preemption and timer settings match the selected physical settings. Virtual DEBUG_PREEMPT remains enabled versus disabled physically; four other selected differences are absent versus explicitly disabled dependent options. CMA is enabled but the guest has no board CMA reservation. Whole-kernel, board and timing equivalence are not claimed. No virtual VETH/NET_NS/board settings were copied to hardware.

The physical BMC config remains `10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`; its Image.gz-dtb remains `e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1` and has not physically booted. No physical kernel source fix was shown necessary by these tests.

At parent priority coordination, the first owned make was terminated and returned -15. The original product lock was proven acquirable/released at 22:22:08 UTC. The existing partial build resumed under a fixture-local lock with explicit parent permission for bounded concurrency; no source/output was discarded. Resume completed with exit 0 at 22:29:27 UTC. Both receipts/logs remain preserved. No owned build or guest is left running.

**Accepted runtime configuration and boundary.** Genuine first-stage/SELinux/second-stage init, ueventd and property service are used. The compiled policy is unchanged: 872,537 bytes, SHA256 `aefaac36c669d59f37fb90c5f42f29bc0d1a60cb90338a4c0335371f5941c847`. Global enforcement is 1. Actual daemon SID is `u:r:lmkd:s0`, UID 1069; its normal capabilities and control socket are retained. The test service graph makes lmkd oneshot to preserve failures, and enables `ro.lmk.debug=true`. The instrumentation harness uses the debug policy's `su` domain and a diagnostic receiver on a correctly labeled logd datagram socket; it is not genuine logd. Consumers have actual UIDs 10000–10006 but inherit the harness's SELinux domain, not an app domain. The final linker namespace/APEX/service chain and production policy as a whole are not accepted by this fixture.

Genuine init expands and logs `ro.config.low_ram=true`, `ro.config.per_app_memcg=false`, `ro.lmk.use_new_strategy=true`, and `ro.lmk.use_minfree_levels=false` before daemon start. The source does not read `ro.lmk.use_psi`. Unset PSI tunables therefore use the actual low-RAM defaults: some-stall 200 ms and full-stall 700 ms in a 1000 ms window. The memory-cgroup-dependent old strategy is rejected. Optional process_mrelease is unavailable; lmkd logs that process reaping is unsupported and successfully uses the supported pidfd kill route. Post-boot eBPF/memevent initialization is outside this pre-framework scope; no boot-completed/BPF/readiness property was forged.

The prepared 192 MiB Dalvik growth limit is a source input only; ART is not running here. lz4 is selected before genuine fs_mgr/mkswap/swapon activation. Logical disksize is 536,870,912 bytes, with 524,284 KiB usable swap after its header. `backing_dev=none` and bd_stat zeros are recorded; there is no writeback device, backing file or persistent flash swap.

**Decisive cases.** Raw serial, commands, status, input hashes and init/property files are under `artifacts/frozen/`.

| Case | Result |
|---|---|
| r20, compressible, correct low-RAM config | Two cycles; real adj -1000 foreground, six background adj 900–905; two daemon notifications, kill count 0→1→2, matching victim wait status 9; both foreground heartbeats pass. |
| r21, incompressible, same config | Same two-cycle result. Neither main case has a kernel OOM message, swap write failure, timeout or harness SIGKILL. |
| PSI registration in r20/r21 | Two actual `/proc/pressure/memory` descriptors, fd5/fd6, registered in epoll with events 0x1a (including EPOLLPRI); fd19 later reads PSI statistics and is not a third monitor. PSI stall totals increase under pressure. |
| r4, original no-PSI kernel | Genuine daemon logs no PSI support, errno 2, initialization failure and exit. |
| r17, PSI window 100 ms | Genuine libpsi trigger write fails EINVAL (22); monitors fail and daemon exits. |
| r18, old strategy with MEMCG absent | Explicit “Old kill strategy can only be used with v1 cgroup hierarchy”; daemon exits. |
| r15, original zRAM label | Actual xattr ram_device, mode 0600 root:root, mkswap Permission denied. |
| r10 and final positives, candidate label | Actual xattr swap_block_device, same mode/owner and compiled policy, enforcing=1; genuine swapon succeeds. |
| r22, auxiliary protected compressible warmup | Registered background adj -900…-895 during bounded warmup; 153,412 KiB of background workload swapped. After promotion to 900…905, one daemon eviction and foreground recovery. No production tuning property changed. |
| r23, auxiliary protected incompressible warmup | Stalled before eligibility promotion; 17,613 recorded swap write errors. No kernel OOM kill log or daemon kill notification. Explicit QEMU SIGTERM after 184.7 s; no recovery claim. QEMU handles SIGTERM with exit 0, which is not a pass. |

The accepted main cycles use the actual LMK_PROCPRIO/LMK_GETKILLCNT/LMK_SUBSCRIBE protocol and false `for_lmkd_only`; `/proc/PID/oom_score_adj` and seven real pidfds are observed. A daemon kill notification plus its kill log and incremented counter precede native SIGKILL wait status. Remaining consumers are intentionally stopped with separately logged SIGTERM after measurement. The foreground is a 64 MiB disposable surrogate, not SystemUI.

Default-policy kills occur early: this SDK37 source caps effective free swap by easy-available memory at the default compression ratio of 1. Thus its “swap is low” log need not mean raw SwapFree is exhausted. This is source interpretation, not a tuning recommendation. Main-case observed global zRAM pool usage remained small. The separate r22 warmup produced 229,601,280 bytes of logical stored pages, 9,408,865 compressed-data bytes and 10,330,112 bytes in the zsmalloc pool. After background cleanup the pool was 4,128,768 bytes; the live foreground/base processes still held swapped pages. Those compressible synthetic data cannot be used as a GMS/app compression ratio or additional physical RAM.

**Preserved failures and corrections.** Early fixture preparation failed on a missing build.prop/fstab. boot-r2 mistakenly selected bionic link-time API stubs and stopped at init's missing __system_property_area_init; final runtime inputs use real implementations. boot-r3's diagnostic log socket context was invalid and was corrected without policy changes. Earlier prop.default files were not consumed by this init; r11/r12 are exploratory default-config runs, r13/r14 ineffective negatives, superseded by r20/r21 and r17/r18. Final fixtures use the source-confirmed `/system/build.prop` and genuine init expansion; the unavailable toybox getprop applet is not used as evidence. Auxiliary C compilation errors are retained. r21's runtime completed normally, but printing its binary-containing serial log as UTF-8 failed afterward; raw evidence and the prior-written terminal receipt are intact. A first qualification parser falsely treated the statistics fd as a third PSI monitor; the rejected result is preserved and the final parser checks actual EPOLLPRI membership. None of these failures was hidden by rerunning into the same directory.

**What remains.** Parent integration must apply/review the single label candidate in a new stage and verify the finished product's merged contexts and actual zRAM startup. The full framework + GMS + root protected working set, per-process PSS/RSS, steady-state free memory, zRAM/PSI/LMKD/OOM/ANR evidence, first-boot compilation versus warmed behavior, and sustained operation remain unmeasured. Physical launcher/touch response, app launches/switches, graphics acceleration, suspend/resume, temperature/battery and actual BMC kernel boot remain unproved. The failed protected-incompressible case reinforces that irreducible memory must be measured. No Android downgrade, Google removal, fake RAM property, flash swap or random tuning is proposed.

The export contains 510 payload files, 17,099,996 uncompressed bytes in a 6,124,968-byte archive, SHA256 `8192550a6960b7bb4a590c58b2ab2f454ed7b6fe807b2228554dc9e7bc8f6fa8`. Every payload hash was verified locally. [qualification.json](../artifacts/frozen/evidence/qualification.json) contains the check results; [export-verification.json](../evidence/export-verification.json) contains the transfer receipt.
'''
(P/'report/REPORT.md').write_text(report)
handoff='''# Parent handoff

**Native functional gate: pass with a staged zRAM labeling correction. Full Android17/Google/root usability: still unproved.** Read [REPORT.md](REPORT.md) for scope and retained failures.

1. In a new parent-owned integration stage, append [vendor-file-contexts.additions](../candidate/vendor-file-contexts.additions) to `device/asus/p00a/sepolicy/vendor/file_contexts`. Do not widen allow rules or make policy permissive. The exact `/dev/block/zram0` label must become `u:object_r:swap_block_device:s0`. Original label ram_device blocks genuine mkswap under enforcement. This worker made no active product/policy/out/kit edits.
2. Preserve the prepared low-RAM properties, 192 MiB heap growth and 512 MiB logical lz4 zRAM; no measured reason for random tuning, Google removal or an Android downgrade was established. BMC already has the selected memory features. Do not copy virtual board/network/debug options to hardware.
3. After the actual product finishes, verify real zRAM activation and lmkd properties/PSI descriptors in the full service chain. Measure SystemUI/launcher/Play services/Store/root components' PSS/RSS and the total protected working set. Complete warmed app-switch/GUI/graphics/hardware qualification before claiming usability. Protected incompressible overload r23 failed; it is not hidden by the positive native cycles.

Accepted cases: r20/r21 have four total daemon-directed evictions and four successful foreground recoveries, native oom_score_adj values, two EPOLLPRI PSI registrations, enforcement=1 and the genuine lmkd domain. r17/r18 are real config-failure negatives; r4 is the missing-PSI negative. r15→r10/final cases proves the one-line label candidate. r22 proves substantial actual compressible workload swapping. r23 is an explicitly aborted protected-incompressible failure with swap write errors and no recovery claim.

The genuine installed daemon is SHA256 `ff975915ad8d1f2882cf297c6fa312e144166d87b1251bf880eb6e890a34353d`. Source cpp is `63b6821d591e11536148ab71fd905665575c7679bfbde61b0bacb674cfa20678`. Runtime closure is pinned locally and remotely at `inputs/native-r3`; all 15 ELF dependencies were independently verified. The parent targeted native success is not full-image success.

Owned remote fixture: `/srv/android/asus-sdk37-lmkd-functional`. No owned build or guest is running. Global product lock was released at 22:22:08 UTC after owned make returned -15; partial compilation resumed under the fixture-local lock, with parent-authorized bounded concurrency, and completed exit0. Do not restart or rebuild that kernel. Image SHA256 is `c59e030cdfc3e752eeddbbf62d091ae9760c94d5fbf780a22824e004ec872080`; all run receipts are terminal. Existing firstboot and hardware fixtures were not modified.

To extend a normal workload, choose a NEW unused revision (for example r30), with no other owned guest running:

```sh
python3 /srv/android/asus-sdk37-lmkd-functional/source/prepare_pressure_r6.py r30 compressible
python3 /srv/android/asus-sdk37-lmkd-functional/source/run_memory_v3.py r30
```

Use `incompressible`, `invalid-window`, `old-strategy` or `startup` as appropriate. These commands compile only the small instrumentation helper and construct the owned 96 MiB filesystem; they do not read active AOSP/out, invoke Ninja or rebuild a kernel. They still consume previously pinned read-only firstboot tools/first-stage init. Existing revision directories intentionally reject reuse. Never infer success from QEMU exit0 alone; r23 demonstrates why. Inspect actual properties, domain/enforcement, PSI fd/epoll records, notifications, wait status, kernel errors and recovery markers. Do not rerun the deliberately protected incompressible overload as a usability benchmark.

Local frozen archive and manifest are under `artifacts/`; every one of the 510 payload hashes has been verified. `scripts/qualify_r2.py` is the final evidence parser. `evidence/elf-runtime-closure.json` is the independent local closure check. The staged candidate and this handoff are complete; hardware/full-framework acceptance remains with the parent.
'''
(P/'report/HANDOFF.md').write_text(handoff)
(P/'README.md').write_text('''# SDK37 lmkd functional qualification

Question: does genuine SDK37 lmkd register PSI and handle controlled memory pressure with approximately 2 GiB RAM, MEMCG disabled and 512 MiB lz4 zRAM?

Status: COMPLETE within the native fixture scope, conditional on the staged zRAM file-context correction. Four verified default-policy eviction/recovery cycles pass. A separate protected-incompressible overload failed and is retained. Full Android17 + Google + root footprint and physical tablet usability remain UNPROVED.

Important outputs:

- [Report](report/REPORT.md) and [parent handoff](report/HANDOFF.md).
- [One-line staged label correction](candidate/vendor-file-contexts.additions); not applied to active product sources.
- [Final qualification](artifacts/frozen/evidence/qualification.json), [verified export](evidence/export-verification.json), [actual ELF closure](evidence/elf-runtime-closure.json).
- `artifacts/frozen/`: source pins, real ELF inputs, kernel configuration/delta, commands, complete serial logs, terminal receipts, retained failures.

Continuation: follow HANDOFF using a new fixture revision. Reuse the already completed owned virtual kernel; do not restart builds or reuse run directories. No owned job remains running. Parent owns product integration and all future hardware/framework/GMS qualification. Preserve Android17, Google and root objectives.
''')
c=P/'candidate/README.md';c.write_text(c.read_text().replace('Pressure qualification remains in progress; inspect the final REPORT/HANDOFF before using this candidate.','Pressure qualification is complete within its bounded scope; inspect report/REPORT.md and report/HANDOFF.md before integrating. The protected-incompressible auxiliary overload failed; full product usability remains unproved.'))
print('wrote REPORT, HANDOFF, README and candidate status')
