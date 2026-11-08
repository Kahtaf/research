# Minimal stock-kernel RAM USB probe

Question: does the unchanged stock recovery kernel reach a minimal static PID1 and expose a read-only RAM report over the existing legacy mass-storage gadget?

Status: offline candidate and verification complete; no physical deployment authorization. Read [HANDOFF.md](HANDOFF.md) for exact hashes, risk limits and the parent physical-test contract.

Outputs: source/init.c, pinned source helpers, artifacts/candidate.img, evidence/manifest.json and HANDOFF.md.

Continue only from exact hashes in the final manifest. Parent owns independent deployment binding, readback, supervised recovery entry, host read-only report acceptance and physical Power fallback. No writer or approval flags are provided. Never infer normal return or Android readiness from host tests.

Owned VM directory: /srv/android/asus-minimal-ram-usb-probe-20261106; one CPU, 1 GiB address space, 256 MiB maximum owned output, finite command timeouts. Existing selected toolchain only. No target contact, private data, active R9 tree, full source/image copying or cloud operations.
