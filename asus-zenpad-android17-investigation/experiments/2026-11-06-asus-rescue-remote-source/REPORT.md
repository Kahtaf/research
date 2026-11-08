# Rescue remote source adapter — implementation handoff

Status: **host implementation and offline QA complete; PLAN_ONLY by default; no target use or arming.** The adapter supplies pinned raw VM bytes to the existing RSC1 rescue transaction without a full Mac image, network mount, FUSE, cloud resource, or new target protocol. It does not establish Android 17 readiness or physical recovery qualification.

All new files are in this spike. No remote directory, uploaded worker file, or persistent remote job was created. The worker is passed to the existing strict SSH connection as fixed Python code and exits with its session. Original rescue source, daemon, proxy, policy, release artifacts, independent review files, frozen R2 image and quarantined transport were untouched. No ADB, device, USB, root/flashing, calibration, private-key-content, cloud lifecycle or goal operation was performed.

## Delivered implementation

- `source/worker.py`: bounded, read-only held-FD source worker with two embedded fixed profiles. It accepts numeric chunk requests, never a caller path or shell command. Fixed SSH host/key alias/known-host options are in `source/sources.py`; SSH configuration, agent forwarding, multiplex reuse and forwarding are disabled. The key is passed to SSH by path only.
- `source/sources.py`: host-side local and remote source adapters. Remote replies must match the requested index, byte offset, exact length, approved chunk digest and independently computed data digest. An SSH EOF, short frame, unexpected opcode or changed source poisons the session. There is no reconnect/retry loop.
- `source/source_client.py`: own copy of the original write function with a source callback. `parse`, `status`, `reconcile`, `send`, and `receive` come from byte-exact, hash-checked original modules under `source/original/`. `evidence/client-source-callback.patch` shows the limited write-function changes. The original client pin remains `0072398a0aa2da83bdf176d672e7ec767b6aaf034892fb603054a22549c5bf69`.
- `source/parent_remote.py`: own parent adapter preserving explicit hash-pinned ADB, current `-t` transport selection, `shell_v2`, non-TTY `shell -T rescue-v1`, parent-approved armed contract, manifest hash and p10 pin. Source preflight precedes even the features query, and therefore the target shell. A source check runs again before the first target status request. Only the parent may execute it.
- `source/source_manifest.py` and `source/build_manifest.py`: original manifest build schema with a digest callback. Original approval fields, ordered 2/4/5 roles, GPT pins, stock BOOT pin and binary encoding are preserved. A review may use `source://stock-system` or, once the complete ordered install pair is separately qualified and bound, `source://userdata-pristine` as the row's existing `path` field. No extra approval schema or skipped role is introduced.
- `source/source_cli.py`: source-only sample/preflight CLI, PLAN_ONLY unless `--read-only-execute`. `SOURCE-SAMPLES1` and `SOURCE-REFERENCE1` never claim full preflight. A fresh complete preflight emits `SOURCE1` plus a compact binary chunk export. A saved receipt cannot be supplied as a prepared source to skip a future preflight.
- `source/journal.py`: journal cap 2 MiB; stderr retains at most 64 KiB while draining excess. Per-session image staging is zero. Readback requests retain the existing at-most-one-MiB output behavior.

The RSC1 sequence still performs status/idle proof, actual-target reconciliation, token activation, sequential one-MiB WRITE or verified SKIP, each acknowledgement, whole-target readback SHA, and explicit commit/receipt. No target daemon/server/policy change was needed. Its Enforcing, secure-ADB/domain, identity, exclusive-writer and role prerequisites remain authoritative. The host source adapter adds no route around them. Every source chunk, including zeros and SKIP candidates, is independently checked on the host before its target frame. SKIP sends no data only where actual-target reconciliation reports a match; the original target rechecks the chunk.

A lost target acknowledgement stops immediately. The adapter does not resend or infer progress from an offset. A later parent-selected invocation must fully preflight its fresh source, obtain a new idle/status response, and reconcile actual chunks. Original inverse recovery continues to use the original `inverse_from` selection and original hashes. No reboot action or reboot deadline is added. Existing transport/process cleanup waits do not reboot or resume a writer.

## Fixed sources and compact pins

| Profile | Role | Raw bytes | SHA-256 | Source metadata |
| --- | --- | ---: | --- | --- |
| `userdata-pristine` | 4 / p26 | 11,331,268,096 | `1602ea3644246871468b6987bc90e9a6e0c430f6b46efb4e79cc3555b688e0c1` | regular, 0400, UID1001:GID1002, one link |
| `stock-system` | 0 / p25 | 3,753,902,080 | `4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49` | regular, 0600, UID1001:GID1002, one link |

Exact VM paths:

- `/srv/android/asus-internal-data-validation/artifacts/A17DATA-pristine.raw`
- `/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img`

The local original SYSTEM/BOOT fallback uses the existing `2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback/` files at fixed absolute paths, mode0400 UID501:GID20, one link. No local SYSTEM copy or new whole-SYSTEM hash run was made. The 16,740,352-byte local stock BOOT was streamed once to derive its compact chunk table and confirm `7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316`; it was not copied. The local inverse retains no VM dependency.

`profiles/*.chunks` contains contiguous 32-byte SHA-256 values in one-MiB chunk order. Userdata has 10,807 hashes / 345,824 bytes; stock SYSTEM has 3,580 hashes / 114,560 bytes. Their table hashes are pinned in `profiles/fixed.json` and embedded worker profiles. `profiles/*.REFERENCE.json` records provenance and explicitly denies current preflight/target authorization. `evidence/reference-provenance.json` pins the prior parent-qualified JSON sources; no large source was rehashed for development.

The real userdata last transfer chunk is **355,840 bytes**, at offset **11,330,912,256**. The final **3,584 bytes** are a subset of this chunk, not its entire length. The production reader returned the entire last chunk as zeros with the approved digest. Its WRITE path sends all 355,840 bytes unless the actual target qualifies for SKIP. Sparse filesystem holes are read as real zeros; Android sparse encoded image files are rejected.

Unknown install SYSTEM/BOOT images are **UNBOUND and refused**, both locally and remotely. No fabricated new-OS hash, approval, or ready manifest is included. Thus the present builder cannot emit a five-role userdata manifest: the install pair must first acquire separately reviewed fixed source bindings. This is an intentional qualification boundary, not authorization to substitute originals for install roles.

## Held descriptor and source checks

A source is opened once with O_RDONLY/O_NOFOLLOW/O_NONBLOCK; O_NONBLOCK prevents a substituted FIFO from hanging before type rejection. The worker requires canonical absolute paths with no symlink/ancestor alias and exact regular-file type, size, UID, GID, mode and link count. It binds device/inode, size, mode, owner, links, mtime and ctime. Before and after each read, the held FD and current path must still match that signature. Replacements, truncation and mutations fail closed. The host also validates the returned stat against its fixed profile.

Full preflight scans the actual held descriptor in bounded chunks, checks every chunk and the full approved SHA, and checks stat again. The host compares the returned whole digest and entire compact table against the selected manifest before opening the target shell. That same source session/FD remains open for transmission. A prepared source is bound to the manifest, role, reviewed hash, stop count and source-object identity; it cannot be consumed twice. Source checks run before target work, after activation and before final readback, as well as around every source read.

Stat checks cannot lock out a privileged concurrent VM writer. Per-chunk hashes still ensure that no changed bytes enter a target frame; a mutation after a checked chunk has been copied may only be detected at the next source boundary. The design trusts the authenticated existing builder OS and Python/SSH environment, and does not claim protection against a malicious builder root. No source lock, chmod, copy, or pristine-image modification was performed.

## Validation and preserved evidence

`evidence/unit-delivery.txt`: **28 tests pass** (earlier passing final log retained). All target transactions use in-process socketpairs and memory-backed RSC1 mocks; no target process, daemon, ADB binary, device node, or actual target Popen was used. Remote reader unit tests run the production worker function over socket streams with small temporary ordinary files and mocked SSH process creation.

Coverage includes:

- symlink and ancestor alias, wrong file type including FIFO, size/mode/UID/GID/link guards; full/chunk hash mismatch; encoded sparse rejection;
- mutation before/during/after preflight, replacement of the pathname while holding the old FD, truncation, short pread and subsequent refusal;
- fragmented/truncated/oversized/wrong-magic/wrong-opcode frames, wrong index/offset/length/digest, corrupt data, dropped source stream, bounded/sequential requests;
- complete RSC1 WRITE + SKIP + last partial + whole readback + commit; source mutation before target status, after activation and after one acknowledged write, with no bad next frame;
- lost write acknowledgement with no automatic resend, later explicit idle/reconcile and actual matching-chunk SKIP; explicit original inverse after an uncertain install;
- lost commit receipt, wrong acknowledgement index, incorrect whole-target hash, bounded partial trial; original SYSTEM/data/BOOT ordering in the mock;
- parent full-preflight failure before any features query or target process; successful preflight before the features query; PLAN_ONLY cannot start a process;
- byte-identical original/adapted manifest output for valid 2-, 4- and 5-role schemas and refusal of unapproved or reordered inputs;
- source-only receipt semantics and bounded journal/stderr retention.

These mocks qualify the new host behavior; they do not redo or replace the original independent target-rescue review or prove the daemon's hardware behavior. The existing daemon's target-side checks remain supported by its prior evidence, which was read, not rerun or edited.

`evidence/unit-r1.txt` preserves the initial failing run: the mock target used socket timeouts, which made raw FD reads nonblocking and closed the mock before its request. The fixture now uses blocking descriptors like the pinned client expects. No production rescue change was made to fix that fixture error. The passing r2/r3 logs are retained.

`evidence/bounded-buffer-final.json`: a **17,133,056-byte** sparse ordinary-file fixture passed full preflight and all 17 source reads, including the real-size 355,840-byte tail. Peak tracked allocations for combined host and worker were **4,401,957 bytes**. This is incremental Python allocation evidence after imports, excluding interpreter baseline, OS buffers and SSH. It is not a total-process RSS claim or a production 11 GB throughput benchmark. The fixture was deleted after the test; peak test logical staging stayed under 32 MiB. Production mode stages no image payload file.

`evidence/readonly-userdata-samples-final.json` and `evidence/readonly-stock-system-samples-final.json`: separate **real read-only SSH** checks using the shipped production reader. First/middle/last requests matched the pinned reference tables; each receipt pins the reader code and records stat/time. Each source transferred at most 3 MiB of payload to RAM, with no payload saved to disk. These sample sessions were closed and are explicitly `full_preflight=false`. The earlier sample receipts are preserved. No 11 GB or 3.75 GB full preflight was run on the VM during this implementation.

`evidence/*patch`: callback/parent/manifest deltas against immutable source. `SOURCE_PINS.json` and `source/verify_handoff.py` provide offline source/profile integrity and original-source checks.

## Parent continuation commands

See `PARENT_COMMANDS.md`. All examples default to PLAN_ONLY unless the parent deliberately uses the documented explicit flag. No current ADB transport ID, armed recovery pin, approved contract, or install-image hash is invented here. The provided original-pair review remains pending, with `independent_rescue_review=false`; it must fail before opening a source.

For any later actual transfer, source full preflight must be performed by `parent_remote.py` in that transfer's held source session. Running `source_cli.py preflight` separately may produce useful evidence and a compact export, but cannot preauthorize/reuse that closed FD for a write. Re-run the live preflight before the target opens. A changed profile requires new exact byte/hash/chunk/metadata qualification and updated integrity pins.

Physical stock-kernel rescue qualification, current authenticated transport, secure ADB/Enforcing checks, actual armed-artifact fit, p10 pin and contract approval remain parent-owned. The parent’s R3 probe correction and first4.9 nearby-fallback requirement are unaffected. No physical readiness or flashing recommendation follows from these host-only results.
