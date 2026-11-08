# Parent-owned factory state preservation

Question: are current factory files and existing raw factory backups preserved
before any Android17 userdata migration?

Status: preservation qualified for the audited sources. Full OS installation
still requires the other boot/rescue/data gates. Parent-only device work used the fixed
authenticated stock Wi-Fi endpoint and existing on-demand root helper. No
calibration values are published or sent to subagents or the build VM.

`private/` is mode0700, ignored, and outside any Git repository. Actual source
metadata, factory payloads and private verification receipts stay there. Public
`evidence/` contains aggregate outcomes only. Existing two-copy raw backups in
the original boot audit are preserved, not overwritten.

Continue using the exact checklist in
`../2026-11-06-asus-hardware-completeness-audit/report/CALIBRATION-PRESERVATION.md`.
Inventory entire factory trees and conditional existing files; absent and
unreadable are distinct. Keep source and archive hashes and metadata, check for
changes during capture, and verify archive bytes independently on the host.
No partition writes, factory reset, calibration regeneration or restore test was
part of preservation. A completed backup does not prove new drivers consume it.

`evidence/parent-preservation-acceptance.json` is the current aggregate receipt.
Two independent source archives match for 39 regular files and metadata across
53 entries. Numeric ownership, modes, timestamps and SELinux labels are saved.
Three sensor FIFOs are metadata-only entries; no IPC content was read. Complete
NVRAM, persist, sensor and akmd trees were captured. The six conditional extra
candidates were absent. Of 71 public record paths, 23 existed in the captured
tree and 48 were absent; absence is not a backed-up value or a regenerated default.

Six raw factory partitions have two new independently matching current snapshots,
with live alias/start/size checks before and after reads. All historical two-copy
backups were also reverified and retained. One current raw snapshot differs from
its historical backup; both revisions are preserved. New and historical payloads
remain private/local. Temporary device staging was removed after host verification.
The device remains in normal Android, boot-complete and Enforcing.

The initial inventory stopped at an unavailable `awk`; its private logs are
retained. Subsequent capture used available shell tools. The initial host archive
check correctly rejected unexpected special files; review established the three
observed sensor FIFOs, now narrowly permitted as metadata-only entries. The final
archive verifier is `scripts/verify_files.py`. Its receipt is one-shot; do not
overwrite the existing private verification by rerunning it.

This acceptance covers the audited files and raw partitions, not every possible
hardware OTP/controller state. New findings require a supplementary inventory.
Restoration and driver consumption remain separate untested tasks.
