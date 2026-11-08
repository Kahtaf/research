# V6 implementation result

The v5 review's six unexpected acceptances now refuse in the original 23-case review harness. The parent duplicate patch is incorporated verbatim. This result qualifies the source model on public synthetic fixtures; independent review remains pending. No real graph or product payload was inspected or qualified in v6.

## Effective Ninja environment

The public Ninja v1.12.1 tag resolves to commit `2daa09ba270b0a43e1929d29b073348aa985dfaa`. The exact source snapshots, SHA256s and commit URLs are in `inputs/ninja-1.12.1-pins.json`.

`manifest_parser.cc::ParseEdge` creates a separate BindingEnv only when actual edge bindings occur. A binding whose value is empty counts; comments do not. `eval_env.cc::LookupWithFallback` checks binding presence in the own environment, then the rule EvalString, then the enclosing environment. Accordingly, an own file `command` shadows a rule when no local environment exists; any real edge-local binding creates an environment where a parent file `command` no longer precedes the rule. Defined-empty values shadow just as nonempty values do. Subninja parents remain enclosing; includes share their lexical environment. Builtin `in`, `in_newline`, and `out` retain upstream precedence.

File and local bindings remain eager. Local values evaluate against the enclosing environment rather than other locals. Rule values remain lazy, with malformed syntax, depth, size and cycle guards. Command lookup uses the final lexical environment. Effective dyndep uses the parse-time cutoff and unescaped builtin paths, matching ParseEdge/GetUnescapedDyndep timing. A nonempty local, rule, own-file or applicable enclosing dyndep refuses with GRAPH_DYNDEP without opening that payload. Empty own/local/rule values retain their distinct shadowing behavior. No native engine or dyndep implementation was introduced.

`source/graph.py` is exactly the parent's supplied patch postimage `8c18686203fcd4c11136b1df6c595c182479ebbd6a86a640b3820df4a612c316`: exactly one indexed producer record is required, including when duplicate raw text matches. The only other production change is the deployed prefix in capture.py. See `minimal-v5-v6.patch`.

## QA and limits

| Linux fixture phase | Result | Wall seconds | CPU seconds | Peak child RSS KiB |
|---|---:|---:|---:|---:|
| Inherited baseline | 115/115 | 26.992 | 9.662 | 90,708 |
| New environment/dyndep cases | 35/35 | 0.872 | 0.440 | 28,676 |
| Original review predicates | 23/23 | 2.528 | 0.801 | 30,608 |
| Parent exact prepatch regression | expected two failures | 0.123 | 0.079 | 20,192 |
| Parent exact patched regression | 4/4 | 0.111 | 0.066 | 19,984 |

Each phase is serial, one CPU, 1 GiB address-space ceiling, 120 CPU seconds and 180 wall seconds; outer upload/runner limits are finite too. RSS is Linux RUSAGE_CHILDREN high-water RSS, not a full instantaneous process-tree sum. Child CPU includes user+system time. Before/after tool hashes are unchanged. Receipts record exact tested pin sets and timing. The original review predicates were unchanged; only fixture-root/output routing and an exit status check were adapted.

The historical duplicate-before-001 receipt incorrectly reported a 120-second child CPU cap although that child inherited 240 seconds. Both were finite; it used 0.066 CPU seconds. The correction receipt preserves this fact. An explicit pre-exec 120-second limit was added and the tiny before/after pair repeated. Baseline, new cases and review children already enforced 120 themselves. No timeout or process signal occurred. Runtime sources and test logic did not change after their passing phases; finalization verifies their exact hash equivalence rather than rerunning them for documentation changes.

New allocation is limited to 128 MiB. Owned prefix pre/post checks, 48 MiB per-file limit, bounded fixture populations and sequential fixture cleanup implement the budget; this is not a filesystem quota or continuous peak-storage measurement. The largest baseline negative fixture is about 32 MiB, with the small graph/index and tool population leaving ample room below 128 MiB. Finalization reports retained bytes and checks the full owned prefix. No large index, graph copy or rehash was made. No real-scale performance conclusion is claimed.

## Preserved contracts and limits

The byte-preservation receipt binds all three inherited test modules and 21 protected files, including metadata roles, source-plan schema, provenance, ELF/APEX/package/safe-I/O/terminal logic, failed-R8 profile and selectors. The external metadata group remains `624ff875e00eea2489502489bfad4587efa398457d110bf404baac76e97aeff3`. All six core/official crypto/APEX/trust selectors remain unchanged. Exact 39-input recognized aggregate provenance and ordinary one-source byte equality remain unchanged; unknown producers refuse. No host metadata resolver was invoked.

V5 and its review were checked locally against their existing static pins; their bytes remain unchanged. No previous VM preparation, graph, index, real source/out/cache/kit, process, R9 or device was inspected. V5 graph receipts, if consulted later, are historical evidence, not v6 requalification or permission to reuse a prior index. Future production must authenticate all actual new graph identities and source/generator/content groups, qualified terminal success and strict metadata bindings.

Default plan remains failed-R8 and is informational only. No real R9 profile or success identity exists here. Parent owns future exact SHA-bound identity after genuine terminal/source success, independent review, actual capture, metadata query and admission. No full capture, runtime readiness or physical authorization is claimed.
