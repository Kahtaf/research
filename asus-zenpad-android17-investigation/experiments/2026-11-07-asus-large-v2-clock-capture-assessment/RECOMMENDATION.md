**Verdict up front:** the rows acquit the clock read. They leave task liveness open, and they add a first-class datum your framing under-weights: the end state is a total blackout, not a starved-but-live system.

**Isolated by rows (runtime, not source):**
- Not a counter-read hang. The stalled call (0x55a00) committed stage 2 — read_seqcount_begin returned even seq 312 — but never entered clock->read: no arch_counter_read row carries parent 0x55a00, and the newest task read (0x55910) belongs to the prior call. Post-stall, IRQ context on the single online CPU reads CNTVCT fine (410/410, increasing). "Broken counter hangs the reader" is refuted for this event.
- Delivery works: hrtimer_interrupt completed 183/183 including the post-stall tick 0x55b21; loss 0 means absent rows are absent events.
- Stage 2 → clock->read holds only loads and calls, nothing blocking. The task didn't hang *inside* that window; it stopped *executing*. Inference, but the only one the rows permit.

**Left open:**
- The last tick hit a task-context unlock at +16 — consistent with PID1's stage-2 cap_seq unlock, though the interrupted context is untagged, so an unobserved non-PID1 context can't be excluded. That PC is the preemption door itself (after msr daif, before preempt dec/need_resched). Whether preempt_schedule or IRQ-exit preemption ran and never returned is unproven: nothing hooks scheduler, switch, or IRQ exit.
- No tick #184, no rows, no oops. That already excludes a perpetual softirq storm (IRQ-enabled; the next tick would be recorded). Remaining: task preempted then lost while idle/nohz stops the tick, or a masked-IRQ lockup/exception. Who owns the CPU is unobserved.
- Whether monotonic advanced across the 390 calls (results weren't captured).

**One step:** hold preempt_disable() across the loop's ktime calls — a ~10-line kernel-side variant in your existing harness (user mode can't hold it; 4.9 has no runtime preempt switch). Recorder, hooks, bootargs untouched. Run past the old exposure, a few repeats.
- Completes ≥1.5s: preemption necessary for the hang, and update_wall_time proven advancing under load. Family: deschedule-never-resume; a preempt_schedule/__switch_to hook is the follow-up, not now.
- Completes via the 2M cap, time still ~0.64s: per-call hang gone but monotonic frozen — a timekeeping-update defect, which would also explain the 100ms sleep without any scheduler bug.
- Hangs again: with preempt_count>0 both doors are structurally closed (unlock's cbnz; el1_irq's count check before preempt_schedule_irq), so descheduling is excluded. Post-hang rows split it: ticks continue, no task rows → task starved/derailed uninstrumented (IRQ-exit family); rows stop → masked-IRQ lockup or exception (check the retained console for an oops).

Diagnostic, not a correction: even a clean run proves only preemption-necessity for this stall, this build, this exposure — nothing about stock parity.