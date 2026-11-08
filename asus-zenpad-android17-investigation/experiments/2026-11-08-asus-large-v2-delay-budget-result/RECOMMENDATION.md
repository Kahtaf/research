# Decision: one non-build adjudication of the delay-route hypothesis, from artifacts already on disk. No flash, no source change.

**Unique hypothesis, falsifiable on paper:** the per-iteration route check in `__delay` — where both cached PCs landed, across two differently compiled builds, with a consistent reconstructed caller SP — selects an out-of-line/indirect counter read, or the same virtual-counter stream that feeds `sched_clock`'s pwrap timeout. If that route is active and contains a stallable access, it matches every observation: budget never exhausting (a stall inside the read executes zero iterations; repeated calls under a healthy counter never reach 2^24 per invocation), kernel commits ending at the workqueue-driven thermal retries, PID1 never resumed, no panic text. The budget trial already covered the continuous-runaway variant and probably excluded it; the two survivors (single-access stall; repeated short calls in an IRQs-off poll) are both touched only by a shared-route change — **but only if the runtime route is actually non-trivial.**

**Deliverables, strictly offline, from the already-bound maps/vmlinux/config/DT/boot-chain source:**

1. Symbolize `0xffffff80087b4cf8` (key) and the chain `+0xd00 → +0x28` in both builds; name the installed read function.
2. Every runtime writer of the key; decide its value for this config/DT/CPU.
3. Whether that OOL read is a stallable access (MMIO/indirect) or a barriered register read.
4. Whether `sched_clock` reads the same counter stream, and what CNTVOFF the boot chain sets. `__delay` is delta-based and offset-safe; `sched_clock` is not — this scopes any pin.
5. From kernel/preloader source: which events arm/capture the aed LAST-PC fields, and whether any can fire after WDT probe-disable — bounding whether the cached PC can even date from the post-compute-begin epoch, versus a normal early-init delay snapshot.

**Pre-committed branches (I authorize no build):**

- **Route obstacle confirmed** (key nonzero or OOL otherwise active and stallable, and the latch epoch can post-date compute-begin): the single justified physical trial is the shared-route pin — direct inline CNTPCT for `get_cycles`/`__delay` system-wide, plus `sched_clock` only if CNTVOFF=0 is proven. Distinct from the CNTPCT cookie test: that changed one call site and left causality unresolved; this moves every consumer at once. Semantics preserved: same 13 MHz stream, deltas, and CNTPCT readability is already demonstrated (3900 ticks / 14262 checks). Positive: compute-end/timer records retained → route was sufficient. Negative: identical retention (compute-begin last plus two thermal lines) → route not necessary; survivors narrow to condition-poll/return-path. Both one-trial, non-categorical.
- **Route eliminated** (key provably 0, pin would be a no-op, or latch provably early-boot): do NOT pin. The smallest missing observable is then one helper-side record printed after the compute-begin `write()` returns and before the loop — no kernel change — separating "write never returned / PID1 never rescheduled" from kernel-side stall. Or stop.
- **Ambiguous offline:** stop and report experiment 3 blocked on that smallest missing observable; no physical trial is justified by the evidence.

**What NOT to infer:** budget no-exhaustion does not rule out long delay (panic/publication can themselves stall); neither cached PC is a proven stop point; the matching caller SP is correlation, not a call chain; one perturbed exposure refutes nothing categorically.

**Stopping rule:** one assessment, time-boxed. At most one follow-up physical trial in the chosen branch. Two consecutive ambiguous physical results → mark experiment 3 blocked on observability, not on the kernel. Experiments 4 and 5 stay gated; stock BOOT/SYSTEM/DATA remain untouched.

This assessment can settle two gating questions — whether the route change is a real experiment or a no-op, and whether our only hardware pointer pertains to the stall at all. It cannot settle the freeze itself, and I won't pretend otherwise; but it converts the next trial from guess to justified.