# Verified continuation of the exact stock p25 backup

Question: can the Android 17 port retain an exact stock OS restoration image
without restarting successful source captures after a transient transport failure?

Status: implemented, 72 offline tests passed; awaiting parent review and live
execution. This agent performed no device, ADB, root, SSH, VM, or cloud operation.
No actual completed backup or new stock-image checksum is claimed.

The default selected source is the strongest existing prefix:
`20261106T155844Z-80cb7ab425df604b`, chunks 0–76, 2,583,691,264 bytes
(2,464 MiB). The remaining 35 chunks cover 1,170,210,816 bytes (1,116 MiB).
The new run must cover all 3,753,902,080 bytes: 111 × 32 MiB plus 28 MiB.
The failed USB and WiFi runs, their staging, source tools, and original helpers
remain untouched. There is no in-place resume, append, overwrite, or failed-run
cleanup. Copied prefixes do not share inodes with the old files.

Important outputs:

- `source/stock_system_backup.py`: functional coordinator; defaults to PLAN_ONLY.
- `source/continuation.py`: captured-source and sequential-journal validation.
- `source/health.py`: nonce-framed, batched, fixed read-only health queries.
- `source/remote_worker.py`: verified prefix copy, upload, assembly and readback.
- `source/policy.py`: fixed scope and explicit schema-2 manifest validation.
- `scripts/root_shell_batched.py`: separately pinned helper clone, restricted to
  the coordinator's exact fixed-operation templates.
- `tests/test_backup.py`, `tests/continuation_cases.py`: audited offline fixtures.
- `evidence/prepared-input.json`: receipt naming the current reviewed-input candidate.
- `evidence/inputs/78c42fa595f2e152ef48f1bfdd7883f723aa63b2f15ad73097ea9ca82dd46251.json`:
  77 validated capture rows, source/dependency pins and 8,659 pinned journal files.
- `evidence/adapter.diff`, `evidence/source-review.json`, `REPORT.md`:
  reviewable changes, hashes, preservation check, tests and limitations.
- `evidence/qa/`: preserved earlier offline results and superseded preparation receipts.
  Older input artifacts are evidence only; use the current candidate above.

## Parent's offline review and plan

```sh
cd /OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-stock-system-backup-continuation
python3 -B tests/test_backup.py
python3 -B source/stock_system_backup.py prepare
INPUT_SHA=78c42fa595f2e152ef48f1bfdd7883f723aa63b2f15ad73097ea9ca82dd46251
BACKUP_RUN="$(python3 -c 'import datetime,secrets; print(datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+secrets.token_hex(8))')"
python3 -B source/stock_system_backup.py backup --run-id "$BACKUP_RUN" --input-sha256 "$INPUT_SHA"
```

Expected: `PLAN_ONLY`, `prefix_chunks: 77`, `chunks: 112`. `prepare` writes only
local metadata and must reproduce the stated input SHA for these exact sources
and captured evidence. It validates the original parent-reviewed source hashes,
exact target/geometry, exact rendered guarded read scripts, successful inner
root status and stage inode receipts, two independent completed binary exports,
byte-comparison completion, equal source hashes, and successful stored-byte
upload acknowledgement. Hashes are not proof that a journal came from the
claimed device: the parent reviews the origin of those captures and attests
that stock `/system` has not changed since capture.

Review `REPORT.md`, `evidence/adapter.diff`, `evidence/source-review.json`, and
the candidate input. `--reviewed-inputs` explicitly attests this review; the
input SHA pins both selected evidence and this implementation. Execution
reconstructs the input from actual evidence again, including prior continuation
lineage, and refuses changed files or code. No arbitrary source path, partition,
ADB endpoint, SSH destination, remote directory or command can be supplied.

## Parent-owned live commands

The parent exclusively owns all device/root operations and the old/new remote
backup files across all spikes. Resolve any previously uncertain root dispatch
before starting a new run; a local lock alone does not establish that ownership.
The parent also checks the existing VM's lifetime. This tool cannot renew it.

Preflight repeats current identity and geometry checks but copies no image data:

```sh
python3 -B source/stock_system_backup.py preflight \
  --run-id "$BACKUP_RUN" --input-sha256 "$INPUT_SHA" \
  --execute --exclusive-device-owner --reviewed-inputs \
  --stock-unchanged-since-capture
```

Expected gates: pinned helper/binary/code and historical evidence; exact endpoint
`IP_REDACTED:5555` independently of hardware serial `DEVICE_SERIAL_REDACTED`;
`P00A_2`, SDK 24, exact `WW_P00A-V5.3.20-20180809` fingerprint; secure ADB `1`,
boot complete and Enforcing; exact p25 alias, sector size/start/length/device
number; unique ext4 read-only `/system` and no writable p25 mount; private safe
staging paths; absent destination run; host and device each ≥128 MiB free;
remote ≥8,581,545,984 free bytes in addition to retained old runs.
The helper uses the existing temporary-root mechanism, including temporary
SELinux transition and verified restoration, and pushes only its pinned binary.

After a successful preflight, use the same fresh run ID:

```sh
python3 -B source/stock_system_backup.py backup \
  --run-id "$BACKUP_RUN" --input-sha256 "$INPUT_SHA" \
  --execute --exclusive-device-owner --reviewed-inputs \
  --stock-unchanged-since-capture
```

Execution repeats preflight. It creates a new private remote run, reads and
hashes every actual selected prefix file, checks owner/mode/link count and
inode/size/time stability through an `O_NOFOLLOW` descriptor, copies bytes with
`O_EXCL`, fsyncs, then independently rereads each destination. Missing, short,
corrupt, replaced or unsafe files stop the run. Filenames or expected offsets
alone never authorize reuse. Old files are opened read-only.

New source staging is exclusively:

```text
/data/local/tmp/asus-stock-system-continuation/<BACKUP_RUN>/
```

Its private parent can persist; the run directory must be absent. Old USB,
WiFi and failed continuation run directories are never removed. The active run
uses at most 64 MiB device payload and one 32 MiB host payload, beyond preserved
older staging. Each remaining range receives two independent source reads,
exact byte comparison, two hashes, host fsync/reread, remote fsync/reread, and
a durable journal receipt before successful-stage cleanup. Read-only health
queries may retry up to three attempts only after status 255 or timeout with
no stdout. Every attempt is recorded. Any partial response, malformed nonce,
wrong identity/security, other status, unknown root completion, push failure,
binary transfer failure or SSH failure stops without an automatic retry.

Successful remote output, all private, is:

```text
/srv/android/asus-stock-system-backup/<BACKUP_RUN>/
    RUN.json
    IMPORT.json
    chunk-0000.bin ... chunk-0111.bin
    system.img                  exactly 3753902080 bytes
    manifest.json               explicit schema 2
    READY.json                  exclusive atomic publication, fsynced
```

The schema-2 manifest preserves each chunk's original capture run, transport,
source/helper/binary pins and comparison receipt hash. It records ordered
construction from double-capture chunks and the actual assembled image hash.
It does NOT claim either fresh contiguous whole-source SHA256 pass. Assembly
rehashes each input while concatenating, then independently rereads the entire
image. Finalization rechecks all chunks and image before publication. A further
remote verification precedes local `COMPLETE.json`. The pinned local manifest
is saved before finalization, so publication ambiguity can be investigated.

Separate, device-free final verification:

```sh
MANIFEST_SHA="$(python3 -c 'import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "evidence/runs/$BACKUP_RUN/manifest.json")"
python3 -B source/stock_system_backup.py verify \
  --run-id "$BACKUP_RUN" --manifest-sha256 "$MANIFEST_SHA" \
  --execute --exclusive-device-owner
```

This validates the pinned local manifest, reads every actual remote chunk and
all 3,753,902,080 image bytes, and checks READY. It writes a separate local
`<run>-verify-<nonce>/VERIFIED.json`. Its `sha256` must equal
`manifest.assembled_sha256` and the COMPLETE receipt. It never downloads the
whole image or contacts ADB. Preserve these local anchors and the sole verified
backup. Successful verification is not a restore/flash operation.

## Explicit continuation after a future failure

Stop and preserve the failed run. The parent reviews its last dispatch,
completion status, live health and exclusive ownership. To prepare a new
candidate from a stopped continuation run in this spike:

```sh
python3 -B source/stock_system_backup.py prepare --from-run "$BACKUP_RUN"
```

It includes the previously verified imported prefix plus sequential newly
verified chunks. It recursively revalidates the earlier selected evidence and
preserves original per-chunk provenance. Choose the newly printed input SHA,
review it, generate a NEW destination run ID, and run the same plan/preflight/
backup commands. Never rerun execute with an existing destination ID.
If prefix import itself failed before its acknowledgement, select the previous
reviewed input/run again; partially copied new files remain untouched.

When the final put response was lost, the default candidate excludes that
chunk. Only if a complete local double capture and its upload dispatch exist,
this explicit alternative can nominate it for inspection:

```sh
python3 -B source/stock_system_backup.py prepare \
  --from-run "$BACKUP_RUN" --include-uncertain-last-put
```

This is not an acknowledgement or an offset resume. Before reuse, execute must
read and verify the entire actual remote file at the expected length/hash.
Missing/partial/corrupt data fails; there is no append or overwrite. Use the
normal candidate to reread that source range into another new destination if
needed. Unknown source-root completion can never be promoted to a capture.
The legacy USB run's partial next export is specifically ineligible.

The existing OEM audit remains a separate future comparison, owned by the
parent. Its zero-discard canonical system SHA256 is
`4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49` and defined-range
SHA256 is `9cbdeef3db97aeae5b68a9e01e7869b6c735c108a9f6ab51c803730a847f11df`.
Neither is substituted for actual stock bytes or a checksum produced by this
backup. Discard-range contents on the tablet remain unproved until comparison.
No calibration, userdata or private keys are read or uploaded. No mount,
reboot, raw block write, BCB/metadata provisioning, public networking or cloud
resource operation is implemented. TCP listener teardown remains parent-owned.
