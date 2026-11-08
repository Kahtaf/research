# ASUS Android 17 networking on Linux 4.9

Question: Can actual SDK37 Connectivity BPF objects, loaders and map consumers provide honest core networking on the ASUS P00A_2 Linux4.9 baseline?

Status: Targeted repairs and runtime tests completed; full Android17 security/readiness remains blocked by a reproduced cross-profile loopback-policy failure. No device operations or active product-source changes were performed.

Important outputs:

- `report.md`: results, concrete blocker, test boundaries and ordered integration.
- `artifacts/handoff-r1/manifest.json`: immutable qualified core patches, source/config hashes and evidence.
- `source/`: reproducible isolated fixture scripts; `evidence/` and `artifacts/` retain attempts and outputs.

Continuation: Read `report.md` and the manifests. Parent/main owner alone integrates reviewed changes. Coordinate separately qualified `CONFIG_BLK_CGROUP=y`, preserve physical `FILE_LOCKING=y`, and never copy the virtual configuration to hardware. Resolve cross-profile enforcement and run genuine Android service integration before calling networking ready. Remote writes are restricted to `/srv/android/asus-network-runtime`.
