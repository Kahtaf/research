**Verdict: run A now. No strictly better single unit exists within your constraints; B is the correct second unit; C is last.**

**Why A discriminates best**

- The premise has two escape clauses: publication-stall and reset-censoring. One is already nearly closed by your own data: across six loss-0 protocols, the PID1 loop (target ≈1.5 counter-sec from ≈0.65 s) never completed and never published final/alarm markers, while your bound puts reset at ≈33 s — roughly 29 s of margin. A ~31 s-class reset cannot censor markers that should publish ~2.2 s in under loss-0 retention. So "reset censored the loop" is weak; the live question is whether observer load stalls execution/publication. A isolates exactly that variable: same kernel/runtime/DT/args/helper logic, barriers and mappings unchanged, all original ops active, only a boolean admission filter — liveness end-markers instead of the flood. The original 0.65 s failure under continuous printk alone also keeps low-load observer-causation alive; only A probes *below* that load.
- B identifies the reset agent but never observes progress. Even a named agent can't separate "stalled, then reset" from "fine, but censored." Given the timing margin above, B's payoff is mainly interpreting an A-negative (stop-acceptance MODE readback + reset_handler marker) — that's the follow-up, not the premise test.
- C adds PoC-clean/DSB observer work — the exact suspected cause class — and observes dispatch, not liveness. Hold it.
- The moving boundary (sample3 delay → sample2 poll under a counter-route change that doesn't touch the PMIC driver) fits a load/time-dependent cause, not a fixed driver defect. The DSB saved-PC clue justifies suspicion but not a decision: epoch is unestablished. Don't let it pick the unit.

**What each A outcome buys**

- **Positive** (BEGIN, initial ≈0.65 s, final marker after the real computed loop result, alarm marker, after-IRQ counts, unique result marker read back): premise rejected for the heavy-observer captures — the PMIC boundary was an observation artifact; the original CNTVCT path, timer/alarm/IRQ, and core ops progress at low observer budget. No PMIC/register/GIC/IRQ fix is justified; next step is observer bisection only if needed. Android 7 link: keep this profile and let boot proceed — if it reaches normal Android, that *is* the recovery; if it stalls later, the fault localizes past the helper with no observers left to blame. Also: don't carry the physical-CNTPCT trial as a fix (boundary moved earlier, no end-to-end progress); A's virtual baseline avoids that claim.
- **Negative** (BEGIN + initial present; no final/alarm/after-IRQ): heavy recorders *and* continuous printk are exonerated as necessary causes — the fault reproduces below the original failing profile's observer load. Premise stands strengthened; remaining explanations are original-environment stall (loop/PMIC/IRQ/counter) or final-publication stall; loop-censoring stays weak on the ~29 s margin. STOP. Next unit = B, not driver edits.
- **Ambiguous** (no BEGIN, UUID/readback mismatch): invalid trial; re-check stock readback only; not premise evidence.
- **Mixed** (final present, alarm/IRQ counts missing): an observer-independent timer/alarm/IRQ lead — a new, narrower question, not a premise failure.

**Free signal inside A's existing budget (no new observer work)**

After the fresh stock boot: re-read the reboot-reason saved PC and passively re-measure the reset interval (host UTC bound). If A-negative and the PC again maps to the DSB after the DC CVAC loop in `__pi___clean_dcache_area_poc` despite only sparse publications, stale-vs-current sharpens — two latches at a now-rare site — but do not assert epoch or hardware DSB deadlock. If the interval is again ≈33 s, a fixed-time reset of a non-progressing system gains a third point; do not decode rr_pl.wdt_status 32 (preloader-saved %d) as raw RGU bits or claim WDT identity.

**Stopping rule / guardrails**

One build, one trial, fresh UUID, full hash readback, fresh stock boot. Explicitly an alternate observability profile — do not claim the six old protocols pass under it. Final marker only after the real computed result; cookie leaves CNTVCT; no DSB/barrier removal while claiming retention; no PMIC/thermal/ADC changes. Decision rule: A now; if negative, B; C only after both.