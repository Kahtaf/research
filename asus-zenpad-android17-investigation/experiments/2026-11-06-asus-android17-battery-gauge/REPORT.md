# Battery implementation handoff

Delivered the bounded main-battery measurement path allowed by the task. It is
staged against `717bb3c9e13ce573cfdd2dda856debd27a0fa17f`, not applied to the VM.
It replaces misleading Health-facing caches with real sensor reads and explicit
unavailability. It does **not** deliver a complete numeric SOC estimator or a
working aggregate Android Health service. Charging remains inhibited.

## Hardware/protocol finding

**UG31xx is the optional cover, not the pad gauge.** Original ASUS
`arch/arm64/boot/dts/asus8163_tb_380_m-Z380M.dts:245` calls the node
`cover_upi_gauge@70`. `drivers/power/mediatek/battery_others/upi_ug31xx/upi_ug31xx.h:25`
names its supply `pack_bat`. That driver's transport checks `COVER_ATTACHED_UPI()`.
Existing stock evidence independently records `battery` present=1, level=99,
Li-ion, while `pack_bat` is present=0, level=-1 and temperature=-2731. No new
hardware observation was made. The reference evidence is
`../2026-11-05-asus-root-hardware-validation/evidence/root-hardware-baseline.txt:69`.

The cover driver does not just proxy a proprietary SOC daemon. Its Makefile
builds `GaugeMain`, `Measurement`, `Capacity`, `VCapacity`, `GasGauge`, `Sbs`,
`Reg` and model tables into the kernel. Work functions call `GMainInit()` and
`GMainTask()`. The source register protocol uses I2C address 0x70; byte-addressed
reads send the register index, plus 0x5a for addresses >=0x80. Words are little
endian, with a repeated-read stability check and a bounded retry count of ten.
These are chip register transactions, not directly usable SBS percentages.

The optional `/dev/upi_ug31xx` ABI uses ioctl magic 'U', direction READ|WRITE,
operations 1..4 for SBS read word/write word/read page/write page. User buffers
start with command byte, length byte, then payload. Word payloads are two bytes;
page payload length is in byte 1. The driver dispatches on direction/number,
ignoring ioctl pointer-size encoding, and assigns the same function to
`compat_ioctl`. Its stock command-line program is referenced only in commented
log-reset actions in the inspected ramdisk. There is no evidence of a mandatory
main-battery proprietary daemon here. Importing that executable or duplicating
this cover ioctl ABI would not solve the pad battery task. No cover support or
unnecessary legacy ioctl surface is added.

The actual main battery uses the MT6323 PMIC ADC and MediaTek's in-kernel
`SOC_BY_SW_FG`/OAM software model, with BQ25896 charge control. Original
`mach/mt_battery_meter.h` selects PMIC channel 6 (ISENSE) for VBAT, 7 (BATSNS)
for VSYS, 4 for charger sense, 5 (BATON1) for the battery NTC, and the external
charger power-path OCV route. The 4.9 generic defaults were 0/1/2/3; its own
MT6323 reader explicitly rejects channel 0. The existing AUXADC0/390k/curve-6
thermal port measures a **board** thermistor and must not replace the main
battery's 16.9k/30k/1.8V, 10k NTC network.

## Implemented source

The 12-file patch adds `CONFIG_ASUS_P00A_BATTERY_DIAGNOSTIC`, dependent on the
existing built-in pad charger and PMIC. It selects the correct routes in the
board header and DT, including the power-path OCV selection and battery
thermistor pull-down value. It adds:

1. A checked MT6323 ADC conversion helper using the existing ADC mutex and wake
   source. ADC4..7 map to ADC2, ADC3, ADC1, ADC0 respectively. Conversion-ready
   and decimation-workaround polls are bounded; transport failures and timeouts
   propagate. A failed read never publishes its uninitialized/stale output.
   Existing callers of these channels use the same serialized helper.
2. Direct BATON presence reads, refusing the detector's disabled/reset state.
   No inferred presence from voltage and no false absence on transport failure.
3. The exact 17-point ASUS battery NTC curve, correct parallel-resistor
   compensation, output in tenths Celsius, and rail/out-of-curve errors.
4. BQ charge-state reads serialized with the existing charger driver. PG high
   plus CHG_CONFIG clear means Not charging, even if old state bits say done.
   The code does not consume REG0C's read-to-clear fault latch or write charging
   controls. Register semantics were checked against
   [TI BQ25896 Rev. C](https://www.ti.com/lit/ds/symlink/bq25896.pdf), sections
   9.2.9 and 9.4.4/9.4.12.
5. A diagnostic override for the existing `battery` power supply: measured
   voltage_now/temp/present/status, known Li-ion technology, Unknown health,
   and ENODATA for unavailable SOC/current/counters and unvalidated engineering
   caches. The existing voltage_now property is retained exactly once.

“Read-only” describes the userspace battery interface and charge policy. An ADC
measurement necessarily writes its conversion request/buffer/decimation bits;
the allowed register set is checked in the host harness. The new code does not
set charging permission, change current limits, program battery models, persist
calibration, or write device storage. No hardware operation was executed here.

## What passed, and what has not run

- 9,713 host assertions pass with Clang, AddressSanitizer and UBSan. This compiles
  the exact three production additions (`pmic_battery.inc`, `battery_status.inc`,
  `battery_diag.c`) against simulated kernel primitives/transports. Assertions
  cover each failing transport position, bounded ADC timeouts, decimation busy
  timeout/recovery, cleanup, source-proven PMIC register routing, temperature
  conversion/domain, all 256 status bytes with charging enabled/inhibited,
  missing hardware and explicit unavailable outputs. The count includes mock
  lock/register checks; these are not 9,713 hardware tests.
- 67 source checks pass: pinned hashes, all 17 original NTC pairs/resistors,
  mappings independently derived from actual 4.9 PMIC accessor source, guard
  preservation and exact `git apply --check`/replay of all twelve files.
- No full kernel or ARM64 kernel object was built in this task. The host harness
  is not evidence of 4.9 API/link correctness. No VM source writes/builds, device
  access, flashing, cloud changes or goal changes occurred.
- IRQ/interleaving behavior, PMIC ADC settling, presence routing, physical units,
  discharge behavior and suspend/resume remain runtime unknown. The main
  charging guard file and charging opt-in DT are unchanged.

See `evidence/host-checks.json`, `evidence/source-checks.json`, and the two source
manifests. Build/apply instructions are in `integration/APPLY-AND-BUILD.md`.

## Remaining SOC and Health work: concrete, not a missing proprietary daemon

There is **no identified external source/proprietary-daemon blocker** for the
main battery. The remaining implementation is the existing software estimator:

- The ASUS profiles provide four temperature axes (-10, 0, 25, 50 C), 104 pairs
  each. The 4.9 implementation has a 100-entry allocation and an extra 10 C axis;
  its `battery_profile_t1_5`/`r_profile_t1_5` and corresponding Qmax data are absent
  from this ASUS DT. Some tail pairs are duplicates, but silently truncating is
  not a source-verified conversion. Reconcile the four-axis model or explicitly
  generate and check the 10 C interpolation and consistent table sizes.
- Multi-battery ID and battery-aging options are enabled in the candidate without
  matching ASUS `_1`/aging data. Select the actual ASUS profile or disable these
  unsupported branches; otherwise blank/default tables may enter the model.
- `oam_init()` passes an uninitialized `charging_enable` to the charging command.
  Initialize it to false when reconciling that path. The current charger guard
  still blocks actual charging; this task does not use OAM for public values.
- Meter callers ignore several transport return values and publish initial 50%
  or stale estimates. Provide a valid hardware sample before model advancement,
  propagate invalid/stale state across the algorithm and suspend/resume, and
  expose capacity only after a successful initialized model update. Do not map
  ADC voltage linearly to a percentage, use the cover SOC, or substitute 50/100.
- The old OAM/charging thread still runs internally; it is not certified by this
  diagnostic override. Its incomplete tables/error behavior remain a boot and
  power-management risk. The patch does not claim that shielding Health-facing
  properties cures that internal path.

Parent can assign this bounded OAM reconciliation next using the source already
present; no stock daemon or private per-unit calibration upload is required.
Then have the build owner compile the changed kernel and validate the primary
sysfs values on hardware under the unchanged charging guard.

**Android 17 aggregate HealthInfo needs special attention now.** The actual
pinned BatteryMonitor converts an unavailable capacity to 0 in its aggregate,
although individual getters return errors. Present + 0 + Not charging can trigger
BatteryService shutdown. `getHealthInfo` is final in the default Health class,
so a naive subclass cannot override it. Do not start that full service with this
measurement-only kernel and claim success. The own-spike integration document
and preflight snippet explain the boundary; the full-product owner must either
wait for valid SOC or implement aggregate error handling. No full Health file
was edited. A preflight alone does not handle later sensor faults.

## Exact charging prerequisites

Keep `asus,allow-battery-charging` absent. Before any later enablement:

1. Build on the case-sensitive Linux tree and verify the new config, source
   hashes and DT guard. Exercise raw measurements on the actual kernel while
   CHG_CONFIG remains clear, including plugged/unplugged and suspend/resume.
   Compare VBAT and battery NTC against stock/independent observations; confirm
   detector enable/presence and ADC failure paths.
2. Finish the internal gauge sample-validity path above. The current charge
   guard consumes BMT_status fields; plausible cached values alone do not prove
   they are fresh. Connect sensor errors/staleness to charge inhibition before
   relying on those values for charging decisions.
3. Confirm BQ fault handling, charge-enable readback, input-source/current limit,
   voltage limit, watchdog/reset behavior and thermal stop/recovery on this
   board. Preserve NTC/safety-timer controls and disabled cover/OTG routing.
4. Only after the parent has a controlled hardware/restore plan, test a bounded
   conservative charge session, measured charge gain and temperature, unplug,
   fault/timeout and suspend behavior. Opting in is a separate reviewed change;
   this patch neither deletes the guard nor treats a successful compile as that
   authorization.

This is a source-checked diagnostic measurement delivery, not a flash-ready ROM
or a complete Android battery service.
