# Concrete ABI ledger and implementation gates

Companion to [CAMERA-ROUTE.md](CAMERA-ROUTE.md). Addresses and sizes below are static inspection/compile results, not observations from opened hardware.

## C camera module/device boundary

The ARM64 [probe source](../fixture/camera_abi_probe.c) was compiled using frozen transitive SDK37 headers, Clang r584948b / Android build 14863223 / LLVM `2d65e4108033380e6fe8e08b1f1826cd2bfb0c99`, target `aarch64-linux-android37`. It linked against actual frozen SDK37 `libcamera_metadata.so`, `libc.so`, and CRT objects with `--no-undefined`; [commands](../evidence/compile.json), [66 input pins](../evidence/input-pins.json), [artifact hashes](../evidence/compile-artifacts.json), [ELF/offset output](../evidence/abi-compile.txt). Its sole function calls genuine `validate_camera_metadata_structure`; it was not executed. It contains no HAL, fake callback, device opener, or successful-camera stub.

| SDK37 ARM64 type/member | Compiled bytes/offset |
|---|---:|
| `sizeof(hw_module_t)` / `sizeof(hw_device_t)` | 248 / 120 |
| `sizeof(camera_module_t)` / `sizeof(camera_info)` | 344 / 48 |
| module `methods` | 32 |
| module number/info/callback/vendor-tags functions | 248 / 256 / 264 / 272 |
| module `open_legacy` / torch / init | 280 / 288 / 296 |
| `sizeof(camera_device_t)` / HAL1 ops | 136 / 184 |
| `sizeof(camera3_device_t)` / ops offset / priv offset | 136 / 120 / 128 |
| `sizeof(camera3_device_ops_t)` | 128 |
| initialize / configure / default request / process request / dump / flush offsets | 0 / 8 / 24 / 32 / 48 / 56 |
| stream / stream-config / stream-buffer | 96 / 32 / 32 |
| capture-request / capture-result / callbacks | 64 / 64 / 32 |

OEM module initializer writes standard fields at those offsets. It initializes `HMI.common.module_api_version=0x204`, `hal_api_version=0x100`, sets `open_legacy` at `0x118`, torch at `0x120`, init null at `0x128`, and carries OEM extension data after the standard 344-byte prefix. Its `HMI` symbol occupies 360 bytes and resides in BSS; the dynamic initializer, not an on-disk BSS dump, supplies values. Standard C prefix compatibility is supported by this evidence; private suffix compatibility is not needed by the upstream wrapper and is not assumed.

OEM `libcam.device3.so` has a real 3.2 `hw_device_t` template at `0x10b30`: tag `0x48574454`, version `0x302`. Ops template at `0x10ba8`: initialize `0xc420`, configure `0xc440`, register buffers null, construct-default-settings `0xc460`, process-capture `0xc480`, vendor-tag query null, dump `0xc4a0`, flush `0xc4bc`. Close is `0xc404` in the common device template. These entries dispatch into real C++ device methods. Null deprecated buffer registration/vendor-tag device slots are not equivalent to missing process-capture implementation. No inference of valid hardware results follows from non-null slots.

Camera3 structs contain versioned fields. A 3.2 device must not read newer request/result tails as though it were 3.5/3.6. The current HIDL bridge branches on `mDeviceVersion`; this is one reason to retain the truthful 3.2 version and upstream adapter. Do not copy a modern struct wholesale into an old private MTK object. Further stream layout/native-handle/vendor-metadata agreement still needs validation.

## ELF closure and exact unresolved contracts

[dependency-audit.json](../evidence/dependency-audit.json) records 64 ARM64 public vendor ELFs, 22,886,792 bytes inspected, including explicit dynamic seeds `libcam_platform.so`, `libcam.device1.so`, `libcam.device3.so`. It walks vendor DT_NEEDED recursively, parses real dynamic exports/imports (including Bionic IFUNC symbols), and compares with 22 found current provider libraries out of 30 attempted providers. Every found modern library is copied into the owned fixture and hashed; no active output is changed.

The direct module and device3 imports resolve in this **optimistic union**. The entire vendor closure does not: the receipt reports 40 distinct unresolved names, spanning the families below. Union resolution does not prove DT_NEEDED/namespace visibility, ELF symbol-version compatibility, vtable shape, object size, callbacks, or runtime behavior. It is a lower bound on work, never an ELF loadability pass.

| Import family, exact examples | Importing libraries / next action |
|---|---|
| `_ZN7android13GraphicBufferC1Ejjij`, `_ZN7android13GraphicBufferC1EjjijjP13native_handleb`, `_ZN7android13GraphicBuffer4lockEjPPv` | `libcam_utils`, `libcam.client`, `libmtk_mmutils`. Old ctor/lock signatures are not in the found SDK37 providers. Current `GraphicBuffer.h` changes usage/layer/ownership/requestor contracts. Inventory allocation size, inline field offsets, RefBase/base layout, ownership and mapper handling before implementing a source compatibility boundary. A forwarding constructor symbol alone can corrupt memory. |
| `_ZN7android19GraphicBufferMapper6unlockEPK13native_handle` | `libcam.client`, `libmtk_mmutils`. Current unlock/fence signature and imported handle ownership require a real translation. |
| `PropertyMap::{C1,D1,addProperty,clear,hasProperty,tryGetProperty}` with `String8` | `libcam_utils`. Locate/rebuild an ABI-correct private source implementation, or replace the importing functionality. Moving exports between modern libraries does not prove old object layout. Do not replace libutils. |
| `String8::setPathName(char const*)`, `String8::getBasePath() const` | `libcam.client`, `libcam.camadapter`. Reimplement exact path semantics with current safe ownership, if layout is demonstrated. |
| `SensorManager` / `SensorEventQueue` methods | `libcam.utils.sensorlistener`. SDK37 declarations now live under `frameworks/native/libs/sensor/include/sensor/`; some signatures still exist, so this may partly require a real `libsensor` dependency instead of old `libgui` placement. Resolve exact exports/version and event struct lifetime before deciding which source adaptation is needed. |
| `fs_mgr_read_fstab`, `fs_mgr_get_entry_for_mount_point`, `fs_mgr_free_fstab` | `libnvram`. Old fstab C struct ownership/layout is a separate dependency. No private NVRAM values were accessed. Do not bring up a default-writing daemon or fake successful NVRAM operations to make cameras load. |
| ASUS/Arcsoft HDR, beauty, night, stabilization, face entry points | Old image-processing dependencies are pulled in even when initially interested in HAL3: `libcam_platform` DT_NEEDED also loads device1 and its pipeline. Later static inspection located the five named Arcsoft libraries in public SYSTEM `/lib64`, so these are **not missing OEM donor binaries**. Their SDK37 compatibility is unproved. `libarcsoftFace.so` adds `libcameraap.so`, whose own closure is not completed here. |

Public-system follow-up inspected five Arcsoft libraries plus the small old `libstdc++.so` for analysis only, total 1,484,632 bytes; all temporary bytes were discarded. [Hashes/dependencies](../evidence/public-system-leaves.json), [exports](../evidence/final-edges.txt). These suppliers were not retroactively counted as SDK37-compatible providers in the union result. `libfs_mgr`, `libnativehelper`, `libstdc++` also lacked the exact current artifacts at checked paths; missing current build products are not proof of absent source. Old system runtime libraries are not a deployment recommendation.

A complete next closure must include `libcameraap`, every dynamically loaded sensor/pipeline/metadata factory, ELF version requirements, and namespaces. It must distinguish proprietary camera libraries stored under old `/system/lib64` from generic Android runtime libraries, which must remain SDK37. ARM32 requires its own complete check. The frozen existing graphics adaptation may provide useful source, but successful display gralloc operation would not prove MTK camera `GraphicBuffer`/ION ABI compatibility.

## Kernel boundary: concrete incompatibility independent of CameraService choice

[Header pins](../evidence/kernel-header-comparison.json) and [diff](../evidence/kernel-header-diff.txt) compare eight actual OEM 3.18 and current 4.9 headers. File inequality alone is not considered an ABI break: much of the diff is comments, formatting or typedef→struct changes. The following concrete contracts do matter.

### Image sensor control

The inspected 4.9 `kd_imgsensor_define.h` selects `kd_imgsensor_define_default.h` except for `CONFIG_CHECKERS`. The evidence and compiled witnesses concern that **default** branch; they are not evidence about a checkers product. Fitted camera drivers remain disabled in the inherited combined configuration.

The OEM FeatureId enum starts at 3000. Current default inserts `SENSOR_FEATURE_SET_DUAL_GAIN` at 3007 and inserts additional entries later. Both enum bodies were extracted from the real headers and compiled as separate translation units against frozen SDK37 includes, with static assertions for the values below. [Full mapping](../evidence/sensor-feature-enums.json), [compile commands](../evidence/enum-compiles.json), [OEM witness](../fixture/enum_oem.c), [4.9 witness](../fixture/enum_kernel49.c).

| Feature | OEM numeric ID | 4.9 default ID |
|---|---:|---:|
| SET_ESHUTTER | 3004 | 3004 |
| SET_GAIN | 3006 | 3006 |
| CHECK_SENSOR_ID | 3040 | 3041 |
| GET_DEFAULT_FRAME_RATE_BY_SCENARIO | 3058 | 3059 |
| GET_CROP_INFO | 3080 | 3081 |
| SET_ISO | 3090 | 3092 |

**Do not use an arithmetic offset.** Exact next source delta: in an owned copy of `drivers/misc/mediatek/imgsensor/src/mt8163/kd_sensorlist.c`, adapt the external `CAMERA_HW_Ioctl` (`KDIMGSENSORIOC_X_FEATURECONCTROL`) and `CAMERA_HW_Ioctl_Compat` entry paths to parse a pinned OEM UAPI, validate arguments, explicitly map the OEM FeatureId to internal enums, and marshal any feature-specific pointer/payload layouts. Internal driver calls keep current enums. The verified current source hash is `39585775078b6d9aab5ee8e61b35d4d1b225b4277038e73d557035708cc2e060`. This is a proposed source change, not one made here. Reject unknown commands; add bounded pure-memory tests for command translation and lengths before kernel compile.

Both versions' feature-control struct have InvokeCamera, enum FeatureId and two user pointers; similar outer layout does not repair different enum semantics or nested payloads. Preserve native/compat pointer handling and copy-back lengths. Also audit GETINFO, CONTROL, GETRESOLUTION2, sensor-index and scenario enums; this research does not certify them.

### Calibration request ABI (public declarations only)

OEM `cam_cal_define.h` has `u4Offset`, `u4Length`, `sensorID`, pointer. Current 4.9 adds `deviceID` before the pointer. On AArch64 the added field occupies what was padding (pointer offset remains 16, total 24); on 32-bit the pointer moves 12→16 and total 16→20. Thus identical 64-bit ioctl size would still hide a changed meaning, and the compat request size changes. These layout values follow the shown types/alignment, not a camera calibration read. [OEM header](../fixture/oem-kernel/drivers/misc/mediatek/cam_cal/inc/cam_cal_define.h), [4.9 header](../fixture/sdk37/kernel/asus/p00a-fd/drivers/misc/mediatek/cam_cal/inc/cam_cal_define.h).

`CAM_CALIOC_G_READ` uses magic `'i'`, nr 5, size of that struct. Before any integration, provide explicit old/new native and compat request handling with validated offset/length and correct sensor→device routing. Never interpret old padding as a valid device ID. No per-unit payload, OTP, preserved data or key material was opened by this study.

### ISP, DMA, ION/M4U, power

- Both `cameraisp/src/mt8163/inc/camera_isp.h` and `_FrmB.h` are retained. Register I/O, wait/read/clear IRQ, RT buffer control, ref-count and sensor-clock ioctls contain pointers or `unsigned long`; review native and compat structures separately. The two ISP variants are not interchangeable based on names. `ISP_REG_IO_STRUCT` contains a register-array pointer and count; `ISP_BUFFER_CTRL_STRUCT` has nested buffer pointers. Do not route these blindly through a generic compat ioctl.
- Actual current ION paths are `drivers/staging/android/ion/mtk/{mtk_ion.h,ion_drv.h}`, not the initially tested `drivers/misc/mediatek/ion/mtk/ion_drv.h`. Final receipt pins these exact sources. Audit MM configure-buffer, cache-sync/get-physical, handle/pointer unions, DMA-BUF FD lifetime, M4U port IDs and address-width/cache coherency against `libcamdrv`, `libcamdrv_FrmB`, `libion_mtk` and the qualified graphics stack. A full numeric ION/ISP ioctl ledger remains open; no claim of compatibility is made.
- OEM board power source exists at `imgsensor/src/mt8163/camera_hw/kd_camera_hw.c`; 4.9 includes multiple other product variants. Select neither the douglas nor another board sequence merely because MT8163 matches. Parent's fitted-sensor identification and exact OEM pinctrl/regulator/clock sequence must determine the future source port. The main sensor list/config gate is currently off, as established by the hardware audit.

## What is complete, and what is not

Complete: current framework/provider rejection and factory paths located; OEM HAL3 selector/factory/ops established statically; exact upstream HAL1 donors pinned; ARM64 vendor dependency inventory with explicit limits; genuine SDK37 ABI link witness; compiled enum mismatch proof; precise next source boundaries identified.

Not complete: usable HAL3 metadata for fitted sensors, full ELF/dlopen/version/namespace closure, C++ object-layout compatibility, all ISP/ION/native/compat contracts, sensor identification and drivers/power integration, source HAL3 adapter or restored CameraClient build, real frames/results, any app test. These are blockers, not false successful stubs.
