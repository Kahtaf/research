**Pick: the RDMA0/1 registration-skip boot (diagnostic fork only).**

**Why this one.** The aed PC is the first hardware-latched pointer into a specific non-timer ISR on the stuck core. The skip is a direct necessity probe with the smallest possible diff on the already-verified kernel/helper/config/bootargs, and both outcomes move you forward. Display-ISR/sched_switch capture is only correlative and would still require this causal test afterward; preemption variants inherit your userspace-loop objection and never touch the display path at all.

**Design and verification (single boot).**
- Confirm the skip took effect: one boot-time line or captured absence of RDMA registration; capture, seq latch, bootargs otherwise identical.
- Positive: helper completes ≥1.5s with timer counts and SIGALRM flag available — same boundary as before.
- Negative: same stuck boundary (PID1 stage-2 read, no helper completion) with skip verified.
- PID1 never appears: record as boot dependency, inconclusive — not negative.

**Interpretation limits to state up front.**
- The aed epoch is unestablished, and no DDP underflow line appeared in the complete console, so no storm during the hang window is proved; the PC may be reset-time servicing. Positive means "RDMA IRQ is necessary for the hang," not "underflow-storm mechanism confirmed."
- Negative clears only RDMA necessity; OVL/DSI/mutex handlers stay registered.
- Headless LK-logo run, diagnostic-only, not a shipping fix.

If positive, narrowing RDMA0 vs RDMA1 becomes justified as a later step — not now.