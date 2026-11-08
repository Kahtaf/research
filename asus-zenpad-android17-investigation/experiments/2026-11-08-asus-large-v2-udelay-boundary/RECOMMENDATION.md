## Pick: your gated `__delay` probe — confirmed, with four tightenings

It is the right single unit because one record splits **all three live explanations** of the PRE→POST absence without changing exposure: (a) absurd requested cycles (runtime LPJ), (b) counter non-progress with CPU executing, (c) boundary actually after `__delay` returns. The alternatives fail as *this* unit: a RAM helper runs the delay off the PMIC route (a pass there leaves the pending call unexplained); `usleep_range` changes spin→sleep semantics and rides the same suspect timer; CNTPCT swap has no provenance and would confound, not diagnose. No source-proven bug exists yet — which is exactly why this probe, not a fix.

**Tightenings**

1. **Verify before edit (same unit, no boot):** disassemble the actual linked `__const_udelay` — confirm where the spin loop lives (BL `__delay` vs inlined) and instrument that body, not the symbol you hope was kept. Byte-for-byte provenance outside the edited region, as before.
2. **Gate + consume-once:** arm only in the existing code38 PRE hook, conditioned on sample index 3 of the channel-6/samples-5 route; clear the flag at `__delay` entry before first read. The PRE→BL window is preemptible, so **record consumer PID and sample index** — theft becomes detectable, not silent.
3. **Record fields (fixed ~1KB, plain stores only at milestones, no locks/printk/MMIO):** tag/UUID, consumer PID, sample idx, preempt_count at entry; **requested cycles**; start counter; first loop-returned counter; milestones at iterations 1/256/65536/1M {iteration, counter, preempt_count}; return marker {iteration, final counter}. Only values already read — no new clock API.
4. **Keep preempt_count at milestones** (one word each). Without it you cannot distinguish IRQs-masked from counter-stalled — a frozen CNTVCT would also stop arch-timer compare firing, so both present identically otherwise.

**Why `requested cycles` is decisive:** observed `x0=0x13A934`=1,288,500=xloops ✓. Expected argument `((1,288,500 × lpj × 250) >> 32)` ≈ **3899** at lpj=52000 (3899 ticks @ 13.00 MHz = 299.9 µs ✓). This is the first direct capture of effective runtime LPJ.

**Interpretation, then STOP**

- **cycles ≈ 3.9k**, milestones advance ~13 ticks/µs, return at ~10²–10³ iterations, POST still absent → delay and counter **exonerated**; boundary is between BL-return and the POST recorder. Work moves there.
- **cycles ≫ 3.9k** → runtime LPJ corruption; locate the writer before any fix. (cycles ≈ 0 would have let POST fire, so that branch is already weakened.)
- **Iterations advance with zero counter delta across milestones** → CPU executing, CNTVCT read not progressing on this route. Caution: first-loop delta 0 alone is *normal* at 13 MHz; only milestone deltas count.
- **Record absent or consumer ≠ 119** → gate stolen in the preempt window or fault before BL; boundary moves earlier than `__const_udelay`.
- **Milestone preempt_count hardirq increments** → IRQs arriving during delay; frozen hardirq count → IRQs masked.

**What you cannot infer, even with a clean record:** absent return marker does not prove permanent hang; iteration counts prove CPU execution, not wall-clock duration; nothing about IRQ arrival after PRE unless preempt counts are recorded; the retained helper's 0.651961537-then-unfinished state is a different context/route and is not evidence about this call; no claim about the last IRQ. Normal return this boot proves nothing about the boundary either.

**Protocol:** fresh UUID, all-5 admission loss 0, strict retained console + full readback, normal Android return verified, BOOT/SYSTEM/DATA untouched, charging opt-in stays absent, **one run, no automatic retry or variant** until this record's sanitized facts are reviewed.