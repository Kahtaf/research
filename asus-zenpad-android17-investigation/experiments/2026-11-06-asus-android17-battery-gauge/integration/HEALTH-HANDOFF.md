# Main battery Health handoff

The staged full product already names the right paths. Do not change them to
`pack_bat`, `upi`, or a cover gauge. This spike does not edit any full-candidate
file. The 2 GiB RAM SKU does not turn the optional cover into the internal battery.

Use `/sys/class/power_supply/battery/` with:

- `status`: actual BQ25896 charge state; `Not charging` with PG high and the
  charging-enable bit clear; errors before probe or during suspend.
- `present`: checked MT6323 BATON detector. Missing/disabled detector or transport
  failure is an error, not an invented absent/present result.
- `voltage_now`: channel 6 (ISENSE), microvolts.
- `temp`: channel 5 (BATON1), tenths Celsius, ASUS **battery** NTC network.
- `technology`: Li-ion, from the original battery declaration.
- `health`: Unknown until fault/health assessment is integrated. It never claims
  Good from presence alone. Health reads do not clear the charger's fault latch.
- `capacity`, `charge_full`, `charge_counter`: `ENODATA`. Current is unavailable;
  do not use charger programmed-current or charge-only ADC as net battery current.

The compatibility aliases `batt_vol` and `batt_temp` use the 4.9 convention of
microvolts and tenths Celsius. Other engineering caches return `ENODATA` through
the power-supply property interface. Legacy debug sysfs outside that interface
is not validated by this patch and must not feed Health.

## Aggregate HealthInfo is NOT error transparent

Evidence: `evidence/platform-source.json` pins actual Android 17 source. In
`system/core/healthd/BatteryMonitor.cpp`, `updateValues()` substitutes zero for
capacity when no last-good value exists; a previous value expires after its
staleness interval. `getProperty()` instead returns NAME_NOT_FOUND for failed
reads. `Health::getCapacity()` preserves this failure status, but the final
(non-overridable) `Health::getHealthInfo()` returns a successful aggregate using
`updateValues()`. Individual-getter error handling therefore does **not** make
the current default aggregate service safe for unavailable SOC.

`BatteryService.shouldShutdownLocked()` can request low-battery shutdown for
present=true, level=0, and status other than Charging. Even Unknown is not a
reliable escape here. Do not manufacture Charging, absent, or a positive level.

`health-preflight.inc` gives a concrete startup gate for the full-product owner.
It is deliberately diagnostic and will reject this patch's unavailable SOC.
It prevents a known-invalid initial aggregate; it does not solve runtime errors.
Keep the full Health service disabled in a measurement-only diagnostic product,
or implement an aggregate interface that can return errors and suppress invalid
callbacks. A genuine full Health service still needs the SOC continuation in
`REPORT.md`, plus a deliberate runtime-error policy. Do not simply leave the
existing service running and call the battery gap closed.

No charger-mode service should be enabled. This patch does not opt in to charging.
No proprietary `upi_ug31xx` executable is required for these main-battery reads.
