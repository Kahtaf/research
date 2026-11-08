# Linux4.9 minimal RAMUSB report collector

Question: can the same bounded collector observe the exact separately built Linux4.9 probe report?

Status: offline profile binding only; no device command, recovery write, boot or physical success. Stock-kernel minimal PID1 trial remains first. The scripts/observe.py bytes are identical to the parent-reviewed stock collector (SHA256 `1d841ddae19394490b3a58b4ef61e6ce24464242af787715daf3b3714a5f0d8b`). Only the separately loaded frozen report contract changes to the public new run ID and compiled 4.9 uname. Original stock probe/collector remains unchanged.

Outputs: evidence/host-acceptance.json derives UUID from the exact probe manifest and uname from pinned compiled headers; source-receipt.json binds these inputs and copied code/tests. The existing25test suite uses a generic release mutation to continue exercising the same rejection on either kernel version.

Continuation: parent checks source-receipt.json and exact candidate/readback, obtains nearby fallback, captures `--baseline-only` while stock Android is running, and uses `--observe --report-via-volume --baseline-receipt <exact-owned-receipt> --seconds 55` with new private output immediately after user selects Recovery. The receipt placeholder is resolved by the parent. This collector has no writer or device reboot command. Only the exact correlated write-protected 65,536-byte RAM disk may be mounted readOnly; only its exact REPORT.TXT is read. This mode does not claim raw FAT verification or a full-media hash. Original raw-read mode remains optional. See the stock collector README for full interface and limits. Never invoke it as a stock 3.18 collector; report versions and UUIDs deliberately differ.

The probe timer begins in PID1; the parent's60-second observation/fallback window begins at actual manual entry. Nominal4.9Powerreset14seconds remains unvalidated; supervise15–20secondPower/NormalBoot fallback and independently verify healthy stockAndroid afterward. No Android17/security/hardware/automaticreturn success is inferred.

## Parent Mac interface-descriptor correction

Actual host inventory repeats descriptor fields on mass-storage driver nubs. The collector now excludes only `IOUSBMassStorageInterfaceNub`/`IOUSBMassStorageDriverNub` from the interface count and requires the sole descriptor to belong to an actual `IOUSBHostInterface`/`IOUSBInterface`. Unknown and duplicate interfaces still refuse. All 28 methods pass for this profile. Current script SHA256 is `776f9f90c748187cbc3e55935a2c8c51a10ae5790500e39d7b22437c08ad16e5`; earlier pins and failed intermediate QA remain historical evidence. See `evidence/interface-fix-pins.json`. This was a host metadata preflight, not a probe boot.
