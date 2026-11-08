# Stock-selected camera drivers

The exact stock ASUS reports cached selected drivers
`CAM[1]:ov5670mipiraw; CAM[2]:ov2680mipiraw;`. Two separately executed reads
agree, after fresh serial/product/SDK/fingerprint/boot-completed/Enforcing checks.
The actual command and output are retained in `evidence/live-read.json`.

This resolves the earlier uncertainty between an OEM build list and selected
runtime drivers. It does not open a camera, read chip-ID registers anew, prove
frames, or qualify the new kernel/HAL. Logical Android camera-ID/facing mapping
is not separately proved here; slots are called main and sub from the OEM enum.

## Why this read is hardware metadata only

Exact copied OEM public source is under `inputs/`, with original paths/hashes in
`evidence/source-pins.json`:

- `kd_sensorlist.c:56–58` defines `/proc/driver/camera_info` and the cached
  128-byte `mtk_ccm_name` buffer.
- `adopt_CAMERA_HW_CheckIsAlive`, especially lines1452–1476, appends the selected
  driver name and socket index after an earlier successful nonzero/non-FFFFFFFF
  sensor-ID response. That function can power sensors, but **was not called by
  this task**.
- `subsys_camera_info_read` at4102–4107 only logs/prints the cache and returns0.
  `proc_camera_info_open` uses `single_open`; its operations select `seq_read`.
  There is no sensor feature, power, I2C, calibration or register call in this
  read path.
- `kd_camera_feature.h:28–29` defines main=1 and sub=2. `kd_imgsensor.h` maps
  the names to OV5670/OV2680 source model identifiers. Those constants are source
  mappings, not a new physical numerical ID measurement.

The neighboring `camsensor*` register-debug interfaces and OTP/unique-ID files
were not read. No root helper, image capture or device-node camera open ran.

## Consequence for camera integration

The previous ARM32 and ARM64 selected metadata-provider export inventories in
`2026-11-06-asus-camera-arm32-route/evidence/stock-compare.json` contain constructors
for OV5648/IMX219/GC2355/SP2518 and DEVICE_CAMERA_COMMON, but no named OV5670 or
OV2680 constructors. The earlier mismatch therefore concerns the drivers selected
on this unit, not just unused OEM sensor options.

That is **not yet proof that OEM HAL3 cannot support them**. Internal dynamic
construction, common fallback and other dlopen/dlsym sources must be traced for
these exact names. Calibration/tuning exports in libcameracustom are not by
themselves static/default-request metadata implementations. No version/property
override or camera provider is enabled by this result.

The next bounded task is exact selected-sensor metadata dispatch and required
HAL3 contract qualification. The existing GraphicBuffer/PropertyMap/dependency,
kernel ioctl and physical-frame blockers remain independently open.
