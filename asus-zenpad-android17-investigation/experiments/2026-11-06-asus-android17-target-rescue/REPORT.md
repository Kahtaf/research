# Stock-kernel target rescue delivery

Status: **offline implementation and local handoff complete; target unavailable and write-disabled pending parent qualifications.** No new OS image is approved. Full OS flashing is not ready. This recovery has a real, tested ARM64 daemon and fixed proxy, not the earlier exit-78 placeholder. It has not been booted on the physical tablet by this continuation.

The existing `/srv/android/asus-target-rescue` fixture was preserved. Process status was inspected before continuation; no rescue job remained active. Completed workloads were not restarted. All earlier failed and successful test logs were retained, and the pre-delivery source/tests were archived in `evidence/pre-delivery-source.tar.gz`. The new local handoff is this directory.

## Delivered recovery

Use `artifacts/candidate-delivery/`, not the preserved older `candidate-release/`.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `UNTESTED-target-rescue.img` | 9,541,632 | `93d647ea58784aefe4104cb0cbddbac04fe6169b30923ad63c5684e0dc920419` |
| `UNTESTED-target-rescue.p10.raw` | 16,740,352 | `dd71729bac68ac161b6ca21bcaad757a51496f24beee546a402eee70d3997de0` |
| `os-rescue` | 775,656 | `30ae9252e575d7c9c837783d60e51016a16bcadb46bd38215d8e49e5bb5d1c53` |
| `rescue-proxy` | 635,624 | `f915eca1b2ae5250afef76d3154a853b933278c283f82cfb4eb0cee7d2736d0f` |
| `rescue-sepolicy` | 389,688 | `189c477ac73ecb161a6527f7f98a6fec76a913b0d5cf8d11591d440dc79af842` |
| `file_contexts.bin` | 223,347 | `505b605f9f9986e0a3432a9980431cd0cf6ad5bbfb6e3cd337f79dbc485948d6` |
| `rescue.manifest` | 112 | `3b5c1c0a65fb1e43a67d18b31c498315b30e3a2d4494396ef5357153bf7bd7f5` |

The kernel component is byte-exact to both saved original recoveries. Its MTK-wrapped SHA-256 is `b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`; the unwrapped 7,471,829-byte payload is `a3e696ebbb222a331c8ba19da306eac709a771089b086baf0d208cb1221c4a4b`. These measured component hashes are the package pins. The unused legacy `KERNEL_SHA` constant in `bootformat.py` is not consulted by assembly and is not a pin for this stock kernel.

Stock init (`e9594c0d1cbe7d05d34acd63e90b424672360ceb09112fa16b5b23390c21b7e5`) and stock adbd (`78a7adbda0a28da4055da1ea68a2ead8ee01764a365778930ef03e6649dcb450`) are preserved. The ramdisk replaces the general shell with the fixed proxy and includes the supplied public ADB key only. It includes no private key, stock recovery executable, guest test helper, ordinary-file backend, fstab, normal-boot repair, power-control service, or unconditional reboot deadline. `os-rescue` is oneshot: it does not restart automatically after failure. Connection timeouts freeze/refuse mutations; they do not reboot.

`session-contract.UNAPPROVED.json` remains `PARENT_REVIEW_REQUIRED`, `armed=false`, `userdata_enabled=false`, `physical_validation=false`. The manifest has **zero image records**, so the daemon serves status but refuses reconciliation, write activation, and image readback. This is deliberate non-authorization, not a dummy executable.

## Accepted stock inverse sources

The preferred sources are now independent of the cloud:

`/OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback/`

- `system.img`: 3,753,902,080 bytes, SHA-256 `4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49`.
- `boot.img`: 16,740,352 bytes, SHA-256 `7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316`.
- `recovery.img`: 16,740,352 bytes, SHA-256 `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`.

Parent materialized every OEM byte, fsynced, and independently reread SYSTEM against all 112 actual-capture chunks and its full hash; BOOT/recovery match both original copies. Parent reports seven passing offline behavioral methods. This continuation inspected `READY.json`, verified its actual-manifest digest, matched its hashes to the existing inverse inventory, and checked actual file sizes. It did **not** repeat that full-size local readback or make another SYSTEM copy. The receipt and manifest are copied under `inputs/parent/`; `evidence/local-rollback-receipt-check.json` records the check and its limits.

`artifacts/local-stock-inverse.PLAN_ONLY.json` contains the preferred exact local paths. `artifacts/parent-review.PENDING.json` is a syntactically usable original SYSTEM/BOOT review input with `independent_rescue_review=false`. It contains no install pair or userdata image. The manifest builder demonstrably rejects it before reading image bytes (`evidence/unapproved-manifest-refusal.*`). Do not change that approval field merely to make a build pass.

The original actual cloud backup remains at `/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img`. `artifacts/stock-inverse.PLAN_ONLY.json` preserves that fallback, freshly checked 1 MiB chunk digests, both saved BOOT/recovery checks, and the parent evidence pins. The accepted actual-capture manifest SHA-256 is `7d6052ca349d56e6cc83eb276988596c99d1c455926a0018aeaf2d3472947673`; both backup and separate verification exited zero. This read-only inverse preparation is distinct from the previously completed synthetic full-size writer workload.

## Identity and protocol implementation

The delivered `ASUSR002` format binds SHA-256 of the lowercase 32-hex-character CID without a newline. It uses parent pin `c03db6320ba5e4e1916c2dce84f87ba26220102701675f1ed638c513b597b7d8`. The daemon validates the sysfs encoding, hashes those 32 bytes, and compares the digest. No actual raw CID was supplied, read from hardware, or stored here. Legacy raw-CID `ASUSR001` manifests are rejected. The RSC1 packet framing remains version 1.

The implementation checks were made against the actual delivered source:

- `common.h`, `proxy.c`: exact framed reads/writes; `RSC1` header, opcode and length; maximum 1 MiB payload. The proxy accepts only `sh -c rescue-v1`, requires real/effective UID2000, `u:r:shell:s0`, Enforcing, and non-TTY descriptors. It checks the server's root UID and `u:r:os_rescue:s0` peer domain. The daemon checks kernel SO_PEERCRED UID2000 and SO_PEERSEC shell domain. Missing peer security fails closed.
- `rescue.c::serve`: requires root, exact daemon domain, Enforcing, a valid bounded manifest, and the init-inherited Unix stream socket at the exact path. An abstract Unix bind is the exclusive lifetime writer lock. There is one accepted session at a time. A later status response therefore proves this process has returned to its idle session loop.
- `open_part`, `validate_fd`: no caller-supplied path. Production opens only fixed nodes, with `O_NOFOLLOW`, `O_CLOEXEC`, and `O_DIRECT`. It checks the actual opened descriptor, inode/path agreement, block mode, root:root/0600, SELinux label, major/minor, `BLKGETSIZE64`, sysfs geometry, by-name alias resolution, holders, and absence of any major179 mounted filesystem. Ordinary files are admitted only under the separate test compile flag.
- `identity`, `recovery_ok`: the exact CID hash, Enforcing, and saved primary/backup GPT hashes are checked before reconciliation, activation, and each write/skip. Full p10 is hashed against the explicit session pin. A reconnect cannot silently replace the pinned recovery after an uncertain write in the same daemon lifetime.
- `load_manifest`, `session`: exact image sizes, role order, count and chunk bounds are validated. Writable roles map only to p25 SYSTEM and p9 BOOT; p26 is possible only in a separately built five-image configuration. p10 and the whole disk are never writable; p20 is not an addressable image. BOOT requires the corresponding whole SYSTEM hash. Optional install BOOT additionally requires whole p26 verification, with SYSTEM before data.
- `session` writes sequential chunks only. Supplied chunk SHA-256 must match the compiled-in manifest bytes. Each chunk is re-read even after reconciliation; SKIP is refused if the current bytes differ. Writes require fsync and readback. Short I/O, corrupt input, failed flush/publication, or lost acknowledgement leaves the operation uncertain. Final success requires complete whole-image readback and an additional commit receipt.
- Reconnect is explicit, with a fresh session token and a scan of actual chunks. No offset-only resume, automatic transport retry, or implicit restart exists. An explicitly pinned original inverse is available after an uncertain install; it does not bypass SYSTEM-before-BOOT. The journal is on tmpfs, not durable across boot; after daemon death/reboot the parent must re-establish identity and reconcile actual bytes. No persistent progress claim is made.

## Policy and runtime evidence

The stock binary policy is extended using the vendored, hash-pinned Android libsepol. Rescue types inherit no broad stock domain/device attributes. The audit checks unchanged constraints/permissive map, exact transitions, and ioctl extended permissions. Only `BLKGETSIZE64` (`0x1272`) is granted for the rescue block types. Default policy denies userdata access, p10/disk writes, generic/protected device writes, mount, setenforce, networking, sys_boot, sys_admin and dac_override for the daemon.

Compiled `file_contexts.bin` is produced with the stock-compatible Android libselinux/PCRE sources, not merely a text file with a binary suffix. Original 894 rows are retained except exact rescue overrides; extraction and reconstruction are checked, and real compiled-context lookups cover executable, socket, journal, direct-node and by-name labels.

Final validation:

- **24 adapter tests pass**, `evidence/adapter-tests-delivery.txt`. Covers packet fragmentation/oversize, malformed manifests, wrong identity/geometry/mounts/holders/aliases, no-follow/length, corrupted chunks, false skip, partial payload, readback, syscall failures, busy writer, disconnect/token binding, lost final receipt, changed p10, explicit inverse, BOOT ordering, optional p26 ordering/tail, and zero-record refusal. These use real Linux files/sockets with the isolated test backend; they are not physical eMMC evidence.
- **66 constraint checks, 15 compiled-context checks, structural audit pass**, `evidence/policy-audit-delivery.json`. Default userdata access is denied.
- **ARM64 QEMU block/policy test passes**, `evidence/qemu-blocks-delivery/`. Real Enforcing policy, stock ueventd, final daemon/proxy, UID/domain transition, exclusive lock, root-peer denial and disconnect survival. Fresh production-code probe exercises aligned direct block write/fsync/readback/restore, denied ioctl, and read-only recovery type. Virtual disks do not reproduce the tablet's exact major179 geometry; positive hardware descriptor/alias checks remain unqualified.
- **Exact saved stock init starts the final daemon and serves the fixed proxy**, `evidence/qemu-stock-init-delivery/`. Observer exits42 under Enforcing using the final daemon hash. The virtual run ends by its 25-second host timeout (recorded returncode124), not by a recovery reboot timer. Stock adbd exits255 in QEMU without its physical USB transport; the observer uses a real adbd-domain socketpair/UID drop. This does not prove physical ADB authentication, USB enumeration or eMMC access.
- **Byte-identical daemon rebuild and recovery/policy/context reassembly pass**, `evidence/reproduction-delivery.json`. Unchanged proxy and host-tool reproduction evidence is retained separately. Build commands and compiler output are in `artifacts/tools-delivery/commands.json`.
- **Earlier full-size SYSTEM workload retained, not rerun**: `evidence/fullsize-r4.json` and `.jsonl`, 3,753,902,080 bytes, 3,580 chunks, one changed chunk written and 3,579 verified skips, complete whole readback. It is a synthetic zero-image Linux-file/socket fixture (`61f807...d5f4a`), not the accepted OEM/actual SYSTEM (`4597a7...5cd49`). It predates the CID-hash header change; targeted final tests cover that change.

QEMU used two CPUs/1536 MiB; builds used at most `-j2`. No other fixture, active AOSP tree, frozen new-kernel probe, cloud lifecycle, device, ADB, root transport or USB operation was performed.

## Preserved failures and corrections

- Adapter r1 recorded EAGAIN from fixture nonblocking descriptors; the current fixture explicitly restores blocking I/O. r2/r3 retain their EOF/prerequisite failures; final source and subsequent passing suites are preserved. Per-revision source for every early attempt was not available, so no invented patch chronology is claimed.
- Policy/guest r1–r3 retain label and daemon-start failures. Current code labels guest nodes before transition, uses explicit fscreate labels and narrow self/proc/socket permissions, and uses an abstract lifetime lock rather than depending on kernel file-locking support. Policy deltas are retained.
- Stock-init r1–r5 retain failed startup/observer attempts. The isolated compatibility kernel, matching compiled contexts, corrected service name/trigger and observable exit marker are retained in source and logs. Successful r6/final were preserved; the new final-daemon run is separately named `qemu-stock-init-delivery`.
- Virtual block r1–r3 remain failures in their own result files. The last attempt observed vda but checked vdb before it existed. This continuation waits for both, rebuilds the probe from actual delivered source, and records a new passing run; it does not relabel old failures as passes.
- Full-size r1/r2 retain BrokenPipe failures. Current client preflights large input before opening the timed transport, and the fixture computes its expensive hashes before connecting. r3/r4 passed and were not repeated.
- This continuation's first assembly attempt ran before inverse preparation finished and failed with missing `stock-inverse.PLAN_ONLY.json`. The job was allowed to finish; assembly-r2 succeeded. Both logs/exit files remain. No source corruption or workload restart was involved.

## Internal data and calibration

Parent accepted pristine 11,331,268,096-byte internal data, SHA-256 `1602ea3644246871468b6987bc90e9a6e0c430f6b46efb4e79cc3555b688e0c1`, with two real4.9 boots, 136 APEX hashes and 18 negatives. The preserved earlier test-only arming receipt matched its 10,807 reference chunks. This continuation did not access or mutate pristine data and does not authorize p26. The delivered manifest contains no userdata role, and the delivered policy denies it.

The private 66/514-byte calibration files were not accessed or uploaded. Parent alone restores future product paths `/data/vendor/p00a/nvram/APCFG/APRDEB/BT_Addr` and `/data/vendor/p00a/nvram/APCFG/APRDEB/WIFI`. Preserve p20 unchanged. Stock inverse inputs do not imply authorization to format userdata, restore calibration, run the OEM updater, or perform metadata-wide wipes.

## Continuation

Read `BUILD.md`, `SOURCE_PINS.json`, `ARTIFACTS.json` and the unapproved contract. Run `python3 -B scripts/verify_local.py` for an offline handoff integrity check. Source, compact evidence, exact stock BOOT/recovery inputs, real recovery binaries and compiled contexts are local. The 3.75 GB SYSTEM remains in the parent's local rollback bundle and the retained cloud backup; no extra full-size copy was made here.

Parent technical qualification must precede any target use or arming: physical stock-kernel boot/Enforcing/UID-domain/authenticated transport, exact device descriptor/alias/geometry behavior, recovery pin and independent rollback availability remain unproven by this virtual handoff. The non-authorizing review template must stay pending until those qualifications and explicit parent approval. A changed manifest creates a different recovery image/p10 pin and requires corresponding review. Userdata and any new OS pair require separate authorization. The frozen new-kernel probe remains independent and untouched.
