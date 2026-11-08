## Verdict: B, still strictly best. A's negative didn't shift the decision space — it validated it.

**Why B, not C:**

1. **A's sparse negative settled the exposure variable, not the agent variable.** Same boundary under 2550B console, fresh-stock PC again at __delay+212, status 32 again: the phenomenon is publication-independent and the stall locus is stable (gated __delay in the PMIC read path). The open question is now *reset agent identity* — exactly B's target. C targets IRQ-storm/delay, and nothing new supports it: before-IRQ snapshot was complete (PPI29=0, PPI30=178), no after-counts, and by your own text C "doesn't identify reset agent or fundamental counter freeze if no IRQ."
2. **C reintroduces the volume A just removed.** A proves heavy publication is *not necessary*, not that observers are exonerated. Re-adding hot-path recorder work now would confound the clean sparse control you just paid for. If B returns EN0 + no SW marker, C becomes justified *then* — not now.
3. **Only B converts your provenance unknowns into named facts.** rr_pl.wdt_status=32 must not be decoded without producer provenance — B's restart_handler marker+caller is the producer test. The watchdog source facts are dated with post-stop readback UNOBSERVED — B's probe entry/early-error/stop-before-after is the runtime confirmation. C delivers neither.

**B scope (your text, unchanged, on sparse base):** verify exact base body vs actual ELF first (decode +212 as delivery verification, no assertion); probe entry/early-error (map/IRQ registration); existing stop with ONE MODE.EN readback after the original keyed clear; limited source-qualified request-reset config reads; restart_handler entry marker+caller before original restart writes. Read-only + few typed ASCII markers, exact PoC barriers, no 29KB area, no hot trace, no timeout/kicker/reset-policy/thermal/charging/clock/IRQ changes. Adds ~tens of bytes to a 2550B console; the single post-stop MMIO read is on the cold probe path, one-shot, not a new frequent observer. New stock binding, Power fallback, one-build/one-trial stop all stand.

**sysfs question: exclude.** /sys/class/watchdog0 state needs a helper change (new variable) and reflects the watchdog core's derived running flag, not raw RGU MODE.EN — it cannot prove stop acceptance. Kernel direct MODE readback is strictly better, as you concluded.

**What EN readback does NOT prove (state in report):**
- EN=0 does not exonerate RGU: pre-stop timeout, thermal/scpsys request path, preloader WDT, or firmware reset remain possible. It proves only that this one stop write was accepted at that instant.
- EN=1 does not prove the ~32.45s deadline identity or any 31s margin — parent already rejected the wall-clock claim. It names only "stop acceptance problem."
- Readback alone does not decode rr_pl.wdt_status provenance; only marker+caller does. Marker *absence* is also consistent with a hardware bite that never enters the kernel path.

**Predictions, each mapping to a named fact, not an automatic chain:**
1. Probe not run / errors before stop → fact names that path; next unit is the path, not a watchdog change.
2. EN still 1 after keyed clear → stop write not landing; next unit verifies base/key translation. No policy change.
3. EN 0 + config reads + no SW marker + UNKNOWN_STOP again → stopped mt_wdt is not the agent; deadline identity stays unproven; return to consult (thermal/scpsys request, preloader WDT, or C justified *then*).
4. Marker + caller present before original restart writes → SW reset path invoked; caller identity **is** the agent — direct fix path opens on that caller.

Predicted console if no SW reset: first complete run including final/SIGALRM/after-IRQ/finish, itself localizing the freeze between initial-end and final.

**Fix path:** only outcome 4 (or 2's base correction) yields a fix candidate; 1/3 return to consult. A's negative granted no watchdog *change* — B changes nothing, so the parent rule is satisfied. No rerun of A; no CNTPCT/PMIC variant without new proof.