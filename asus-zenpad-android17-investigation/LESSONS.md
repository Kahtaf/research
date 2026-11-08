# Process and lessons

## What helped

- **Calibrate the observer on known-working stock first.** The biggest advance was separating a broken reporter from a broken kernel. A marker's absence could be guard refusal, transport failure or retention loss.
- **Use one-variable experiments with explicit outcomes.** Fresh run identity, exact source/config/image hashes, one physical exposure, complete retained bytes and a separately verified stock return made the results interpretable.
- **Keep proof layers separate.** Source consistency, actual ARM64 compilation, isolated guest runtime, target physical behavior and whole-product usability are different achievements. A passing host checker is not a boot.
- **Follow real failing paths.** The WebView pointer, Make-string boolean, namespace duplication and BPF attribute failure each had a reproduction and a small mechanism-specific correction.
- **Preserve failed evidence.** Failed r8/r9 attempts, rejected audits, old validator outputs and superseded candidates were kept, rather than touched/cleaned/renamed into apparent success. Controlled incremental trust did not require fabricated timestamps or log rows.
- **Review mutation boundaries separately.** Rescue/source admission, expiry, USB binding, durable host receipts, child cleanup and UNKNOWN handling all mattered. “Unknown completion” must not trigger an automatic inverse or retry.

## What cost too much

- We let many small captures accumulate around the same unresolved boundary. A more detailed partial trace did not necessarily distinguish a hypothesis. The owner repeatedly had to pull the work back to practical usefulness.
- We delayed the coarse reduced-platform experiment while following individual workers, PMIC stages, timer paths and logging seams. Its retained protection closures still limited causal conclusions, but it was a better premise test than another tiny trace.
- Build/host constraints imposed by launchers created avoidable failures. An unrequested address-space cap and a supervisor stop consumed time without testing the target hardware hypothesis.
- Hundreds or millions of host assertions attracted attention disproportionate to their value. They helped validate local code contracts; they did not establish that a tablet could compute, wake, display or charge safely.
- Automated selection rules also needed review: potential installables were the wrong LFS scope, current-log membership was an accidental cache requirement, and archive filters initially missed C++/Java/untracked source. Each selection predicate needed to match its actual question.

## Cross-model consultation

The owner requested Opus 5.5 first and Large v2 only after refusal. Consultations supplied useful counter-hypotheses, but were not authority. Exact selected-model metadata and fallback notices were recorded. Unrequested fallback answers were not accepted as Opus 5.5 responses.

Concrete rejected recommendations included: assigning walltime to iteration counts without calibration; interpreting missing panic/marker output as a negative; decoding retained decimal 32 as a raw hardware bit; treating a zero workaround key as making CNTPCT/CNTVCT selection a no-op; and returning early from a required hardware delay. The delay-budget implementation used a diagnostic fail-stop instead of early return. It remained inconclusive.

## A better restart protocol

1. State the user-visible outcome: useful dashboard/browser and reliable small services, not a boot-count milestone.
2. Write the current uncertain premise and the one observation that would distinguish it.
3. Calibrate that observation against stock or a known-good path; bound its retention/identity/readout limits.
4. Run at most one physical exposure per admitted experiment. State positive, negative and UNKNOWN in advance. Do not call absent output negative unless delivery is qualified.
5. After repeated unknown results, stop for an independent reassessment. Require new causal leverage before building again.
6. Preserve a compact source-and-decision checkpoint and retire paid infrastructure when the goal changes.

The next proposed direction is a lightweight Linux userspace on the working stock kernel, with small services and a usable touch/browser interface as real checkpoints. It is not an already proven shortcut; display/input/network/package compatibility remain to be established. Heavy coding builds can run on the owner's other computer while the tablet acts as a client.
