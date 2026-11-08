# Findings and resolved blockers

These findings are reconstructed from the indexed reports and receipts. “Resolved” below always names a bounded problem; it does not mean that the complete device port worked.

## 1. Physical kernel execution and reporting are separate problems

**Initial symptom:** red-state warning, return to Android, and no expected USB/SD report. Many early interpretations treated that absence as evidence of a kernel boot failure.

**What changed:** stock control boots, exact boot-container inspection, OEM retained-layout analysis and fresh per-run identities calibrated the observation path. The OEM Linux record could be at offset `0xc0`; a writer requiring at least `0x200` silently refused. A before-reset scalar read of 167 followed by a saved zero also showed that a scalar setter/getter pair was not a calibrated cross-reset channel. The adopted text route eventually captured actual 4.9 entry and PID1.

**Result:** physical 4.9 execution is proved. The earlier missing reports cannot retrospectively establish where those earlier kernels stopped.

Useful records: `2026-11-07-asus-stock-entry-linux-offset-control`, its physical trial, `2026-11-07-asus-entry-checkpoint-dt-guard-fix`, and the later calibrated-entry builds/trials in the ledger.

## 2. Boot packaging assumptions needed exact firmware evidence

The exact LK path supports concatenated kernel/DT packaging and supplies runtime initrd bounds. The proposed blanket 2MiB limit was refuted for the inspected successful recovery path; a hypothetical truncation is not an observed physical bound. MTK wrappers, payload-only lengths, Android-v0 geometry, stock boot arguments and runtime DT edits all mattered. Whole-DT equality was unsuitable because LK legitimately changes boot metadata; bounded structural admission replaced it.

**Boundary:** correct static packaging does not establish physical execution. Stock and ported-kernel controls were required. Disabling early UART was one exposure change, not a proven universal root cause.

Useful records: `2026-11-07-asus-stock-initrd-size-premise`, `2026-11-06-asus-full-boot-lk-contract`, and the entry/stock-bootargs controls.

## 3. USB and SD diagnostics initially tested the wrong assumptions

The stock kernel's working gadget contract was legacy `android_usb`, while one RAM reporter tried configfs. A negative stock control exposed the reporter limitation. Intermittent physical USB data and Android authorization also changed transport availability. A stock SD frontend needed the observed major/minor identity; the pinned 4.9 MMC driver reports `removable=0` even for SD media, so an assumed `removable=1` rejected the intended card.

**Result:** these specific reporting/admission assumptions were corrected. They do not establish a fully operational 4.9 USB/SD installation or a qualified offline rescue route.

Useful records: `2026-11-07-asus-stock-legacy-ram-usb-reporter`, `2026-11-07-asus-sd-media-flag-probe`, `2026-11-07-asus-sd-media-flag-core`, and the stock SD controls.

## 4. WebView was an LFS input problem

The selected arm64 WebView source was a 134-byte pointer. The pinned Lineage project was `android_external_chromium-webview_prebuilt_arm64`, commit `5de662a4d42b57a2efe4114e499d38fa3ce41f9d`. Its `.lfsconfig` named the official Lineage LFS endpoint. That endpoint supplied the exact object: 260,835,655 bytes, SHA256 `1d2f61832b2596b0046cb82cf3634609ea866098d097a83fac27c35272ac726a`.

The genuine failing manifest/aapt2 command then exited 0; the pointer retained its original invalid-file reproduction. ZIP CRC and actual metadata checks were separate. Actual image dependency ancestry, rather than all potential installables, bounded which APKs needed materialization.

**Lesson:** a GitHub media 404 did not establish artifact unavailability. Preserve the exact manifest/commit/LFS origin and selected dependency closure. The APK itself is excluded.

Useful records: `2026-11-06-asus-r9-webview-continuation` and `2026-11-06-asus-r9-executable-continuation`.

## 5. Controlled incremental builds did not require manufactured freshness

Siso's per-invocation `.ninja_log` behavior meant missing current rows were not proof an existing output lacked valid lineage. Frozen completed commands/metrics were joined with native command hashes and current output digests. Explicit baseline artifacts were distinguished from actual prior/current executions. No historical input-byte attestation was invented, and successful actions inside a failed overall attempt were not called product success.

**Result:** a bounded controlled-incremental method allowed the product work to proceed without touching timestamps, fabricating rows or forcing a clean build merely to satisfy an accidental log-membership predicate.

Useful records: `2026-11-06-asus-native-cache-premise-review`, the blocked r9 kit and executable continuation.

## 6. Two product problems had small, concrete fixes

**Root property:** Make serialized the nonempty string `false` as boolean true for `PRODUCT_NOT_DEBUGGABLE_IN_USERDEBUG`. Clearing that device setting produced the intended generator boolean and actual raw properties: `ro.debuggable=1`, `ro.secure=1`, `ro.adb.secure=1`.

**Linker namespaces:** actual early startup aborted linkerconfig because of duplicate `heapprofd_client_api.so` providers. A scoped source-ownership/namespace correction made genuine generation succeed. A later enforcing guest trial activated 39 APEXes and exercised Keymaster/Keystore IPC; later ART/odsign also completed in a bounded actual-image run.

**Boundary:** property/namespace tests and guest service progress are not physical tablet boot. A legacy P/FCM3 compatibility declaration eventually passed the selected VINTF check; that experimental declaration does not certify Android17 support on 4.9.

Useful records: `2026-11-06-asus-root-enabled-incremental`, `2026-11-06-asus-r9-linkerconfig-ownership-fix`, `2026-11-06-asus-linux49-historical-vintf`, `2026-11-07-asus-final-image-startup`.

## 7. BPF failures had distinct causes

- A networking fixture lacked `BPF_OBJ_GET_INFO_BY_FD`; ARRAY map create/read/write succeeded while metadata queries failed. The inspected physical source already had that implementation. Fixture parity, not a product source change, was needed there.
- The vendor power-supply filter contained a verifier-rejected backedge. An isolated loop-free implementation preserved the specified packet offsets/fallback and passed verifier/attach plus datagram comparisons.
- The genuine loader later failed `BPF_PROG_LOAD` with E2BIG because it supplied `prog_name` beyond the old kernel's accepted attribute size. A measured-kernel version guard omitted only the unsupported name. A candidate guest run then completed both BPF loaders and started zygotes.

**Boundary:** final-image native library bytes differed from an isolated candidate. Exact installed bytes need their own admission; compiled execution is not runtime qualification. Cross-profile loopback/UID migration limits remained open. Guest display/HWC became another boundary, not proof of physical display failure.

Useful records: `2026-11-07-asus-final-bpf-loader-gap`, `2026-11-07-asus-linux49-power-supply-filter`, `2026-11-07-asus-vendor-bpf-load-compat`, `2026-11-07-asus-bpf-name-product-build`.

## 8. Peripheral source work did not equal functioning peripherals

**Audio:** ALSA `.copy` returns status, not partial frame counts. The three-file repair fixed that contract. Stock speaker topology uses a GPIO28 gate; the combined AW8737S path used GPIO24 and lacked required DT timing. Lifetime/suspend defects in a proposed GPIO28 port were found and repaired, then compiled. Electrical identity, routing and microphone calibration remained unqualified.

**Sensors:** an accelerometer-only BMC156 kernel/HAL path and matching event ABI compiled. Full sensor coverage and physical calibration were not proved.

**Camera:** SDK37 rejection of HAL1, metadata/GraphicBuffer/PropertyMap contracts, recursive provider closure, nonuniform kernel enum changes and ARM32 compat ioctl layouts all remained material. A PropertyMap adapter linked, but the first ARM32 importer rewrite corrupted packed relocation targets and symbol-section associations; the rewrite was repaired for static packaging only. No camera operation was established.

Useful records include the audio-copy repair, GPIO28 lifecycle/full-kernel handoffs, BMC156 stages, camera ABI ledgers and PropertyMap repair.

## 9. Rescue and private preservation stayed independent gates

Restoring SYSTEM/BOOT after internal userdata provisioning is not a complete stock rollback. Exact OEM evidence supported whole-p20 reset behavior, no-op wipe hooks and unchecked erase failures. The stale BCB wipe request needed explicit reconciliation before another recovery implementation could be treated as harmless. Host receipt uncertainty, expiry enforcement and write/cleanup failures were independently reviewed; software guard tests did not commission real recovery.

Original stock images were preserved on the owner's Mac and rehashed before cloud deletion. Existing factory/NVRAM/calibration backups also stay local. **Neither their mere existence nor two radio backups prove calibration completeness.** No raw private payload belongs in this public archive.

## 10. The final delay lead remains a lead

The minimal-platform run retained PID1/normal scheduler/compute-begin, followed by two deferred thermal-probe messages. The budget descendant preserved helper/config/DT/bootargs and added a fail-stop after 2^24 completed continuing iterations of one `__delay` invocation. No exhaustion/panic/compute-end/timer record appeared; stock return was independently verified.

Cached CPU0 PC moved from minimal `__delay+0x44` to budget `__delay+0x54`; the corresponding frame grew by 0x20 and saved SP moved by 0x20. This supports build correlation but not a proven last instruction, caller or firmware latch epoch. The old location is a workaround-key comparison; the new one is a key load, not itself a counter MRS.

The bounded offline review found the OOL key and pointer, a 200-pair-bounded FSL CNTVCT accessor and a one-read A76 workaround. No hidden unbounded MMIO accessor was found on that route. Runtime key and firmware CNTVOFF/latch state were not established. A physical-counter pin would still change the register even with a zero key; treating it as a no-op was rejected. Another blind clock change was not admitted.
