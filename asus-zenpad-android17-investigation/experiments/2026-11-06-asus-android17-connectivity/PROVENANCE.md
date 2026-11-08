# Provenance and data boundary

All stock inputs come from the already captured
`../2026-11-05-asus-latest-android-feasibility/evidence/device/vendor`.
`evidence/stock-input-manifest.json` records exact source paths, SHA-256 hashes,
sizes, staging paths and intended installation. No new device extraction occurred.
Only the four generic firmware/config files are in the base product. Two ELF32
Bluetooth libraries are retained under `staged/deferred-bluetooth/blobs` as
reference inputs; they are not installed by any product snippet.

The firmware and stock libraries are proprietary ASUS/MediaTek material.
Their presence in an owned device capture does not establish redistribution
permission. Do not publish these blobs as part of a distributable ROM without
appropriate rights. FM firmware, engineering tools, full NVRAM libraries and
unrelated vendor binaries were deliberately not copied into the staging bundle.

Selected ASUS GPL files come from the existing `sources/asus-original/kernel-3.18`
release. See `evidence/local-source-manifest.json`; original notices and `COPYING`
are preserved. Patches and modified versions of those files retain GPLv2 terms.
These selected files are evidence/patch bases, not a buildable replacement tree.

Modern AOSP/Lineage files were read from the existing builder with the SSH options
in `scripts/remote_read.py`. `evidence/remote-files.json` records hashes, and
`evidence/module-availability.txt` records source repository revisions. The three
Bluetooth 1.1 service source files in the device staging directory are copied
unchanged from that source, under Apache-2.0; the isolated Soong module selects
ELF32. AOSP's license is included in `connectivity/LICENSE`. New supplicant
adapter code and scripts use BSD-3-Clause; the passive checker uses Apache-2.0.

No Wi-Fi network list, password, per-device radio calibration, real MAC/BDADDR,
NVRAM partition, or private key was copied into this spike or uploaded anywhere.
The MAC in the host test is a synthetic fixture. The four firmware files are
program/config inputs, not calibration records. `WMT_SOC.cfg` contains antenna
and shared-clock settings; retain the ASUS version, not another tablet's config.

If later device work needs calibration, first identify exactly which record the
selected transport requires. ASUS gen2's `platform.c` actually opens only
`/data/nvram/APCFG/APRDEB/WIFI` on its read path; `WIFI_CUSTOM` is defined there but
not consumed. Preserve that one record on the device or in a device-local backup;
do not upload a whole NVRAM tree. Bluetooth needs its own correct radio record
and a valid local BDADDR. This task has not reverse-engineered or replaced its
record ABI, and does not invent a record layout or mark `service.nvram_init`
ready. Stock userdata is encrypted, so mounting fresh `/data` does not make those
records automatically available.
