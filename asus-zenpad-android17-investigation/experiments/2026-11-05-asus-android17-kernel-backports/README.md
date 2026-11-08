# ASUS P00A Android 17 kernel feature backports

Question: Can the Linux 4.9.337 ASUS hardware candidate gain the actual BPF, filesystem and memory interfaces required by Android 17, without reporting fake capabilities?

Status: EROFS compile/link passes on a clean Linux source tree. Android 17 platform source is pinned; the generic init/adbd check stops at Lineage kernel-header configuration. Device work is stopped at a fastboot transport/physical-access gate. Read STATUS.md. The separate power/board spike holds the hardware integration and its tests. No device changes or flashing are part of this source experiment.

Inputs: ../2026-11-05-asus-p00a-power-port; pinned Android 17 / LineageOS 24 manifest; the Galaxy Tab S5e 4.9 backport reference at a668db21f3cfddc5b73f081c6bb532b1b3351b36. Samsung drivers and product definitions are not ASUS support.

Build machine: existing experiment VM in PROJECT_REDACTED, inventory and teardown under ../2026-11-05-asus-p00a-power-port/infrastructure/README.md. All added support files, logs and patches for this experiment belong here. Keep the hardware candidate unchanged while testing modern feature backports in a separate source tree.

Continuation: Inspect evidence and scripts for source pins and work state. Freeze the resolved platform manifest before building. Compile and behavior-test real feature implementations; do not substitute a kernel version string for implementation. A fully built platform or kernel still requires an exact-unit backup and restore path before custom boot.
