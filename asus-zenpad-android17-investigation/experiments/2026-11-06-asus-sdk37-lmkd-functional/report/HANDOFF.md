# Parent handoff

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
