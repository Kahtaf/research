# One sparse-observer liveness control

Question: does the unchanged RAM PID1 clock/alarm/IRQ observation progress below the prior retained-observer load?

Status: **one candidate built, packaged, verified and delivered; STOP**. Same prepared UUID `e6799dac-43cb-4222-8ab6-5119397460b6`. One `-j8 Image.gz-dtb` build and exactly one isolated default PLAN passed. No device/ADB/root/private factory/raw target-log access, installation, reboot or physical trial. Parent owns one physical trial and eventual Power fallback.

- [Candidate](artifacts/candidate.img): 7,989,248 bytes; SHA256 `839ad49e644574b5dee970d39c01ff9ae728eb189fb357a3b644b1a5393b947f`.
- [Full p10](artifacts/candidate.p10.raw): 16,740,352 bytes; SHA256 `8ed918339c0adcfdad461390b0316073b515b43e839ec8094975546e314f8b22`.
- Guarded installer admission appends parent-supplied current physical B `a30aabe163d8a934752fac00944b0cb3515d19c3614805fdfe2bbe60e4ea5b4f`; not freshly observed by this worker.
- [Handoff](evidence/handoff.json), [all artifact hashes](artifacts/SHA256SUMS), [genuine System.map.gz](artifacts/System.map.gz), [uncompressed map pin](evidence/System.map-uncompressed.json). Large out/vmlinux remain on the VM.

Exact compile-mode marker (not readiness or a passed result):

```
ASUS49-MODE run=e6799dac-43cb-4222-8ab6-5119397460b6 profile=sparse-v1 hot=disabled ordinary_printk=filtered delay=original-virtual
```

[Mode contract and exact whitelist](evidence/mode-contract.json) retain only the seven existing entry-stage markers plus true getpid/release, clock.path, alarm1 setup, initial clock, real final/loop result, actual alarm, before/after timer counts/snapshot completion, and existing finish markers. Other regular/MMC retention is rejected before trace_lock/cache cleaning. The ~29KB old areas are not reserved/initialized; all six ready pointers remain zero BSS and the actual recorder has zero ready-publication STLR instructions (baseline six). Old six protocols are deliberately absent, never claimed passing.

[Actual source/ELF proof](evidence/sparse-proof.md), [109-line kernel diff](source/changes.patch), [pre/post pins](evidence/prepost.json), [preservation](evidence/preservation.json), [packaging](evidence/packaging-receipt.json), [isolated PLAN receipt](evidence/plan-isolation-receipt.json). Source/caller checks used the actual VM virtual baseline `/srv/android/asus-arm64-delay-loop-observation-20261108-f3da846c`, independently copied kernel/out with preserved base inodes/nested repositories. Original driver/core/delay operations, CNTVCT/OOL route, RDMA diagnostic skip, helper/whole ramdisk, config, DTs, args, initrd and load addresses remain. Accepted writes retain original PoC/header cleans and DSB SY. Image extent is 64KiB smaller; actual load-map nonoverlap is verified. execute/Transport/Guard/adapters remain byte-identical; adb0755.

The unchanged local filter/parser controls were not rerun. One ELF-checker correction recognized the proven __memcpy/memcpy alias; no source change or rebuild. Original authentication failure and blocked handoff/README are preserved under evidence. The [VM is verified TERMINATED](evidence/after.stdout); only this spike's master was closed. remote.py SHA remains `c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab`.

Continuation: parent uses [exact commands](evidence/exact-commands.json) and [guarded installer](source/install.py) for one trial. Decode the parent-private complete console offline:

```
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-08-asus-sparse-observer-liveness/scripts/decode_sparse.py /absolute/parent-private/complete-console.txt > /absolute/parent-private/sparse-result.json
```

Early 2M iteration-cap completion is progress, not failed timer/full pass. Full bounded liveness requires actual counter-target/delta>=1.5e9, alarm flag or real alarm marker, and complete after-IRQ growth. Missing final remains unresolved publication/environment; positive supports load/timing sensitivity, not exclusive cause or Android17 readiness. UNKNOWN STOP; consult Large before another guess. No automatic retry, next unit, watchdog/CIRQ build or full-OS GO.
