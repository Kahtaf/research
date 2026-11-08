# Selected OV5670/OV2680 metadata: bounded result

**The inspected stock machinery does not supply a complete supported HAL3 contract for either selected sensor.** This is stronger than a missing-export-name observation: actual dispatch instructions show that static lookup errors are discarded, COMMON supplies HAL1 version `0x100`, and the separate default-request path fails with `-ENOENT`. No request COMMON exists in the inspected stock closure. This does not prove that these sensors cannot work through a future source implementation.

Status: completed static investigation and bounded instruction fixtures. No device operation, enumeration, frame, calibration read, native vendor execution, product integration, active AOSP/out modification, or cloud lifecycle action occurred. Parent identification is inherited; logical Android ID/facing remains unqualified.

## Inputs and scope

Parent `2026-11-06-asus-fitted-camera-identification/evidence/identification.json` establishes cached stock selections `CAM[1]:ov5670mipiraw; CAM[2]:ov2680mipiraw;`. Main/sub terminology comes from the OEM enum. The source IDs below are constants, not newly measured chip IDs. The private live-read payload was unnecessary and was not copied.

Selected public ELF copies and per-file pins are in `inputs/`. SYSTEM whole hash `4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49` is inherited; SYSTEM was neither copied nor rehashed. Remote analysis used one CPU, 1 GiB address-space limit, serial jobs and its own `/srv/android/asus-selected-camera-metadata` scratch. Only selected public ELF leaves were extracted. Metadata constructor inventories cover **292 ELF files**, including the transitive stock 32-bit camera/cameraserver dependencies and the broader 64-bit seeded camera closure. Only metadata-provider and halsensor export these constructors. The broader 64-bit closure has absent `libjpeggifcodec.so`; this is recorded, not silently considered resolved. Unknown injected/preloaded runtime libraries and namespace accessibility are not measured.

Primary receipts: `evidence/{mapping,complete-closure-constructors,fixture-results,fixture64-results,oem-tag-schema,schema-witness,artifact-pins}.json`. All addresses below are ELF virtual addresses. Thumb callable entries have bit 0 set.

## Selected name, ID, and caller data

`libcameracustom` registry initialization is ARM32 `0xb35b0`, ARM64 `0xd2244`. It binds:

| Kernel driver | OEM source ID | Metadata lookup suffix |
|---|---|---|
| ov5670mipiraw | 0x5670 | SENSOR_DRVNAME_OV5670_MIPI_RAW |
| ov2680mipiraw | 0x2680 | SENSOR_DRVNAME_OV2680_MIPI_RAW |

ARM32 registry names are at `0x6536e8/0x653708`; SensorInfo lowercase/name-label pairs at `0xd9573/0xd9581` and `0xd95a0/0xd95ae`. The corresponding ARM64 pairs are `0xf930b/0xf9319` and `0xf9338/0xf9346`. `SensorList` entries have strides 56/80 bytes. SensorInfo accessors at ARM32 `0xd4dee/0xd4df2` return its lowercase name / metadata label; numerical-ID getters `0xd4de8/0xd4df6` return the IDs above. Raw type getter `0xb3c72` returns zero. ARM64 counterparts are in `lib64_sensor-accessors.txt`.

Static analysis of `HalSensorList::enumerateSensor_Locked` (`0xe704`) shows selected driver objects feeding `addAndInitSensorEnumInfo_Locked` (`0xe8fc`). **Neither was executed.** Its EnumInfo record is 24 bytes on ARM32: index at +0, type +4, String8 label +8, IMetadata +12, sensor-device mask +20. `queryDriverName` (`0xe248`) returns that label; `queryStaticInfo` (`0xe1e0`) returns that metadata. The vtable selects these exact methods.

`MetadataProvider` constructor (`0xee10`, ARM64 `0x12638`) queries IHalSensorList type, device mask and label. The callback Info region starts at object +8/+16 and contains open index, device mask, type, then label pointer at relative +12/+16. IMetadata is object +28/+48, converted metadata pointer +24/+40. Halsensor's separate callback Info instead contains physical index, type, sensor ID, then String8 at +12/+16. Do not reinterpret these as one SDK structure. Request objects store open index/type/name at +8/+12/+16 (ARM64 +16/+20/+24); request constructors receive metadata and template integer, not this Info pointer.

## Full lookup behavior

Both static layers iterate DEVICE, then PROJECT; each iterates **LENS, SENSOR, TUNING_3A, FLASHLIGHT, SCALER, FEATURE, CAMERA, REQUEST**. Each first formats `constructCustStaticMetadata_<family>_<category>_<exact suffix>`, then tries the same name ending `_COMMON` on failure. `mapping.json` retains all 32 computed names per sensor and width, with constructor origins.

Halsensor `buildStaticInfo` ARM32 `0xde50`, ARM64 `0x106e8` uses helper `0xdf98` / `0x108ac`: format library `libcam.halsensor.so`, `dlopen(...,2)`, `dlsym(handle,name)`, call `(IMetadata&, Info const&)`, close handle. The helper treats nonzero constructor result as true; the outer loop skips fallback only for result exactly 1. Missing lookup/open returns false. Even all missing constructors yield a final **true** after sorting the empty EnumInfo metadata (`0xdf44–0xdf5e`). No named selected constructor or COMMON exists in this handle's inspected dependencies.

MetadataProvider `impConstructStaticMetadata` ARM32 `0xe8f4`, ARM64 `0x11e98` uses helper `0xe870` / `0x11dd0`. It calls `dlsym(RTLD_DEFAULT,name)` with handle `0xffffffff` on ARM32 and zero on ARM64. Helper return is status_t: missing symbol gives -2; constructor status is preserved. Outer branches `0xe93e/0xe9b0` (64-bit `0x11f2c/0x11fd8`) try COMMON on any nonzero result, then **discard both errors and retain partial writes**, ultimately returning zero. No selected-name-to-other-sensor alias or third format is present.

The width-specific handle constants and breadth-first handle dependency lookup agree with pinned [AOSP Android 7 dlfcn.h](https://android.googlesource.com/platform/bionic/+/android-7.0.0_r1/libc/include/dlfcn.h) and [linker.cpp](https://android.googlesource.com/platform/bionic/+/android-7.0.0_r1/linker/linker.cpp). RTLD_DEFAULT searches eligible loaded objects plus caller local-group fallback. Upstream semantics are not an assertion that OEM linker namespaces were tested.

## COMMON, dynamic construction, and version selection

The actual `constructCustStaticMetadata_DEVICE_CAMERA_COMMON` ARM32 body at `0x91c8` supplies these internal tags: hardware level `0x150000=0`, sync max latency `0x170001=0`, orientation `0xf000b`, wanted orientation `0xf0012`, facing `0x80005`, version `0x1a0000=0x100`, and flash availability `0x50000=0` for normal indices. The version writes at `0x9684`, `0x96da`, `0x972e` are all HAL1, independent of the orientation branches. Hardware-level byte zero means LIMITED in the SDK schema; it is not proof of LIMITED support and is not LEGACY. The offline COMMON-body tests stubbed its board-file open to failure; 90/270 and facing outputs in those tests are synthetic-index defaults, not newly qualified physical mapping.

Static assembly at `0xea38` first runs the permissive constructor dispatcher, then copies `IHalSensorList::queryStaticInfo`, merges `DngInfo::getStaticMetadata`, updates each resulting entry into the provider metadata, performs updateData and converts/sorts. It can therefore pass partial COMMON metadata onward; it has no HAL3 completeness gate.

Two dynamic sources must be distinguished:

- `buildSensorMetadata` (`0xf234`, ARM64 `0x12558`) builds separate exported `gSensorMetadata` from cached driver sensor facts and scenario packages (array/size/range/frame-rate information). It is not the EnumInfo metadata returned by `queryStaticInfo`. The traced `addAndInit` → `buildStaticInfo` path initializes EnumInfo through the missing constructor lookups and sorts it; it does not merge this global. Direct/global-reference evidence is retained. Computing a global is not evidence that the selected HAL3 contract receives it.
- DNG (`getStaticMetadata` ARM32 `0x1398`) conditionally supplies illuminants and color/calibration/forward matrices. Its real constructor at `0xf58` uses an NVRAM source; **that constructor and source were not executed/read**. These tags cannot supply streams, capability/key lists or templates. Data values remain unqualified.

Generic `IMetadata()` (`0x97c0` in libcam.metadata) creates an Implementor with an empty entry vector and sentinel entry. DefaultMetadataTagSet registers types/conversions, not sensor values. The actual registration-body fixture records 248 schema tags and 219 conversion rules. Internal version `0x1a0000` has no Android conversion rule; SDK37 uses that numeric Android tag for logical-camera physical IDs. Raw internal-tag copying would be wrong. Static `updateData` (`0xec08`) computes JPEG maxSize from existing BLOB stream configurations; it does not invent stream configurations.

`getDeviceVersion` (`0xee70`, ARM64 `0x126d0`) reads entry `0x1a0000`, item 0 without an emptiness guard. The module default selector (`0x4e2c–0x4e36`) uses it. Thus the normal COMMON path explicitly selects HAL1. A force selector could still hand the partial characteristics to Cam3; it would not repair them or the templates. No selector/property change is proposed.

## Default requests: decisive missing contract

Actual names are `constructCustRequestMetadata_SENSOR_DRVNAME_OV5670_MIPI_RAW`, `constructCustRequestMetadata_SENSOR_DRVNAME_OV2680_MIPI_RAW`, followed by `constructCustRequestMetadata_COMMON`. All are absent in the inspected closure for both widths.

ARM32 dispatcher `0x24500` uses helper `0x2447c`; ARM64 `0x2a36c` / `0x2a2a4`. Missing sensor constructor returns -2 and tries COMMON; missing COMMON returns -2 to `constructRequestMetadata` (`0x245d8`). Unlike static dispatch, this error stops construction before conversion or request `updateData`. The latter only derives a crop from static active-array data after constructor success; it is not a fallback request builder.

`onCreate` (`0x26da8`) attempts templates 1 through 6, but the actual missing path fails at template 1, caches none, and returns -2. `ITemplateRequest::getInstance` (`0x26f84`) ignores that status and returns an allocated object. Its empty-map `getData` (`0x26ed4`) returns the initialized null pointer at object +40. Cam3's `i_construct_default_request_settings` (`0x6a54` in libcam.device3) caches the object and forwards getData. This explains why non-null factory/object results cannot qualify requests. The copied SDK37 camera3.h at lines 3213–3242 requires use-case settings and defines a null default-request result as fatal.

## Tests and implementation boundary

Executed **107 ARM32 and 68 ARM64 instruction-fixture cases** cover exact names, missing/present constructors, COMMON presence/absence, constructor errors, static error swallowing/partial retention, dynamic merge ordering, templates 1–6, error propagation, empty metadata, converter error, simulated allocation/conversion null, unchecked missing-version access and getInstance's ignored failure. External sensor, dlsym/dlopen, allocator, metadata-container, converter and file operations are explicit Python stubs. Only whitelisted instructions run in Unicorn with a 50,000-instruction call bound; no vendor code runs natively. Positive stub cases are control-flow witnesses, not metadata qualification. Converter-null tests expose status-zero paths; they do not model native null-pointer safety.

A compile-only ARM32 ELF schema witness uses the actual copied SDK37 enum header (system/media HEAD `f150131cfd6d8dacecf86a3e0cded02d249296a4`). It does not validate C++ ABI or actual OEM values. Required-entry candidates and exact tag IDs are in mapping.json: capability/key lists, truthful stream configurations and durations, sensor geometry/ranges, supported control/FPS ranges, JPEG sizing and valid request templates. Requirements vary by advertised capability/level; this is not an exhaustive CTS checklist.

**Next boundary:** keep camera disabled in active product. A separate source contract implementation must supply exact selected-sensor static characteristics and templates tied to demonstrated OV5670/OV2680 modes and the MT8163 ISP/3A pipeline. Every emitted entry needs provenance and behavioral justification; retain conversion/error semantics and test negative/empty paths. No matching public metadata donor is asserted or proposed here. Tuning/calibration exports alone cannot fill this gap. Do not substitute another sensor's constructor or change only version/capabilities.

Independent unresolved work remains GraphicBuffer 136 versus SDK37 1784-byte ARM32 layout, old PropertyMap KeyedVector ABI, the prior 19 external closure symbols, native/compat ioctl translation, and real pipeline/frame/hardware qualification. This result does not alter those ledgers and **does not block the first RAM kernel probe**. Parent owns all future device/build integration.
