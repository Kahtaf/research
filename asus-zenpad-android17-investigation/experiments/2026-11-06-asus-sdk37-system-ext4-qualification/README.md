# SDK37 SYSTEM ext4 qualification

Question: Do actual SDK37 SYSTEM mkfs/e2fsdroid selections work with the pinned ASUS 4.9 kernel, and what final-image gate is required?

Status: Complete: bounded 64 MiB SDK37 ext4 mechanism PASS on pinned virtual 4.9.337; full SYSTEM and physical GO remain unqualified.

Outputs: [REPORT.md](REPORT.md), [acceptance.json](acceptance.json), [FINAL-SYSTEM-GATE.md](FINAL-SYSTEM-GATE.md), reusable read-only `scripts/check_system_header.py`, deferred `scripts/propose_full_gate.py`, and pinned `evidence/`/`source/`. Large files remain under `/srv/android/asus-sdk37-system-ext4-qualification-20261106`; accepted run: `fixture-r2/runtime-r4`.

Continuation: Read REPORT.md and acceptance.json before reuse. Preserve all prior fixtures. Never mutate active r8/source/out, run captured Ninja commands, rebuild AOSP/kernel, or infer wholeSYSTEM acceptance from the small specimen.

Reverify local receipts with `python3 -B scripts/finalize.py`. Historical preparation/runtime scripts document preserved failed attempts and must not be rerun over these fixtures. Only the header checker is an executed reusable final-image tool; the full-product command emitter and mount contract are deferred proposals.
