# Model and caller audit

Pinned search results are in `evidence/kernel-callers-complete.txt` and
`evidence/kernel-callers.txt`. Sources are preserved under `source/` with hashes.
The main battery is MT6323 AUXADC plus SOC_BY_SW_FG. `pack_bat` is not consulted.

## Model

The original ASUS DT has four temperatures (-10, 0, 25, 50 C), eight 104-pair
voltage/DOD and resistance/voltage tables, and eight Qmax constants. Source checks
compare every number to the original ASUS DT. The kernel's live tables are now
104 entries for this config. The optional 10 C path is bypassed in the existing
four interpolators, including both Qmax variants; no synthetic 10 C fit is made.
Missing intermediate tables cannot alias the 0 C parser destination. The parser
is bounded before writing (the old limit check admitted an extra pair).

The exact ASUS interpolation convention is retained: battery voltage and R are
interpolated by temperature, with the battery DOD field taken from the upper
profile at each index. The raw DOD axes differ between temperatures. This is
source fidelity, not a newly validated calibration scheme. All repeated tail
pairs remain; lookups preserve the original first matching segment at an exact
repeated voltage. Skipping zero-width segments prevents division by zero without
silently choosing a different tail resistance or DOD. Host differential tests
compare the original ASUS constructors, Qmax and three lookups over 111 integer
temperatures, 2000–5000 mV and DOD 0–100.

The original DT chooses `oam_d5=0`. D2 is an independent recurrence in original
ASUS `oam_run`: inferred I2 from OCV2, VBAT and R2; elapsed-time integration into
CAR2; D2 from D0 and Qmax; updated OCV2 and R2 from the original profiles. D1/D3/D5
do not feed it. The new transaction retains that recurrence with widened
arithmetic and the existing lookup functions. Independent statements extracted
from ASUS 3.18 are compared against production for both signs of inferred
current. This intentionally uses ASUS's recurrence, not the generic 4.9 clamp
against charger-programmed current. Inferred current is not exposed as measured
net current. High-current Qmax tables remain exact and tested but the disabled
OCV2CV transform is not activated.

Initialization uses the source's measured-VBAT fallback with charging disabled
and its 50 ms settling interval. It does not pretend the PMIC wakeup OCV latch
has known freshness. No RTC/UI SOC, default 50%, assumed sleep current, aging
fit, alternate-battery data or persisted per-unit calibration participates.
The loaded-voltage seed can be biased by load/relaxation; this and the inherited
profile interpolation behavior need actual discharge/resume validation.

## Ownership, callers and timing

`FGADC_mutex` protects model construction, state transitions, publication and
PM invalidation. Each sample checks detector presence, five VBAT conversions,
five battery-NTC conversions, BQ status, and detector presence again. BATON is
enabled by checked writes/readback of the same two bits used by the legacy
battery check. The prior read helper still rejects disabled/reset detectors.
No ADC/transport result is inferred from an output left behind after failure.

A batch taking more than two seconds is rejected. Initialization is private;
a second actual batch after 1.1 seconds and a successful D2 step are required
before capacity becomes available. One monotonic boot clock is used. Repeated
calls within one whole second cannot advance or refresh validity. Capacity
expires after 30 seconds. Errors invalidate immediately; the next successful
transaction re-seeds and performs a new model update.

The board-specific BAT_thread updates real measurements and SOC, retains USB/AC
reporting and existing thermal checking, and requests charging inhibition on
failures. It does not run old UI-SOC tracking, current smoothing or charge-limit
programming. The unchanged independent BQ guard still runs every five seconds.
The worker no longer waits for USB readiness; charger/USB detection itself is
called only when USB is ready. BQ initialization still gates the battery worker.

Direct `oam_init`, `oam_run` and `battery_meter_initial` entry points dispatch to
the checked transaction. `battery_meter_get_battery_percentage` reads only valid
state and returns errno otherwise. UI reset functions cannot overwrite D0/CAR
or import a fabricated UI percentage; `battery_meter_reset` returns unsupported.
The charger interrupt no longer runs the sleeping initializer itself and wakes
the worker instead. The external reset caller in switch_charging cannot mutate
the model. Unsupported multi-battery/aging options and their unguarded baseline
references are corrected in the selected configuration.

Meter suspend invalidates under the same mutex and prevents sampling. Resume
invalidates again and wakes the battery worker. The old unchecked wakeup-OCV and
assumed-sleep-current arithmetic is unreachable for this board. A missing or
suspended interval is never integrated using a later voltage; the two-sample
source-derived seed is repeated. Legacy battery timer resume reaches the same
checked BAT_thread; locks remain in battery-mutex then FGADC-mutex order.
No charging/PMIC helper acquires FGADC_mutex while retaining its own hardware lock.

Standalone failed voltage/temp/presence/status property reads invalidate cached
SOC immediately. The battery thermal zone uses the same checked battery NTC
property and returns errno instead of converting errno into a temperature or
using its old synthetic 25 C boot value. The separate board thermistor driver is
unchanged. The auxiliary battery-presence check no longer interprets failed
reads as absence and shutdown; actual checked absence preserves the prior
power-off behavior. Legacy engineering/debug sysfs is not a Health input and
is not claimed as a validated measurement interface.

## Android callers

Source pins cover BatteryMonitor, Health, HalHealthLoop, BatteryService and both
AIDL framework wrappers. BatteryMonitor's aggregate failure-to-zero behavior is
unchanged for generic products; P00aHealth replaces critical fields only after
its checked read succeeds. Capacity is read last, so a preceding measurement
error cannot be hidden by a formerly valid SOC cache. Failed aggregates return
STATUS_UNKNOWN and valid callback delivery remains intact.

Two additional actual callers required changes: HalHealthLoop had a fatal CHECK
on aggregate error; initial HealthRegCallbackAidl.update caught only transport
exceptions. The staged patches fix both. The initial BatteryService wait now
requires non-null genuine data under its lock. A preflight alone would leave
these later/error-race paths broken.

The host suites compile exact production bodies/includes with simulated clocks,
PMIC/I2C, kernel primitives, binder and BatteryMonitor. They test actual dispatch,
reset immunity, PM invalidation, failure/recovery, battery thermal errno, original
model arithmetic, retained callback registration, later recovery and genuine 0%.
They do not validate Linux linking, Android binder ABI, IRQ concurrency, PM ordering
on the physical tablet, sensor accuracy, aging or remaining full-ROM integration.
