# Offline stock firmware restore source

Question: can the already downloaded exact ASUS firmware reconstruct a bounded
stock system image without keeping another multi-gigabyte file on the Mac?

Status: offline payload audit passed. Both original full boot backups match the
zero-padded OEM boot member exactly. The canonical system payload is hashed;
comparison with the actual system backup remains pending. This spike never contacts a device,
executes an updater, writes a block device, or replaces the real device backup.

`scripts/audit_restore_source.py` verifies the pinned ASUS ZIP, transfer-list
coverage and payload lengths, hashes a streamed canonical system image, and
compares its boot member with both original boot backups. Canonical output uses
zero for discard ranges; discard bytes on the tablet need not equal zero.
Actual stock-system backup comparison is required before accepting this source.

Run `python3 scripts/test_restore_source.py`, then
`python3 scripts/audit_restore_source.py`. Results stay in `evidence/`.
Continuation: compare defined block ranges and whole-image hash with the actual
verified system backup when available. Do not run the ZIP updater: it also
writes bootloaders and trust-zone partitions outside the planned restore scope.

Verified outputs: `evidence/audit.json` and `evidence/system-block-map.json`.
The pinned ZIP SHA256 matches the original download evidence. All916,480
4KiB blocks are covered once:740,938 new,24,066 zero,151,476 discard.
Canonical zero-discard system SHA256:
`4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49`.
Full padded OEM boot SHA256:
`7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316`.
Four small binary/invalid-input tests passed, including truncation, trailing
payload, range overlap/gaps/bounds, unsupported commands/version and physical
placement. These do not establish device/system-backup equivalence.

The new scripts/prepare_comparison_manifest.py streams the pinned OEM bytes
without writing an image and produces evidence/oem-comparison-chunks.json:
112 fixed32MiB/last28MiB comparison entries. It records both canonical zero-erase
hashes and non-erase slice hashes with explicit offsets, independently matching
the earlier full canonical, defined-range and new-data digests. Four behavioral
tests cover segment/chunk boundaries, the short final chunk, malformed maps and
truncated/trailing input. The old audit tool and evidence remain unchanged.

Offline historical comparison shows all77 old USB verified chunk digests and
all11 new Wi-Fi chunk digests match the public OEM canonical bytes exactly.
See evidence/partial-capture-oem-comparison.json. These receipts alone do not
prove the remote stored files are still intact or that all112 chunks exist.

scripts/compare_remote_prefix.py defaults PLAN_ONLY. With --execute it contacts
only the existing builder over authenticated SSH, reads the exact old77-chunk
prefix and independently checks actual stored bytes against captured double-
source hashes, OEM canonical hashes and OEM defined-slice hashes. It never
contacts the tablet or writes a remote file. A full backup and final independent
whole-image verification remain pending regardless of prefix success.
