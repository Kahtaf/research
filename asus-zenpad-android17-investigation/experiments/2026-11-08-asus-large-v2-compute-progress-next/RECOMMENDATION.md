## Choice: A — completion-only compute helper (remove 500k/1M/1.5M writes, keep 2M + afterIRQ path). Helper-only, one compile, one trial, no kernel build.

Yes, removal is now justified: the 500k capture already exhausted what intermediate milestones can prove (compute reaches 500k; log_store completes there). Their only remaining value is 1M/1.5M granularity, while each write carries the one unobserved step — its return — which is currently your prime bounded suspect. Removing them cuts write opportunities from 4 to 1, placed exactly where its failure is maximally informative: immediately before the same-thread afterIRQ snapshot.

## Critique

**A (chosen)**
- (+) Cheapest: fresh helper UUID + fresh control UUID admitted in clock.path VALUE, full p10 readback, new stock boot, complete-console bind, one physical trial. Subtracts instrumentation rather than adding an observer layer — this ends the loop-variant series either way.
- (+) Best case advances directly, not diagnostically: the afterIRQ snapshot is published by the same thread after the completion write returns, so its presence *proves* the sole write returned. Next step is storage/MMC, not another loop.
- (+) Partial result localizes as well as B would: "2M captured, no afterIRQ" pins the stall between the completion write's log_store and snapshot publication.
- (−) Negative is coarse: stall anywhere in 0–2M compute/time, or the single write blocked pre-log_store (kmalloc/copy_from_iter — low prior). You deliberately sacrifice 1M/1.5M granularity.
- (−) Single-trial inference assumes the stall reproduces across boots.

**B (write-return observer / direct retained endpoint)**
- (+) Measures the one datum the log_store-end hook cannot see: whether devkmsg_write returns (printk_emit/console tail).
- (−) Kernel incremental build plus a new capture ID — another observer layer, against your stated aim.
- (−) Purely diagnostic: both branches still require a further trial before anything advances; if A completes, B's information was unnecessary.

## Exact outcome semantics

| Result | Meaning |
|---|---|
| **POSITIVE**: 2M event with actual checksum == e4ca7075, plus restore confirmation and afterIRQ snapshot (PPI29/PPI30) in the complete console | Loop traversed 0→2M under normal policy 0; the sole write published **and returned** (same-thread snapshot proves return). The intermediate write was the stall boundary. Proceed to the storage/MMC step as a separate decision. |
| **PARTIAL**: 2M event == e4ca7075, but no afterIRQ/restore | Compute traverses the full 0→2M range — exonerated. Stall is between the completion write's log_store capture and snapshot publication; the write's return is the bounded suspect (printk_emit tail/console flow), sub-point unproven. Confirms the logging boundary was load-bearing. |
| **NEGATIVE**: no 2M event; initial clock marker present, console complete, stock Android returns | Stall recurs with **zero** intermediate writes → the 500k write was not required for it. Stall lies in compute/time within 0–2M, or the single write blocked pre-log_store (low prior). Does **not** prove publication innocence, CPU lockup, timer death, or prior-epoch effects. |
| **UNKNOWN (all outcomes)** | Cross-trial reproducibility of the stall; elapsed wall-clock; whether the prior trial's 500k write returned; on negative, the stalled sub-range. |

## Bounds

Same loop/LCG constants/seed 0x6d2b79f5/2M; delete only the three milestone writes; completion write keeps the identical bounded format and /dev/kmsg O_NONBLOCK path. Initial direct clock + alarm preserved (in-trial control: its return precedes the loop, as before). Restore-on-exit discipline and afterIRQ snapshot path unchanged; no RT changes, no final clock, no new observers, no kernel build. Fresh profile (e.g., sparse-compute-final2m-v1), fresh helper/control UUIDs, full p10 readback, new stock boot, complete console bound, one physical trial, no automatic follow-ups. Manual Power fallback remains the accepted end if negative.