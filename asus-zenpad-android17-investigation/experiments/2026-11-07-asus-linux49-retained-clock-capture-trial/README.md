# One retained kernel clock/timer capture trial

Question: which selected clock/counter/timer callback entered without a matching captured return?

Status: one recovery-only trial prepared. Fresh kernel/capture UUID fef31ed4-f62b-4f2a-8cc8-8f5a6c96dbdb; unchanged helper UUID f0c3c82c-d639-4d8a-90f2-155fd4224ceb. Exact candidate and full preimage/readback required. Normal Android partitions unchanged. Owner explicitly authorized future trials without nearby availability checks and accepts eventual manual fallback; this does not assert presence. All identity/readback/one-dispatch/uncertainty checks remain unchanged. Decode complete retained rows privately, reject loss/torn records, and do not infer a cause from missing data.

## Physical capture result

Full-p10 installation/readback and cleanup verified, one recovery entry and new stock boot verified. Complete fresh capture UUID decoded with fault0 and no invalid/torn rows. Latest PID1 monotonic operation is stage2 with sequence312 (even), 391entries/390completions. Its previous counter sample belongs to an older parent. Latest hrtimer_interrupt callback and all its captured counter reads completed. The last recorded timer interrupted _raw_spin_unlock_irqrestore+16, after IRQ restore and before preempt-count decrement; interrupted task identity was not captured. This can reflect preemption/descheduling rather than a clock-core hang. See evidence/CAPTURE-SUMMARY.json; pointer addresses/rawdecoded data remain private. Large v2 assessment and a cached-lastPC clue are being evaluated before another experiment.
