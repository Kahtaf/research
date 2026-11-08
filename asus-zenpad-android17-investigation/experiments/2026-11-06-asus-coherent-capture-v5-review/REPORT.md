Independent review completed with three actionable preparation defects. The requested seal and all 40 tool pins match. The unchanged Linux fixture suite passes 115/115; the corrected independent harness reproduces six unexpected acceptances across three defects in 23 focused cases. No production files were fixed, and no actual capture or product admission was attempted.

Reviewed seal: `94ad6e101159c8d975fce97f9003efd77c498ca2454abe4aea2d6c06d8be92b6`.

1. **P1 — The reader can authenticate the wrong effective command when an edge has no build-local environment.** Location: [source/ninja.py:147](/OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-official-runtime-capture-v5/source/ninja.py:147).

   Minimal graph:

   ```ninja
   command = echo unreviewed-producer
   rule cp
     command = cp $in $out
   build out/a: cp src/a
   ```

   Observed: `Graph.edge('out/a')['command']` is `cp src/a out/a`, and `copy_source` accepts `src/a`. The full synthetic capture also writes `COMPLETE` and classifies the installed init as an ordinary copy after the same file-level binding is prepended to its graph.

   The expected command follows from upstream source, not from running a native engine: [Ninja v1.12.1 ParseEdge](https://github.com/ninja-build/ninja/blob/v1.12.1/src/manifest_parser.cc#L290) reuses the file environment when there are no build bindings, and [LookupWithFallback](https://github.com/ninja-build/ninja/blob/v1.12.1/src/eval_env.cc#L78) consults that environment's own binding before the rule. Here that selects `echo unreviewed-producer`. V5 always tries rule bindings before file bindings. Matching installed/source bytes does not correct this command attribution error.

   Smallest correction: preserve whether Ninja creates a build environment and add a presence-aware lookup of the current environment's own bindings before rule fallback. Defined-empty values must still shadow. Do not simply prioritize every enclosing binding over the rule: the control case with an otherwise unused build binding correctly selects the rule command. A narrower explicit refusal for conflicting reserved bindings is also safe until modeled. Keep ordinary installed/source equality and all terminal gates.

   Actual repro cases: `file_command_overrides_rule_without_build_environment`, `complete_fixture_wrong_effective_file_command`; control: `edge_environment_keeps_rule_precedence_over_parent_command`.

2. **P2 — Identical raw edges are accepted despite producer/scope ambiguity.** Location: [source/graph.py:127](/OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-official-runtime-capture-v5/source/graph.py:127).

   Minimal main graph:

   ```ninja
   rule cp
     command = cp $in $out
   build out/a: cp src/a
   subninja out/child.ninja
   ```

   Child graph:

   ```ninja
   rule cp
     command = arbitrary-generator $in $out
   build out/a: cp src/a
   ```

   Observed: both indexed output rows have identical raw build text, so `edge()` accepts them and interprets only the first row's scope. It returns the ordinary-copy command while discarding the second rule environment. A repeated identical edge in one file is also accepted; different raw duplicate edges correctly refuse.

   This is a reader ambiguity defect, not evidence that a genuine successful native build had duplicate producers. The raw-text uniqueness condition predates v5, but retaining it across v5's scope-aware interpretation makes that text equivalence insufficient.

   Smallest correction: require exactly one indexed producer record for a selected target, rather than one distinct raw string. Refuse duplicate records before choosing a scope. No whole-graph comparison or historical input attestation is needed.

   Actual repro cases: `identical_duplicate_edges_same_file_are_ambiguous`, `identical_duplicate_edges_different_scopes_are_ambiguous`; control: `nonidentical_duplicate_edges_refuse`.

3. **P2 — Unsupported dynamic dependency semantics are silently accepted.** Location: [source/ninja.py:142](/OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-official-runtime-capture-v5/source/ninja.py:142) through the returned binding inventory at line 156.

   Minimal graph:

   ```ninja
   rule cp
     command = cp $in $out
   build out/a: cp src/a || out/extra.dd
     dyndep = out/extra.dd
   ```

   Observed: the edge is accepted as an ordinary copy with one output and source `src/a`. Its build-local `dyndep` is missing from `rule_bindings` because the reader expands only fields present in the raw rule. Moving the same binding into the rule retains it in evidence but still accepts the copy. No dyndep file is opened or interpreted in either case.

   V5's pinned semantics contract and README promise refusal for unsupported dynamic dependency payload semantics. Such a binding can add implicit inputs or outputs, so the literal output/dependency inventory cannot be treated as complete. See [Ninja's dynamic dependency specification](https://ninja-build.org/manual.html#_dynamic_dependencies).

   Smallest correction: resolve the effective `dyndep` binding, including edge-local and applicable file bindings, and explicitly refuse nonempty values for producers whose payload provenance is being qualified. Do not implement a native engine, read real dyndep payloads, or scan unrelated graph edges for this review. Ordinary controlled incremental native cache does not need historical all-input byte attestation.

   Actual repro cases: `nonempty_rule_dyndep_must_refuse_unsupported_semantics`, `nonempty_edge_dyndep_must_refuse_unsupported_semantics`.

The following bounded checks held:

- The v4 seal is `bb23b4634369750f54059becaa9d96c3ec3a607c8e88ebb273b964255faf155b`. The small local v4 delivery archive matches its delivery hash and contains that same tool-pin seal. Its static delivery receipt agrees with v5's inherited FINALIZED/index pins. No remote historical index, graph, or identity was rechecked. V5's projection/supplemental-scan claims were reviewed as completed static receipts only.
- `gates.py`, `safeio.py`, `elf.py`, `packages.py`, the failed-R8 profile, and all 65 inherited v4 tests remain byte-identical. The five-file diff recomputes exactly from the v4 preimages, including its summary of new core files. All HANDOFF receipt hashes match.
- The selector's mandatory six core modules—init, apexd, keystore2, servicemanager, linkerconfig and hwservicemanager—remain required, along with toybox, sh, keymaster service, both actual BoringSSL output paths, signed runtime APEX, adbd CAPEX, canonical properties, policy/context/mapping sets and the public-trust tree. All existing selector fields except the expanded graph inventory are unchanged; the two new SHA bindings are present. Package inspection still makes no signature/trust or extracted-payload claim.
- Twenty mandatory ordinary install sources remain pinned. Ordinary captures still require one explicit source/output, an exact recognized copy command, and installed/source equality. Unknown metadata filenames do not acquire a generation exception. Those current coherent-byte and genuine-terminal checks are appropriate to the stated incremental-cache scope; this review adds no historical all-input attestation requirement.
- The sole aggregate exception retains 39 ordered explicit inputs and 39 exact raw-copy producers, three generator-source hashes, cmp/cp path references and streamed ordered aggregate equality. The three generator pins match the already-captured public-source evidence. The baseline covers changed dependencies, producers, raw inputs, generator bytes and tool aliases; the additional reordered stream refuses with `GENERATION_BYTES`.
- Metadata source roles retain the accepted tool-group digest `624ff875e00eea2489502489bfad4587efa398457d110bf404baac76e97aeff3`, exact source-plan/profile/validator binding, source-postimages binding and the validator's installed-four content-receipt binding. Missing/spoofed validator bindings refuse. No external resolver binary/dependency was rehashed or run.
- A full synthetic qualified-terminal → role collection → select/copy case succeeds with an explicit present zero-byte system slot and five separately attested absent slots. The zero-byte copy's before/copy/after hashes match. Malformed override/fallback tests pass; independent slot/context symlink, forged absence and >1 MiB override probes refuse. Baseline fallback tests use injected metadata-only observers; the integration probes also inject host-fallback observers and never inspect actual absolute fallback locations.
- Compiled magic is only a preparation format guard: a four-byte header can pass collection while every native/admission flag remains false. Native loading/PCRE compatibility is expressly deferred. The end-to-end unknown final compiled-context producer refuses with `PRODUCER_COMMAND`; no filename exception was introduced.
- A failed terminal refuses before metadata collection is called. Genuine terminal/source/kit/launch/configuration qualification remains in its original order. Default `PLAN_ONLY` continues to inspect no source/output and acquire no build lock. Null metadata roles remain confined to synthetic legacy use by the production-root guard.

Evidence and execution:

- [Baseline receipt](evidence/baseline-execution.json): Linux, 115 tests, zero failures/errors, 22.52 seconds wall, 90,584 KiB maximum child RSS.
- [Corrected focused receipt](evidence/adversarial-r2-execution.json) and [individual cases](evidence/adversarial-r2-cases.json): Linux, 23 cases, 17 expected outcomes, six unexpected acceptances supporting the three findings; 2.479 seconds wall, 30,516 KiB maximum child RSS. A zero harness exit means collection completed; `expectation_met` determines each result.
- [Seal/pins](evidence/local-seal.json), [v4 static binding](evidence/v4-static-binding.json), [final static verification](evidence/final-static-verification.json), [runner](scripts/remote_review.py), and [focused harness](scripts/review_adversarial.py).

The baseline was run once through the established parent SSH wrapper, only under NEW `/srv/android/asus-capture-v5-review-20261106`. Both Linux runs use one CPU, 1 GiB address space, a 120-second CPU limit, a 180-second wall timeout and 48 MiB per-file limits. Owned storage is checked before/after against 128 MiB; final recorded size is 360,745 bytes. There is no continuous filesystem quota: the serial finite fixtures' largest allocation is the inherited 32 MiB+1 graph-line case, with small fixture trees/indexes/logs, within the authorized aggregate allocation. No timeout fired and no process signal was sent.

The first focused run is preserved in `adversarial-execution.json` and `scripts/review_adversarial-r1.py`. Two integration cases initially lacked the synthetic selector's resolver-reference field and stopped with KeyError; the corrected run supplies that existing pinned reference and both cases pass. These were harness setup errors, not findings.

Local seal/diff/static checks ran on Darwin/macOS 26.7.2 arm64. No inherited Linux test was run locally. No children were used. The first workspace filename inventory was overly broad and listed unrelated paths without reading their contents; subsequent content reads stayed within v5, necessary static v4 material and the established wrapper. No real source/out/cache/kit/process/build progress or real product/index/graph was inspected or consumed. No native engine, device/ADB/root/USB action, private-data read, cloud lifecycle action, actual R9 profile, runtime claim or physical GO was performed. No original pinned file changed.

Continuation: address the three reader defects in a separately owned preparation revision and add the named finite regression cases. Preserve every current output requirement and terminal/nonadmission gate. Review receipts and remote scripts are one-shot artifacts; existing upload paths deliberately refuse replacement. Any follow-up fixture revision must use a fresh script/receipt label inside the same authorized review prefix. Real capture, R9 execution, metadata product admission and guarded native queries remain separately owned parent work.
