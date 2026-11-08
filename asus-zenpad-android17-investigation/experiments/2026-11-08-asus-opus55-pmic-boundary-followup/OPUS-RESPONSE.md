# One next step: add a finite backstop budget to `pwrap_wait_for_state`, plus a one-shot record when it runs out

## A. Why this unit

This change both unblocks and measures. If the PMIC wait is trapping the CPU, the change lets execution continue. If it isn't, the result rules that out in one run.

**Evidence-to-action link:**
- With `nr_cpus=1`, PID1 is last seen handing the CPU to the kworker.
- The kworker's last confirmed position is the ADC channel-6 sample sequence, near a 300 µs delay or a PMIC read.
- That PMIC read runs under an IRQ-save spinlock with preemption off.
- The wait loop in `pwrap_wait_for_state` has no iteration bound. It only exits through hardware readiness or sched_clock progress.

You've confirmed by disassembly that this loop exists, has no bound, and runs with IRQs masked. If it spins, it alone would account for PID1 never being scheduled again, even with `PREEMPT=y`. A bounded loop is the smallest change that turns that possibility into a yes or no.

**Why not battery-uevent suppression:** it removes the whole PMIC/ADC workload. If PID1 then progresses, you still don't know which inner wait was responsible. It also changes what charging and thermal consumers see. The budget leaves normal behaviour identical, and the existing `-ETIMEDOUT` path is already the designed failure route.

**Confounders:**
- `udelay()` can't be bounded and returns nothing. If the counter is frozen, the delay can stall before any pwrap read.
- A single MMIO or `CNTVCT` read that never completes is outside any loop budget.
- Other PMIC users share the pwrap state machine after a timeout.

The recorded fields below are chosen to separate these cases.

## B. Boundary, bound and semantics

**Boundary:** only the loop body of `pwrap_wait_for_state`. Leave unchanged:
- `udelay`
- ADC retry counts
- regmap locking
- the battery driver
- watchdog and thermal behaviour

**Deriving the bound:** make it a backstop that physically can't fire before the existing 10 ms deadline under normal conditions. Don't make it a new timeout.
- Every iteration does at least one uncached device read of the pwrap register plus a counter read. On this SoC's bus, that has a conservative minimum cost per iteration.
- Budget = 10 ms ÷ that minimum cost, times a large safety factor (≥10×). For example, a ≥100 ns minimum gives about 100k iterations in 10 ms, so a budget of about 1M.
- Write the derivation into the patch comment. If the counter is advancing, the deadline always wins, so false timeouts can't happen under normal timing.

**Semantics to keep exactly:**
- The readiness check and deadline check stay first.
- The final readiness recheck runs after the budget runs out too.
- Return the same `-ETIMEDOUT`.
- An idle-wait timeout still triggers the existing VLDCLR recovery.
- A read timeout after the command still returns directly.
- The write path only gains the bound through its idle wait.
- Add no new clock reads and no retries.

**Record (static memory only; emit nothing under the spinlock):**
- which wait (idle or WFVLDCLR)
- the raw readiness/state register value at exhaustion
- sched_clock at start and at exhaustion
- iterations used
- a one-shot flag

Emit it once through the existing retained writer from the battery error-handling path after the lock is released, or at the next ordinary log site.

**Criteria (same calibration, identity and complete-console checks as your logging trial):**
- **Positive:** the budget record appears, PID1 then reaches seq101 / the 2M marker, and stock Android returns.
  - Counter delta ≈ 0: the selected clock stopped advancing during the wait.
  - Delta > 10 ms: the deadline logic itself is suspect. Look at the clock-comparison path next, not the hardware.
- **Negative:** no budget record, the stall again ends at seq100, and the console bound is complete. That rules out the unbounded pwrap loop as the trap. The next unit then targets the stalled-read or `udelay` possibilities, not more pwrap work.
- **UNKNOWN:** the record appears but PID1 still doesn't progress (for example, the counter is frozen and `udelay` stalls next). Also UNKNOWN: an incomplete console, an identity mismatch, or a record that only partly decodes. Don't draw conclusions from an UNKNOWN beyond what the record fields show.

## C. Stop rule and how this moves you forward

- **One** build and **up to three** identical cold boots, to account for stalls that don't reproduce every time.
- No retuning of the budget between boots.
- Manual Power is the accepted fallback.
- After three boots, stop and classify the result, whatever it is.

**Progress criterion:** this counts as progress only if PID1 keeps running at normal priority past the battery-uevent window. That's the point at which you can schedule the next unit: read-only MMC discovery, with the battery path still returning its legitimate error.

A one-off record with no sustained execution counts as UNKNOWN or Negative, not progress. Absent records mean only "not observed". They don't prove the CPU hung, that timers died, or that the syscall returned.