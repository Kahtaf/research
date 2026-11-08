# Main-battery SOC / Android 17 Health handoff

Implemented and staged a numeric main-pad SOC continuation plus startup and
later-fault Health integration. All changes are in this new spike. The previous
measurement spike and candidate/full remain unchanged. No hardware operations,
VM writes/builds, cloud changes, goal changes or subagents were used.

## Implemented model and validity

The kernel patch applies **after** the previous measurement patch on
`717bb3c9e13ce573cfdd2dda856debd27a0fa17f`. It preserves the original ASUS four
axes (-10, 0, 25, 50 C), all eight 104-pair tables and all eight Qmax constants.
The existing interpolators use the four ASUS axes; absent 10 C tables cannot
enter the model. Table parsing is bounded before writing. Unsupported
multi-battery and aging configurations are disabled, including fixes for their
previously unguarded references.

The board transaction uses the original ASUS OAM D2 recurrence and existing
profile lookups; D2 is selected by the original `oam_d5=0`. It is not a linear
voltage-to-percentage shortcut or cover gauge. It seeds from the source's
measured-VBAT fallback, then requires a second actual ADC batch and a successful
elapsed-time model step before capacity is available. Charging enable is
initialized false, including in legacy `oam_init`.

Presence, VBAT, battery NTC and BQ status are checked. Failed/slow batches,
missing hardware, stale state and suspend invalidate SOC. A single boot clock,
30-second freshness limit and locked state prevent advancement over missing
intervals. Resume requires a new initialized update; no assumed sleep current
or unchecked wakeup OCV is integrated. Standalone failed critical measurement
reads also invalidate cached SOC. Errors remain errors, never default 50/100 or
an invented empty battery.

The actual worker, direct OAM entry points, charger interrupt, UI resets and PM
callbacks are handled. Sampling no longer depends on USB readiness. Legacy UI
tracking cannot overwrite the model. The battery thermal zone propagates checked
battery-NTC errors; the board thermistor is untouched. Charging remains inhibited:
BQ policy/control, charge limits and the absent DT charging opt-in are preserved.

## Android integration

`getHealthInfo` stays final. A status-returning hook supplies a checked board
snapshot or STATUS_UNKNOWN; existing valid callbacks and registration remain
active. HalHealthLoop retries errors instead of aborting. Device startup waits
for real SOC before service registration. Framework changes handle an initial
service-specific update error and wait for genuine initial data, closing the
race after preflight. Every battery path is pinned to the main supply.

Later faults produce errors/dump/log evidence and no invalid aggregate callback;
registered callbacks resume after recovery. The framework retains its last
valid delivery during a fault. Genuine initialized 0% remains deliverable. No
properties are spoofed and no callback is replaced with a no-op.

## Tests and limits

Three Clang ASan/UBSan host suites pass:

- Exact production model, sampling, dispatch, reset and PM logic; differential
  checks against original ASUS interpolation, Qmax, lookups and D2 statements.
  Sweeps cover 111 temperatures, 2000–5000 mV, repeated tails and both inferred
  current signs; failure tests cover each sample transport position, absence,
  initialization, freshness, suspend/resume, recovery and genuine zero.
- Exact PMIC/NTC/BQ measurement code, including checked BATON enable/readback and
  retained measurement guards.
- Exact Health aggregate, registration/update/callback and retry-loop method
  bodies, plus the production file parser: invalid startup, later faults,
  recovery without re-registration, genuine zero and a mid-update failure.

**215 strict source/replay checks pass**, including sequential prerequisite/SOC
application, both platform patches, all model numbers, tested-source hashes,
charging invariants and byte-for-byte preservation of the prior spike. Logs and
manifests are in `evidence/host-checks.json` and `evidence/source-checks.json`.

These are native macOS host tests with simulated hardware/binder primitives.
No Linux ARM64 kernel object/full kernel or Android service/framework was built;
the Mac filesystem is case-insensitive. Java changes were source-checked; no
local JDK is installed. Physical accuracy, IRQ/PM ordering and discharge/resume
behavior remain unvalidated. The original upper-profile DOD interpolation and
loaded-VBAT seed are retained, so source fidelity is not proof of calibrated
accuracy. Current/counters/full-charge individual properties remain unavailable;
health stays Unknown.

## Apply/build order and remaining work

1. Pinned kernel base, then prior `0001-asus-p00a-measured-battery.patch`.
2. This `0002-asus-p00a-checked-main-battery-soc.patch`.
3. This `0003-android17-health-checked-snapshot.patch` in hardware/interfaces.
4. This `0004-android17-battery-startup-errors.patch` in frameworks/base.
5. Merge `integration/device/asus/p00a/health/` into the parent's full product.
6. Update the actual kernel output config: enable MAIN_BATTERY_SOC, retain
   BATTERY_DIAGNOSTIC, disable MULTI_BAT_PROFILE_SUPPORT and
   BATTERY_LIFETIME_DATA_SUPPORT. Build a fresh kernel output, Health/library,
   framework services and full images. Never add `asus,allow-battery-charging`.

Exact commands, repository pins and merge details are in
[integration/APPLY-AND-BUILD.md](integration/APPLY-AND-BUILD.md). Runtime validation
covers inhibited charge-state readback, plausible measurements, startup/race
handling, discharge, suspend/staleness and fault/recovery in
[integration/RUNTIME-VALIDATION.md](integration/RUNTIME-VALIDATION.md).

No missing proprietary daemon or model-source blocker is identified. The actual
remaining gates are parent-owned Linux/Android compilation and controlled device
validation, including SOC accuracy and prolonged-fault behavior. This is a
concrete SOC/Health implementation handoff, not proof of a boot-ready persistent
tablet or authorization to charge.
