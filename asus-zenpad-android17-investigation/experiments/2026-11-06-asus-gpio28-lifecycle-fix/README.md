# P00A GPIO28 cross-driver lifetime/suspend source repair

Question: fix independent routing PM and other private-state readers racing codec teardown, and preserve active suspend intent through reprobe.

Status: **source candidate staged and host-verified for fresh independent review**. UNQUALIFIED, not integrated or built for target. Prior source candidate and review remain unchanged.

- [Handoff, synchronization policy, evidence and remaining gates](report/HANDOFF.md).
- [Incremental five-path patch](patches/lifecycle-from-gpio28-candidate.patch) and [exact pre/post pins](evidence/pre-post-pins.json).
- [Actual corrected production-body results](evidence/corrected-final-run.txt):38 inherited +12 lifecycle scenarios; deterministic lifetime blocking and bounded five-actor concurrency. Assertion counts depend on scheduling.
- [Private consumer audit](evidence/private-consumer-audit.json), [scope/static checks](evidence/scope-and-static-checks.json), and [source/API pins](evidence/input-pins.json).
- Original failures are preserved in inputs/review/ and rerun under evidence/baseline-*-run.txt. [Darwin limits](evidence/host-limits.json) are explicit.

Continuation: use report/HANDOFF.md for fresh independent review; scripts/final_verify.py rehashes the completed package. Real ARM64/full-kernel validation and physical commissioning remain separate gates. HAL routes remain false. GPIO command cache follows reported API status; actual electrical low/success is not established because the controller discards register-write errors. No physical GO.

No children, device/hardware, network/cloud/VM, private data, active-source/out mutation, target/full-kernel build, excluded PCM repair access or qualification change occurred. Everything new belongs to this distinct spike.
