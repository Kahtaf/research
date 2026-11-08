# Android 17 loopback policy on Linux 4.9

Question: Can pinned SDK37 cross-profile loopback policy run faithfully on the frozen ASUS Linux 4.9 baseline within a bounded patch?

Status: **Research/test unit complete; kernel compatibility BLOCKED.** Baseline cross-profile isolation remains FAILED for IPv4 and IPv6. No kernel implementation patch is staged or runtime qualification granted.

Important outputs:

- [report.md](report.md): exact source/ELF dependency graph, existing-hook assessment, donor bytes and implementable next unit.
- [runtime-test-plan.md](runtime-test-plan.md): real socket, FD/UID lifecycle, policy controls, namespace and concurrency gates; not executed.
- [evidence/handoff-manifest.json](evidence/handoff-manifest.json): selected input/output hashes and inherited failures.
- [evidence/host-tests.json](evidence/host-tests.json): passing unchanged production-body tests and AArch64 layout object, with explicit helper doubles and limitations.
- `inputs/`: selective frozen and primary upstream source. Upstream `.patch` files are reference donors, not staged 4.9 patches.

Reproduce local checks: `python3 tests/run.py`, `python3 source/audit_elf.py`, then `python3 source/finalize.py`. Run from any directory. Do not rerun collectors as part of tests; all required selected inputs are present.

Continuation: Review V+L+R+N (typed socket references, lookup/release and namespaces) as the next source implementation unit described in the report. Preserve the previous network-runtime core handoff. Do not enable the Android wrapper without the connected storage/creator/metadata/loader prerequisites. No devices, active builds, full kernel, mutable R9-exec/final3changedBPF work or production integration was touched. No remote writes were made; the only authorized new remote prefix remains `/srv/android/asus-loopback-compat-20261106`.
