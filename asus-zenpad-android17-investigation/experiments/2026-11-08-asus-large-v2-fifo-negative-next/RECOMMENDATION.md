## Re-evaluating the timer-IRQ entry counter

It is **not** the best next step anymore, for three reasons:

1. **It doesn't separate your two live hypotheses.** Both "helper stuck in a loop-body syscall" and "milestone publication failing" predict counter *growth*. A positive leaves that fork open; a null can't distinguish stopped-timer / masked-IRQ / truncated capture (your own caveat — it proves no lockup). As a sole instrument it's asymmetric, and completing it (entry/exit pair + a helper-side watermark) means adding a kernel observer before a zero-observer behavior test has run.
2. **The FIFO result is a harness-validity datum, not a trigger/IRQ datum.** The run stopped self-reporting, so nothing about the trigger or IRQ state can be mined from it. The decision-relevant unknown is "why did the harness stop publishing," not "did the timer tick during the loop."
3. Note what your own evidence already pins down: the getparam line confirming policy1/priority1 published *after* FIFO was already set. So publication worked under FIFO right up to the loop edge; silence began specifically inside the loop. That sharpens the suspect set to the loop body or the milestone write — exactly what a policy A/B discriminates.

The counter does extend beforeIRQ-180 into the loop window, so it isn't redundant — but it's a fallback, not the next move.

## The one next experiment (decisive behavior, safe, zero new observers)

Fresh re-run of the identical sparse-fifo harness with **exactly one delta: `setscheduler(SCHED_OTHER, 0)` instead of `(SCHED_FIFO, 1)`**. Everything else byte-identical: markers at 500k/1M/1.5M, initial direct-clock step, beforeIRQ snapshot, restore-on-every-exit, afterIRQ ordering, fresh helper UUID, new profile tag (e.g., sparse-norm-v1). One helper compile, **no kernel change**, one physical trial. Under SCHED_OTHER nothing is starved (no RT-throttle involvement, WDT kicker schedulable), so this is strictly safer than the FIFO run. No watchdog, thermal, or walltime assumptions anywhere — markers are iteration counts, not seconds.

*If a fresh full-harness normal-priority run already exists in this generation, skip the trial and apply the decision rule directly.*

## Fresh-capture validation and outcome semantics

Pre-declare the exact expected line sequence: policy0/getparam → setscheduler rc0 → policy0 confirm → direct clock → beforeIRQ → 500k → 1M → 1.5M (or trigger exit + line) → restore request → restored → afterIRQ.

- **Positive** = fresh UUID + fresh profile + complete console + full sequence.
- **Negative** = fresh UUID + complete console, but truncated at or before the FIFO run's last line.
- **UNKNOWN** = UUID/profile mismatch, incomplete console, or stale/out-of-order markers → discard; one validation retry of the *same* trial only, then stop.

No register-latch epoch is assumed anywhere: "fresh" is decided by console content, not by counter timing.

## Next decision and stop condition

- **Positive:** FIFO was self-breaking (silence was FIFO-induced blocking/starvation of the loop or its publication — state it that way, not as "starvation confirmed"). Sustained normal-priority PID1 is demonstrated — the goal milestone. **Decision: retire FIFO permanently; next step is the storage extension.** No further scheduling experiments or observers.
- **Negative:** FIFO exonerated; the blocker is the loop body or milestone publication. **Decision: one helper-only follow-up — pure-compute loop body (no syscalls between milestones; publish only at milestones).** No kernel observers yet.
- **Stop condition:** if the pure-compute variant is also silent, stop experimenting on the loop entirely — the publication mechanism itself is the proven blocker and needs a structural fix. Until a normal-priority run fully publishes, no trigger/IRQ theory is testable and no more observers may be added.

## Conditional capture spec (only if a timer-delivery question survives the clean baseline)

One 64B retained block: fresh UUID/version header; kernel `T_enter`/`T_exit` u32 incremented at timer-handler entry/exit (plain stores, no printk, no barriers; cache-clean the line every ~1024 ticks); helper `H_iter` watermark (uncached store every ~4k iterations) and `H_phase` (uncached store around each distinct loop syscall); plus a next-boot print of the reset-cause register.

Reader rules: UUID/version + console-completeness check; counter values reflect the last cache-clean, *not* reset time; no tick→seconds conversion. Semantics: **T grows + H advances** → CPU/timer/helper alive, failure is publication-side; **T grows + H frozen** → stuck syscall, named by H_phase; **T frozen** → UNKNOWN (masked/stopped/truncated — never "lockup"); `T_enter−T_exit == 1` → in-handler at last persist, not a hang; **H advances + T frozen** → genuine IRQ-delivery issue — the one outcome that re-opens PPI29=0 root-cause work.

## Framing challenge

Stop counting the absent alarm/restore markers as independent negatives — once publication went silent they carry no information. And accept that FIFO answered nothing about the trigger: it only proved the harness can't self-report under FIFO. The cheapest path back to decision-grade data is the same harness at the priority you actually want to sustain — which is also your goal state, not another observer.