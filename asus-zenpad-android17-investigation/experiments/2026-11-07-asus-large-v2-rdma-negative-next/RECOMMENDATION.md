## Recommendation: candidate (a), narrowed to one hook — `finish_task_switch`

**The one experiment:** add a single capture at `finish_task_switch(struct task_struct *prev)` (kernel/sched/core.c), recording per switch: raw CNTVCT (register read only), `prev->pid`, `prev->state`, `current->pid`, `current->prio`. Bounded ring of ~12 latest records, ~40 ASCII bytes each (~500B inside your existing 5952B retained-console budget), same generation/token/cache-clean+barrier/sticky-fault discipline. No printk, no ktime calls, no locks, no allocation — it runs under rq->lock, so only word copies plus the raw counter read you already use in the reader. Everything else — helper binary, bootargs, DT, timer/clock/capture slots, RDMA predicate — unchanged except a fresh UUID. One physical trial.

## Why this seam and not another driver or timekeeping change

Three facts now triangulate to the context-switch/IRQ-return boundary, and only there:

1. **Every captured kernel function completes** (mono 395/395 stage4, counter 396/396, hrtimer 181/181, IRQ 401/401), the raw counter advances (task 176234377 → IRQ 176234774, microseconds apart), seqcount exits even. There is no timekeeping anomaly to fix — (c) has zero supporting delta.
2. **The CPU stays alive in interruptible context** — timer IRQs keep being delivered and handled. So nothing is wedged with IRQs masked.
3. **The stable interrupted PC is exactly the preemption point**: `_raw_spin_unlock_irqrestore+16`, post-`msr daif`, pre preempt-count decrement. "PID1 never returns to userspace after that point" is the single state that explains *all* observations at once: completed clock reads, completed hrtimer_interrupts, absent loop-end (needs userspace), absent alarm marker (SIGALRM delivery also requires return-to-userspace), no oops.

The RDMA negative reinforces this: removing IRQ sources doesn't move a boundary that sits after IRQ delivery. Any further driver trial or random timekeeping change can only remove work that the data already shows being handled — it cannot observe the seam where the failure actually lives. That is why this observation beats another mutation.

Two live mechanisms fit all current data and are distinguishable *only* by switch records: (i) PID1 is preempted at that unlock and never rescheduled — starvation; (ii) the CPU wedges in a non-task context (inline softirq at IRQ-return) where `preempt_count` stays elevated, so preempt never fires and the stable PC at unlock+16 never leaves — also consistent with never scheduling.

## Predictions

- **POSITIVE (starvation proven):** after the boundary raw-counter value, a record `prev_pid=1, prev_state=TASK_RUNNING`, then no later `next_pid=1` record, while the timer IRQ slot keeps producing complete updated records and helper logs stay absent. `next_pid` names the culprit: 0/idle → pick_next/sched-class defect; a kthread → that thread hogs. The next action is that single named target — not a driver, not a clock.
- **NEGATIVE-1 (scheduling exonerated):** repeated `next_pid=1` records after the boundary. PID1 keeps cycling kernel↔userspace, so the fault is helper-visibility: signal delivery or kmsg sink. Then, and only then, run (b) as the next single experiment.
- **NEGATIVE-2 (softirq/IRQ-return wedge):** no switch records after the boundary while the IRQ slot updates. That is the elevated-preempt-count signature above; the next single hook is the IRQ-return/softirq entry boundary.
- **UNKNOWN:** sticky fault, dropped/nested token, or ring ambiguity → trial INVALID, one retry, else stop. Do not interpret absent records as absent switches — same lesson as the kmsg limiter and the alarm marker.

## Why not (b) first

Its negative is ambiguous — a missing post-loop log cannot separate "descheduled" from "wedged before returning to userspace," which is precisely today's ambiguity. Its positive still wouldn't name the mechanism; you'd need (a) anyway. And it mutates the helper source whose untouched state made the RDMA control clean. (a) is decisive under every outcome; (b) survives as the designated follow-up only for NEGATIVE-1.

## STOP conditions

One physical trial. On POSITIVE: halt all driver/clock speculation; pursue only the identified `next_pid`/sched class. On NEGATIVE-1: (b) next. On NEGATIVE-2: softirq boundary hook next. No new toolchains, UART, bootarg/DT changes, or broader tests under any outcome. The cached WDT/PMIC-ADC PC stays corroboration only — though on POSITIVE it becomes interpretable (it's a bounded-poll code path a wedged CPU could sit near, and `next_pid` would tell us who).

## Link to Android 17

Android 17's boot is this seam at scale: init/zygote scheduling, hrtimer→userspace delivery (vsync, input, binder timeouts), and GC threads all assume PID1-class tasks reliably resume from preemption. If this kernel can starve PID1 at 0.65s or wedge in softirq at IRQ-return, an Android 17 port will hang in bootanimation/init with the same signature, indistinguishable from a porting bug. This experiment is the gate that converts "userspace stops after 0.65s" into a named mechanism — only then is storage/full-Android work interpretable, and only its named outcome justifies the next single change.