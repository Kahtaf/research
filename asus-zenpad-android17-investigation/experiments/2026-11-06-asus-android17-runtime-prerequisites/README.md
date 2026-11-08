# Android 17 runtime prerequisites on Linux 4.9

Question: Can genuine SDK37/Google APEX payloads mount through ext4-backed direct-I/O loops, and can genuine SDK37 libbinder transact across processes using the physical candidate's driver code?

**Status: PASS for these bounded virtual workloads.** Final run r5: 68 matching material-file reads over bare EROFS and AVB-derived dm-verity, real corruption rejection, 200 Binder replies, 20 one-way calls and one client-death callback. Four client threads and multiple server pool threads ran. No physical-device or full Android/APEX activation claim.

Start with [report.md](report.md). Authoritative runtime result: [evidence/run-r5/result.json](evidence/run-r5/result.json). Local integrity/outcome checks: [evidence/validation.json](evidence/validation.json). Exact source/configuration equivalence, ELF and payload hashes, build commands, failed runs and successful logs are under evidence/. Source and tests are in their named directories. artifacts/ contains the compact capture, standalone probe and virtual-only config.

Owned remote fixture: `/srv/android/asus-android17-runtime-prereqs`. Kernel builds used at most two jobs; QEMU used two CPUs and 1536 MiB, with no network or physical USB. All kernel inputs came from committed Git archives. Active AOSP and hardware kernel builds were untouched.

Continuation: validate the local capture with `python3 -B tests/validate_evidence.py`; use `source/run_fixture.py r6` remotely only for a new justified run, preserving every existing revision. The report documents setup, known fixture corrections and exact limits. Parent owns integrated first boot, device/restore gates, cloud lifecycle and any physical changes. Binder freezer and spam-detection features remain unsupported; ordinary tested IPC works without faked acknowledgements.
