# Future RSC recovery phase proof

Question: Can repeated full p10 reads in the ordinary RSC writer be replaced by a descriptor-bound phase proof without weakening the fixed RAM image's recovery ownership contract?

Status: **source-only implementation and bounded local host verification complete; pending independent parent review.** No image, deployment, physical approval, Android17/data role enablement, or timing qualification. Frozen stock candidate/helper/manifest/host contracts remain unchanged.

Important outputs:

- [Report and invariant](REPORT.md): reachable writers, exclusive helper handoff, consistency/failure semantics, counterexample witness and future integration constraints.
- [Narrow future patch](future-source.patch): only `rescue.c` plus new `recovery_phase.h`; [proposed sources](source/), [exact baseline](baseline/).
- [Acceptance receipt](evidence/acceptance.json), [before/after full-geometry counts](evidence/full-geometry-counts.json), [effective policy query](evidence/policy-reachability.txt).
- [Frozen source/artifact hashes](evidence/frozen-input-receipts.json), [proposed source hashes](evidence/proposed-source-receipts.json), [exact model-body receipts](evidence/model-body-receipts.json).
- [Resource-isolated local command](evidence/local-container-command.json), [final test log](evidence/final-linux.stderr), [test suite results](evidence/linux-sessions-after.stderr). Both baseline and revision pass 23 methods with ASan/UBSan/bounds; focused guard and unchanged-handoff tests pass. Cgroup peak 216,031,232 bytes under 1GiB; CPU0 only, quota 1CPU, serial tests. Native Darwin limit failures and the corrected lost-receipt/runner failures remain in evidence.

Arithmetic: per-chunk recovery reads decrease by 241,111,289,856 bytes for exact full SYSTEM/DATA/BOOT geometry; retained phase reads total 251,105,280 bytes. No tablet throughput prediction. Full geometry uses symbolic SHA/storage only for counts; small regular-file/socketpair tests use exact production SHA and session bodies. Legacy five-role manifests are synthetic modeling, never authorization.

Continuation:

1. Review `REPORT.md`, the patch and receipts independently. Preserve its explicit boundary-detection semantics: unexpected same-node content mutation can be detected later than baseline, but cannot obtain verified/committed image success while persistent.
2. Offline integrity check: `python3 -B scripts/receipts.py` then `python3 -B scripts/audit.py` from this directory. These never connect to a device or remote builder. SHA256SUMS seals final compact outputs.
3. Optional local host replay: `python3 -B scripts/run_local.py` uses only the already-present local audit tool image, no network/root/capabilities, oneCPU/1GiB and this owned spike. Then rerun `scripts/audit.py`. It does not build an Android target/image. Native Darwin executables are not final test artifacts.
4. Parent alone integrates into a separate future revision with genuine images and rechecks its exact final service/policy/source graph. Never patch/repack the frozen stock-only candidate. Current helper still requires the fixed two-role stock manifest; a future compatible helper/core/manifest handoff plan is separate work, not enabled here. Parent owns all physical, build, deployment and timing work.
