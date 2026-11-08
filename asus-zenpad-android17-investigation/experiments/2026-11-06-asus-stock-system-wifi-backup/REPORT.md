# WiFi adapter implementation report

Ready for parent review and runtime execution. All 47 offline tests pass.
No ADB, helper, device, SSH, VM or cloud operation was executed by this agent,
no private SSH key was read, and no stock-system backup was produced.

The baseline is the original three-source implementation at the parent's
`parent-review-shell-v2.json` hashes (39 tests). Its source hashes were checked
before copying. Only source, tests and small metadata were copied; no old
payload, staging or run evidence directory was traversed or copied. Selected
original source/test/docs/review files and both external helper sources were
hashed again at handoff and are unchanged. `evidence/input-baseline.json` and
`evidence/source-review.json` record that comparison. Historical runtime
evidence copied here belongs to the parent, not this implementation run.

The coordinator now selects only `IP_REDACTED:5555`, requires that exact
honest `get-serialno` response, and independently checks hardware serial
`DEVICE_SERIAL_REDACTED`. `ro.adb.secure=1` joins the unchanged exact product, SDK,
fingerprint and boot-completion predicates before/after root and inside the
root guard. Transport metadata is separate from the unchanged hardware target
in the plan and final manifest, and manifest validation requires the fixed
transport/security record. There is no arbitrary endpoint, discovery or
automatic reconnect path.

The helper is the parent's validated WiFi helper, pinned to SHA256
`684bbe346488dfd0e7dfce741b7547021f019d3749235e6208eb1c9766395f34`.
The root binary path explicitly stays under the original
`2026-11-05-asus-root-hardware-validation/sources` directory with SHA256
`328632e853ff6427af9f35cb83a91d9e960f35d01188ee66d46ae9c7ce7c7827`.
Neither helper was edited or executed. Root operation nonce/status handling,
before-root component symlink/owner/mode checks and every-session canonical
path checks are retained. The parent's copied helper validation records UID0,
deliberate exit17 propagation and restoration to Enforcing.

The new staging base is `/data/local/tmp/asus-stock-system-wifi-backup`.
Setup demands its absence; the original USB staging is never inspected,
resumed or deleted. All staged directory, marker, owner, mode, inode, link
count, canonical path and exact-length guards remain. Payload uses the binary
`shell_v2` non-PTY stream, never the text helper. The SSH endpoint, key path,
host alias, known-hosts path, authenticated options and cloud base are
unchanged. `remote_worker.py` is byte-for-byte identical to the reviewed
original; it imports the new policy, including transport validation.

The bounded algorithm is unchanged: exact full p25 geometry; 112 chunks;
two actual source reads; byte comparison; independent source hashes/counts;
host fsync and readback; remote upload and stored-byte readback; remote full
assembly and independent reread; pinned manifest; atomic READY; separate
remote verification; then local COMPLETE. Device chunk deletion happens only
after durable verified-upload evidence, followed by host inode/size/hash
checks before unlinking. Lost status or failed cleanup stops immediately.
No retries, resumption, failure cleanup, raw block destination or additional
source partition was introduced. Device and host payload caps remain 64 MiB
and 32 MiB respectively. All remote mutations stay in a private fresh run
under `/srv/android/asus-stock-system-backup`.

Tests retain all 39 original cases and add eight WiFi-specific cases covering
separate endpoint/hardware identity, secure ADB refusal before root and after
root, the actual pinned helper path/hash, the explicit original binary path,
dependency corruption/missing files/symlinks, unchanged SSH scope, plan-only
actions, and invalid source slices. Existing manifest mutation and binary
transport tests now also enforce WiFi scope, the new staging path and binary
NUL/CRLF/non-UTF8 preservation. Existing negative geometry/mount, file safety,
truncation/overflow, source change, upload loss, fsync/publication, corruption
and cleanup-order tests remain. A real local 32 MiB stream still passes the
buffer/allocation bound; exact observations are in `offline-tests.json`.

Test subprocesses use mocks for ADB/SSH/helper operations, isolated temporary
local filesystem fixtures, and local Python/shell-only byte and predicate
checks. The test runner installs an audit hook forbidding external transport,
helper invocation and socket connection/address lookup. No PATH shims or
real endpoint probes are used. Temporary fixture payloads are removed by
their test owners; this does not touch any historical failed-run staging.

Remaining runtime work belongs to the parent: review source hashes/diff,
ensure exclusive ownership across tools, verify current VM lifetime and
available capacity, run preflight, execute a fresh full backup, independently
verify the result and disable TCP ADB after use. The exact commands and output
paths are in README.md. Availability, throughput, sustained WiFi stability,
actual export access and success of the full backup have not been tested by
this agent. Existing failed-run evidence and cloud chunks remain preserved.
