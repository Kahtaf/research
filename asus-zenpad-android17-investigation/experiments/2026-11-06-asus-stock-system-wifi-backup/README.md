# Stock system backup over authenticated WiFi ADB

Question: can the reviewed bounded stock-system backup use the parent's
authenticated private LAN ADB connection to avoid the finicky ASUS USB bulk
path, while preserving the same source and verification protections?

Status: implementation ready for parent review and execution; 47 offline tests
passed. This implementation agent performed no ADB, root-helper, device, SSH,
VM or cloud operations. No stock-system backup was produced here. Test images
are temporary local fixtures, not device backups.

This is a fresh adapter of `2026-11-06-asus-stock-system-stream-backup`, matched
against `evidence/parent-review-shell-v2.json` before copying. Only the three
Python sources, test file and selected small review metadata were copied. The
original spike, its failed evidence/payloads, and both external helpers remain
unchanged. Per parent handoff, the USB attempts stopped after one 32 MiB export
and then after 77 verified/uploaded chunks (2,464 MiB); neither completed.
Those partial runs are not resumed, deleted or trusted by this adapter.

Important outputs:

- `source/stock_system_backup.py`: coordinator; default PLAN_ONLY.
- `source/policy.py`: fixed hardware, TCP transport, p25 geometry and manifest validation.
- `source/remote_worker.py`: unchanged verified upload, assembly and readback worker.
- `tests/test_backup.py`, `evidence/offline-tests.{txt,json}`: 47 offline checks.
- `evidence/source-review.json`, `evidence/adapter.diff`: final hashes and bounded source changes.
- `evidence/input-baseline.json`: original source/review/helper hashes.
- `evidence/parent-wifi-helper-runtime-validation.json`: copied parent evidence,
  not execution by this agent.
- `REPORT.md`: implementation boundaries, verification and remaining runtime work.

The fixed ADB selector and honest `get-serialno` result are
`IP_REDACTED:5555`. Actual hardware `ro.serialno` must be `DEVICE_SERIAL_REDACTED`.
Every root session checks product `P00A_2`, SDK `24`, the exact stock fingerprint,
`ro.adb.secure=1`, boot completion, and Enforcing before/after root. The
manifest and plan record transport separately from hardware identity. There
is no endpoint argument, discovery, reconnect, fallback or PATH shim.

The external text-only helper is
`../2026-11-06-asus-wifi-device-access/scripts/root_shell_wifi.py`, SHA256
`684bbe346488dfd0e7dfce741b7547021f019d3749235e6208eb1c9766395f34`.
Its binary is explicitly pinned to
`../2026-11-05-asus-root-hardware-validation/sources/mtk-su-mirror-b`, SHA256
`328632e853ff6427af9f35cb83a91d9e960f35d01188ee66d46ae9c7ce7c7827`.
The helper source and binary are checked locally before invocation. Payload
bytes never travel through helper stdout; they use advertised `shell_v2` and
binary `adb -s IP_REDACTED:5555 shell -T` streams with exact lengths.

Parent continuation starts with these offline commands:

```sh
cd /OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-stock-system-wifi-backup
python3 -B tests/test_backup.py
python3 -B source/stock_system_backup.py
```

Review the report, diff and hashes, then exclusively own all device/root
operations across both spikes. The per-spike local lock does not arbitrate
against the older tool or unrelated helpers. Keep stock Android healthy,
Enforcing and `/system` read-only. The parent already validated authenticated
TCP access; current availability still needs runtime preflight. Confirm the
existing VM's remaining lifetime separately. This adapter cannot extend it.

The existing SSH destination remains `android@IP_REDACTED`, identity path
`~/.ssh/asus_p00a_android17`, HostKeyAlias `compute.8549823276971553556`, and
known hosts `~/.ssh/google_compute_known_hosts`. StrictHostKeyChecking,
IdentitiesOnly and BatchMode remain required. Private keys are passed by path
to SSH, never read into Python or copied. No new cloud resource is provisioned.

Generate a fresh run ID once, then run parent-owned preflight:

```sh
BACKUP_RUN="$(python3 -c 'import datetime,secrets; print(datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+secrets.token_hex(8))')"
python3 -B source/stock_system_backup.py preflight --run-id "$BACKUP_RUN" --execute --exclusive-device-owner
```

Only after successful preflight, run the full fresh backup with the same ID:

```sh
python3 -B source/stock_system_backup.py backup --run-id "$BACKUP_RUN" --execute --exclusive-device-owner
```

Preflight invokes the pinned helper for predicates and contacts the existing
VM, but does not export the system payload or create backup staging. The
helper itself pushes its fixed executable, temporarily obtains root and
restores Enforcing. Backup repeats preflight, then creates the distinct
`/data/local/tmp/asus-stock-system-wifi-backup` staging base, which must be
absent. It never accesses or cleans the uncertain old USB staging base.

The full source is only `/dev/block/mmcblk0p25`, exactly 3,753,902,080 bytes:
111 chunks of 32 MiB plus one of 28 MiB. Host payload is bounded at 32 MiB,
device payload at 64 MiB, and stream buffers at 1 MiB. Two independent source
reads must match byte for byte before upload. Actual host/remote readback,
full assembly/hash checks and READY/COMPLETE publication remain mandatory.
There are no userdata/calibration uploads or raw block writes.

Host and `/data` each need at least 128 MiB free. The VM needs at least
8,581,545,984 bytes free: two full image lengths plus 1 GiB reserve, in
addition to already retained failed-run storage. Python 3 and a trusted,
`android`-owned writable `/srv/android` are required. Remote directories are
0700 and files 0600. An unsafe existing backup base or reused run is refused.

Successful remote output is under the unchanged fixed base:

```text
/srv/android/asus-stock-system-backup/<BACKUP_RUN>/
    RUN.json
    chunk-0000.bin ... chunk-0111.bin
    system.img                 exactly 3753902080 bytes
    manifest.json
    READY.json                 atomic publication marker
```

Local output is `evidence/runs/<BACKUP_RUN>/`, with journals, manifest and
`COMPLETE.json` only after final remote verification. The full image is never
downloaded to the host. Remote chunks are retained.

For independent verification, pin the saved local manifest bytes, then run:

```sh
MANIFEST_SHA="$(python3 -c 'import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "evidence/runs/$BACKUP_RUN/manifest.json")"
python3 -B source/stock_system_backup.py verify --run-id "$BACKUP_RUN" --manifest-sha256 "$MANIFEST_SHA" --execute
```

This contacts only SSH, rehashes every chunk and the entire assembled image,
and checks READY, exact size, hardware/transport scope and the pinned manifest
hash. It performs no device/root operation and writes only separate local
verification evidence. The returned image SHA256 must match both source
aggregate hashes in the local manifest and its COMPLETE receipt. Keep these
local anchors. The new manifest requires WiFi transport metadata; use the
original tool for verification of any older USB-format manifest.

On any failure, timeout, mismatch or uncertain response, stop and preserve all
evidence and staging. There is no retry, resume or automatic failure cleanup.
Inspect parent-owned health and the last dispatch/acknowledgement before any
new action. A new attempt needs a fresh run ID, all source bytes reread and
an absent WiFi staging base; any cleanup of uncertain staging requires a
separately reviewed parent action. Loss after publication may be investigated
using the explicit verification command if the local manifest exists.

When finished, the parent owns disabling the TCP listener:

```sh
adb -s IP_REDACTED:5555 usb
```

The parent must then verify TCP access is gone. This implementation agent did
not run that command. Record actual runtime results and resulting hashes in
the parent handoff; offline success alone establishes no device backup.
