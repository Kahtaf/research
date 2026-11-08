# P00A_2 → SDK37: camera implementation decision

**Recommendation: qualify the existing OEM HAL3.2 implementation first, but do not enable it in the product yet.** Static analysis found an actual selector-to-factory-to-camera3-ops path, not merely a library named `device3`. It is the shortest candidate that could preserve SDK37 CameraService and support both app APIs. The stock fitted cameras nevertheless actually enumerate as HAL1; HAL3 operation for either fitted sensor is unproved. The next implementation should close the OEM dependency/graphics ABI and sensor-command ABI in an isolated fixture, then hand a precise qualification plan to the parent. If sensor-specific HAL3 metadata/pipeline support cannot be established, stop that route rather than advertise HAL3 from a changed number.

This research is complete as a source/ABI investigation, **not camera bring-up**. No camera, physical boot, newest-Android usability, Google, or root result is claimed. Cameras remain separate from the first RAM kernel probe.

## Facts and exact inputs

- Parent static receipt at `2026-11-06T20:04:13.771279+00:00`: back 90°, front 270°, both `device_version=0x100`; no camera open or captured frames. Input: [stock-camera-static.json](../../2026-11-06-asus-camera-api-feasibility/evidence/stock-camera-static.json).
- Fitted part numbers remain unknown. OV5670/HM2051/OV2680/OV2680B are an OEM build list, not a physical identification.
- Public SYSTEM input remains at `/srv/android/asus-stock-system-backup/20261106T172146Z-89fc7700813aad85/system.img`. Prior parent pin `4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49` and public ZIP pin `eea443c205596106f041f1054fcbed0158c6c7986b899b9545d84fcd9d38a81c` are inherited from the hardware audit; no whole-image rehash/copy occurred here.
- Actual SDK37 source repo heads: frameworks/av `1c5914737a1a89d0c5b3e52e8289019eab3f8cbf`; frameworks/base `696a5773fa284f53429dbb6c3e5dcc96bf5bd0b3`; hardware/interfaces `a0221f11248a924532444fc7de85d41998b9fe1e`; hardware/libhardware `d7f13275b6a210f56110b46609a2e83b2feccd99`; system/media `f150131cfd6d8dacecf86a3e0cded02d249296a4`. Per-file hashes, rather than repository HEAD alone, pin the actual read contents: [source pins](../evidence/sdk37-source-pins.json), [additional pins](../evidence/source-edge-pins.json).
- Source copies and ELF analysis are static. No ELF was `dlopen`ed, no camera enumeration was executed here, and no vendor constructor ran. Vendor enumeration itself can touch sensors; it is not treated as a harmless offline test.

## 1. OEM HAL3: a real candidate, with unresolved selected-camera support

ARM64 `camera.mt8163.so` SHA256 `2828cc2b636cc038b98422fd68131683921af35c640cbfc8db9ca8caaac7e660` provides the following chain. Addresses are ELF virtual addresses, not runtime addresses. [Disassembly](../evidence/oem-elf.txt), [platform/metadata disassembly](../evidence/oem-dispatch.txt), [data and relocation receipt](../evidence/module-layout.txt).

| Evidence | What it establishes |
|---|---|
| Module initializer `0x60f0–0x61d4` fills `HMI` in BSS; header constant writes module API **2.4**, HAL API `0x100` | Module version is distinct from device version. `HMI` is 360 bytes with an OEM suffix; the standard prefix offsets match the SDK37 compile witness. Reading raw BSS bytes as an initialized module would be wrong. |
| `CamDeviceManagerImp::enumDeviceLocked`, `0x6654–0x66b8` reads `debug.camera.force_device`, default `"0"` | Value 1 chooses device `0x100`; value 3 chooses `0x302`; default calls `IMetadataProvider::getDeviceVersion`. This is an OEM selection mechanism, not a recommended product property change. |
| `CamDeviceManagerBase::open`, `0x7270–0x72c0` | Normal open with requested version zero reads the enumerated `camera_info.device_version`, then passes that version to open-device dispatch. |
| `openDeviceLocked`, `0x895c–0x8a00`; platform vtable relocation at `0x2c90` | `0x100` uses the Cam1 factory; versions ≥ `0x300` use the platform Cam3 factory. |
| `getPlatform`, `0x7bd8–0x7c08` loads `libcam_platform.so`, resolves `getHandleToPlatform` | The dynamically loaded platform is part of the required closure, even though it is absent from the module's DT_NEEDED list. |
| `PlatformEntry::createCam3Device`, `0x1584–0x15e8` in `libcam_platform.so` | Calls the real `createCam3Device` export; that library DT_NEEDED includes both `libcam.device1.so` and `libcam.device3.so`. |
| `libcam.device3.so`, template at `0x10b30`, ops at `0x10ba8` | Genuine `hw_device_t` tag and `version=0x302`; non-null initialize, configure, default-request, process-request, dump and flush slots. `Cam3Device` constructor copies these templates. |
| `Cam3DeviceImp::onConfigureStreamsLocked` `0xa60c`, `i_process_capture_request` `0xab9c`, `flushRequest` `0xb8cc` | Substantial existing pipeline/request implementation, with real app stream manager, pipeline and error/buffer handling paths; not a return-success façade. This does not prove those paths work on this tablet. |

`libcam_platform.so` SHA256 is `86cab4973acdd5b194cf9eb6bfc3cf6ab9e9c180a6d01cc2a1ff5638301d4df3`. All twelve initially inspected ARM32/ARM64 module/device/metadata/pipeline files have individual pins in `oem-elf.txt`. The detailed dispatch analysis and closure below are ARM64; the presence of ARM32 exports is not an independently completed ARM32 ABI qualification.

**Critical remaining metadata question:** `MetadataProvider::getDeviceVersion` (`0x126d0`) reads a private metadata entry (`0x1a0000`), not a universal hard-coded HAL3 version. The inspected `libcam.metadataprovider.so` exports sensor-specific static/request constructors for OV5648, OV5648_TRULY, IMX219, GC2355 and SP2518, plus DEVICE_CAMERA_COMMON. It does **not** export corresponding named constructors for OV5670/HM2051/OV2680/OV2680B. `libcameracustom.so` does contain OV5670/OV2680/OV2680B tuning/calibration-code symbols, but these are not HAL3 static/request metadata constructors. This mismatch is an explicit qualification blocker, not proof that HAL3 is impossible: internal/default/dynamic construction still needs tracing. No fitted sensor is inferred from any of these names. [Metadata evidence](../evidence/metadata-edges.txt).

The public `/build.prop` and `/vendor/build.prop` excerpt contains only camera sound policy; it does not establish the effective runtime selector. No live properties were queried. The known stock HAL1 selection remains authoritative.

**Shortest parent integration if this candidate qualifies:** use the existing SDK37 HIDL C-module bridge, `android.hardware.camera.provider@2.4-service_64` plus `android.hardware.camera.provider@2.4-impl`, instance `legacy/0`, genuine device@3.2/3.3 wrapper selected by the upstream provider, with matching ARM64 private dependencies. Use unmodified SDK37 service validation. The default service executable is 32-bit; do not package it with this ARM64 closure. For a future ARM32 choice, redo the closure, C++ and kernel compat analysis. Exact package definitions are in the frozen [Android.bp](../fixture/sdk37/hardware/interfaces/camera/provider/2.4/default/Android.bp).

A selector is legitimate only when it selects the real working factory, matching characteristics/templates and functioning pipeline. A property alone, patched `device_version`, successful enumeration, or non-null ops is never completion.

## 2. What SDK37 really accepts

Three distinct interfaces must not be conflated:

1. **Module C ABI:** `camera_module_t` 2.4 can describe either HAL1 or camera3. Its `open_legacy` is an optional older-device open entry point; it is not an upstream HAL1→HAL3 converter. `CameraModule.cpp` lives at `hardware/interfaces/camera/common/default/`, not the guessed `common/1.0/default/` path.
2. **Provider/device HIDL:** `LegacyCameraProviderImpl_2_4::getHidlDeviceName` accepts actual device C versions 1.0 and 3.2–3.6; device1 wrapper still forwards real HAL1 operations. Device3 wrapper checks the opened version and initializes a real camera3 session. `CameraModule::getCameraInfo` derives some newer characteristics for older camera3 HALs; it does not manufacture a HAL3 implementation from HAL1.
3. **CameraService:** `CameraProviderManager::ProviderInfo::addDevice`, lines 2682–2691, rejects HIDL device major 1 **before client creation**. `HidlProviderInfo::startDeviceInterface` calls only `getCameraDeviceInterface_V3_x` and constructs `HidlDeviceInfo3`. `CameraService::makeClient`, lines 1574–1582, independently rejects C device HAL1/HAL2. AIDL camera device major 1 in another branch is the modern AIDL protocol, not legacy HAL1.

The scoped current `out/soong/.intermediates/hardware/interfaces/camera/provider/2.4/default` directory does not exist, so no built provider ELF was available there for inspection ([receipt](../evidence/provider-inventory.json)); proposed provider packaging is source-backed and unbuilt in this task.

The removed service implementation is not hiding behind a build flag: SDK37 has no `api1/CameraClient.{h,cpp}`, no `device1/CameraHardwareInterface.{h,cpp}`, and no frameworks/base `camera2/legacy` directory. A vendor-only HAL1 provider is therefore insufficient. [Discovery](../evidence/discovery.txt), [SDK37 CameraProviderManager](../fixture/sdk37/frameworks/av/services/camera/libcameraservice/common/CameraProviderManager.cpp), [SDK37 CameraService](../fixture/sdk37/frameworks/av/services/camera/libcameraservice/CameraService.cpp).

## 3. Honest native HAL3 adapter over actual HAL1

No complete native HAL1→camera3 implementation for this device was found among the inspected OEM/AOSP inputs. The genuine older upstream compatibility implementation is largely a Java Camera2→Camera1 bridge, described below. Reusing its algorithms would still require a real native implementation; renaming a wrapper does not supply it.

If OEM HAL3 fails its selected-sensor qualification but real HAL1 can operate on the new kernel/userspace, a source-built adapter is a defensible way to keep SDK37 service paths intact. Suggested new isolated module: `camera.p00a_legacy_bridge`, implementing standard C camera module/device3.2, with these explicit source units:

| Proposed file/function group | Required implementation, not a stub |
|---|---|
| `module.cpp`: `get_camera_info`, `open`, vendor tags | Open the underlying HAL1 privately, parse its actual supported parameters and sensor facts, construct internally consistent static metadata and request templates. Decide a non-recursive module load path. Report only demonstrated capabilities. |
| `hal1_backend.cpp`: callback memory, preview, AF, JPEG, recording | Own HAL1 callback allocation/lifetime, message-mask changes, start/stop sequencing, parameter error propagation and release. Preserve exactly-once releases of HAL1 video/memory buffers. Avoid MTK proprietary video metadata until its contract is known. |
| `session.cpp`: `configure_streams`, `process_capture_request`, `flush`, close | Validate supported stream combinations; serialize parameter changes and captures; handle null settings reuse, request IDs, backpressure and device/stream state. Flush must return every accepted buffer exactly once and stop callbacks safely. |
| `buffers.cpp` | Import actual gralloc handles, wait/close acquire fences, respect plane strides/chroma layout, produce truthful release fences; distribute real preview frames into each accepted output. Implement YUV conversion/copy and JPEG BLOB footer/size correctly. No buffer marked OK before actual valid output. |
| `results.cpp` | Frame-number association, monotonic shutter timestamps, ordered results, truthful AE/AWB/AF states, physical metadata limitations, error request/result/buffer/device callbacks, teardown races. Unsupported controls must be rejected or omitted from capabilities. |

A LEGACY hardware-level adapter can expose useful Camera2 without pretending to be FULL. It still must implement the level's required stream combinations, controls and result semantics. A one-stream experiment should remain a lab implementation until these requirements are met. HAL3 protocol version 3.2 is not hardware capability level FULL. Manual exposure/focus, RAW, reprocessing, high-speed recording and concurrent cameras are not promised.

Missing contracts: actual supported HAL1 parameters and preview formats; meaningful timestamps; per-sensor orientation/stream sizes and request-result mapping; real gralloc import/layout/fences; MTK callback/recording extension semantics; error behavior; exact kernel userspace ABI. The same proprietary ELF/kernel blockers apply to this adapter as to OEM HAL3. It cannot bypass missing ISP/sensor drivers.

## 4. Genuine upstream HAL1 restoration: bounded API1 first, much larger Camera2 restoration

Pinned donor is AOSP `android-9.0.0_r61`, not an unspecified historical fork. Exact repository commits: av `fb027a5efa741f03e8d1f33a486a365ff38c0724`; base `ad31dbbdcd76091d7d2d1fc6c863ee17c3bfe87d` ([donor pins](../donors/pins.json)). The files were fetched individually from android.googlesource.com, saved with license headers and SHA256; no old binary system libraries were copied.

The donor [CameraClient](https://android.googlesource.com/platform/frameworks/av/+/fb027a5efa741f03e8d1f33a486a365ff38c0724/services/camera/libcameraservice/api1/CameraClient.cpp) and [CameraHardwareInterface](https://android.googlesource.com/platform/frameworks/av/+/fb027a5efa741f03e8d1f33a486a365ff38c0724/services/camera/libcameraservice/device1/CameraHardwareInterface.cpp) are real implementations. They use HIDL device@1.0, preview windows, callback memory and recording paths; `CameraHardwareInterface::initialize` calls the old manager's HAL1 `openSession` overload. This is a useful donor for source restoration against current interfaces, not a drop-in current source build.

Required API1-only delta in `libcameraservice`:

- Restore `api1/CameraClient.{h,cpp}` and `device1/CameraHardwareInterface.{h,cpp}`; add them and the genuine HIDL1 dependencies to current `Android.bp`.
- Add a current `HidlDeviceInfo1` and HAL1 session overload to `common/hidl/HidlProviderInfo.{h,cpp}` and `common/CameraProviderManager.{h,cpp}`. Port donor `DeviceInfo1` getCameraInfo/resource-cost/torch/status/dump semantics. Admit major 1 only into this implemented branch; preserve unknown-version rejection and the existing camera3 branch.
- Extend `ProviderInfo::addDevice`/API1 enumeration and `CameraService::makeClient` to route actual HAL1 to restored `CameraClient`; API2 native connection must remain unsupported for that device until a real implementation exists.
- Adapt `CameraClient` to current `Client` constructor (attribution/permission utility, `AttributionSourceState`, string and API1 IDs, sensor orientation, compatibility info, sharing policy). Match current `initialize(manager, monitorTags)`, `dumpClient(..., bool)`, `setVideoTarget`, shared-client callbacks and all remaining abstract methods. Explicitly reject unsupported sharing; do not bypass AppOps, foreground/privacy, attribution or policy handling.
- Port old Surface/BufferQueue/mapper/IMemory/native-handle callback code to current APIs and verify actual buffer ownership. Rebuild with SDK37 libbinder/libui/libgui/libcamera_client/libhidlbase; do not ship old replacements.

This is plausibly less semantic work than a full native HAL3 adapter for a first API1 preview/JPEG milestone. It is still a service port, not a few-line relaxation. It has **not been compiled** here; the ABI probe must not be mistaken for that port.

For Java Camera2 LEGACY coverage, additionally restore the donor's 21 `camera2/legacy/*.java` files and both `android_hardware_camera2_legacy_{LegacyCameraDevice,PerfMeasurement}.cpp` JNI units, including JNI registration/build integration. Donor `CameraManager` selects legacy characteristics via `getLegacyParameters`/`LegacyMetadataMapper`, and opens through `CameraDeviceUserShim.connectBinderShim`; the current manager always follows the modern connection path. Current `supportsCameraApi` service AIDL entry is absent, so an explicit current classification/query contract is needed.

Port `CameraDeviceUserShim` to the **current** `ICameraDeviceUser`/callbacks: changed `endConfigure` return/parameters, session support/configureStreams, input/multi-resolution/offline methods, and callbacks using `CameraMetadataInfo`, physical results and shared priority. Correctly return unsupported for unavailable features while retaining real capture behavior. Port renderer/JNI/native window format APIs and lifecycle/permission integration too. This is not bounded to libcameraservice alone.

Even a successful restoration of that Java bridge does not automatically serve **NDK Camera2** clients: they connect directly to CameraService instead of running the Java shim ([actual SDK37 NDK source receipt](../evidence/ndk-camera.txt)). Broad native Camera2 coverage requires a service-side implementation or the real HAL3 route. No FULL capability or current CTS/GMS/CameraX compatibility follows from restoring LEGACY behavior.

## App/API coverage comparison

| Route after implementation and physical qualification | API1 apps | Java Camera2 | NDK Camera2 | Claim allowed now |
|---|---|---|---|---|
| OEM real HAL3.2, supported fitted-sensor configuration | Via SDK37 Camera2Client | Via SDK37 native service, actual advertised level | Via same service | Static selectable implementation exists; operation unknown |
| Complete native HAL3-over-HAL1 adapter | Via SDK37 Camera2Client | LEGACY target, subject to real conformance | Via native service, subject to metadata support | Architecture/work list only |
| Restored upstream native HAL1 service/client | Potential preview/JPEG/video as ported | No automatic support | No automatic support | API1-only partial path; uncompiled |
| Above plus rebuilt upstream Java legacy bridge | Potential | LEGACY subset as ported | Not supplied by Java bridge | Larger uncompiled framework/JNI port |

Camera apps that require RAW/manual/FULL/extensions may remain unsupported even on a working camera. Video needs a separately verified encoder/buffer path. An app's fallback behavior is app-specific; none was tested.

## Next bounded implementation and parent handoff

1. **Common prerequisite:** implement an isolated OEM camera ABI fixture before selecting a large service rewrite. Complete the missing external-library closure and exact C++ ownership/layout audit; build only source compatibility pieces that have real semantics against frozen SDK37. Do not interpose constructors by symbol spelling alone. See [ABI ledger](ABI-LEDGER.md).
2. In a separate owned kernel fixture, preserve the OEM sensor FeatureId numbering at the userspace boundary. Translate explicit OEM IDs to current internal enums and validate payload lengths/pointers; keep kernel-internal callers separate. Do not apply a global `+1`: the shift changes again later. Port the exact fitted sensor driver, sensor list and board power sequence once parent has identified the fitted hardware. Keep both ISP register/DMA and ION/M4U contracts explicit. Parent owns any integration into a future kernel.
3. For OEM HAL3, finish static tracing of selected-sensor metadata/template lookup and the real pipeline's required sensor modes. Obtain a matching OEM source/donor metadata contract if defaults are insufficient. Do not substitute metadata for a different sensor. Produce an isolated, reviewed provider package only after closure.
4. Parent alone can later qualify genuine module characteristics and opened device3.2 ops, initialization, legal stream configuration, actual preview/JPEG, request/result timestamps, buffer/fence accounting, flush, errors and reopen on each fitted sensor. Test stock-selected HAL1 vs genuine OEM alternate selection in a disposable commissioning configuration if authorized. A successful probe must record the selected implementation, not merely the reported version. No action in this step was performed here.
5. If OEM HAL3 lacks the correct sensor pipeline/metadata, choose an explicit scope: full native HAL3 LEGACY adapter for native modern-app coverage, or source restoration of API1 as an honest earlier partial milestone. Do not label API1-only restoration as a complete Camera2 fix.
6. Only after parent acceptance: future product packaging, exact VINTF, narrowly scoped camera/ISP/ION/sensor/calibration access policy, feature XML based on actual capability, genuine ELF/init/SELinux/VINTF checks and app tests. All live r5, sealed staging, kernel/probe artifacts remain unchanged by this research.

## Reproduction and limits

See [README](../README.md). Remote scripts use the authorized SSH wrapper and an owned `/srv/android/asus-camera-source-abi-route` fixture. All remote analysis/compile children inherit one CPU affinity and a 1 GiB address-space limit. No Ninja/Soong invocation or full build was made. The ARM64 dependency walk read 64 specific public vendor ELFs totaling 22,886,792 bytes; temporary additional ELF contents were discarded. Its union export check is deliberately optimistic, not a loadability proof; dynamic libraries beyond explicit seeds, missing providers, symbol versions and object layouts remain gates.

One genuine SDK37 ARM64 ABI witness was compiled and linked with `--no-undefined` against pinned current `libcamera_metadata.so` and Bionic. Two extracted source enum witnesses also compiled, confirming the numerical mismatch. No interface stubs were used to satisfy link symbols; no camera provider/adapter/service was implemented by the witness. No target execution occurred. The old compatibility donor was inspected, not compiled. Static verification is reported separately from runtime proof.
