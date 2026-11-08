# Implementation review and parent handoff

Ready for parent runtime preflight: the tool covers the whole fixed
3,753,902,080-byte system partition in 112 bounded chunks, with two actual source
reads per chunk. All 36 offline tests passed. No physical or cloud execution
occurred, and no original-OS backup has been claimed or produced by this agent.

I read the latest orchestration README, its data-storage audit and saved root
geometry evidence, the recovery-control transport and its tests, the unchanged
root_shell.py, backup_encryption_areas.py, live partition-layout JSON, and the
initial/verify boot and recovery backups. The two boot files remain local,
16,740,352 bytes each, SHA256
`7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316`.
The two recovery files remain local, same length, SHA256
`902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`.
No other storage area is sent to the VM. Historical scatter offsets disagree
with live GPT; the tool pins the actual live start sector 1072424 instead.

Review of source-read and transport boundaries:

- Every root operation rechecks the unchanged helper SHA256
  `951b3b7f8c099550554a9689b0be5995981def7060735109c66761be611ad8ec`
  and mtk-su SHA256
  `328632e853ff6427af9f35cb83a91d9e960f35d01188ee66d46ae9c7ce7c7827`.
  They match the existing recovery transport. The helper was not edited.
- ADB selection/ro.serialno, SDK24, P00A_2, exact stock fingerprint,
  boot_completed=1 and Enforcing are checked fresh before and after each root
  session. The immutable helper temporarily changes SELinux state during its
  root session; Enforcing is deliberately checked outside that session.
- Root predicates before and after every dd check canonical by-name resolution,
  canonical block path, p25, start, size, 512-byte logical sector, sysfs 179:25,
  numeric `ls -ln` device numbers, unique ext4 `/system` read-only mount and
  read-only mountinfo entries for every alias of 179:25. Unsupported Android
  stat %t/%T is absent. Predicates are fresh shell reads, never cached evidence.
- dd reads only the fixed system block into new fixed a.bin/b.bin files, with
  1 MiB bs and exact bounded skip/count. Source errors or short reads fail; no
  conv, padded errors, head -c, device sha256sum, or raw block destination exists.
- An outer mandatory nonce-tagged operation status survives a successful EXIT
  cleanup trap. Missing/duplicate status, nonzero inner status or nonzero helper
  completion stops the entire run. No following retry/cleanup is dispatched.
- The helper carries only scripts/text/status. Actual payload uses `adb exec-out`
  without a PTY, binary stdout and a concurrent bounded stderr drain. There is
  no shell pipeline whose last exit status can conceal an upstream failure.
- The first read is written to a single exclusive 32 MiB-or-smaller host file,
  fsynced and rehashed. The second independently staged source read is streamed
  and compared byte-for-byte against that file; both source SHA256 accumulators
  and byte counts advance independently. Full source counts must each equal
  3,753,902,080 and both full source hashes must agree.
- SSH consumes the verified first file as binary stdin. Python source and request
  JSON are separate shlex-quoted argv fields. SSH host identity is verified via
  the pinned alias/known-hosts file. No private key is read into Python, logs,
  artifacts or repositories. Remote Python writes exact bounded bytes, fsyncs,
  reopens and hashes the stored chunk before returning its size and SHA256.

Review of ownership, deletion and completion:

- Device staging is the fixed `/data/local/tmp/asus-stock-system-stream-backup`,
  shell UID/GID 2000, 0700. This permits the binary ADB channel to read exports
  without transporting binary through root_shell.py. Its run marker is root
  UID/GID 0, 0600; payload exports are shell-owned 0600. Parent exclusively owns
  device operations. No attempt is made to defend against a malicious actor
  already controlling UID shell/root during the backup.
- The base must be absent, including dangling symlinks. Each access verifies
  canonical directory path, owner/mode, run marker and regular nonsymlink file
  metadata. Cleanup also pins the recorded payload inode, exact size and link
  count. No recursive deletion, wildcard cleanup, or automatic failure cleanup
  exists. The immutable helper's separate executable path is prechecked for
  symlink/type/ownership/mode/link safety before its existing adb push behavior.
- Only after two matching source reads, actual host hash, actual remote readback
  hash and a durable local chunk_verified event are device a.bin/b.bin removed.
  The host file is then checked for inode, size, permissions and actual hash
  before unlinking. Device marker/directory are removed after all chunks pass.
  An error during cleanup stops and leaves all remaining staging untouched.
- Remote base and run directories are 0700, files 0600. Trusted nonsymlink
  ancestors are required. Each run/chunk/image/manifest is exclusively created;
  concurrent reuse is refused. All remote mutations are below the fixed backup
  base, isolated from product, kernel, radio and rescue build trees.
- Finalization validates all chunk geometry/hashes, rehashes stored chunks,
  assembles the exact-length image, compares its streaming aggregate hash with
  both source hashes, then rereads the assembled file independently. Manifest
  bytes are written, fsynced and reread. READY is published by an atomic exclusive
  hard link after file/directory fsync, then the temporary link is removed.
  A crash between link and unlink can leave READY with two links; verification
  conservatively refuses it. This is inspectable partial state, never silently
  repaired or overwritten.
- A separate remote verify command reopens/rechecks all chunks, image, manifest
  and READY. Local COMPLETE is created only after that response passes exact
  run/size/hash checks. The manifest binds the run id, fixed target, both full
  source counts/hashes, every source/remote chunk hash, source-code hashes and
  immutable helper/binary hashes. The READY and local receipt pin the final
  manifest SHA256. Loss after remote publication may leave a valid remote image
  but no local COMPLETE; explicit read-only verification resolves that case.

Allowed mutations are only local private journals and the reused chunk file;
the guarded device staging just described; the existing pinned helper's own
fixed `/data/local/tmp/asus-mtk-su64` push/chmod and transient root/SELinux
behavior; and private files under `/srv/android/asus-stock-system-backup`.
There are no block writes, mounts, reboots, fastboot calls, userdata operations,
VM lifecycle actions or writes into build trees. The helper executable is left
in place as the existing immutable helper does; the new tool does not delete it.

V1 deliberately has no resume or failure-cleanup command. Default collisions
are refused, and even explicit reuse is unsupported. This avoids treating
uncertain staged bytes as a new source read. Parent can investigate partial
state with the saved dispatch/status/inode/hash records, verify a published
run read-only, and prepare a separately reviewed cleanup before a genuinely
new full attempt. No stale ownership marker or lost-transport timeout grants
permission to remove files. Keep the failed run's evidence and remote files.

Offline verification evidence is in evidence/offline-tests.txt and .json. Tests
exercise the real remote worker against a temporary local filesystem, the real
coordinator against a byte source, actual local binary subprocess transport,
and generated shell predicates with all device commands/data replaced by local
fixtures. They cover exact binary 0/CRLF/non-UTF8 preservation; full-size chunk
coverage; two-source change detection; truncation/overflow; invalid geometry;
wrong identity, node number and mount state; symlink/hardlink/owner/collision
refusal; SSH error/timeout and lost acknowledgment; inner-root failure hidden
by an outer successful EXIT; publication/fsync failure; remote corruption; and
cleanup ordering and changed host staging. The real local 32 MiB stream used
one file and approximately 1.1 MiB peak Python-tracked allocation (actual value
recorded in JSON); no allocation scaled with the full 3.5 GiB source.

Runtime limitations are explicit: Android toybox/file permissions, actual
mtk-su timings, ADB export access under restored SELinux, and current SSH/VM
availability have not been exercised here. Real preflight will refuse
unexpected `/data/local/tmp` owner/mode, device identity/geometry/mounts, unsafe
remote permissions, unavailable tools or insufficient disk. Preflight does not
prove the subsequent payload read will succeed. If actual export access or
a 32 MiB root read fails, preserve evidence and adjust only after parent review;
do not weaken status/size/hash guards or modify the pinned helper.

The exact parent preflight, backup and independent verification commands,
expected paths and disk requirements are in README.md. Completion here means
the offline executable and tests are ready, not that physical recovery or the
later clean internal-data migration has been approved or performed.
