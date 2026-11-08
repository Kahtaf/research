# Decision for experiment 3: bound the global `__delay`, then one physical trial

**One change:** add an iteration-capped escape hatch to `__delay` itself (the function containing the saved PC), everything else byte-identical. This is fault isolation, not a shipping fix.

## Why this and not a helper reorder

The 2M loop is pure EL0 arithmetic with no calls — it cannot hang, only be starved or never started. Moving compute before any kmsg write cannot separate those (a missing record stays ambiguous; a present record mostly re-tests logging). It grows the logging rabbit hole you want closed.

The delay/liveness family is where the evidence converges, with nothing positive pointing at the logging path:

1. The cached CPU0 PC (capture/rearm caveats acknowledged) is the per-iteration key-check *inside* the `__delay` spin — `cmp w1,#0` at +0x44, re-reading the workaround key every pass, not a counter read. Positional, unproven, but it is the only location datum you have.
2. The retained pwrap poll runs IRQs/preemption-off and times out on the same 13MHz counter family.
3. The thermal records after compute-begin show kernel-side work and printk still emitted later, so this was not instantaneous whole-system death at the write — consistent with a spin or starvation, not with logging having killed the box.

You have never changed the global `__delay` in the minimal baseline, and this is not the cookie control: that swapped one matched call site; this bounds the shared primitive all poll paths use, which is exactly the untested common factor.

## Design

One function. Keep semantics; break out after a hard iteration cap (e.g., 10^9 passes — seconds of spinning, far beyond any legitimate single delay here). On first escape only, printk one line: requested cycles, CNTVCT delta, iteration count, workaround-key value, and caller PC via `__builtin_return_address(0)` — one word names the polling subsystem, no per-function instrumentation. Same kernel config, DT, helper, compute loop; no protection/thermal/BQ/driver changes. A false escape (legit multi-second delay) would show as advancing delta with a plausible caller — data, not damage.

## Criteria

**Positive — obstacle confirmed and characterized:** escape record appears.
- Delta ≈ 0 or frozen across reads → counter not advancing in that context; this also explains the sched_clock pwrap timeouts.
- Delta advancing but repeated escapes, same caller PC → device status never becomes ready; caller identifies the site.
- Escape then compute-end/success follows → experiment 3 closes: obstacle removed, mechanism named.

**Negative — delay family demoted:** complete UUID-selected fresh run, stall persists, no escape record. Stuck-`__delay` is not this obstacle. Remaining family is PID1's write/return path or scheduling starvation. Do not iterate then; the smallest missing observable becomes a single retained marker that PID1 returned from the compute-begin write to EL0 and entered the loop (one helper word after the write, before the loop). Decide on that word only after this negative, not now.

**Unknown:** escape fires but no compute-end → delay family confirmed but insufficient (outer poll with frozen-clock timeout, or a second obstacle). Record caller PC and delta, stop. Retained output missing entirely → unknown, not negative, per your existing rule.

## What it cannot conclude

Whether compute-begin's write() returned (unless compute-end follows); whether the saved PC reflects this reset; causality of the earlier cookie control.

## Stopping rule

**One physical trial.** Positive → close or localize experiment 3 and stop; no variant chain. Negative or unknown → stop experiment 3 as blocked-on-observability with the PID1 EL0-return marker named as the single missing observable; experiments 4 and 5 stay gated; stock BOOT/SYSTEM/DATA untouched; manual Power fallback accepted.