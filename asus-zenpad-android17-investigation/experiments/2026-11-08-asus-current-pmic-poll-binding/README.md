# Current PMIC polling binding

Question: Does the compiled e7acab50 AUXADC/pwrap route have an IRQ-off polling escape dependent only on hardware readiness or a clock/counter, and is a self-blocking dependency established?

Status: **One bounded evidence acquisition/source qualification unit complete; STOP.** Current compiled pwrap has IRQ-off/preemption-off clock-bounded polling without an independent iteration limit. No concrete self-blocking jiffies/IRQ dependency established; conditional nonprogress remains unproved physically. Exact VM verified TERMINATED; owned master closed.

Outputs: [report, under 900 words](REPORT.md), [source pins/ranges](SOURCE-PINS.json), [actual route and limits](ACTUAL-ROUTE.json), [artifact manifest](ARTIFACT-MANIFEST.json), preserved source/slices and evidence; lifecycle receipts under evidence. Eight current production bodies fetched; five prior battery/power files plus original delay bound by remote hashes only and matching preexisting local bytes.

Continuation: Parent may review the finite-budget hardening contract described in the report. Counts need defensible derivation; no patch staged. No automatic source/out edit, fix, build, test, candidate, device operation or physical trial. Runtime causal evidence remains absent; WRET is not userspace resumption.
