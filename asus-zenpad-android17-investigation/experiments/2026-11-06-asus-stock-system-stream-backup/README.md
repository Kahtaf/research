# Verified stock system stream backup

Question: can the parent preserve the entire original 3,753,902,080-byte stock
Android 7 system partition while the Mac has only about 1.3 GiB free?

Original handoff: implementation complete and reviewed offline; 36 offline tests passed.
No ADB, root-helper execution, device, SSH, VM, or cloud operation was performed
in this spike. There is no actual stock-system backup yet. Parent execution is
required. This is independent of the new rescue-recovery implementation.

The executable is `source/stock_system_backup.py`. Its default is PLAN_ONLY,
including when an action is supplied. `--execute` is required for any transport;
backup/preflight additionally require `--exclusive-device-owner`. It reads only
`/dev/block/mmcblk0p25`, with the exact live system identity/geometry pinned.
There is no configurable partition, remote host/path, resume, flash, mount,
format, or reboot command. Userdata and calibration/key areas are excluded.
The user's later clarification that personal data need not be preserved does
not change this tool or authorize any added upload scope.

Important outputs:

- `source/stock_system_backup.py`: host coordinator, guarded root reads, bounded
  binary ADB transport, source comparison, journal, and default plan-only CLI.
- `source/remote_worker.py`: private storage, exclusive chunk creation, actual
  byte hashes, assembly, independent full-file readback, atomic READY marker.
- `source/policy.py`: fixed identity, full-size geometry and manifest validation.
- `tests/test_backup.py`, `evidence/offline-tests.{txt,json}`: executed offline
  checks, including fault injection and a real local 32 MiB binary stream.
- `evidence/source-review.json`: source and reviewed-input hashes, including
  the two existing boot/recovery backups, read locally only.
- `REPORT.md`: implementation review, mutation scope, uncertainty handling and
  remaining runtime limits.

The parent should first review the report and source. Use a shell in this spike:

```sh
cd /OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-stock-system-stream-backup
python3 tests/test_backup.py
python3 source/stock_system_backup.py
```

Those commands are offline. For a real attempt, the parent must exclusively own
all device/root operations, keep stock Android booted with `/system` read-only,
and check that the existing authorized builder will remain running long enough.
The orchestration README last recorded an automatic stop at
2026-11-06T17:04:43.960284Z; refresh that fact as parent before starting. This tool
does not change VM lifecycle or build trees. If the VM address or SSH identity
has changed, review/update the pinned source; do not relax host-key checking.

The fixed authenticated SSH endpoint is `android@IP_REDACTED`, identity file
`~/.ssh/asus_p00a_android17`, HostKeyAlias `compute.8549823276971553556`, known
hosts `~/.ssh/google_compute_known_hosts`. The tool passes those paths to SSH;
it never reads or copies the private key. IdentitiesOnly, BatchMode and
StrictHostKeyChecking are enabled. It needs Python 3 on the existing VM and an
`android`-owned writable `/srv/android` parent with no group/other write bit.
Existing backup directories must be owner-only 0700. A missing backup base is
created by the backup action only; an unsafe existing base is refused.

Generate a fresh run id once and use it for both preflight and backup:

```sh
BACKUP_RUN="$(python3 -c 'import datetime,secrets; print(datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+secrets.token_hex(8))')"
python3 source/stock_system_backup.py preflight --run-id "$BACKUP_RUN" --execute --exclusive-device-owner
```

Preflight contacts SSH and uses the pinned root helper for fresh predicates.
It does not read the system payload or create device/remote backup staging.
The existing helper itself pushes its fixed executable, temporarily obtains
root, and restores Enforcing. Local preflight evidence is created. Any refusal
must be investigated, not bypassed by weakening a guard.

After preflight succeeds, execute the full backup with the same run id:

```sh
python3 source/stock_system_backup.py backup --run-id "$BACKUP_RUN" --execute --exclusive-device-owner
```

The tool repeats preflight itself. It transfers all 112 chunks: 111 of 32 MiB
and one of 28 MiB. It keeps one host payload file (32 MiB maximum), two device
payload files (64 MiB combined maximum), and <=1 MiB stream buffers. Host and
`/data` preflights require at least 128 MiB available. Remote preflight requires
8,581,545,984 bytes free (7.9921875 GiB): full chunks plus assembled image plus
1 GiB reserve. The successful remote payload retains 7,507,804,160 bytes
(6.9921875 GiB), plus small JSON metadata. It does not delete remote chunks.

Expected remote output:

```text
/srv/android/asus-stock-system-backup/<BACKUP_RUN>/
    RUN.json
    chunk-0000.bin ... chunk-0111.bin
    system.img                 exactly 3753902080 bytes
    manifest.json
    READY.json                 atomic publication marker
```

Every directory within the fixed backup base is 0700 and every backup file is
0600. All creation is exclusive. An existing run or chunk is never overwritten.
A run without a valid READY marker is incomplete, even if `system.img` exists.
The parent gets local `evidence/runs/<BACKUP_RUN>/manifest.json`, detailed JSON
journals, and `COMPLETE.json` only after the final remote reread is acknowledged.
The full image is never downloaded to the Mac.

Explicit independent verification, using the local manifest's actual hash:

```sh
MANIFEST_SHA="$(python3 -c 'import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "evidence/runs/$BACKUP_RUN/manifest.json")"
python3 source/stock_system_backup.py verify --run-id "$BACKUP_RUN" --manifest-sha256 "$MANIFEST_SHA" --execute
```

Verification contacts only authenticated SSH, rehashes every remote chunk and
the entire image, and checks exact size, run identity, manifest hash and READY
contents. It performs no device/root operations and does not modify the remote
backup. It creates separate local verification evidence. The returned full
SHA256 must match both source aggregate hashes in that run's local manifest.
Keep the local manifest, its hash and COMPLETE receipt as the verification
anchor. A helper-source pin mismatch also refuses invocation, even for verify.

On any short read, failed status, timeout, changed source, mismatch, disk error,
or lost response: stop, keep all evidence, and do not repeat the backup command
blindly. There is no automatic retry, resume, rollback, uncertain-stage cleanup,
or automatic deletion of incomplete remote runs. Parent must inspect the last
dispatch/acknowledgement and independently recover fresh device health. If a
publication response was lost, a local manifest may exist: the explicit verify
command above can establish whether the remote READY file is actually valid.
A new source attempt must use a new run id after reviewed staging cleanup; it
must re-read all source bytes. Existing partial chunks are never trusted.

Continuation: the parent executes the reviewed commands, reviews actual
runtime journals, and records the resulting run/image/manifest hashes in the
orchestration handoff. Offline test success is not proof of physical execution
or a replacement for the separate rescue/image gates.

## Parent runtime continuation, 6 November15:59UTC

Full backup remains pending. Firstpreflight revealed Androidshellcannotuse
readlink-f under/data; parentnowchecks each fixedparentcomponent andexpected
ownership/mode before root, with canonicalidentityrequiredinsideeveryroot
session. Binary path checks use the same no-symlink components plus staged
inode/size/owner/link checks. One32MiB exec-outtransfer completed, thenUSB
brieflydisconnected before secondrootoperation. No payload was uploaded and
no OSblockwritten. Originalkerneluptimecontinued; actualcauseundetermined.
Parentpreservedevidence, reviewedandcleanedonlyexactdevicestaging.
Actual32MiB shell_v2/non-PTY probe matchedoriginalbytes andimmediatehealth
passed. Binarytransportnowrequiresadvertisedshell_v2 anduses adb shell -T.
39offline tests pass after these changes. Current sourcepins/review:
`evidence/parent-review-shell-v2.json`. Immutablehelper remainsunchanged.
Currentrun20261106T155844Z-80cb7ab425df604b isstarted; sourcefrozen.
Cloudruntimeactuallyrenewed24h from2026-11-06T14:52:14.001Z; historical
17:04stopnoteaboveissuperseded. No additional cloudresource created.
