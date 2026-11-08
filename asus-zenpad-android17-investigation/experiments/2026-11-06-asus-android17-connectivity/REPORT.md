# Connectivity findings and integration gates

The current kernel cannot provide either radio: it has MT8163 adapter/BTIF
support but no WMT/STP or WLAN implementation. There is a credible next route
through a matching 4.9 MTK transport plus source-built modern userspace. There
is no credible claim that firmware copies or an Android 7 HAL alone close it.
The base bundle is integratable now; radio activation remains blocked.

## Kernel and firmware evidence

The read-only audit pinned
`/srv/android/asus-android17/kernel-bpf-fd` at
`717bb3c9e13ce573cfdd2dda856debd27a0fa17f` and checked the real build's
`.config` and `System.map`. `evidence/kernel-gate.json` contains the hashes and
exact results. All six checked transport/driver symbols are absent, all five
implementation filenames are absent, and no `.ko` files were found in that
build. `CONFIG_MTK_COMBO_WIFI=y`, `CONFIG_MTK_COMBO_BT=y` and `CONFIG_MTK_BTIF=y`
do not change that. The actual connectivity Makefile says “move to standalone
repo” and builds only `connadp`. `wmt_export_platform_bridge_register` and BTIF
exports are present; these are the boundary to which missing transport code
would attach. No remote source or build was changed.

The ASUS target is `CONSYS_8163`, not a justified identification as a discrete
MT6630 card. The original ASUS defconfig selects it; `wlan/Makefile` selects
`gen2`, whose Makefile defines the historical `MT6628` compatibility macro while
using `os/linux/hif/ahb`. STP's MT8163 transport is BTIF. Neither that macro,
FM firmware named `mt6627`, nor the stock GPS property naming `MT6625L` proves
the physical analog-die revision. The published WMT driver distinguishes
analog die IDs at runtime; no new kernel query was made here.

The captured inputs are `WIFI_RAM_CODE_8163`, `WMT_SOC.cfg`, and both
`ROMv2_lm_patch_1_{0,1}_hdr.bin` patches. They are staged with hashes; do not
arbitrarily select one ROM patch. WMT's launcher/driver protocol selects and
orders patch metadata. `wmt_ic_soc.c:965` explicitly asks the launcher to search
patch information. Stock init runs `wmt_loader`, then a resident `wmt_launcher
-p /vendor/firmware/`; neither executable is present in the captured vendor/bin
files. Their matching source/binary dependency closure remains needed.

Reference paths below are under
`sources/asus-gpl/kernel-3.18/drivers/misc/mediatek/connectivity/` unless marked
otherwise. Their snapshots and hashes are included.

| Interface | Source evidence | Implication |
| --- | --- | --- |
| `/dev/stpwmt` | `common/conn_soc/linux/pri/wmt_dev.c:1783` onward | Poll/read kernel command strings; write `ok` only after actually handling the command. A dummy daemon acknowledging commands is invalid. |
| WMT ioctl family `0xa0` | Same file, definitions at 72–88; implementation at 1869 onward | STP/HIF mode (5), chip info (12), patch count (14), patch info (15), query chip ID (22). Several `_IOW` requests use scalar `arg`, not a pointer. |
| WMT 32-bit compat | Same file, 2227 onward | Pointer-sized request numbers have explicit translations; preserve these if using an ELF32 launcher. |
| `/dev/wmtWifi` | `common/conn_soc/linux/pub/wmt_chrdev_wifi.c:317` | Character writes `1`/`0` power Wi-Fi; `S`/`P`/`A` request STA/P2P/AP modes. Not a firmware-path sysfs node. |
| `wlan0`, cfg80211 | `wlan/gen2/os/linux/gl_init.c`; `wlan/gen2/Makefile` | Requires the actual gen2 WLAN driver and AHB platform integration, not just cfg80211. |
| Private Wi-Fi ioctl | `wlan/gen2/os/linux/gl_wext_priv.c:300–315,2814` | `SIOCDEVPRIVATE+1` expects `char buf[512]; int used_len; int total_len`. The generic Android helper has `char *buf` instead. Several familiar command handlers are compiled out under `#if 0`; do not silently forward them. |
| `/dev/stpbt` | `common/conn_soc/linux/pub/stp_chrdev_bt.c:168–396` | `open` powers BT via WMT and requires STP ready; read/write carry the BT channel; close powers it off. Merely opening this node is not a passive probe. |
| BT ioctl family `0xb0` | Same file, 48–52 and 283 onward | Published HW/FW requests contain `sizeof(void*)`; existing compat handler simply forwards numbers. ELF32 numbers do not match ARM64 native definitions. |

The staged firmware-path patch redirects original GPL WMT and WLAN fixed file
lookups to `/vendor/firmware/`. A kernel command-line `firmware_class.path` alone
cannot fix these direct `filp_open` paths. The second patch translates the three
known pointer-width-sensitive BT compat requests. Both patches apply cleanly to
the captured original GPL files. They **cannot apply to today's 4.9 tree**, which
has no corresponding files. They are carry-forward patches for a transport port,
not a completed kernel port or a proven compile.

An additional real gap remains: the captured ELF32 `libbluetooth_mtk.so` issues
ioctl **0xc001b001**, with a scalar enable argument, in `mtk_set_psm_control`.
See `evidence/bt-psm-disassembly.txt`. The published ASUS BT switch has no case for
it. The native HW-version opcode is different despite sharing command number 1.
Neither staged patch accepts it or returns fake success. Match the shipping
transport's PSM semantics before enabling the stock vendor library.

## Exact Android 17 userspace route

Source was inspected at `/srv/android/lineage24`; repository revisions are in
`evidence/module-availability.txt`, and exact module-definition paths are in
`evidence/platform-module-index.json`. The important current modules are:

| Module | Current source result |
| --- | --- |
| `wpa_supplicant` | Present in `external/wpa_supplicant_8`; vendor binary is `/vendor/bin/hw/wpa_supplicant`, AIDL `ISupplicant/default`, V5 NDK, own VINTF fragment. |
| `wificond` | Present in `system/connectivity/wificond`. |
| `android.hardware.wifi-service` | Present, AIDL V4 service backed by `libwifi-hal`. |
| `android.hardware.wifi@1.0-service` | Not defined in the scanned current source. HIDL interface folders do not imply a legacy service implementation. |
| `libwifi-hal-mediatek`, `lib_driver_cmd_mt66xx` | Not defined. Copying the karnak BoardConfig would request missing modules. |
| `libwifi-hal-fallback` | Present, but its `init_wifi_vendor_hal_func_table` returns `WIFI_ERROR_NOT_SUPPORTED`; it is not a functional vendor HAL. |
| `android.hardware.bluetooth@1.0-impl`, `@1.0-service`, `@1.1-service` | Present. The implementation loads `libbt-vendor.so` and `BLUETOOTH_VENDOR_LIB_INTERFACE`, not stock `bluetooth.default.so`. |
| `android.hardware.bluetooth-service.default` | Present as an AIDL reference implementation. It is not a wrapper for MTK's vendor library; direct H4 access does not perform MTK NVRAM/preload initialization. |
| `libbt-vendor` | A Broadcom implementation is present. It is not an MTK provider. |

Wi-Fi's current `WifiNative.java:736` skips vendor HAL startup if none is
supported; `createStaIface` uses `wifi.interface`/`wlan0` through the non-vendor-HAL
path. At `setupInterfaceForClientInScanMode:1633`, wificond/nl80211 setup occurs
**before supplicant startup**. Powering the WLAN driver only inside a supplicant
wrapper would therefore be too late. For the first STA trial, establish WMT and
`wlan0` before enabling Wi-Fi in the framework. Keep that netdev present across
framework toggles for this bounded trial; a full power lifecycle is later work.

`wifi-sta-trial.mk`, its BoardConfig include, and `P00aWifiBringupOverlay` prepare
that path. They install the current AIDL supplicant and keep mainline supplicant
selection off using the actual `config_wifiMainlineSupplicantEnabled` resource
(`MainlineSupplicantAidlManager.isServiceAvailable`). Do not declare/install an
IWifi vendor service. The new `lib_driver_cmd_p00a` supplies the five exact current
private-driver function signatures. It implements MACADDR using the current
Linux helper and rejects other private extensions, including AP/P2P operations.
It does not translate the incompatible generic private ioctl or assert feature
support. Standard scan/association/key traffic remains on nl80211. Country-code,
optional private-extension failures and usable STA behavior still need the
Linux build and physical tests. This is a bounded bring-up route, not feature
parity or proof that all modern nl80211 requests fit the legacy driver.

Bluetooth's current `hci_hal_impl_android.cc:212–215` explicitly tries AIDL then
HIDL; `hci_backend_hidl.cc` tries 1.1 then 1.0. The source-built
`android.hardware.bluetooth@1.1-service.p00a` duplicates the current service
source unchanged but selects `compile_multilib: "32"`. Its dependencies use the
current `@1.0-impl` bridge. It can be built separately for review; it is not
installed by the base product. This clears the obvious ELF32/ELF64 loader mismatch
without installing the Android 7 Bluetooth stack.

The captured `libbt-vendor.so` exports the expected 16-byte ARM32 interface object
and depends on `libbluetooth_mtk.so`; that library depends on `libnvram.so`.
`evidence/bt-elf-dependencies.json` records the actual imports. Stock libnvram
requires `fs_mgr_read_fstab`, `fs_mgr_get_entry_for_mount_point`, and
`fs_mgr_free_fstab`. A scan of the actual **system/fs/fs_mgr** source finds only
old names in a test name/comment, no implementations. This is an actual private
userspace ABI gap, not a reason to disable ELF checks. No fake libnvram or fs_mgr
shim was made. Resolve a narrow, correctly specified BT-record provider or an
isolated verified legacy dependency closure before installing those libraries.
The bridge additionally requires a valid device-local BDADDR before vendor init;
it fatally rejects a missing address. Do not fabricate a shared MAC or bypass
NVRAM initialization.

## What was checked and what remains

`python3 scripts/verify_staging.py` passes: all captured/staged input hashes,
product-copy paths, XML parsing, both patch applicability checks, native host
checker compilation, expected missing-driver failure, and ASan/UBSan host tests
for MAC query/error/truncation/unsupported behavior. The five adapter declarations
match the captured current header. Host adapter tests use explicit mock headers;
they are behavioral checks, **not** Android ABI/build proof. No target compilation,
Mac kernel build, VM build, boot, device access, or radio tests occurred.

After the current build, parent can copy `staged/device/asus/p00a/connectivity`
into the platform, inherit `connectivity-base.mk`, and merge the ueventd fragment
into the existing input. That adds generic firmware and passive preflight only.
Build `p00a-connectivity-check`, `lib_driver_cmd_p00a`, and the optional ELF32
Bluetooth bridge on the real Linux builder. Keep strict ELF checks. Existing
product namespaces/32-bit support, SELinux labels, directory permissions and
VINTF integration must be validated in that build; no broad permissive policy is
provided here.

The **first blocker** to radio operation is still the absent 4.9 WMT/STP/WLAN
transport source and resulting devices. Obtain/integrate a compatible standalone
MT8163 transport or port the supplied GPL implementation into a separate kernel
revision. The `module-manifest.json` names reference Kbuild objects only; no
stock 3.18 module is suitable for the 4.9 image. Next resolve the matching WMT
loader/launcher, firmware selection, device-local calibration and BT ABI gaps.

Physical tests, only when the parent authorizes them: verify WMT chip/firmware
selection and nodes; power Wi-Fi and confirm nl80211 phy plus `wlan0`; confirm
AIDL supplicant registration, foreground scan, a deliberately entered test
network, DHCP/DNS/internet and Wi-Fi toggles; then verify ELF32 BT dependency
loading, FW_CFG callback, HCI reset, discovery/pairing, BT off/on and coexistence.
Collect errors without credentials or full NVRAM dumps. Stock Wi-Fi internet and
BT discovery are pre-existing evidence only; none demonstrate the new kernel.
