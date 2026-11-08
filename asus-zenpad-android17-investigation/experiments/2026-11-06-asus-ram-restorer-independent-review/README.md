# Independent RAM original-recovery restorer review

Question: Does the exact unarmed p10 restorer preload and bind original recovery, preserve RSC guards, and report terminal uncertainty truthfully?

Status: **offline review complete; two parent actions remain before terminal commissioning.** No arming, execution or physical/full-OS approval. No payload/preimage/write-scope bypass was found within the documented external-image trust boundary.

Read [REPORT.md](REPORT.md) and [HANDOFF.json](HANDOFF.json). Findings concern post-rename receipt publication failure and the 15-second silent-response limit around two whole SYSTEM/BOOT proofs.

Important outputs:

- `snapshot/`: immutable copies of the selected original implementation, tests, scripts, evidence and bounded public recovery artifacts.
- `evidence/provenance.json` and `evidence/final-input-integrity.json`: all 112 inputs unchanged.
- `evidence/independent-artifact-audit.json`: fresh independent parser and exact supplied image/payload/kernel/policy pins.
- `linux-results/evidence/`: fresh 69 baseline behavior tests, 37 added core cases, 11 added handoff cases, host edge evidence, 72 policy checks/29 compiled lookups, and byte-identical binary/policy/context reproductions.
- `scripts/`: review harnesses, including retained failed first handoff marker revision.

Continuation: parent resolves the receipt acceptance rule and phase timing budget, then separately reviews a newly bound original STOCK-only build and separately authorizes bounded physical commissioning. The current zero-record candidate refuses operational restoration; no boolean-only arming, five-role profile, or full-OS claim is supplied.

Reproduction: local read-only audit can run with `python3 -B scripts/artifact_audit.py`; the explicit timeout model is `python3 -B scripts/timeout_model.py`. For Linux replay, create a NEW owned fixture from `snapshot/` and the review scripts, adapt the fixture-root assertion, retain all outputs, and use one CPU/1 GiB/serial execution. Do not rerun builders into the completed fixture or any original fixture. Commands and failures are retained in the review logs; `resume_linux.py` only corrects the owned fixture executable permission and continues remaining tests. `final_checks.py` uses the corrected 41-byte test marker and reproduces policy/contexts. Do not run the original `build_remote.py`.

The completed Linux fixture is `/srv/android/2026-11-06-asus-ram-restorer-independent-review`. No device, private data, active AOSP tree/output, original source, cloud lifecycle, or full SYSTEM/data workload was accessed or modified. Parent alone owns all physical actions and later reset/preservation decisions.
