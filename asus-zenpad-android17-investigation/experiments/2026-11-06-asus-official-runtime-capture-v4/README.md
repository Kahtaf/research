# Official runtime capture preparation v4 — actual graph scale

Question: can the coherent capture graph parser/index handle the complete generated graph inventory within finite CPU, memory and storage budgets?

Status: graph resources and the 25 known selector/generation producers are qualified on exact frozen graph copies. **Full capture provenance remains unqualified**: the graph-only path projection exposes retained v3 refusals. This is a bounded preparation, not a real output selection, verification, copy, runtime acceptance or physical GO. R8 actually failed at 2026-11-06 23:48:28 UTC, exit 1, WebView LFS pointer (parent report). Its exact retained identity cannot authorize capture. No R9 seal, PID or profile is invented.

Owned VM preparation: `/srv/android/asus-official-runtime-capture/preparation-v4`. V3 and all older preparations/profiles remain untouched. Local v3 pins still match accepted seal `36c81e2d3f4c21f0499e69bc9a19403728784b10a4b357c361533802628dd47f`.

Important outputs: `HANDOFF.json`, `tool-pins.json`, `REPORT.md`, `evidence/graph-resource-summary.json`, `evidence/all-graphs-qualification.json`, `evidence/real-index-boundary.json`, `evidence/linux-offline-tests-final.json`, `evidence/minimal-v3-v4.diff`, source/, inputs/, tests/, and scripts/. Graphs and SQLite indexes stay on the VM. Only compact receipts are returned locally.

The three-file parent observation was incomplete for the existing selector. The Soong top graph includes ten large shards that already match `build.lineage_p00a*.ninja`. The qualification indexed all 14 files: the 12 selector matches plus the 174-byte combined envelope and 29,326-byte package graph. Total: 10,983,490,939 bytes; 63,293,671 lines; 4,713,743 output-producer rows, 782,013 rule rows and 495,500 variable rows. Index: 23,803,400,192 bytes, SQLite quick_check `ok`. All include/subninja directives are covered. All actual source hashes/identities match before and after; frozen copies are read-only and separately hashed.

Full-run receipts: 813.889 seconds elapsed, 420.602 CPU seconds, 141,060 KiB maximum RSS, CPU affinity [0], 1,073,741,824-byte address-space cap. Index construction alone took 381.612 seconds. These qualify these exact graph bytes only, not future outputs or parent build success.

Explicit graph ceilings are 2 GiB per file, 12 GiB total, 32 MiB per physical line/logical block, 24 GiB SQLite index and 128 graph files/includes. Actual largest file is 1,550,844,208 bytes; largest line 23,073,958 bytes and block 23,073,979 bytes. The 24 GiB index ceiling is above the measured 23,803,400,192 bytes by 1,966,403,584 bytes; future growth can still refuse. The full qualification has 900 CPU seconds and 1,200 wall seconds; CPU/address-space limits remain process-enforced. Real CLI actions additionally have the 900 CPU-second ceiling. The owned preparation storage budget is 48 GiB, including all preserved failures and the negative 3 GiB index experiment; final storage is recorded in preparation-verification.json.

The ordinary file ceiling (256 MiB), selected/hash-only total (3 GiB), file/selected-edge counts (8,192), terminal log ceiling (2 GiB), enumerated directory entries (20,000), graph evidence (16 MiB), and JSON/journal budgets (64 MiB) remain. Graph bytes/index storage use separate limits and do not consume selected_bytes. Actual selected-payload/provenance byte fit is not asserted because no payload selection or inspection is authorized. Every profile limit field has a hard ceiling; missing/unknown fields, bools, nonpositive values and values above ceilings refuse. The parser uses bounded readline and an incremental byte counter, an 8 MiB SQLite cache and disk-backed indexing. No producer is skipped to fit a budget.

The canonical SDK37 paths, selector, full policy/CIL/mapping/context groups, signed ELF/APEX boundary, source/generator requirements, symlink/private exclusions, success-only terminal gates and schema remain. `inputs/selector.json`, gates.py, safeio.py, elf.py, packages.py and the manifest schema are byte-identical to accepted v3. New tests preserve all inherited 58 cases and add graph/profile ceilings, low-limit refusals, SQLite page exhaustion, include completeness and the streamed 32 MiB+1 line refusal. Linux QA uses source/run_tests.py (final repeat: source/run_tests_final.py) under one CPU, 1 GiB and 120 CPU seconds; exact results and tested pins are in the evidence receipts.

The first failed fixture preserved the real 2 MiB block refusal. The second three-file fixture preserved missing shard-producer refusals. The complete run preserves 40 errors from an intentionally broad host-compiler traversal. A separate graph-only projection follows the capture traversal and enumerates 962 graph candidates; it records 461 refusal observations (401 unique path/error pairs), including candidate overapproximation and duplicates. Candidate targets are not proof of existing files or symlinks. No output payload, private key, image, ELF, policy or APEX content was opened.

A concrete required-path blocker is aggregate apexkeys.txt: its exact graph has 39 explicit inputs, but unchanged Selection.provenance applies the ordinary one-source install-byte equality guard to every installed regular file. Optional undefined rule variables such as cpFlags also refuse in candidate graph traversal. These are provenance semantics findings, not resource failures or permission to relax guards. Review/fix them in a separately reviewed preparation before any full capture. Do not interpret graph resource PASS as full-capture PASS.

One local diagnostic invocation (62 tests, 2.228 seconds) accidentally overlapped VM graph QA and lacked the Linux resource harness. It is explicitly excluded from qualification; evidence/local-diagnostic.json records this deviation. Accepted VM qualification and Linux QA are serial and resource-limited.

Continuation: parent owns the next exact R9 profile and full capture after independently qualified R9 terminal success and provenance blocker review. Preserve this seal and all failed fixtures. A future profile must contain actual revision, kit path/seal, original lock inode, exact supervisor/native child PIDs, roots and configuration; never copy failed R8 identity into R9. Nondefault profiles under the new preparation require an externally reviewed exact --profile-sha256. No future profile file is created here. The default still prints a static failed-R8 plan and real selection must refuse its failed terminal.

Safe parent commands (no real output operations):

```sh
sha256sum /srv/android/asus-official-runtime-capture/preparation-v4/tool-pins.json
python3 -B /srv/android/asus-official-runtime-capture/preparation-v4/source/capture.py
python3 -B /srv/android/asus-official-runtime-capture/preparation-v4/source/capture.py --help
```

The SSH wrapper remains ../2026-11-06-asus-product-input-build-kit/scripts/remote.py, imported via run(script). Do not rerun upload.py, historical graph fixtures or v3 scripts. Existing fixture names are exclusive and failures are never resumed. sync_owned.py refuses after FINALIZED.json. Future select/verify/copy commands belong to the parent once exact identity and genuine success exist; none is authorized or executed here.
