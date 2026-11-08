# Independent review packet

Review is pending. Evaluate the source model and fixture evidence, without accessing real graphs, outputs, kits, R9, native engines or devices.

## Review targets

1. Compare `minimal-v5-v6.patch` with pinned Ninja 1.12.1 source. Inspect `Scopes.file_binding` presence, lexical scope and eager cutoff, `Scopes.edge` environment creation, effective lookup and parse-time dyndep. Check own-file vs new edge environment, defined-empty shadows, enclosing parent fallback and builtin handling. Source snapshots, not an executed native engine, are the semantic oracle.
2. Confirm graph.py matches the exact parent postimage and the exact tiny Graph/index four-case test fails before/passes after. Historical duplicate-before-001 has a corrected CPU-limit receipt; use duplicate-before-002 for acceptance.
3. Inspect the unchanged 23 predicates in `scripts/review_23.py` against the original copy. All six prior unexpected acceptances now refuse. The parent-command-with-local-environment control still accepts. Inspect all 35 new tests for empty/presence/scope, eager/dollar/cycle/malformed and no-dyndep-payload behavior.
4. Confirm runtime QA equivalence in finalization and byte-preserved provenance/metadata/terminal/source/private-path guards. No claims about actual graph acceptance or full payload validation follow from these fixtures.

## Exact safe parent commands

On the VM, verify the externally delivered seal first (the exact SHA256 is in HANDOFF.json), then run:

```sh
sha256sum /srv/android/asus-official-runtime-capture/preparation-v6/tool-pins.json
python3 -B /srv/android/asus-official-runtime-capture/preparation-v6/scripts/verify_seal.py
python3 -B /srv/android/asus-official-runtime-capture/preparation-v6/source/capture.py plan --mode PLAN_ONLY
```

The verifier reads only this preparation and enforces one CPU/1 GiB/30 CPU seconds with a finite internal byte budget. The plan reads its fixed contracts only; it does not authenticate or authorize a build. The finalizer exercised this exact default plan under a 30-second wall bound. Avoid rerunning QA in the immutable prefix because tests create fixtures/receipts; an independently reviewed new small-fixture sibling is required for any replay.

No select/verify/copy command for a real build is supplied: the actual future profile identity, genuine terminal success and metadata/content bindings are unavailable and belong to the parent. Add them only in a new preparation sibling after review and qualified build success. Authenticate all actual graph identities; do not reuse an old index without full identity equivalence. Follow the preserved METADATA-SOURCE-CONTRACT.md for six fs_config slots, host fallback absence, compiled contexts, exact roots, tool/source/API/library/cap/perms bindings and complete installed-four content receipts. Exit zero alone is insufficient.
