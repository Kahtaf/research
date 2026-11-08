# Checked charging integration handoff

**Staged for parent review; not applied or hardware-qualified.** The 11-file
kernel patch applies after measured-battery 0001 and SOC 0002 on
`717bb3c9e13ce573cfdd2dda856debd27a0fa17f`. Default DT charging permission remains
absent. No candidate, live kernel, VM, device, cloud, goal, calibration or user
data was changed. No subagents or target builds were used.

## Implemented

- A charger-owned, mutex-serialized copy of the real checked SOC sample,
  original boottime timestamp and publication generation replaces cached
  `BMT_status` plausibility. Startup, ADC/status failure, absent battery, stale
  state, source transitions and PM invalidate authorization. The charger never
  takes the SOC mutex; publication and enable cannot race across separate locks.
- Disable and enable writes have real readback. Configuration, programmed limits,
  source and faults are checked around enable. Failures remain errors; failed
  disable attempts input isolation and retains an explicit unverified state.
  Safety timer, hardware NTC and termination remain enabled; watchdog reset to
  charging defaults is not used as an off timer. Unexpected faults/config drift
  stop charging, with conservative sticky fault handling.
- One owner consumes REG0C, preserving the first fault even if its second read
  fails. Telemetry does not consume fault latches. The read-only `charge_guard`
  attribute exposes actual enable/state/limits, errors, sample age, raw safety
  registers and fault history. Completed BQ ADC charge-path current has a
  separate validity/age indication; it is never claimed as net battery current.
- Checked MT6323 BC1.2 transactions propagate transport/readback/cleanup errors.
  Unknown/nonstandard/SDP stay at 100 mA; checked DCP/CDP ceilings are 1000/1500 mA.
  The actual threaded charger-detect callback clears the prior cap and sample,
  including rapid unplug/replug. No arbitrary writer or new service was added.
- The existing OAM model is retained. Only seeding requires charging off; regular
  checked updates now accept real charging state. The worker stages a bounded
  4.208 V / 512 mA request behind the unchanged permission guard. An approved
  future charging session holds a wake source for supervision. Suspend still
  verifies off; resume requires fresh sampling/classification. Remove/shutdown
  serialize stopping and report failed disable instead of acknowledging success.

## Actual validation

Three native Clang ASan/UBSan suites pass using exact production includes or
extracted method bodies with simulated hardware/time:

- **3,339 charger assertions:** startup/staleness, temperature hysteresis,
  transport failures at every successful apply position, ignored writes,
  enable/disable readback, fault retention, BQ conversion timeout, reset during
  conversion/programming, source limits/events, telemetry errors, PM/lifecycle
  and a real pthread publication/enable serialization case.
- **1,736,569 model assertions:** retained ASUS-source differential oracle,
  actual sampling/dispatch/PM logic, charging samples, publication rejection,
  missing battery, later ADC faults, stale state and recovery. Most assertions
  are model sweeps, not distinct hardware scenarios.
- **17,364 BC1.2 assertions:** every classification branch, each transport
  failure position, ignored writes, cleanup and unchanged outputs on error.

**173 source/configuration/provenance/replay checks pass.** All three kernel
patches replay sequentially and reproduce the staged bytes. Re-generating this
patch gives the same SHA256:
`aa827a36912d94012ebf85b10dd07af576ac29adbd3c68976a3bf7aa43c9a187`.
Forty-four comparisons confirm relevant prior frozen/staged inputs are unchanged.
Evidence and commands are under `evidence/` and `scripts/`.

No ARM64 object/full kernel or Android build ran. Host tests do not establish
kernel ABI/link correctness, real IRQ/PM ordering, physical measurement accuracy,
source classification or charging safety. I2C loss cannot be turned into a
physical-off guarantee; scheduler/transport stalls are not hard real-time bounds.

## How the parent advances

Use [APPLY-AND-BUILD](integration/APPLY-AND-BUILD.md) for exact parent-owned ARM64
commands and [LOCKS-AND-CALLERS](integration/LOCKS-AND-CALLERS.md) for the ordering
and error audit. Follow [COMMISSIONING](integration/COMMISSIONING.md) in order:
inhibited target build/first boot, measured PMIC/BQ/source/PM validation, fault
and thermal qualification, then a separately reviewed enablement candidate and
attended charge-gain test. No enable-property patch is supplied here.

This is a functional runtime charging path awaiting those gates, **not a claim
that always-inhibited charging completes the tablet**. The awake supervision
policy avoids silently suspending into net discharge during an approved session,
but consumes standby power and remains awake at hardware termination. Unknown
or SDP 100 mA can still yield net discharge. Efficient overnight charging across
real suspend, USB enumeration current grants, long-term SOC accuracy, heavy-load
charge gain and hardware reset/thermal behavior remain daily-use gates. Never
solve them by declaring stale samples fresh or simply removing suspend guards.
