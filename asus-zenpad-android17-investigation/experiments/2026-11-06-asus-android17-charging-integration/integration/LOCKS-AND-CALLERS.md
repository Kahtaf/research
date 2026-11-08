# Ownership, callers, errors and timing

The only board model remains the preceding SOC patch's OAM D2 implementation.
The new charger-owned object contains a copy of its checked sample, its original
boottime timestamp, a publication generation and validity. It contains no second
SOC estimator, NTC table, fallback percentage or invented current.

`FGADC_mutex` may acquire `p00a_global_lock`, then `p->lock`. The charger never
acquires FGADC_mutex and never calls a SOC or battery-property getter. The
existing SOC sample calls the BQ status API under FGADC_mutex; that API acquires
global then charger lock and reads its own regmap directly. Publication takes
the same locks. A charger decision and an invalidating publication therefore
cannot interleave between a snapshot check and an enable write. The invalidator
returns only after disable/readback was attempted. A failed disable remains an
error, with separate `disable_error`; publication does not promise physical off
when I2C is unavailable. No spinlock is held over sleeping I/O.

The publication helper is called from the successful SOC transaction while
FGADC_mutex remains held, after a real model step. The existing repeated-call
path does not publish or refresh time. Every `p00a_soc_fault_locked` publishes
invalidity, including ADC/status failure, missing battery, stale model, explicit
invalidation and suspend. Direct Health voltage/temperature/presence/status
errors already reach this path through the SOC patch. Failed BQ status and
transport-backed command reads also invalidate the charger's copy and attempt
disable without recursively invoking SOC. A newly published unsafe temperature
or voltage stops an existing session immediately; thermal recovery retains the
reviewed hysteresis in tenths Celsius, without truncating 46.9 C to 46 C.

The battery worker still calls charger detection before sampling when USB is
ready. Its next successful model update publishes the snapshot; then the new
runtime request sets a bounded 4.208 V / 512 mA request through the existing
permission guard. SOC seeding disables charging and retains ASUS's 50 ms settle
and second real sample. Regular initialized D2 updates no longer disable every
cycle or reject actual Charging/Full status. Model staleness is tested before
capture so a re-seed cannot accidentally occur with charging enabled; a capture
which crosses the age limit fails and the next transaction seeds from off.

There is also an actual source-event path, not just a getter. The pinned PMIC
`chrdet_int_handler` invokes `do_chrdet_int_task` from its nested threaded IRQ.
`mt6323_irq`/`mt6323_do_handle_events` hold the wake source but not pmic_lock or
pmic_access_mutex while invoking the callback. The new callback invalidates the
charger copy, disables, restores 100 mA and clears classification even if a rapid
unplug/replug produces the same final REG0B value. This avoids adding an opposite
PMIC-mutex-to-charger-mutex edge. No sleeping SOC update is added to the IRQ.
The legacy callback then wakes the battery worker as before. Physical delivery
of this IRQ and the I2C/PMIC interrupt timing remain acceptance gates.

The BQ monitor checks actual status/faults, checked sample age and a BQ one-shot
ADC completion. It normally runs every five seconds and schedules sooner when
the 30-second sample deadline is closer. All enable attempts recheck age after
conversion and before the write. No enable succeeds on an expired snapshot.
This is scheduled software supervision, not a hard real-time cutoff: scheduler
stalls, I2C timeouts and interrupt latency are not bounded by these host tests.
Hardware NTC and safety timer remain essential independent protection.

BQ REG0C has exactly one reader: the guard. The first result is saved and its
upper fault bits latched before the second read. A second-read failure cannot
lose the consumed fault. NTC bits use the current second result, not an OR of
different encoded NTC states. Watchdog/charge/boost/BAT faults remain sticky
until observed unplug; reset/config drift can require driver reprobe because
fixed safety settings are not silently repaired into charging. Telemetry and
legacy DUMP/GET_FAULT use cached results and never consume the hardware latch.

Checked BC1.2 uses the existing MT8163 sequence with PMIC read/write/readback
errors and cleanup propagated. It takes a separate BC1.2 mutex, then the
existing pmic_lock and pmic_access_mutex for individual register operations.
It never acquires FGADC_mutex or calls BQ. USB PHY init/release retain their
existing void MMIO ABI; clock/mux correctness still requires target/hardware
validation. No result from the old error-discarding PMIC classifier authorizes
an increased limit. Unknown, nonstandard and unqualified SDP are 100 mA;
checked DCP is capped at 1000 mA and CDP at 1500 mA. These never exceed the old
reviewed policy. No USB enumeration-granted current ABI is invented.

Suspend quiesces and invalidates before the bus suspends, then cancels work
outside the charger mutex. An unverified disable aborts suspend and schedules
retry. Resume verifies off, clears request/sample/classification and requires a
new publication and source check. APIs invoked while suspended return an error
without touching a suspended I2C bus. Remove withdraws the global pointer and
read-only attribute, serializes disable, cancels work and reports errors;
shutdown latches `stopped`, disables and reports failures. No BQ-to-SOC call is
used in any lifecycle path.

While approved charging is active, a device wake source keeps supervision
running with the display off. It is released on verified disable, not after an
unverified failed write. Autonomous charging in system suspend is deliberately
not implemented: the hardware TS thresholds, actual battery wiring, safety
settings, reset behavior and IRQ wake route have not been physically qualified
against this board's stricter software thresholds. Sleep freshness is never
fabricated. This awake policy is a functional intermediate, with daily-use
power costs documented in REPORT.
