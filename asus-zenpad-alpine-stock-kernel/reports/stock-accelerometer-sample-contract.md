# Stock accelerometer: stationary sample contract

Superseding source caveat: actual2018kernel differs from retained2017V4.7.0 source. Do not rely on older driver show/store implementations as exact ABI safety proof. Active sensor/MD32 work is parked; see sensor-hub-blocker.md and opus-accelerometer-baseline.md. The passive observer was reduced to input-core operations only.

2026-11-08. Source review only. No tablet, SSH, ADB, USB, sensor/sysfs/ioctl operation, calibration access, display change, package/build or helper/config change was performed. Physical orientation mapping and touch qualification remain deferred.

**Do not enable the accelerometer or change its delay from the presently available baseline.** `/sys/android_gsensor/power` would be a pure cached-flag query in the retained source, but is not sufficient to reconstruct enable/report/polling state. The parent reports that this directory is absent in this boot. The nearest driver attribute, `powerstatus`, returns no value. The concrete blocker is that the common driver exposes no truthful getter for its active-data, active-nodata, polling or delay state, so activation followed by “disable again” cannot prove restoration of the original state.

A passive evdev observation can preserve those unknown states because it does not activate the sensor. The next live action should be the narrowly scoped metadata inventory below; it must not become an enable/sample/disable experiment if no reports are already flowing.

## Driver identification and actual attribute location

The parent's fresh metadata, `private/live/accelerometer-metadata-inventory.txt`, establishes I2C `2-0011`, device name `gsensor`, bound driver `BMA255`; `m_acc_input` currently maps to event6/dev13:70 and `m_acc_misc` to dev10:34. Event numbers are not stable identities.

This matches the retained ASUS driver **`drivers/misc/mediatek/accelerometer/bmc156_acc/bmc156_acc.c`**, despite its BMA255 function names:

- Line 71 defines `BMA255_DEV_NAME` as `BMA255`; lines248–265 register that I2C driver against `mediatek,gsensor`.
- Line 155 selects the cust-data compatible `mediatek,bmc156_acc`; lines3121–3125 register through the common accelerometer layer.
- `arch/arm64/boot/dts/asus8163_tb_380_m-Z380M.dts:47–55` supplies I2C2/address0x11/direction4/firlen0/no batching; lines287–293 supply the bound I2C node.
- The retained normal defconfig has `CONFIG_MTK_BMC156_ACC=y`, `CONFIG_MTK_BMA2X2` unset, and `CONFIG_CUSTOM_KERNEL_SENSORHUB=y` (lines495–517). The running config must still be checked; a retained defconfig is not binary-build evidence.

The driver-specific attributes are attached to the **platform `gsensor` driver**, not to the I2C BMA255 directory: `bmc156_acc.c:2933–2936` passes `bma255_init_info.platform_diver_addr->driver` to `bma255_create_attr`; `accel.c:524–533` assigns that pointer to its platform driver named `gsensor` (`accel.c:478–487`). Thus the source-derived location to inventory is **`/sys/bus/platform/drivers/gsensor/`**. `bmc156_acc.c:1983–2028` declares and creates its driver attributes.

The source separately creates `/sys/android_gsensor` and its files at `bmc156_acc.c:2986–2994`. Its absence in the current metadata is a real source/live discrepancy to retain, not a reason to guess another power path. The `power` entries already listed under input6 or `m_acc_misc` are ordinary device-PM directories, not the cached sensor-power scalar.

All source paths and line numbers here are under the retained original kernel at `../2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18/` relative to the spike root.

## What the available reads actually mean

| Attribute/path | Exact source behavior | What it cannot establish |
|---|---|---|
| `m_acc_misc/accactive` | `accel.c:337–345` returns `acc_data.vender_div`; BMC156 sets 1000 at line 2962. | Whether reporting, hardware or polling is enabled. |
| `m_acc_misc/accenablenodata` | `accel.c:273–278` logs unsupported and returns zero bytes. | `is_active_nodata`. |
| `m_acc_misc/accdelay` | `accel.c:382–387` logs unsupported and returns zero bytes. | Existing common-layer polling interval or sensor-hub delay. |
| `m_acc_misc/accbatch` | `accel.c:444–447` always returns 0. | The stored batch flag in every build. |
| `/sys/android_gsensor/power`, if present | `bmc156_acc.c:2812–2815` prints cached `sensor_power`, without hardware I/O or calibration access. | `enable_status`, active-data/nodata, polling, delay, or exact sensor-hub ownership. It is not a hardware register read. |
| Platform `gsensor/powerstatus` | `bmc156_acc.c:1867–1874` only emits debug text based on the cached flag and returns zero bytes. | A machine-readable baseline. Do not infer Off from an empty response. |
| Platform `gsensor/cpsopmode`, if inventoried | `bmc156_acc.c:1531–1538` calls `bma255_get_mode`; lines1346–1357 only read a mode register and shift its top bits. No enable or calibration operation. | Software demand flags, poll timer or sensor-hub state. It is a mode observation, not a complete enable-state getter. |
| Platform `gsensor/chipinfo`, if inventoried | Lines1500–1511 call ReadChipInfo, which formats the literal “BMC156 Chip” at line 1150. | Fresh chip-register identification or enable state. |
| Platform `gsensor/status`, if inventoried | Lines1848–1864 format configured I2C/direction/power metadata. | Dynamic enable or polling state. |

The common layer keeps **independent state**: `is_active_data`, `is_active_nodata`, `is_polling_run`, `is_batch_enable`, and atomic polling delay (`inc/accel.h:119–122`; `accel.c:149–162`). `acc_real_enable` enables hardware when either demand flag is true and disables only when both are false (`accel.c:170–203`). Enabling data sets its flag, calls open_report_data, and starts polling; disabling data cancels the timer/work and invalidates stored samples (`accel.c:206–247`). Nodata activation changes another flag (`accel.c:253–269`). A hardware Off observation does not prove that all these software fields are Off, especially after failures or direct driver controls.

The BMC156 report callback itself is a no-op (`bmc156_acc.c:2578–2581`); the common polling layer emits the input reports. Its low-level enable callback also tracks `enable_status` separately (`2585–2604`). With SENSORHUB enabled there is an additional private enable-map/status pair (`543–582`) that the power attribute does not return. The sysfs power setter calls the hub directly without updating `sensor_power` in that branch (`2817–2837`), so equal power reads cannot even prove that all hub demand returned to its old state.

Changing `accdelay` is particularly unjustified: it stores a nanosecond-derived common polling interval and calls the backend (`accel.c:348–379`), while its read callback returns nothing. Backend delay may alter hub configuration or filtering (`bmc156_acc.c:2607–2654`). The allocation default 200 ms is not evidence of the current value.

## Sample paths that must not be mistaken for pure queries

- `/sys/android_gsensor/value`, platform `cpsdata` and platform `sensordata` reach CompassReadData/ReadSensorData (`bmc156_acc.c:1642–1667`, `2707–2719`). Those functions power on a disabled chip and set `sensor_power = enable_status = true`, with no paired restoration (`1171–1180`, `1221–1226`). They are unsuitable baseline reads.
- `/dev/gsensor` `GSENSOR_IOCTL_READ_SENSORDATA` reaches the same auto-power-on function (`2296–2307`). INIT reinitializes the device (`2278–2279`) and changes configuration. Neither is allowed for this gate.
- The chip driver's READ_RAW_DATA calls a register-read function without explicit power-on (`1266–1283`, `2323–2333`), but cannot establish a fresh measurement while suspended; its ioctl wrapper ignores the read function's error and subsequently uses `strlen` on its stack buffer. It is not the selected contract. Never use a generic “read all sensor ioctls” tool.
- The common factory implementation's READ_SENSORDATA explicitly enables nodata before obtaining data (`accel_factory.c:71–91`). Its node is normally skipped when `is_use_common_factory` is false (`229–237`). A device name alone does not make different ioctl implementations interchangeable.
- **Never open/read/write `gs_cali`, `resetcali`, `atd_caligs`, `cali`, or calibration files/ioctls.** The first two are read callbacks that write/reset calibration (`bmc156_acc.c:2728–2800`); gs_cali can also persist it. Do not recursively cat sysfs. FIFO/self-test/mode/range/bandwidth controls are outside this experiment.

## ONE nonactivating observation contract, after metadata confirmation

The permitted sample mechanism is a bounded, passive observation of the existing **`m_acc_input` evdev stream**. It requires no enable or delay preimage because neither is changed. It is not a route to force data from an inactive sensor.

`accel.c:562–594` allocates/registers that input device and installs **no input open/close callback**. The stock evdev open calls input_open_device (`drivers/input/evdev.c:325–342,404–433`), which calls a hardware driver's open hook only if present (`drivers/input/input.c:581–598`). Here no such hook is set. Closing similarly has no sensor close hook. Opening this exact input node cannot start the common accelerometer timer or call the BMC156 enable function. Evdev gives each reader its own queue, so a passive extra reader does not consume another client's events.

If the parent chooses this observation after confirming the names below:

1. Keep the tablet stationary and preserve the current display/session. Resolve the current event node from `accdevnum` plus canonical input name/dev metadata; require `m_acc_input`, not a remembered event6.
2. Open that evdev node read-only/nonblocking, without EVIOCGRAB, writes, enable/delay operations or other sensor devices. A maximum 3 s wall-clock window and a small event cap are sufficient. Native aarch64 input_event records are 24 bytes; decode their signed values correctly.
3. Read-only EVIOCGABS for ABS_X/Y/Z may seed cached axis values; `evdev.c:1026–1038` only copies cached absinfo. Cached values alone are **not fresh samples**. Track subsequent ABS updates and require fresh REL_X update/timestamp fields followed by SYN_REPORT. The common driver emits ABS_X/Y/Z/ABS_WHEEL status, REL_X update, REL_HWHEEL timestamp-high, REL_DIAL timestamp-low and SYN_REPORT (`inc/accel.h:40–46`; `accel.c:668–683`). Unchanged ABS axes may be suppressed, so do not demand three new ABS events on every stationary packet.
4. End on the first small set of fresh complete reports or the deadline, then close only this descriptor. No cleanup write is needed. A timeout means “no existing reports observed”; **do not enable, alter delay, reset, move the tablet or try another ABI**. An event reports the driver's value, not independently proven sensor health: the non-hub getter does not propagate ReadSensorData errors (`bmc156_acc.c:2697–2703`).

This can establish only that the already active stock reporting path supplies stationary values. It cannot establish portrait/landscape axis mapping, auto-rotation, touch alignment or physical usability. If no reports are present, the activation blocker remains.

## Next live step: names/metadata inventory only

Before any additional value read or passive observation, parent should inventory only:

- `/sys/bus/platform/drivers/gsensor/` entry names, mode/type and symlink targets; specifically whether `chipinfo`, `status`, `powerstatus`, `cpsopmode` exist. Do not traverse/read attribute contents in bulk.
- `/sys/bus/i2c/devices/2-0011/{name,driver,of_node}` metadata and compatible/DT cust_accel names to bind the source choice; preserve current driver BMA255 evidence.
- Existing `m_acc_misc`/`m_acc_input` canonical paths, name, dev major/minor and input capability metadata; `accdevnum` is a source-proven pure mapping query (`accel.c:390–401`).
- Existence/type of `/sys/android_gsensor` and `/dev/gsensor` only. Absence must remain absence; do not create nodes, rebind drivers or load modules.
- Running kernel configuration for BMC156_ACC, OF and CUSTOM_KERNEL_SENSORHUB if `/proc/config.gz` is already available. This is ordinary kernel metadata, not a sensor query.

Do not treat those inventories—or a later cpsopmode/cached-power read—as permission to activate. A truthful readable snapshot/restore interface for demand flags, polling and delay, or an independently proved exclusive known initial state, is still missing for an active experiment. No script or active sampling implementation was added.
