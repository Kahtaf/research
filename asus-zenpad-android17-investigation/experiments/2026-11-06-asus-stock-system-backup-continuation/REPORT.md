# Implementation and offline review

The continuation is implemented and passes 72 offline tests. It is ready for
the parent's code/evidence review and parent-owned execution. No live device,
ADB, root helper, SSH, VM or cloud operation was performed in this implementation
session. No stock backup was completed, and no runtime throughput or WiFi
availability is claimed. The purpose is a trustworthy stock p25 restoration
anchor for the Android 17 port.

The selected USB run has 77 contiguous completed double-capture/upload rows.
The current candidate pins 8,659 journal JSON files through the last accepted
chunk receipt and validates actual guarded source-dispatch scripts against the
parent-reviewed original implementation. It does not use the failed next
export or the shorter 11-chunk WiFi run. Original tools, helpers, failed-run
payloads and private staging were not copied, edited, removed or resumed.
Selected immutable input/source hashes are checked against the initial
baseline again in `evidence/source-review.json`. The source binary's actual
SHA256 is `328632e853ff6427af9f35cb83a91d9e960f35d01188ee66d46ae9c7ce7c7827`,
matching the original authoritative constant.

## Changes for review

`continuation.py` validates the captured target, geometry, original reviewed
code pins, root helper/binary, exact root-envelope script and inner nonce/status,
stage inode, two ordered independent exports, byte-comparison completion,
equal digests and upload readback acknowledgement. It checks contiguous chunk
indices/ranges and pins the selected journal bytes. Inputs additionally pin
this implementation and its dependencies. Every execute reconstructs the
candidate from actual evidence; future candidates recursively validate prior
inputs and keep capture provenance rather than rewriting it as a new capture.
The explicit uncertain-put option requires a completed double capture and put
dispatch, while remote actual-byte verification still determines eligibility.

`remote_worker.py` adds prefix copying and separates assembly from publication.
Copying preserves old inode/link counts and cannot mutate old files through a
shared hardlink. Reads use no-follow descriptors and compare inode/device,
length, mtime and ctime before/open/after reading, plus private ownership, modes,
link count and the expected actual-byte hash. New writes use exclusive creation,
fsync and stored-byte reread. Prefix-copy uncertainty stops; the previous source
run remains available. Assembly checks every chunk both before and during
concatenation, checks full length, and independently hashes the resulting file.
Finalization checks the complete data again, stores the pinned manifest and
publishes READY with exclusive atomic link semantics and directory fsync.
Separate verify reads all actual chunks and the entire image.

`policy.py` introduces schema 2. The manifest has `assembled_sha256`, exact full
geometry, both source hashes per chunk and capture provenance. It rejects the
old `source_sha256_a/b` and `source_bytes_a/b` aggregate fields because Python's
original streaming hash state is unavailable. It makes no claim that a fresh
whole-device source pass occurred. The aggregate comes from actual ordered
assembly of individually verified captures and independent whole-image readback.

The coordinator uses a fresh per-run host/device/remote namespace and preserves
all previous staging. It emits a durable double-capture receipt before putting
bytes, enabling explicit inspection after lost acknowledgements. Successful
chunk cleanup still follows durable remote verification; failures do not clean
up. Default invocation remains PLAN_ONLY. Execution requires a pinned input,
explicit parent review, unchanged-stock attestation and exclusive parent
ownership. Verify uses the pinned local manifest and does not contact ADB.
The fixed SSH endpoint, host-key alias, known-hosts path, identity path and
strict authentication options remain unchanged; private keys are never opened
by Python. Metadata requests are compressed/base64 encoded, decoded with a
1 MiB bound, and constrained to a 64 KiB SSH command. Binary put stdin remains
binary. This avoids the near-128 KiB argv size of the full provenance manifest.

The separately pinned helper clone batches fixed identity/health fields in a
nonce-delimited shell snapshot and independently checks the honest ADB endpoint.
A healthy snapshot takes two ADB launches. Read-only queries can retry at most
three times on status 255/timeouts with empty stdout, recording all attempts
and diagnostics; any partial or malformed response, wrong identity/security or
other status fails immediately. Root dispatch, push, binary exports and remote
operations are never retried. Healthy-path code accounting is 43 ADB launches
per completed new chunk, including both stage roots, cleanup, features and
binary exports; this is not a measured live timing result. The outer helper
client timeout is 300 seconds to accommodate bounded health retries around the
unchanged 60-second root-operation limit. The clone retains the inner nonce,
status propagation, SELinux restoration trap and post-root Enforcing check.
It uses a separate guarded binary staging filename and accepts only exact
coordinator-generated fixed-operation templates, not arbitrary stdin commands.
Original helper files are unchanged.

## Offline evidence

`evidence/offline-tests.{txt,json}` records 72 passing tests. Tests install a
Python audit hook rejecting external executable/transport/helper invocation and
socket connections/address lookups. The only real subprocesses are bounded
local Python and local shell fixtures. ADB/SSH/helper branches are mocked; the
remote worker runs against private temporary local directories. Both the CLI
backup execution path and the separate verify path run end to end under these
fixtures. A real local 32 MiB stream checks binary preservation, 1 MiB callback
bounds, one host payload file and bounded allocation.

Coverage includes corrupt/missing/short/symlink/wrong-mode/owner/hardlinked
prefixes, copy-time inode replacement, destination collision, source-script and
journal forgery, missing comparison/upload receipts, wrong identity/endpoint,
insecure ADB, nonce parsing, bounded health retries, nonretryable errors,
unknown root completion, push failure, short/oversized binary streams, uncertain
put with complete versus partial remote bytes, future continuation provenance,
prior-input revalidation, gaps/overlaps, changed prefix before finalization,
failed fsync/publication, manifest pins, all-chunk/full-image independent verify,
CLI review/ownership gates, template-only helper requests and full-geometry
compressed metadata. Earlier failing offline passes are retained under
`evidence/qa/`; they exposed fixture umask and reduced-geometry setup issues,
which were corrected. Final tests pass without skipped cases.

## Parent handoff and remaining limits

The exact offline plan, preflight, execute and separate verify commands are in
README.md. The current candidate is
`78c42fa595f2e152ef48f1bfdd7883f723aa63b2f15ad73097ea9ca82dd46251`.
Review that candidate and `evidence/adapter.diff` with `evidence/source-review.json`.
No permission or live action was requested by this implementation agent.

Journal origin and unchanged stock across captures are explicit parent trust
inputs. Local hashes cannot authenticate a fabricated journal without that
review. Private-file/inode checks detect replacement and corruption but are
not a defense against a hostile process with the same owner or root privileges;
exclusive ownership is required across all tools and backup runs. VM lifetime,
current free space, sustained transport behavior and temporary-root compatibility
must still pass the parent's live gates. A run with an uncertain root operation
must be resolved by the parent before any subsequent root dispatch. Existing
failed staging is intentionally not reclaimed, and the 32/64 MiB payload caps
are for the active run in addition to retained earlier failed staging.

The parent must compare the completed actual image with the separate OEM source
audit before relying on OEM canonical-zero reconstruction. That audit explicitly
records actual-backup comparison as pending and tablet discard contents as
unproved. This implementation neither substitutes OEM bytes nor performs any
restore, flash, boot, recovery, calibration, userdata or Android 17 build action.
