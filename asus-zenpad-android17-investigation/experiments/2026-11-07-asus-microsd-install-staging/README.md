# Actual microSD installation sources

Question: can the already available real DATA and stock rollback bytes be ready
for the SD installer while the final Android product build continues?

Status (2026-11-07): all five real roles are staged locally. Final Android
SYSTEM/BOOT native builds, host checks and genuine VINTF compatibility passed.
The complete source tree contains 5,409 files totaling 5,687,439,360 bytes;
actual all-zero chunks are omitted and remain bound by the complete chunk table.
The final manifest is `private/admitted.manifest`, 576,340 bytes, SHA256
`9fe4ec15800257262092f11698525939ebdfb404e150fbc7d308c7f8280ba534`.
No private DATA was uploaded.

`private/` is mode0700 and ignored. The DATA chunks include device calibration
and this Mac's public ADB key. Do not upload them to the VM or delegate access.
`private/card/asus-rescue/role-4` and `private/card/asus-stock/role-{0,1}`
are the actual fixed-path trees. Report directories are empty. Exact original
`asus-stock/recovery.bin` is copied and verified. `private/final-arm.id` contains
one actual parent-generated pairing ID, not an execution authorization. There
is no card-root mode or execution trigger yet.

`private/staging.json` records full and per-chunk identities, lengths and omitted
zero chunks. Original full images remain unchanged. No manifest or execution
trigger is fabricated.

Continue: add real final Android roles2/3 after build admission; assemble their
five-role RAM manifest with DATA4 and original roles0/1. Join the finalized SD
core's exact normal/stock directory and trigger contract, verify card capacity,
then copy sources to the prepared FAT32 card. These partial directories are not
an armed card and do not authorize a write.

`scripts/fetch_final.py` connects this staging layout to the completed native
build. Its default invocation is PLAN_ONLY. After reading the genuine successful
build report, the parent supplies the exact VM raw SYSTEM path/hash and packaged
BOOT path/hash/length with `--execute`. The script downloads over the existing
pinned SSH connection, checks all uncompressed source bytes, zero-pads BOOT to
the fixed partition length, and reuses the actual chunk stager for roles2/3.
Only then does it join the real original-pair authority, final image tables and
private DATA table into `private/admitted.manifest`. It never invents hashes or
uploads private DATA. Verified temporary full downloads are removed after the
chunk trees and final source receipt are durable; source VM images are retained.

After that real join, run the completed offline-stock-fallback final packager
with `private/admitted.manifest`, `private/final-arm.id` and the pinned physical
kernel. Stage only its actual emitted control files. No final download,
manifest assembly, card control-file write or final recovery assembly has run
yet. Missing build outputs are not replaced by an old image.

## Current parent continuation

Final fetch completed once; do not rerun it. `private/final-sources.json` is the
actual source receipt. The corrected core assembled the genuine candidate in
`../2026-11-07-asus-sd-media-flag-core/artifacts/final/`; its assembly receipt
binds the actual five roles. Physical Linux 4.9 startup remains unproved, so the
candidate is not deployed and no internal OS partition has been written.

The parent is copying the inert source trees to the already prepared ASUS17
card through USB ADB; see `../2026-11-07-asus-unarmed-sd-transfer/evidence/transfer.json`.
No mode, manifest selector or execution triggers are included in that copy.
Do not copy final control files or reboot during the transfer. The rescue's
whole-source preflight is still required before any installation writes.
