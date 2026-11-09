# External inputs intentionally excluded from Git

This archive is not self-contained install media. Keep the original local spike and private rollback inputs. Do not fetch or rebuild anything merely to inspect this checkpoint.

## Private owner inputs

- Verified stock BOOT/recovery/SYSTEM archives in the sibling `2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback/`, with the hashes in STATE-AND-RESUME.md.
- Original tablet firmware files, private factory Wi-Fi calibration and the stock Android WMT/bionic dependency closure. reports/stock-wifi-dependencies.md describes the actual dependency contract; it does not publish calibration.
- Existing microSD filesystem, its marked `2026-11-08-asus-alpine/` folder, the2GiB alpine-root.ext4, protected state/keys, browser profile and service data. They remain on the tablet/owner's local storage, not in this archive. A file copy of the mounted root is not a consistent backup.
- Private SSH key/known-hosts and the pinned boot binding under the original spike's private/. Use those only after reviewing actual resumed state. No sample credential is a substitute.
- The currently installed recovery capsule binary and local generated build outputs. evidence/paused-capsule-manifest.json preserves its identity and build metadata, not the image.

## Public fetchable sources

- Donor: https://github.com/kaantcp/z380m-alpine at7218a276f252a59874ab860683c061fa2b856519. Original local nested Git repository was clean at export and was not copied. Fetch to sources/z380m-alpine only after an explicit resume and source review; do not execute the donor's BOOT/SYSTEM installation guide.
- Alpine minirootfs3.24.4/aarch64: https://dl-cdn.alpinelinux.org/alpine/v3.24/releases/aarch64/alpine-minirootfs-3.24.4-aarch64.tar.gz , SHA2564b14c18f7e90a063b61462ea1462a5732c154bf6adad594974fe6487cd98a8de. Historical recovery builder expects it in downloads/.
- JWM2.4.6 release: URL and SHA256/SHA512 in evidence/jwm-reflow/provenance.json. The historical native recipe expects the release tarball at evidence/jwm-reflow/jwm-2.4.6.tar.xz. This fetched archive, the APKBUILD and full extracted/QA source trees are intentionally absent; the authored workarea patch and build script are included.
- FFmpeg7.1.5: https://ffmpeg.org/releases/ffmpeg-7.1.5.tar.xz , SHA256de668509caf9e35e3cd162473441fdb29538c6d96ed080292b3cf9e6fc5d558f. The authored builder expects the tarball, pinned Firefox FFmpegLibWrapper.cpp and retained synthetic media under sources/browser-ffmpeg61-validation/input/. That input directory is absent. The corresponding builder/ABI/ELF/decode harness source is included.
- FFmpeg build container: alpine@sha256:f59abe656b692d901e184be3445e084786602108599d2a51d229c0f5a48c71bf. No container or compiled library is in Git. Existing offline gates are retained as evidence/ffmpeg61-offline-gates.json.
- Firefox source, vendor kernel references, PulseAudio17/musl sources and analysis inputs: URLs/pins are in the relevant reports. Complete fetched code is omitted. The running2018 vendor kernel does not match the retained2017 ASUS source; do not substitute the latter to justify sensor activation.

Synthetic audio/video fixtures, screenshots, traces and ELF/build products remain local. Some historical links point to these intentionally excluded paths. Matching fixture hashes cannot be recreated merely by making similar media; either retain the owner's exact fixtures or qualify new ones and update their contracts explicitly. Do not present a rebuilt image as the already-proved installed image without checking its identity and behavior.

## Code and license boundaries

The archive includes authored source, adapted integration files and focused diffs. It does not vendor full fetched repositories. Existing copyright/SPDX headers remain. overlay/goodix/LICENSE applies to the GPL-derived Goodix/donor adaptations as documented there. licenses/jwm-2.4.6-MIT.txt retains JWM's separate MIT notice. The FFmpeg recipe produces an unpatched decoder-only build and copies its LGPL notices when run. This archive asserts no blanket relicensing over upstream projects or vendor firmware.

Scripts are frozen historical references, not an automatic installer. Packaging assigns ordinary0644 Git modes to avoid accidental direct execution; explicit sh/python execution still performs their actions. Review script preimages, actual geometry, source versions and local private inputs before restoring an executable mode or running a command.
