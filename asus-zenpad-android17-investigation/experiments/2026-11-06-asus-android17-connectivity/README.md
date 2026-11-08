# ASUS Z380M / P00A_2 Android 17 connectivity

Question: can we close practical Wi-Fi/Bluetooth integration for the current
Linux 4.9 / Android 17 product without reusing the entire Android 7 HAL stack?

Status: **bounded staging delivered; radio activation blocked by missing kernel
transport**. The real kernel at `717bb3c9e13ce573cfdd2dda856debd27a0fa17f`
contains adapter/BTIF support but no WMT/STP/WLAN implementations or modules.
No VM writes/builds, device operations, flashing, cloud changes or other agents'
files were touched. Stock Wi-Fi internet/BT discovery are prior evidence; no
new-kernel radio behavior has been proved.

## Integrate now

Copy `staged/device/asus/p00a/connectivity` into the platform after the current
build. Inherit its `connectivity-base.mk`; merge its ueventd fragment into the
existing device ueventd input. This installs four hashed stock firmware/config
files and a passive preflight binary, and creates the current Wi-Fi data dirs.
It does not enable the radios or install the old Bluetooth stack.

Build on the existing **Linux** builder, after parent integration:

```
m p00a-connectivity-check lib_driver_cmd_p00a android.hardware.bluetooth@1.1-service.p00a
```

These are build targets, not commands run in this task. The adapter and bridge
still need real target compilation. The Bluetooth bridge is explicitly ELF32
and uses the current platform's legacy vendor interface.

## Staged for the next gates

- `wifi-sta-trial.mk` plus `BoardConfig-connectivity.mk`: current AIDL supplicant,
  STA-only config and an overlay selecting the vendor supplicant. Current
  framework supports `wlan0` without an IWifi vendor HAL. **WMT and wlan0 must
  exist before wificond starts**; the base product does not create them.
- `src/driver_cmd_p00a.c`: minimal MACADDR support using the actual current
  supplicant interface. Other private extensions return unsupported. This avoids
  the real ASUS-inline-buffer versus Android-pointer-buffer ioctl mismatch.
- `staged/patches`: firmware path and BT 32/64-bit compat ioctl fixes against the
  captured ASUS GPL source, with patched source copies. These are **not** a 4.9
  transport port and do not apply to files absent from the current kernel.
- `staged/deferred-bluetooth`: hashed ELF32 reference inputs and disabled
  service/manifest templates. Stock libnvram's removed fs_mgr APIs and an
  unimplemented BT PSM ioctl remain unresolved. No success shim is supplied.
- `evidence/module-manifest.json`: actual missing transport components; it does
  not invent .ko files or a modules.load order.

## Checks and continuation

Run `python3 scripts/verify_staging.py` for offline validation. Current checks
pass: hashes, copy paths, XML, two patch dry-runs, host compilation of the passive
checker, and sanitized adapter behavior tests. Tests use mocks for Linux helper
calls; neither a target build nor hardware success is claimed.

Read [REPORT.md](REPORT.md) for exact source paths, module availability, ABI
findings, integration gates and device-only tests. Read [PROVENANCE.md](PROVENANCE.md)
before using or distributing blobs. No per-device calibration or credentials are
included; preserve necessary radio records on the device only.

First continuation: integrate/build the missing compatible 4.9 MT8163 WMT/STP
and gen2 WLAN transport, then resolve WMT launcher and calibration prerequisites.
Only then activate the STA trial. Bluetooth additionally requires a real NVRAM
ABI solution, valid device-local BDADDR and matching ioctl support. Parent owns
all Linux builds, live integration and decisions about physical testing.

`scripts/remote_read.py` and `capture_kernel_gate.py` document the exact verified
SSH options and perform read-only capture only. Source hashes and revisions are
under `evidence/`. The ready-to-review tarball under `artifacts/` contains the
device staging subtree, patches and key evidence; deferred Bluetooth blobs and
captured source snapshots remain in this local spike, outside the tarball.
