**Pick B** — and yes, it is now justified, because B as specified is self-gating and self-disambiguating with infrastructure you already trust. It is also the only option that can *end* the failure this boot.

## Why B is no longer speculative

1. **The start read is the access probe.** If the first substituted `MRS CNTPCT_EL0` completes and appears in the retained capture (start + iter1 with sane delta), EL1 physical-counter access is proven *for this epoch* — no assumption, no separate gate. If it never completes, that failure is itself distinguishable: the aed PC would sit at the **new** instruction address, not at `__delay+0x64`.
2. **One domain, CNTVOFF cancels.** Use CNTPCT for *both* the initial read and every loop read; the unsigned `x20 − x23` delta never crosses domains. Never mix a CNTVCT start with CNTPCT loop reads.
3. **The arithmetic says exit was already due.** From your own numbers (~0.43 ticks/iteration after the 256 marker), the 3900-tick exit lands around iteration ~9,000 — between the 256 and 65536 markers, which are *not* expected to fire on normal completion. The only missing mandatory marker is the **return**. Reads 1 and 256 worked; then nothing. The live alternatives are: a later read/accessor fault, or departure via an IRQ invisible to timer-only scope. B separates them, because CNTPCT is a different instruction and a different access-permission bit from CNTVCT.
4. **The aed clue** (epoch unestablished — consistency only, not proof): PC deterministically at the *direct fast-path* MRS is exactly what a stuck read predicts, and it also implies the fast path executes, since an active OOL workaround path would bypass the `+0x64` MRS entirely.

## Exact boundary

Selected PMIC `__delay` only. Swap the two direct `MRS CNTVCT_EL0` sites (initial `x23`, loop-head `x20`) for inline `MRS CNTPCT_EL0` — do **not** call `arch_counter_get_cntpct()`. Keep ISB, static-key branch, loop order, YIELD, unsigned compare vs 3900, exit path, capture calls, fresh UUID, p10 readback, stock-return verification. All other kernel CNTVCT uses unchanged. Read-only: no register writes, no GIC/counter writes, BOOT/SYSTEM/DATA untouched, no charging/thermal change, no global read-backend change, no retry. One confound to close passively: log the static-key word once through the existing capture — if the key is active, the loop value comes from the OOL CNTVCT path and B is a no-op.

## Predictions and proof limits

- **Positive** (markers advance, return fires, ADC post-sample, PID1 stage-4 completes): causal proof that this delay's CNTVCT *read route* was the blocker — and the substitution is the recovery fix for that site. If a later site stalls on CNTVCT, that is a bounded route finding; extend one site at a time. B+ does **not** prove global counter health or the mechanism, and makes no stock-parity claim.
- **Negative 1** (values advance, no return): exit arithmetic and the read instruction are exonerated for this route; blocker is a later stall affecting both counters or IRQ departure → A becomes justified with a sharp question.
- **Negative 2** (values freeze after advancing): the system counter stopped advancing — corroborated by the missing tick due ~2.16 ms after loop start — a different failure class; fix decided separately, no semantic bypass now.
- **Negative 3** (no start capture): CNTPCT trap or both-register access stall; aed PC address discriminates the old site from the new one. EL1PCTEN stays unproven until the start read completes — the working EL1 physical-timer CTL/TVAL programming (same CNTHCTL register) is supportive, not proof.

## What A proves, and why second

A can only observe. Its positive — an IRQ entry after delay start without return — identifies the departing hwirq and refutes the read-route hypothesis. Its negative shows no IRQ was taken; with IRQs unmasked and a tick falling due, that implies the CPU stopped reaching instruction boundaries, but **cannot localize which instruction**, so A− funnels straight back to B. Under the best-supported hypothesis, A costs a full boot cycle and cannot fix anything. C is strictly worse: per-read accessor hooks alter the measured loop and add exactly the breadcrumb layer you're trying to escape.