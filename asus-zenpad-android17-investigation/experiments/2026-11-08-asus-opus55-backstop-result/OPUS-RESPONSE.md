# Recommendation: run the battery-uevent property-omission A/B once

Your proposal is the right next unit. It is the only option left that removes the one chain we have actually seen during the loss window, without touching protection paths and without adding more polling or loop variants. Another readiness or counter capture would have the same problem as the budget trial: if the stall sits inside a single MMIO read, counter read or lock, the capture can't report it. The A/B gives a binary answer on the path. It does not give a mechanism, and it shouldn't claim one.

## Exact intervention boundary

- **Where:** inside `power_supply_uevent()` only, and only when `psy->desc->name` matches the named battery.
  - Emit `POWER_SUPPLY_NAME` as now.
  - Skip the loop that calls `power_supply_show_property()` / `get_property` for each property.
  - Return 0. Don't return an error, don't put placeholder values in the environment, and don't fake data.
- **Leave unchanged:** everything else in `power_supply_changed_work`. That means the `changed_lock` handling, the `changed` flag, the `class_for_each_device` loop that calls each supplicant's `external_power_changed`, the notifier chain, the `kobject_uevent()` call itself, and `pm_relax`. Sysfs property reads, thermal-zone `get_temp`, charger and battery-meter workers, WDT, SPM and thermal routes all stay as they are.
- **Evidence the path ran:** add one static first-hit flag (a count of omitted readouts) set in the skip branch. Drain it once, cold, through the existing calibrated writer at the same post-callback drain point you used for the budget record. Don't publish under locks, and don't add new clock reads.
- **Keep frozen:** the helper, ramdisk, config, DT, bootargs, and the budget patch. Keep the budget in, so the delta from the last trial is exactly one change.

## Interpreting the result

**POSITIVE:** the drain flag appears, and so do seq101, the 2M marker, and afterIRQ/alarm.
- Conclusion: the property read inside the battery uevent is necessary for the execution loss in this exposure.
- It does not tell you whether the cause is pwrap, AUXADC, the delay, or locking.
- Next step: repair the real battery read separately. You can then use the sustained PID1 window for MMC work.

**NEGATIVE:** the drain flag appears, meaning the omitted path ran and returned, and seq100 is still the last write.
- Conclusion: the uevent readout is not required for the loss.
- Stop treating the battery-notification chain as the main suspect.
- The 100th write being consistently last then becomes the main question, because the loss is then probably about whatever runs after WRET (IRQ restore, preemption point, syscall exit) and not about this worker.

**UNKNOWN:** no drain flag and no seq101.
- Either the path wasn't reached in this exposure, or the drain never happened. You can't tell which.
- Draw no conclusion and stop. Don't repeat the boot.

**Also UNKNOWN for the path question:** seq101 appears but there's no drain flag.
- The run differed for a reason other than the omission.
- Record it as non-causal.

## Stated limits

- The A/B tests "uevent property readout is required". It does not test "AUXADC channel 6 is never touched". Other in-kernel readers of the battery may still drive channel 6: `external_power_changed` callbacks, a thermal zone, or the battery-meter thread.
- So a NEGATIVE result excludes the uevent path, not AUXADC or pwrap as a whole.
- A POSITIVE result is also limited: it shows that the extra uevent-triggered read, on top of whatever traffic remains, is what matters.

## The one source fact to check first

In the compiled tree, list every in-kernel caller that reaches the AUXADC channel-6 / `batt_vol` read for this battery, outside `power_supply_uevent`. Use the System.map plus call sites. In particular, check:

- the charger's `external_power_changed` path;
- any thermal zone registered via the TEMP property;
- any periodic battery-meter kthread.

How to use the answer:

- **No other caller:** a NEGATIVE result fairly clears the channel-6 read path for this exposure.
- **Other callers exist:** state that limit in the result before you boot, so a NEGATIVE isn't over-read later.

Either way the trial is worth running. The check only changes how much a NEGATIVE result can claim.

## Stop rule

One build, one physical trial, the same binding/readback/console checks as before, then stop and classify. Don't retune, run a second boot, or start an automatic follow-on unit.