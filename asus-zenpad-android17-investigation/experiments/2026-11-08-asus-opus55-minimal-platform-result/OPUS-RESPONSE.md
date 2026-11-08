# Decision: don't flash or build anything yet. First, read the bytes you already have.

**Next step:** decode the preserved raw `last_kmsg` (sha `d8875e65…`) offline, and pull the boot-reason data from the stock boot that came back. A readback is not a new trial, and nothing new gets flashed.

## Why this is the step

1. **The compute loop can't explain the stall.** 2M LCG iterations take a few milliseconds at this CPU's speed, and 500k has completed before. If `compute-end` never arrived, the cause is not how long the loop runs. The stall happened somewhere in this window:
   - the `compute-begin` `write()` committing to the buffer but never returning to user space,
   - PID1 never being scheduled again,
   - or the whole system freezing.

   A printed `compute-begin` proves the record was committed, not that the call returned.

2. **The subtraction run already refuted one idea.** Disabling all 99 display, storage, USB and other consumers did not change the outcome. So "a removed consumer is needed for the stall" is false. What's left is the set you kept: BAT/SOC notification, PMIC/pwrap, thermal, SPM/idle/HPS, TEE and watchdog. That matches what the earlier captures showed: `power_supply_changed_work`, then battery/ADC activity, then the pwrap poll. That poll runs with IRQs off and times out using `sched_clock`. If the 13 MHz counter stops or isn't advancing in some SPM state, that timeout can never fire. This is the one mechanism the next decode can confirm or rule out. It is not yet a finding.

3. **Another physical run wouldn't settle anything.** It would give "partial observation, unknown reboot cause" again.

## What to extract

From the 16737 B raw file and the stock reboot. Don't loosen the strict decoder; just annotate the selected records.

- **A. Ordering:** is `compute-begin` the last kernel record of the run? List every record after it with its printk timestamp. Also note the timestamp gap between `entry` and `compute-begin`.
- **B. MTK ram_console / pstore trailer fields**, if present: WDT status, fiq step, exception type, last-IRQ enter/exit per CPU, idle/SPM/hotplug footprints, last init function. Also decode the "Not Clear oldstatus32" line against the RGU/ram_console source in your tree. Decimal 32 is a bit pattern, so map it to its register bits.
- **C. The stock boot's own reason:** the preloader/LK boot reason, PMIC power-off/PONSTS, and RGU status from the boot that came back.

## Outcomes and what each means for experiment 3

- **Kernel records after `compute-begin` have later timestamps.** The kernel kept running while PID1 made no progress. Experiment 3 narrows to "runnable PID1 not resumed or not returned to user space". RAM and timers become secondary. That justifies exactly one physical test aimed at that path. *Falsifies:* a whole-system freeze.
- **`compute-begin` is the last record, and the footprints or reset status point at the pwrap/IRQs-off region or an SPM/idle state.** The whole system froze in the kept PMIC/idle path. The one justified experiment is a single change: bound that poll with a counter that is known to keep running in that state (verify CNTVCT advances there), and change nothing else. *Falsifies:* the scheduler/return explanation.
- **`compute-begin` is last, and the trailer is missing or can't be interpreted.** Stop experiment 3. **The smallest missing observable** is one retained word recording CPU0's state at the freeze, captured with the reset cause. In practice that's a pwrap-poll enter/exit marker in the existing ram_console slot, plus the RGU status read on the next boot. Add that one word and no other logging.

## Stopping rule

Do one offline decode. Build only if the result clearly falls into the first or second outcome. If it falls into the third, add only that one word. If two runs with that word are still ambiguous, mark experiment 3 as blocked on observability, not on the kernel. Experiment 4 (storage/rescue) and experiment 5 (first Android 17 flash) stay gated, and the stock BOOT/SYSTEM/DATA partitions stay untouched.