# ASUS authenticated Wi-Fi ADB APK

Question: Can a small explicit-tap app use the exact previously ADB-tested on-demand binary to enable authenticated Wi-Fi ADB on the owner's stock ASUS P00A_2 Android 7 tablet without USB data or terminal input?

Status: **Actual signed APK built and packaging verified. App-context rooting remains unproved. No device, emulator, root, ADB, hosting-server, parent-build, or Termux operation was performed.**

## Outputs

- `artifacts/asus-wifi-adb-development.apk`: 57,876-byte development-signed installable APK, package `com.kahtaf.asuswifisetup`, version 1.0 (1).
- `source/com/kahtaf/asuswifisetup/MainActivity.java`: plain programmatic Android Activity; no third-party libraries.
- `AndroidManifest.xml`: minSDK 24, targetSDK 24, no permissions, no backup, non-debuggable; launcher Activity only.
- `assets/mtk-su64` and `assets/root-actions.sh`: byte-identical copies of the originals in the existing local Wi-Fi setup spike.
- `evidence/verification.json`, `apksigner.txt`, `manifest-badging.txt`, `manifest-tree.txt`: actual package/signature/manifest/assets results. SDK24 APK Signature Scheme v2 verification passed; v1 signature entries are also present. The verifier skips v1 validation when verifying platforms starting at SDK24.
- `artifacts/SHA256SUMS`: exact APK and original asset hashes.
- `HANDOFF.md`: short parent continuation instructions.

## Behavior and limits

Install/open only draws the UI. The single **Enable Wi-Fi debugging** button starts a worker; lifecycle callbacks only refresh displayed text. No services, receivers, automatic retries, network permission, analytics, uploads, or external storage are used.

Before execution, the Activity reads exact stock serial `DEVICE_SERIAL_REDACTED`, device `P00A_2`, SDK `24`, fingerprint `asus/WW_P00A/P00A_2:7.0/NRD90M/WW_P00A-V5.3.20-20180809:user/release-keys`, `ro.adb.secure=1` and `getenforce=Enforcing`. Any mismatch/read failure refuses execution. If both ADB port properties already read 5555 with those checks satisfied, it reports already configured without root.

Embedded binary and script SHA-256 are checked. The binary is copied into an app-private directory and file, both chmod 0700; the on-disk binary is checked again. A second immediate preflight also avoids execution if already configured. A create-exclusive, synced app-private attempt sentinel is written before process launch. A process-wide atomic guard and this never-automatically-cleared sentinel prevent concurrent and repeated root attempts, including after recreation/process death. Keep app data intact after an uncertain result; clearing data or uninstalling removes this protection.

Execution is exactly the copied `mtk-su64 -c /system/bin/sh` with the unchanged 447-byte root script on stdin. Environment removes LD_PRELOAD/LD_LIBRARY_PATH and uses system PATH. The script verifies root/serial/device/secure ADB, sets the two port properties to 5555, restarts only adbd, and traps restoration with `/system/bin/setenforce 1`. It contains no loops, downloads, flashing, boot/system writes, root daemon, or Magisk installation.

The app waits up to 60 seconds for the native process and captures at most 24 KiB of merged output, draining excess without retaining it. A timed-out native process is left alive to allow its restoration trap to finish; completion/state are explicitly uncertain and no retry is allowed. This is a bounded wait, not a guarantee that the native exploit itself terminates. Short read-only property/IP commands have 3-second waits. After any reserved root attempt the app independently reads SELinux and ADB properties. A success message requires process exit 0 and exact device/secure/Enforcing/5555 readback. It shows wlan0 IPv4 if readable and directs the owner to accept the recognized Mac RSA prompt. It does not claim network reachability, RSA acceptance, or successful app-context rooting merely from building/installing.

## Build and continuation

Only this isolated builder prefix was created: `/srv/android/asus-wifi-adb-apk-20261107`. Existing SDK37 `android.jar`, aapt2, zipalign, D8 9.1.11-dev, apksigner jar and JDK21 were read in place through the fixed existing `remote.py` helper. Java compilation, single-worker D8, packaging and signing are serial with one-CPU affinity and a 256 MiB Java heap. No AOSP/Soong/kernel build or parent-job control was used.

`scripts/build.py` is the small build/package/check recipe. `scripts/remote-build.py` uploads only this spike's source/assets and retrieves only the APK and public evidence through the fixed helper. A fresh run refuses an existing prefix; `--resume` rebuilds only this spike; `--verify-existing` only verifies the existing signed APK. These commands do not operate the tablet. `evidence/build-note.txt` records compatibility fixes needed for existing in-tree tool layouts.

The disposable DEVELOPMENT PKCS12 key and generated password remain only under the builder spike's `private/` directory (0700; files 0600). `.gitignore` includes `/private/`, and `git check-ignore private/development.p12` was checked before generation. No key or password contents were logged or retrieved. The key is not a user credential; this is not a production signing identity.

Parent: serve the local APK via the already-existing LAN server only in the parent workflow, then have the owner manually install/open/tap once. Do not run concurrently with the pending Termux route. If the app reports uncertainty, retain its data and assess SELinux/ADB state before any further attempt. This implementation spike does not host, install, or execute the APK.
