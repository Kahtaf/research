# One experiment: starvation-exempt PID1 (SCHED_FIFO self-boost), single run

## Framing check (brief)

- The reset-request premise is now adequately cleared by e0b1a1ba: WDT EN cleared at probe (0xdd→0xdc, rc0, source-qualified REQ registers read), the loop still fails, stock returns cleanly. Do not revisit WDT/reset/thermal-request paths this run.
- The live unknown is the post-0.65s dark window: every observer was finite, the task's prints end after the before-snapshot, and alarm-absence is uninformative until the loop completes. Two hypotheses remain: **PID1 stops executing** (starvation / non-preemption / lockup) vs **PID1 executes but the tick/timer side dies**.
- A behavioral control is justified *without* further observation because the dominant hypothesis (starvation/non-preemption) can be removed with one safe syscall — and if the loop then completes, the task's own after-snapshot and alarm flag are exactly the missing timer evidence, obtained for free. Only on failure does kernel-side observation become essential (pre-committed below).
- One nuance: "starvation" need not be fair-CFS stealing. A stuck/uncalibrated sched_clock can zero out `entity_tick` preemption deltas entirely, which fits "PID1 switched to equal-priority kworker0:3, no later captured switch." FIFO bypasses both mechanisms — that is precisely why this control adjudicates execution without presuming the mechanism.

## Exact intervention boundary (single delta from baseline e0b1a1ba)

1. After the existing initial prints (mono value, before-IRQ snapshot), PID1 makes **one direct syscall**: `sched_setscheduler(0, SCHED_FIFO, {sched_priority=1})`, and prints its return code as one line via the unchanged helper. PID1 is root with full caps, so rc should be 0; the rc line prevents silent-no-op misattribution.
2. Loop, caps (2M reads / ≥1.5 kernel-counter s), alarm, after-IRQ snapshot, alarm flag, reboot: **unchanged**.
3. Interim progress lines via the existing proven helper at iterations 512k / 1M / 1.5M: `iter= mono= alarm=` (≤3 lines, ~+150B console). This is in-task measurement through the proven print path, not a kernel observer.
4. Kernel otherwise identical to e0b1a1ba: WDT probe/stop unit retained (EN stays 0), headless/RDMA-skip baseline retained, nohlt, nr_cpus=1, direct syscalls, sparse console. New candidate UUID, fullp10 hash verified, one recovery dispatch, fresh stock boot, verified runtime profile — same liturgy.
5. Exposure: pre-declared fixed **45s**; if no completion → manual Power (accepted fallback); read back retained console in stock. **One physical run.**

Safety: hard IRQs (local timer, PMIC) still preempt FIFO, so tick/timekeeping and PMIC IRQ servicing continue; CFS work is delayed ≤45s, not disabled; no thermal/PMIC/WDT policy change.

## Expected outcomes

| Result | Evidence | Establishes |
|---|---|---|
| **P-A** exit ≥1.5s | after-IRQ3 delta ≈ 250×Δ; alarm=1; sched rc=0 | Non-preemption/starvation was the blocker; execution, tick delivery, timekeeping, alarm all alive during loop. This is the task's own defined timer pass — **under RT (conditional)**. Starver identity NOT established. |
| **P-B** exit ≥1.5s | after-IRQ3 delta ≈0 and/or alarm=0 | PID1 executes at RT but tick/timer subsystem died after ~0.65s (mono advances by counter interpolation, not ticks). Timer-IRQ-side blocker; original non-completion also implies execution was blocked at normal priority. |
| **P-C** exit via 2M, mono >1.5s | ticks may be alive | 1.5s exit arithmetic broken (task units / uncalibrated counter); starvation also implicated (2M should have finished inside 30s if executing). Fix task arithmetic; not a timer pass. |
| **P-D** exit via 2M, mono <1.5s | ticks advanced, alarm as observed | Execution restored by RT → original stall was execution-side; timer alive; cap simply hit first. Partial: starvation confirmed, ≥1.5s exit not yet demonstrated. |
| **N1** no completion | interim lines show mono advancing, then stop at line k | PID1 execution death **even at RT**, bounded at iteration/time k. Not CFS starvation. UNKNOWN: CPU alive after k? |
| **N2** no completion | interim mono frozen early, lines continue/stop | Timekeeping death while executing (clock-side blocker). |
| **N3** no completion | no interim lines, sched rc=0 | Death before 512k iterations even at RT. |
| **X** | sched_setscheduler rc≠0 printed | Run is a no-op; do not attribute any outcome to RT. |

## Overclaim guards (preserved conditions)

- Single behavioral delta plus measurement-only lines from a hash-verified baseline; rc line guards silent failure.
- Any pass is explicitly "under RT": no normal-priority reliability claim, no starver identity claim (kworker/battery chain remains correlation only), no PMIC causal claim.
- Alarm-absence and missing after-counts in non-completing runs are uninformative (both printed only after the loop).
- Tick evidence comes only from the task's own before/after GIC counts.

## Stop conditions and pre-committed follow-ups (one per branch)

- **Run level:** 45s manual Power, single run, readback; no ad-hoc re-runs or variant matrices.
- **N1/N3:** the one next step is the smallest kernel-side observation — a single retained u32 incremented in the existing local-timer IRQ entry path (PPI30), read back after reboot. Exit criteria: ≈250×exposure → CPU+tick alive → preempt-disabled region or IRQ storm (kernel-side hunt); frozen → CPU lockup. Only now is observation essential: the task cannot report CPU state after its own death, and RT has already excluded CFS starvation.
- **N2:** one timer-side probe, similarly bounded.
- **Thread level:** two consecutive runs with no new discriminating evidence → stop and reassess rather than layering.

## Next broad milestone only on positive (P-A/P-D)

Proceed to the first bounded **storage/MMC0 readback probe** under the RT-PID1 task. Before any later normal-priority Android17 init attempt, exactly one starver-identification control (defer/hold of the power_supply_changed_work battery chain, PMIC safety preserved) — deferred, not part of this run.