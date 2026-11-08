# ARM32 does not establish a shorter genuine HAL3 route

Status: offline source/ELF/compile qualification complete, 2026-11-06. No target execution, camera opening, property change, or integration occurred. Fitted sensor part numbers and usable camera operation remain unproved.

The public stock **cameraserver is ARM32**, and SDK37's default HIDL 2.4 service is built 32-bit. Those are real packaging advantages. However, ARM32 has **the same 21 metadata constructors and the same sensor-name mismatch as ARM64**, plus a demonstrated legacy `GraphicBuffer` allocation mismatch and a changed 32-bit calibration ioctl. It does not establish a shorter functioning HAL3 path. Retain the earlier ARM64 source/ABI report as the implementation research baseline; do not interpret that as proof ARM64 works or as a final architecture decision. Reconsider width after the shared metadata and object boundaries are solved. ARM32 remains a useful stock-width qualification alternative.

The prior recommendation to qualify the real OEM HAL3 implementation first still stands. This study does **not** support changing only the reported device version, deploying a constructor alias, or replacing SDK37 system libraries with stock libraries.

## Stock width and actual selector

[stock-compare.json](../evidence/stock-compare.json) records hashes, sizes, and ELF classes for the stock server, init files, and both sets of five camera libraries. The public SYSTEM image was already present on the builder. Only selected files were read; the image was not copied or hashed.

- `/system/bin/cameraserver`: ELFCLASS32, ARM. The exact init entry is `service cameraserver /system/bin/cameraserver`, user `cameraserver`, class `main`. This establishes the configured stock service binary's width, without inspecting a live process.
- Both `camera.mt8163.so` libraries, platform libraries, metadata providers, device3 libraries, and camera-custom libraries exist in matching ELF widths.
- The parent's [property receipt](../../2026-11-06-asus-camera-api-feasibility/evidence/stock-camera-selector.json) has empty `ro.hardware.camera` and `debug.camera.force_device`, with `ro.board.platform=mt8163`. The earlier live read-only metadata reports two HAL1 devices (`0x100`). No live `force_device=1` override was observed.
- ARM32 enumeration at `0x4dfc–0x4e36` reads `debug.camera.force_device`, default string `"0"`: value 1 selects `0x100`, value 3 selects `0x302`, otherwise it calls the metadata provider's version getter. [Decoded literals](../evidence/binary-layout.json), [module disassembly](../evidence/vendor_lib_hw_camera.mt8163.so.thumb.txt).
- ARM32 `MetadataProvider::getDeviceVersion` at `0xee70` queries MTK metadata tag `0x1a0000`. The observed HAL1 selection is consistent with this default path. No metadata object was executed or synthesized here.

## Real HAL3 implementation exists in both widths; fitted-sensor coverage remains open

The ARM32 module's `openDeviceLocked` at `0x650c` chooses platform vtable offset `0x10` for versions at least `0x300`. `PlatformEntry::createCam3Device` at `0x1144` calls the imported real `createCam3Device` factory at `0x1160`; device3 exports that factory at Thumb symbol `0x88ad`. The separate HAL1 branch uses platform offset `0x0c`. This is genuine factory dispatch, not merely a HAL3 filename.

The ARM32 device3 binary contains a hardware-device template at file offset `0xc4e0`, tag `0x48574454`, version `0x302`. It is followed by the real camera3 operations table. Function pointers include the Thumb bit:

| Operation | ARM32 pointer | ARM64 code address from prior report |
|---|---:|---:|
| Close | `0x8595` | `0xc404` |
| Initialize | `0x85a5` | `0xc420` |
| Configure streams | `0x85b7` | `0xc440` |
| Construct default request | `0x85c9` | `0xc460` |
| Process capture request | `0x85d9` | `0xc480` |
| Dump | `0x85eb` | `0xc4a0` |
| Flush | `0x85f9` | `0xc4bc` |

Deprecated register-stream-buffers and device-level vendor-tag slots are null. The listed wrappers dereference the real private device at offset `0x44` and dispatch its methods. Non-null pointers do not prove valid metadata, streams, frames, or callbacks. [Template words](../evidence/binary-layout.json), [device disassembly](../evidence/vendor_lib_libcam.device3.so.thumb.txt), [prior ARM64 ledger](../../2026-11-06-asus-camera-source-abi-route/report/ABI-LEDGER.md).

Both metadata providers export the **identical set of 21** `constructCust*` functions. The sensor-specific suffixes are:

`OV5648_MIPI_RAW`, `OV5648_MIPI_RAW_TRULY`, `IMX219_MIPI_RAW`, `GC2355_MIPI_RAW`, `SP2518_YUV`.

Neither provider exports those constructors for the OEM build-list names `OV5670`, `HM2051`, `OV2680`, or `OV2680B`. Both `libcameracustom.so` binaries contain the same OV5670/OV2680/OV2680B raw sensor driver-name strings and custom code. These public binary strings and the OEM build list are **not identification of fitted sensors**. No calibration file or factory value was read.

ARM32 `impConstructStaticMetadata` at `0xe8f4` formats `%s_DEVICE_%s_%s`, using `constructCustStaticMetadata`, a section name, and the stored sensor-name pointer at object offset `0x14`. It calls `impConstructStaticMetadata_by_SymbolName` (`0xe870`), which uses `dlsym`, and retries `COMMON` when a sensor-specific constructor fails. `getDeviceVersion` then reads the constructed MTK metadata. [Lookup literals](../evidence/binary-layout.json), [metadata disassembly](../evidence/vendor_lib_libcam.metadataprovider.so.thumb.txt).

The COMMON fallback means missing sensor-named exports alone is **not a proof that HAL3 can never work**. It also provides no evidence that default requests, stream tables, durations, capabilities, or result keys are correct for the fitted sensors. ARM32 supplies no missing constructor family that resolves this question. The metadata lookup is also a dynamic-symbol-visibility requirement, beyond DT_NEEDED closure.

## SDK37 C ABI: genuine ARM32 compile and link

[camera_abi_probe.c](../fixture/camera_abi_probe.c) was compiled for `armv7a-linux-androideabi37`, ARMv8-A/Cortex-A53, softfp, with frozen SDK37 headers, ARM UAPI include paths, and genuine SDK37 ARM CRT/libc/libcamera_metadata inputs. The shared witness links with `--no-undefined` to real `validate_camera_metadata_structure`. It was never run and implements no HAL or successful-camera stub.

| Compiled type/offset | ARM32 | Prior ARM64 |
|---|---:|---:|
| `sizeof(hw_module_t)` | 128 | 248 |
| `sizeof(hw_device_t)` | 64 | 120 |
| `sizeof(camera_module_t)` | 176 | 344 |
| `sizeof(camera_info)` | 28 | 48 |
| Module methods offset | 20 | 32 |
| Module number/info offsets | 128 / 132 | 248 / 256 |
| Module callbacks/vendor-tags offsets | 136 / 140 | 264 / 272 |
| Module open-legacy/torch/init offsets | 144 / 148 / 152 | 280 / 288 / 296 |
| `sizeof(camera3_device_t)` / ops / private offsets | 72 / 64 / 68 | 136 / 120 / 128 |
| `sizeof(camera3_device_ops_t)` | 64 | 128 |
| Modern stream / stream-config / stream-buffer sizes | 64 / 16 / 20 | 96 / 32 / 32 |
| Modern capture-request / capture-result sizes | 32 / 36 | 64 / 64 |

The OEM module has a 184-byte HMI symbol, with a 176-byte standard prefix and private suffix. Its initializer sets module `0x204`, HAL API `0x100`, and the standard methods at the ARM32 offsets above. This supports the C module prefix boundary only. Version-specific camera3 tails still require the upstream adapter's genuine 3.2 handling; do not read modern fields from old private structures.

Exact [commands](../evidence/compile.json), [65 input pins](../evidence/input-pins.json), [ELF output](../evidence/abi-compile.txt), and [artifact hashes](../evidence/artifact-pins.json) are retained. Toolchain identity is the same Clang r584948b recorded by the prior spike. Initial include-path/flag probes were corrected before the retained successful compile: final paths use `asm-arm` and libc++ `platform/arm`, with one ARM32 target selection.

## Dependency closure: smaller unresolved set is not loadability

The like-for-like first audit has 70 ARM32 vendor ELFs, 22,877,120 bytes, 23 found SDK37 providers, and 40 unresolved names. Its scope matches the prior ARM64 audit's vendor closure plus module/platform/device1/device3 seeds; ARM64 had 64 vendor ELFs and 40 unresolved names. Counts do not establish equal runtime compatibility.

The [extended ARM32 audit](../evidence/extended-closure.json) includes actual public-system proprietary Arcsoft dependencies, `libmpbase`, and SDK37 `libsensor`/`libandroid`: **82 OEM ELFs, 42,768,392 bytes, 25 found modern providers, 19 unresolved names**. It inspected one named ELF at a time with a 24 MiB per-file and 64 MiB total-read cap. Large temporary inspection bytes are not retained locally. It does not include arbitrary dlopen factories, ELF version resolution, or namespace runtime behavior.

ARM32 ArcsoftFace pulls in real `libarcsoft_face_detection.so` and `libarcsoft_beautyshot.so`; other wrappers add night-shot, HDR, stabilization, and night-hawk implementations. This differs from the earlier ARM64 `libcameraap` edge, and provides no evidence of a shorter stack. ARM32 `libcameraap.so` was inspected separately but is not in this seeded DT_NEEDED closure.

`libfs_mgr.so` and `libnativehelper.so` were not present at the exact current variant paths checked. That is an artifact-availability limitation, not proof that source is absent. A zero unresolved-symbol count would still leave a missing DT_NEEDED library as a loader failure. Generic runtime libraries must stay SDK37; old libui/libutils/libinput were inspected only as ABI evidence.

| Importer | Remaining contract |
|---|---|
| `libcam_utils.so` | Nine old `PropertyMap` methods; two old `GraphicBuffer` constructors; old three-argument lock |
| `libcam.client.so` | GraphicBuffer ctor/lock, mapper unlock, `String8::setPathName` |
| `libcam.camadapter.so` | `String8::getBasePath` |
| `libmtk_mmutils.so` | GraphicBuffer ctor, mapper unlock |
| `libcam.utils.sensorlistener.so` | `SensorManager::createEventQueue(String8,int)` |
| `libnvram.so` | `fs_mgr_read_fstab`, `fs_mgr_get_entry_for_mount_point`, `fs_mgr_free_fstab` |

The sensor service split is partly resolvable by including real SDK37 `libsensor`: seven of eight previously missing sensor names resolve in the optimistic union, but the create-event-queue signature still differs. This does not validate object layout, vtables, or permissions.

## Concrete object mismatch: a constructor alias is unsafe

ARM32 `libcam_utils` loads `r0=0x88` before `operator new(unsigned)` at `0x13c66`, then calls `_ZN7android13GraphicBufferC1Ejjij` at `0x13c78`. It directly reads stride at object offset `0x30` at `0x13c8a`. `libmtk_mmutils` independently allocates `0x88` at `0x1b5a–0x1b5e` before the same constructor. This is concrete **136-byte caller storage**, not a size inferred from a generic header. [Call sites](../evidence/vendor_lib_libcam_utils.so.selected_disassembly.txt), [second caller](../evidence/vendor_lib_libmtk_mmutils.so.selected_disassembly.txt).

The genuine SDK37 ARM32 [C++ layout witness](../fixture/cpp-out/layout.cpp), compiled against frozen headers including generated graphics AIDL/HIDL headers, gives:

- `GraphicBuffer`: **1,784 bytes**, alignment 8.
- `ANativeWindowBuffer`: 96 bytes; `RefBase`: 8 bytes.
- GraphicBuffer native-buffer base offset 8; stride offset 48; handle offset 68.
- Private owner/mapper/init-check offsets 104/108/112 still resemble old prefixes, but current transport counts occupy 116/120, current ID starts at 128, callbacks at 144, and `DependencyMonitor` at 160.

The old public libui constructor uses owner/mapper/init-check at 104/108/112, ID at 120, and generation at 128, within the 136-byte object. Prefix similarities do **not** make the current constructor safe in this memory. Its current class exceeds that allocation before considering the dependency monitor. [Old constructor](../evidence/lib_libui.so.selected_disassembly.txt), [compiled current layout](../evidence/cpp-layout.txt), [frozen C++ header hashes](../fixture/cpp-out/pins.json), [compile commands](../fixture/cpp-out/commands.json).

Old `PropertyMap` is also incompatible. Its OEM constructor at `0xb64c` calls `SortedVectorImpl(8,0)` and installs the vector vtable; destruction calls `finish_vector` then `SortedVectorImpl` destruction. SDK37's class contains `unordered_map<string,string>` (20 bytes in this compile) and exposes a different string/result API. The inspected Karnak shim source is already the newer unordered-map implementation, so it is not a donor for the requested old String8 ABI. [OEM method trace and current header](../evidence/property-map.txt).

The existing graphics work supplies a useful product-specific linker namespace arrangement and a narrow three-argument lock forwarder. It does **not** supply a proved 136-byte camera GraphicBuffer facade or the old PropertyMap representation. Do not reuse its success claim as camera ABI proof. No existing graphics source was changed.

## ARM32 adds explicit compat obligations

The prior feature-ID mismatch remains independent of width: `CHECK_SENSOR_ID` 3040→3041, `GET_CROP_INFO` 3080→3081, `SET_ISO` 3090→3092. Use the prior [name-by-name enum evidence](../../2026-11-06-asus-camera-source-abi-route/report/ABI-LEDGER.md), not a global numeric shift.

The new ARM32 [calibration layout compilation](../evidence/compat-layout.txt) uses the exact previously saved public OEM and 4.9 header declarations plus genuine SDK37 ARM ioctl headers. It does not define CONFIG_COMPAT or compile a kernel handler; it proves the 32-bit userspace layouts that a 64-bit kernel's compat handler must translate:

| Contract | OEM | Kernel 4.9 source |
|---|---:|---:|
| Structure size | 16 | 20 |
| Buffer pointer offset | 12 | 16 |
| `CAM_CALIOC_G_READ` | `0xc0106905` | `0xc0146905` |

The new `deviceID` occupies offset 12 and moves the pointer. An old request must have a dedicated decoder, validated sizes/lengths, checked `compat_ptr`, explicit sensor→device routing, and correct copy-back. Neither a native ioctl alias nor treating an old pointer as deviceID is valid. No calibration payload was opened.

Also preserve full native/compat ISP register/IRQ/RT-buffer structures, sensor feature nested pointer handling, scenario/index enums, and ION/M4U handle and address-width semantics. These contracts remain unaudited in full. ARM32 process choice increases the importance of `CONFIG_COMPAT` and real `.compat_ioctl` implementations on the 64-bit kernel.

## Exact next implementation delta, not a deployment patch

No provider or compatibility implementation is ready to integrate. The shortest useful next bounded source unit is a camera-private **legacy object facade and metadata-contract fixture**, before any property override or device opening:

1. Add owned `camera/compat/legacy_graphic_buffer.{h,cpp}` and a separate SDK37-facing `graphic_buffer_backend.cpp`. Model the proved 136-byte OEM object, RefBase/vtable/native-buffer offsets, constructors, destruction, imported-handle ownership, lock/unlock and fences. Keep a real current GraphicBuffer in separately allocated storage; never placement-construct it in the 136-byte block. Retain an explicit mapping for every legacy field read by the vendor callers. Use distinct shim symbol names or equivalent proved symbol binding so a modern library cannot resolve its own calls to a legacy-layout method by accident. The supplied lock forwarder alone is insufficient.
2. Add camera-private `legacy_property_map.{h,cpp}` with the old String8/KeyedVector behavior and exact constructor/destructor/clear/add/has/try-get contracts. Reconstruct and compile the matching old public source representation against SDK37 types only after confirming vector/String8 allocation and ownership. The current unordered-map shim cannot be substituted. A donor whose exact layout and semantics match is still needed; this report does not invent that proof.
3. Add narrow, source-built adapters for the enumerated String8 path, sensor queue, and old fstab contracts. Resolve exact return/ownership semantics first. Pin a real modern provider for every DT_NEEDED edge and preserve private NVRAM access boundaries; no stub fstab success or calibration synthesis.
4. Add an offline `metadata_contract` fixture that inventories all selected static/default-request constructors and dynamically visible names. Obtain an evidence-backed fitted sensor identity separately through the parent, then map actual sensor modes and MTK metadata to truthful HAL3 stream/capability/result contracts. COMMON defaults must be evaluated, not assumed sufficient. If needed, reconstruct sensor-specific constructors from a matching public donor or implement the full contract; changing `0x100` to `0x302` alone remains invalid.
5. Add kernel-side explicit old/native/compat ioctl translators in the actual imgsensor, cam_cal, ISP and ION dispatchers, with a name-based feature map and payload-specific validation. These are proposed file/function changes only; all active kernel and probe inputs remain frozen.

For facade testing, use canaries around a 136-byte allocation, constructor/destructor and strong/weak-reference lifecycle, handle borrow/clone/own cases, lock/fence failure propagation, field consistency and metadata rejection cases. Compile for both actual widths before choosing one; interface or link tests do not replace real frames and correct capture results. This study adds no successful HAL stub and does not claim those facade tests have passed.

If ARM32 is later chosen, the actual SDK37 packaging requirements are:

- `android.hardware.camera.provider@2.4-service` is `compile_multilib: "32"`; the separately named `_64` module is 64-bit. The default service uses `/vendor/bin/hw/android.hardware.camera.provider@2.4-service` and instance `legacy/0`.
- Include a **32-bit** `android.hardware.camera.provider@2.4-impl`, all required camera device3 HIDL support libraries and their real dependencies, plus the 32-bit OEM module at `/vendor/lib/hw/camera.mt8163.so` and the complete qualified 32-bit closure. Preserve module/platform dlopen and metadata `dlsym` visibility. A 32-bit provider can serve a 64-bit CameraService through Binder/HIDL; app process width need not match the provider.
- Declare the real HIDL provider instance/transport in the product VINTF manifest, use the matching init rc, and ensure cameraserver user/groups, device nodes, SELinux, allocator/mapper, linker namespaces, and binder services agree. The inspected source has no adjacent service XML; do not assume a VINTF fragment is automatically installed by this binary's Android.bp.
- Retain SDK37 CameraService validation and the upstream version-aware device3 bridge. Declare only true hardware capabilities. No API1, Java Camera2, NDK Camera2, still/video, or third-party app coverage is proved by this study.

[Current service build source](../evidence/srv_android_lineage24_hardware_interfaces_camera_provider_2.4_default_Android.bp.text.txt), [init source](../evidence/ACCOUNT_REDACTED), [previous SDK37/provider source qualification](../../2026-11-06-asus-camera-source-abi-route/report/CAMERA-ROUTE.md).

## Reproduction and boundaries

All remote work is serial, CPU-affined to one allowed CPU, and address-space capped at 1 GiB, through the existing authorized SSH wrapper. Remote scratch is `/srv/android/asus-camera-arm32-route`. No Ninja, product build, device command, live camera action, cloud resource operation, active source/output edit, staging/probe mutation, or private data read occurred.

From the workspace, the scripts in this spike reproduce the selected-file comparison, bounded dependency audits, C and C++ ABI witnesses, and compat layout. `run_remote.py` accepts a script file and a result path; `run_compile.py` and `run_compat.py` also stage only their small public fixture sources in the owned scratch. `stock_compare.py`, `abi_edges.py`, and `binary_layout.py` initially emit expanded receipts; the saved split evidence retains the exact ELF/disassembly/source text in adjacent files. Source hashes are in the JSON manifests and compile pin files. No full-system image or per-unit calibration material is part of this deliverable.

The final evidence establishes a **static candidate and concrete blockers**, not functioning cameras. Camera work remains separate from the parent's first RAM kernel probe.
