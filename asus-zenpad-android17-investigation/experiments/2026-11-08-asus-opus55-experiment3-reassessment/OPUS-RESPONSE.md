# Opus 5.5 reassessment: experiment 3, Linux 4.9 on P00A_2 (advice only)

I took no actions and launched nothing.

## 1. What this trial eliminated, and the fact that matters most

**Your STOP rule applies.** The result is negative for progress, so you stop and reassess, and it is right not to iterate.

**What it weakened:** The battery uevent property-getter chain (batt_vol → AUXADC6 inside `power_supply_uevent`) is not *necessary* for the stall in this exposure. The omission really ran on that path, `kobject_uevent` returned 0, and PID1 still made no progress. So the specific trigger from my last recommendation is weakened. Taken with A (no pwrap exhaustion record), "one PMIC read spins forever" looks less likely, though it is not excluded.

**What it did not eliminate:** the other AUXADC readers (BAT_thread, thermal channel 5), scheduling, preemption, the reporting paths, or any platform-level cause.

**The hard fact that matters most:** after PID1's last WRET, the CPU was still running kernel code in the kworker, through a full uevent emission and its return. At that point the machine was not hard-hung. PID1 simply never produced another marker. The problem has moved from "a specific device read hangs" to "PID1 loses forward progress while the kernel stays alive, at least briefly." That is a system-level liveness question about scheduling, timer/IRQ delivery, idle/SPM or platform power. Statement-level hooks in one worker are poorly suited to answer it. That is why the binary search kept producing absence rather than answers.

## 2. Leading recommendation, and one alternative

**Leading: one bounded reset to a minimal-platform 4.9 baseline, precommitted as the last 4.9 investment.**

- **What the baseline contains:** CPU0 only, GIC, arch timer, UART/console, RAM and the existing ramdisk.
- **What it removes or compiles out:** the vendor power-supply, battery, charger, AUXADC consumers, thermal, SPM/idle extensions, MMC and other nonessential MTK drivers. They come out of the DT/config, not via hooks.
- **The single pass criterion:** PID1 completes the 2M compute workload and then shows sustained timer-driven runtime (for example, alarm/sleep returns over minutes). It must be reported via the already-calibrated kmsg path, with no new instrumentation.
- **If it passes:** add back whole subsystems one class at a time (power-supply, then thermal, then MMC). That is coarse bisection by subsystem, not by statement.
- **If it fails:** the defect is in core platform support: timer, GIC, clocks, idle or the vendor tree. 4.9 on this vendor base is then not worth more effort, and you go to the alternative.

This changes the question from "where in this worker" to "does the platform core run 4.9 at all." Either answer is decisive.

**Alternative: close the 4.9 line now.** Pick another OS strategy, such as a userspace that runs on the stock vendor kernel line, or a different device for the Android 17 goal. Do not assume either works without substantial work. Android 17's kernel requirements (BPF, APEX/crypto) are exactly why 4.9 was chosen, and an older kernel will likely not satisfy them.

## 3. Reset hygiene: separate two kinds of change

- **Removing diagnostic complexity is good and low-risk.** Revert the WENT/WRET emitters, hot/sparse recorders, the pwrap budget, the omission patch, the FIFO/nohlt/directclock experiments and the helper loops. Keep only the calibrated reporter and the console-offset fix.
- **Disabling hardware protection is a separate, explicit owner decision.** This covers battery, charger and thermal drivers and the WDT. Compiling them out of a short RAM-only boot relies on hardware/PMIC thermal and UVLO limits, the bounded run time and stock recovery. State that plainly, cap the run duration, and supervise the device.

**Before flashing any normal Android partition, all of these must hold:**
1. Gate 3 holds with protections *re-enabled and working*: sustained runtime, IRQs and alarms.
2. Gate 4 holds: reliable block readback of real partitions, checksum-matched against stock.
3. A verified full backup exists.
4. A rescue path has been proven by an actual restore (BROM/preloader flash or equivalent), not just assumed.

Never flash with protections disabled.

## 4. Candid status for the owner

- Experiment 3 is still open. Gates 1–2 are closed. Gates 3–4 are open. Gate 5 has not started, and stock Android 7 is intact (only recovery changed).
- **Yes, we have hit diminishing returns** on seam-by-seam tracing. Each trial has weakened one hypothesis without closing gate 3.
- **The decision now:** either authorize one minimal-baseline trial with a precommitted rule ("fail → end the 4.9 line"), or end the 4.9 line today. Absence of progress does not prove 4.9 is impossible on this device. It does show that the current approach isn't converging.

**One missing fact that would sharpen the choice:** whether the whole kernel stays alive long after line 225, or dies shortly after. Long-lived points toward a scheduler/userspace-resume issue, where the minimal baseline is the right bet. Dying soon after points toward platform power/idle, which favours closing the line. You do not need this fact to decide, though: the minimal-baseline trial answers it as a side effect.