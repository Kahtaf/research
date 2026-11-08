# Camera source-input decision

Pinned Echo Show donor commit: `1381755099398de8b5c09ad2f85023c40ec0ec12` (matching tree and each selected Git blob verified). Its working implementation is an Android11 HAL1 path for a different sensor and tuning. It does not supply OV5670/OV2680 HAL3 constructors or request templates, and its shelved DpIspStream adapter explicitly fails moving the old camera stack's VA buffers through the newer ION-only pipeline. Do not add that shelved module to the ASUS product.

Primary sources: the pinned files in inputs/echo-camera and their exact raw URLs/hashes in evidence/echo-camera-source-pins.json. The ASUS selected-camera report independently shows the fitted sensors' missing static/request constructors, partial COMMON metadata and HAL1 selection. These are distinct findings; the donor does not repair them.

Next implementation unit: extract the exact fitted ASUS sensor tables and execute their unchanged mode-programming bodies in a bounded host register recorder. Compare actual programmed crop/output/HTS/VTS with declared mode and winsize tables, preserving differences. This produces source facts for future metadata work; it cannot establish ISP stream formats, pipeline combinations, lens calibration, exposure/3A results, JPEG bounds or a working HAL3 provider. Never map kernel grab-window dimensions directly into Android stream/active-array metadata without those contracts.

ASUS public source root: 2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18/drivers/misc/mediatek/imgsensor/src/mt8163/{ov5670_mipi_raw,ov2680_mipi_raw}. Both selected names are parent-verified cached stock selections. OV2680B is a separate driver and must not be substituted.

No device operations, private calibration reads, active source mutations or camera enablement occurred. Existing build/kernel/probe bytes remain unchanged.
