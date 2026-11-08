# BMC156 accelerometer-only implementation receipt

**Completed: isolated OEM-derived kernel port, matched minimal SDK37 C sensors HAL, compiler/link evidence, boundary tests, exact patches, and future integration instructions. Not completed or claimed: a bootable combined Image, active product integration, Android17 execution of this HAL, physical sensor operation or calibrated readiness.**

The original compiled physical r5 kernel has never booted. This stage does not change the intended genuine Android17/SDK37 target, introduce certification/CTS requirements, or claim root/Google Play/hardware success. All device/root/USB/flashing, private calibration restoration, product combination and physical decisions remain with the parent.

## ABI and OEM source

The decision was recorded in `ABI-DECISION.md` before implementation. The inspected OEM accelerometer uses legacy evdev; the existing physical4.9 core uses a packed36-byte MediaTek `sensor_event`. The new source HAL matches the latter and exposes C sensors API1.3, the real minimum accepted by the inspected SDK37 HIDL1.0 wrapper. It does not load the Android7 sensors blob or mix event layouts. The actual SDK37 SensorDevice/HidlSensorHalWrapper sources also retain the2.1→2.0→1.0 connection fallback; source pins and excerpts are in evidence/sdk-route*.txt. This establishes the intended framework source route, not successful Android runtime.

The ASUS `bmc156_acc` driver really names its internal register functions BMA255. This port starts from that exact OEM source/header and board evidence, not the unrelated BMA253 option. It retains chip ID0xfa, six-byte signed12 sample decode, ±4g configuration, 512counts/g, OEM gravity9807mm/s², actual NORMAL/SUSPEND register ordering and direction4 (-X,+Y,-Z). The existing I²C2/address0x11 DT and no-external-LDO semantics are preserved. The4.9 DT helper maps the OEM `power_id=0xffff` sentinel to `-1`; the port validates that actual API behavior.

The retained raw/register routines and adapted callback layer are in `source/kernel/.../bmc156_acc/`. The OEM calibration diagnostic/DMA/FIFO/debug/legacy ioctl/sensorhub surfaces were removed. New real callbacks implement enable, batch/rate, flush, absolute calibration and device PM. The old OEM set-delay function selected a bandwidth but never wrote it; the new callback calls the actual bandwidth register setter and propagates I²C errors. Missing/short I²C transfers do not generate sensor success. A partially failed power transition invalidates the cached power state. The core forwards disable even after a failed enable left its power flag off; the driver then requires real register writes before reporting success. The core retains the requested period while disabled, so batch-before-enable still starts real polling.

The common accelerometer core now emits only actual successful samples, including zero vectors and legitimate -1 components. It no longer backfills duplicated samples at fabricated timestamps. Sample read/report and flush-marker insertion share a mutex; malformed controls and calibration errors reach userspace. Registration allocates its event queue before publishing the character device, propagates failed device creation, and unwinds queue/sysfs/workqueue failures. The built-in driver suppresses bind/unbind controls because the existing core has no safe unregister-data-path API.

The exact kernel delta is nine files: four new OEM-port files, accelerometer core/Makefile/Kconfig, the physical defconfig, and the sensor character-device registration helper. Only four resolved config values change: enable CUSTOM_KERNEL_ACCELEROMETER and BMC156_ACC; disable the inherited BMA253 and MC3416 alternatives. Magnetometer0x13, ALS0x1e, gyro, sensorhub and fusion work are deferred.

## Minimal HAL behavior

`source/hal/` contains the production C source, Android.bp, product/BoardConfig includes, sole sensor feature reference, HIDL1.0 manifest, init fragment, ueventd merge rules and narrow policy. The HAL opens `/dev/m_acc_misc` and `/sys/class/sensor/m_acc_misc`, not `/dev/input/eventN`. Its byte decoder avoids unaligned struct dereferences and is matched by kernel compile-time size/offset/action assertions.

- One non-wakeup continuous accelerometer, framework handle1/kernel handle0; no other sensor, injection or direct-channel claim. Corrected range/resolution derive from the actual OEM driver rather than the inconsistent old binary descriptor. Power0.13mA is retained as the public OEM descriptor's estimate, not a measured current. The conservative maximum advertised sampling rate is the stock descriptor's100Hz; supported requested periods are10–200ms.
- CLOCK_BOOTTIME nanoseconds pass through without wall-clock conversion. XYZ are divided by1000 once; no second orientation transform occurs in the HAL. Malformed, short, wrong-handle/status/action, impossible-range, future or nonmonotonic packets fail rather than yielding made-up data.
- Enable/rate writes are checked, period requests clamp to the advertised bounds, legacy dry-run validates without I/O, negative periods/latencies and unsupported flags are rejected. There is no hardware FIFO: positive maximum latency requests use immediate delivery.
- Flush markers come from the kernel queue in sample order; inactive flush is rejected and failed queue insertion is not acknowledged. Poll blocks while empty, understands this core's zero return on a drained queue, allows one consumer and wakes safely on close. Callback tests exercise actual C HAL code with mocked OS boundaries.
- Calibration is read only from the proposed private vendor layout; valid original records are transferred as checked raw counts. Missing calibration sends no synthetic record and forces unreliable status. Malformed present calibration fails HAL open. The kernel never opens a vendor/data pathname and never regenerates factory values. The precise gs_cali.ini contract, HWMON_ACC limitations and parent restoration steps are in `CALIBRATION.md`.

## Evidence and limits

The affected **entire `sensors-1.0` subtree** compiled and linked as ARM64 relocatable objects with the pinned physical configuration at `-j1`, in independently owned source/out. The new driver, accelerometer core and registration helper compiled; BMA253 and MC3416 were excluded. A complete ARM64 Image was not built: this bounded future hardware input leaves the full kernel combination/build to the parent, and does not create a second full build beside the original AOSP work.

The minimal ARM64 shared HAL compiled with `--target=aarch64-linux-android37` against independently frozen actual SDK37 Bionic/libhardware headers, with `-Wall -Wextra -Werror`, and linked against preserved real Bionic with no undefined-link allowances. Its only DT_NEEDED entry is libc. The final verifier checks its strong imports against that exact libc, including the real AArch64 IFUNC representation. This is target compile/link proof, not Android execution or linker-namespace runtime proof.

Tests run serially, on one CPU, with a1GiB address-space cap and30-second CPU limit. UBSan/bounds instrumentation is enabled:

- **8,207 assertions:** actual extracted OEM-derived decode/get-data/calibration functions, exhaustive4096-value signed12 X decode, axis signs/order, integer scale, bounds, absolute calibration/idempotence, suspended/disabled state, I²C error propagation, no overwritten output on failure, and forced hardware writes after a partial power-transition failure.
- **106 assertions:** actual production packet/calibration decoder and control-state engine, every short packet length, malformed records, signed/truncated calibration, checksum/range/clock errors, rates/dry-run/enable failure/recovery, disabled/stale samples and flush accounting.
- **30 assertions:** actual production C HAL callbacks with mock OS boundaries: module enumeration, ABI version, unsupported APIs, open failure/exclusion, short write, enable/poll conversion, metadata flush, short packet, truncated calibration, short regular-file reads, single poll and close waking a blocked poll.
- **Nine core state assertions:** actual extracted enable/batch function, failed-enable recovery through the core, preserved pre-enable period, timer start/rate change, suspend rejection without state mutation, disable and failed-batch recovery.
- **Four registration-failure/order scenarios:** actual extracted kernel registration function, duplicate minor, queue allocation failure, device-create failure/unwind and successful queue-before-publication ordering.

These are injected boundary/model tests and **do not prove hardware**. No physical gravity, axes, rates, auto-rotation, controller PM/suspend/resume, real restored calibration consumption or complete Android framework behavior was tested. No QEMU or Android runtime result is implied by the native host tests.

Frozen actual SDK37 policy generation, versioned platform/vendor merge with neverallow enforcement, file-context validation and init verification passed. Only the dedicated character device, four controls and reviewed calibration types receive new HAL permissions. The sole manifest is schema-assembled; final whole-device VINTF compatibility and full-product policy/install/architecture checks remain parent work.

The separate r5-source-chain receipt proves the entire62,224-file baseline equals the parent’s61,976-file base plus its exact268-file compiled-r5 delta. The final receipt verifies all62,224 baseline regular source files in the original physical kernel are unchanged and restricts the owned fixture to the exact nine-file delta. All282 protected runtime source hashes,58 runtime config options,16 network options and134 firstboot options remain preserved. The DT source is byte-identical and `asus,allow-battery-charging` remains absent; no framebuffer, radio or charging source is changed. The original image/config remain pinned. These preservation checks do not upgrade inherited runtime qualification.

## Artifacts and continuation

`HANDOFF.md` gives exact parent integration order and gates. `COMMISSIONING.md` gives precise paths, packet/control formats and missing parent observations without executing device commands. `patches/pre-post-hashes.json`, `patches/kernel-from-physical-r5.patch`, and the compact remote receipt/object bundle are the concrete integration inputs. `scripts/check_preimages.py` refuses mismatched source bytes; `scripts/verify_bundle.py` checks the delivered bundle locally.

No active `/srv/android/lineage24` source/out, original physical source, frozen probe or parent product-staging/r1 was modified. No competing Ninja, installclean, build restart, original-build waiter, shell worktree/checkout, private factory/key-content read, cloud lifecycle/resource action, SYSTEM/userdata copy, device command or physical GO occurred. SSH used the existing identity by path only. The source fixture uses independent copies, not hardlink-and-edit.

## Exact final pins

- Kernel patch SHA256: `1f40942ee014bda87c4e4c382b881e27c98b2034b227a06020a7e96126399cec`.
- Resolved accelerometer config SHA256: `10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`.
- Compiled SDK37 ARM64 HAL SHA256: `d083cc3d4c66a8f72f7ea9821ecc68564c5dfc9d599bed0620db369d318b9731`.

`SOURCE-PINS.json` and `patches/pre-post-hashes.json` contain the complete source and object pins. No complete kernel Image is part of these final outputs.
