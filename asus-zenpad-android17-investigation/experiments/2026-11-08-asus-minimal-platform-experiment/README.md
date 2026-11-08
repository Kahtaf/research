# One minimal-platform experiment: experiment3 reset

Question: can a substantially smaller protection-preserving Linux4.9 platform execute normal RAM work and repeated timer wakeups, after removing accumulated diagnostic and nonessential subsystem complexity?

Status: owner authorized this change of approach. Preparing a concrete configuration/DT/helper design first; no kernel build or physical action yet. This is one new coarse experiment, not a continuation of loop/poll/property variants.

Pass target: normal-priority compute completion plus repeated timer-driven wakeups and increasing IRQ/clock observations, then verified stock return. Precise walltime and fullOS readiness are separate; timer-based intended duration is not a guaranteed fallback if the kernel stalls.

Protection boundary: preserve existing inhibited-charging/write-permission settings, PMIC/regulator infrastructure, thermal critical/shutdown and watchdog/power-key paths. Do not silently compile those out. Removal of diagnostics and nonessential consumers must be distinguished from removal of safety/control paths. Any unresolved dependency blocks build pending parent review.

Outputs: design/config/DT delta and keeper/removal evidence in the implementation sibling; parent review before one build. Existing normalAndroidBOOT/SYSTEM/DATA and all former artifacts remain unchanged.

Continuation: review exact resolved configuration and run contract, consult Opus first if a decision is unresolved (Large only if Opus refuses), then one build/one trial if scope is sound. No automatic matrix or repeated source/budget/loop variants; negative/ambiguous outcome ends this approach for reassessment.
