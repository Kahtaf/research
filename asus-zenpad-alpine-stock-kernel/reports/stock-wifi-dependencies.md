# Stock Wi-Fi startup dependencies

Status: source and retained-stock-init audit, 2026-11-08. No radio state was changed by this task. Parent is collecting fresh physical evidence. This report deliberately contains no device identifier, network identity, credentials, MAC address or calibration payload.

## Finding

The donor’s absent `wlan0` is consistent with omitting the stock MediaTek userspace initialization and firmware paths. It is not evidence of an absent kernel WLAN driver. The retained ASUS board configuration enables built-in CONSYS_8163, BTIF and Wi-Fi. Preserve those dependencies before considering driver changes.

The smallest useful experiment is the parent’s RAM Alpine chroot using the already running stock radio. It can prove current Alpine applications communicate over this tablet’s Wi-Fi on the actual 3.18 kernel; it cannot prove autonomous Linux radio startup. After that, capture exact stock loader/launcher dependencies and firmware aliases, then test native Alpine supplicant control with Android’s station manager stopped, under a bounded rollback. Avoid reinitializing WMT in the same kernel session: the stock loader is not demonstrably safe to run twice.

## Exact stock startup chain

Paths below are relative to this spike’s parent directory.

| Layer | Evidence | Implication |
|---|---|---|
| Board configuration | `2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18/arch/arm64/configs/asus8163_tb_eg_380_defconfig:250-255` | `CONFIG_MTK_BTIF=y`, `CONFIG_MTK_COMBO=y`, `CONFIG_MTK_COMBO_CHIP_CONSYS_8163=y`, Wi-Fi enabled. Source configuration, not fresh `/proc/config.gz` proof. |
| Load built-in connectivity | `2026-11-06-asus-stock-userdata-recovery/inputs/boot__init.connectivity.rc:47-51` | Root one-shot `/vendor/bin/wmt_loader`. |
| Resident protocol server | Same file `:53-56` | `/vendor/bin/wmt_launcher -p /vendor/firmware/`, user/group system, core class. It must remain alive to serve WMT requests. |
| Character devices | `2026-11-06-asus-stock-userdata-recovery/inputs/boot__ueventd.mt8163.rc:16-20,34` | `/dev/wmtdetect`, `/dev/stpwmt`, `/dev/wmtWifi`, `/dev/stpbt`; stock permissions matter. Standalone no-devtmpfs startup needs real nodes from sysfs device numbers. |
| Power WLAN | `2026-11-06-asus-stock-userdata-recovery/inputs/boot__init.mt8163.rc:1251-1255` | `wlan.driver.status=ok` writes `1` to `/dev/wmtWifi`; `unloaded` writes `0`. |
| Station association | `boot__init.connectivity.rc:107-118` | Stock `/system/bin/wpa_supplicant -iwlan0 -Dnl80211 ...`; disabled until Android requests it. nl80211 is a concrete lead for Alpine wpa_supplicant. No need to reproduce Android framework for a Linux station. |
| IP setup | `boot__init.mt8163.rc:1265` onward | Stock dhcpcd handles wlan0. Standalone Linux needs its own DHCP/DNS lifecycle after association. |

Fresh parent capture `private/live/root-inventory-details.txt` currently shows a running `/vendor/bin/wmt_launcher` and existing WMT/WLAN control nodes, with only unrelated texfat/tntfs modules in `/proc/modules`. Those are physical observations; they do not establish that standalone Alpine can bootstrap the radios. Keep raw capture private.

## Firmware and calibration path contract

Let `K` be `../2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18/drivers/misc/mediatek/connectivity/`.

- `K/common/conn_soc/core/include/wmt_conf.h:33-34` defines `WMT_SOC.cfg` under **`/system/etc/firmware/`**. `core/wmt_conf.c:475-476` constructs that name.
- Stock launcher explicitly searches **`/vendor/firmware/`**. The retained prior radio audit identifies `WMT_SOC.cfg`, `WIFI_RAM_CODE_8163`, `ROMv2_lm_patch_1_0_hdr.bin`, `ROMv2_lm_patch_1_1_hdr.bin`. Verify these against the actual running firmware and its symlinks. Do not replace them with arbitrary linux-firmware blobs.
- `K/wlan/gen2/os/linux/gl_kal.c:796-860` uses direct `filp_open`, including **`/etc/firmware/WIFI_RAM_CODE_` plus runtime chip information** on the MT6628-compatible compile route. A normal Alpine `/lib/firmware` layout alone will miss this contract. The precise compiled path should be checked in the retained running kernel or actual successful stock resolution; GPL source is evidence of a likely contract, not proof of the exact compiled binary.
- `K/wlan/gen2/os/linux/platform.c:124-125` defines **`/data/nvram/APCFG/APRDEB/WIFI`** and `WIFI_CUSTOM`. `:378-411` opens calibration read-only for normal reads; `:442-479` also implements a separate write API. Use original private calibration copies exposed read-only in standalone tests. Do not start the stock NVRAM daemon against factory partitions merely to populate files.
- That kernel also checks `/data/misc/wifi.cfg` and `/data/misc/wifi/wifi.cfg` (`gl_init.c:2888-2896`). Capture any existing stock configuration without publishing private contents.
- Preserve stock aliases between `/etc`, `/system/etc`, `/vendor`, and `/system/vendor` in the eventual Android compatibility subtree. Fresh inventory’s `/system/etc/firmware` listing contains touch/MD32 files, so the WMT/vendor aliases require an explicit read rather than assuming all directories are identical.

Firmware names encode protocol ordering. The prior source audit (`2026-11-06-asus-android17-radio-kernel-port/REPORT.md:23-25`) found sequence 1 in `_1_1_hdr.bin`, sequence 2 in `_1_0_hdr.bin`; filename sort is not the protocol. This is useful protocol knowledge, not a recommendation to reuse the parked 4.9 implementation.

## Why stock userspace is needed before supplicant

`K/common/common_detect/wmt_detect.c:119-138` dispatches chip query and module-init ioctls. `common_detect/drv_init/conn_drv_init.c:41-79` calls common, BT, GPS/FM and WLAN initialization in that order. `conn_soc/linux/pri/wmt_dev.c:1836-1862` exposes kernel commands over the character device; `:1889-1919` applies HIF configuration and `:2111-2159` publishes patch metadata. `conn_soc/linux/pub/wmt_chrdev_wifi.c:376-391` powers Wi-Fi through `mtk_wcn_wmt_func_on` on a `1` write. Merely running wpa_supplicant before this chain cannot produce the missing interface.

The old source-built `p00a-wmt` loader is paired with a changed 4.9 bootstrap, not a validated drop-in for stock 3.18. Prefer the tablet’s original Bionic binaries plus their exact interpreter/shared-library closure first. Check ELF interpreter, `DT_NEEDED`, property-service use, and launch arguments; copying the executables alone into Alpine does not satisfy Android runtime dependencies.

## Bounded next experiment

1. Complete the RAM-chroot shell/TLS/package/SSH workload using existing stock Wi-Fi. Positive: Alpine applications transfer data through wlan0 on this 3.18 kernel. Negative: isolate a userspace/syscall, DNS, route or Android permission failure without touching radio initialization.
2. Read-only inventory: exact vendor firmware paths/hashes, `/vendor/bin/wmt_loader` and `wmt_launcher` ELF interpreter/`DT_NEEDED`, launcher process command line/maps/open FDs, kernel config, existing calibration file metadata/hashes, stock firmware aliases. Keep private payloads/logs under ignored `private/`; record only generic dependencies publicly.
3. Once USB control is reliable and rollback scripts are concrete, a separate bounded experiment may stop Android station control, retain stock WMT launcher/loaded firmware, and use Alpine `wpa_supplicant` against the existing wlan0. Avoid concurrent supplicants. Restore original Android manager on every exit. A successful native association/DHCP/DNS/TLS pass proves Linux station compatibility, still not cold initialization.
4. A later RAM/SD boot tests the original stock loader/launcher and exact firmware path contract without Android framework. That is the independent Wi-Fi startup qualification gate; it is not satisfied by steps 1–3.
