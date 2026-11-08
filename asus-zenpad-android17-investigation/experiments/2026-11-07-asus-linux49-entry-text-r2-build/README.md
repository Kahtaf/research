# Experiment 2: structurally guarded Linux4.9 entry checkpoint

Question: does one fresh pre-MMU retained-console tag establish physical Linux4.9 execution?

Status: one complete build exit0; linked entry/ABI/preservation checks pass; package and actual parent PLAN pass. One recovery-only installation was full-readback verified and its physical trial is under ../2026-11-07-asus-linux49-entry-text-r2-trial. No physical entry result yet. VM stopped.

Run UUID: 95c88f32-9471-4354-9a36-e44e98901a0f.
Kernel SHA256: cb8de5a1ab14e05d6bd96b0fe1bae2be774ba4ae8c848711208d695bd32711e1.
Candidate SHA256: 34452d98081a5bd69e9d31d78035085419d2fc65a60a0177bde875984f90e125.
Full p10 SHA256: f547c8fd3819b01efef6a232197aa5670dcbe332a83edcbc20529b2a07a08e42.
Complete config remains708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1.

Source: independent ordinary copy of the early-watchdog baseline plus the four exact R2 files from ../2026-11-07-asus-entry-checkpoint-dt-guard-fix. The whole-DT guard from R1 is replaced by bounded structural admission. No driver/config/hardwareDT/ramdisk changes. No R1 artifacts reused as new build output. Build started 2026-11-07T23:25:54.168662+00:00 and finished 2026-11-07T23:28:41.501508+00:00.

Actual linked entry contains 3492 bytes; primary entry, original argument-preservation and EL setup fallthrough, required register/SP/LR preservation and payload commit were checked. Existing expected-DT array is absent. Packaged reference DT is provenance only. The physical writer still may refuse; absent text remains UNKNOWN.

Evidence: source-copy/build-launch/build-status/build-receipt/linked-entry/packaging-receipt/fresh-marker-absence and actual installation receipt. Continue only with the recorded single trial and complete retained-log collection; do not repeat blindly or advance to experiment3 without a positive fresh entry tag. BOOT/SYSTEM/DATA remain intact.
