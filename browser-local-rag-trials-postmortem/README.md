# Browser-Local RAG Trials Postmortem

Date: 2026-05-17

## Purpose

This document consolidates the local browser-based RAG experiments into one durable research artifact. It intentionally preserves the meaning, logic, validation results, and next direction rather than preserving disposable prototype files.

The short version:

> Browser-local private-data reasoning is viable as an evidence-engine problem. It is not viable if the small browser LLM is asked to be the indexer, planner, memory writer, retriever, and final judge.

Kuzu was the most promising substrate because typed graph relationships gave the small model a smaller and more meaningful world to query. It still failed where the graph did not already encode the right semantics: source disambiguation, negation, return/refund logic, fuzzy product intent, broad multi-source synthesis, and reliable summary coverage.

The next useful direction is not another one-off prototype. It is a local evidence engine, likely using LocalMode or LlamaIndex.TS for ergonomics, with Kuzu/source trees as the evidence substrate and the small model behind strict retrieval and citation gates.

## Consolidated Experiments

| Trial | Core logic | What worked | What failed | Lesson to keep |
| --- | --- | --- | --- | --- |
| Large lexical baseline | Generate a 50 MiB+ local corpus, chunk it, build an inverted index, and test planted-fact recall before involving an LLM | 52 MiB indexed quickly with 100% recall@10 on controlled facts, low pollution, and modest memory use | Controlled planted facts are easier than real private exports; real records need schema and role filtering | Start every future system with lexical/source-backed retrieval metrics before model synthesis |
| Uploaded file-shape gate | Parse uploaded JSONL, Markdown, CSV, and text into one local retrieval surface | Browser import and indexing worked across multiple file shapes | File parsing did not automatically produce meaning; schema-free records still polluted context | Local ingestion is solved enough; meaning comes from source shape, field roles, and provenance |
| Schema-guided real JSON smoke | Infer compact schema from nested exports, suppress metadata, and retrieve role-bearing user-authored records | Concrete source-specific queries could retrieve the expected user-authored evidence | The small local model failed internally on a real schema-guided packet | Schema makes retrieval sane, but not model synthesis reliable |
| Memory-first graph compiler | Turn raw observations into facts, support sets, graph nodes, communities, and durable memories | The architecture exposed useful review surfaces: verified, candidate, and rejected support | It over-promoted tasks, prompt artifacts, programming snippets, assistant text, and generic repeated words; stricter gates then rejected nearly everything | Durable memory must be rare, support-backed, and downstream of source evidence, not the primary output |
| Graph packet retrieval | Retrieve verified memories, support sets, communities, and event snippets, then build a compact packet | It made broad-profile questions fail closed when no verified durable memory existed | Community labels and graph neighborhoods were only useful when upstream nodes were meaningful | Graphs amplify whatever they ingest; only source-backed typed nodes are worth traversing |
| PageIndex-style source tree | Organize local data into source trees, briefs, knowledge pages, and cited leaves | Hierarchical navigation is the right shape for large private corpora | A literal PageIndex port is wrong because strong remote models do most of PageIndex's indexing and repair work | Port the pattern, not the implementation: deterministic source trees first, small model only after narrowing |
| Hybrid retrieval research | Combine BM25/FTS, field-aware exact match, optional embeddings, RRF fusion, reranking, segment expansion, and citations | The logic matched the observed failures better than vector-only RAG | It adds complexity and needs evals to avoid accidental overfitting | The winning retrieval unit is a cited evidence segment, not a naked chunk or vector hit |
| Kuzu schema evidence engine | Compile source mappings into typed Kuzu tables, evidence chunks, FTS/vector indexes, and graph relationships | Best overall direction. Kuzu gave local graph queries, cited rows, and meaningful relationship retrieval | Small models still struggled with planning, unsupported operators, broad questions, and summary coverage | Kuzu is useful when the graph already encodes the relationship the user asks about |
| Kuzu relationship contracts | Replace freeform planning with authored relationship query contracts and source/entity gates | Clean relationship cases passed: saved+rated Netflix titles, search+watch, message+connection, reminder overlap, adversarial grounding | Contracts failed when source intent was ambiguous or the required operator was missing | Relationship contracts are safer than freeform Cypher, but they need refusal rules and coverage gates |
| Mobile model candidate pass | Test whether newer 0.8B-3B WebLLM candidates fix quality | Qwen3.5 0.8B loaded and completed the rich prompt matrix | It did not beat Llama 1B; other candidates timed out or errored; same architecture failures remained | Model shopping is not the fix. Improve the evidence layer before revisiting models |
| On-device/browser support research | Compare platform LLM APIs, WebGPU runtimes, and browser-local abstractions | WebGPU runtimes are the portable browser path; LocalMode and LlamaIndex.TS look promising above raw WebLLM | Apple Intelligence, Android AICore, and Windows local AI are native-app stacks, not portable browser APIs | Build for WebGPU/browser runtimes first; treat native system LLMs as optional wrappers later |

## Session-Derived Learnings

I inspected recent Codex session logs and the memory index for the last week of work in this research workspace. The extra signal is consistent with the project files:

- The biggest improvement came from moving away from memory extraction and toward schema-first evidence retrieval.
- Language-specific stop-word and keyword hacks were explicitly rejected because they break non-English documents.
- The better generic ranking pattern was Unicode token/ngram generation, corpus-relative term weighting, and exact selective-span coverage.
- Strict filters reduce cross-source contamination, but they can drop useful neighboring context; the next retrieval layer needs source-local expansion after a precise hit.
- Browser-local semantic retrieval helped only when fused with lexical and structure-aware signals; embeddings alone did not recover meaning.
- Query-centered snippets improved evidence quality because long source records often hid the relevant span.
- Small-model answer quality improved only when bad answers were rejected and deterministic cited evidence remained the primary UI.
- The deployed Kuzu path proved import, schema compilation, typed tables, and domain graph generation, but fresh-origin WebLLM loading was still unreliable in automation.
- The Kuzu direction became stronger only after fake embeddings, SmolLM paths, and English-only ranking logic were removed.

## What Worked

### Browser-local platform basics

The platform layer is good enough to keep:

- local file, folder, and zip import;
- local persistence for source records, derived cards, traces, and compiled artifacts;
- static hosting with no private data upload;
- local model download/cache separate from private corpus storage.

This part should not be re-proven in the next iteration.

### Lexical retrieval as the baseline

The lexical baseline was stronger than expected. On the controlled 52 MiB corpus it produced:

- 25,741 chunks;
- 103,197 unique tokens;
- 1,943,672 postings;
- 100% recall@10;
- average distractor pollution in top 10 of 0.00;
- approximate index size of 28.1 MB;
- approximate resident memory of 132.1 MB;
- about 1 second of browser indexing time.

The important interpretation is not that lexical search solves semantics. It is that browser-local retrieval can be fast, cheap, and inspectable enough to serve as the first gate.

### Schema and source-shape gates

Real private exports are not generic prose. They contain:

- user-authored text;
- assistant/system/tool text;
- metadata dumps;
- device/session/account telemetry;
- private address and payment fields;
- table rows where field names carry meaning;
- repeated task prompts that look like interests but are not durable traits.

The useful logic was structural:

- infer source shape;
- detect field roles;
- preserve source IDs and source spans;
- separate user-authored text from assistant/tool/system context;
- suppress metadata and telemetry;
- route source questions differently from profile questions;
- fail broad profile questions closed unless verified durable support exists.

### Kuzu as the best substrate

Kuzu helped because it turned raw records into typed local relationships. That is the closest any trial came to making a small model reason over large private data.

The strongest Kuzu loop was:

```text
known source shape
-> typed local graph
-> authored relationship contract
-> local graph query
-> cited rows
-> optional small-model summary
-> deterministic fallback if summary is weak
```

That worked when the graph already encoded the relationship:

- saved Netflix titles joined to positive ratings;
- search events joined to watched titles;
- LinkedIn messages joined to connections;
- Reddit and LinkedIn records joined through a shared reminder topic;
- adversarial prompts rejected because no local rows supported them.

### Deterministic fallback

The best UX pattern was rows first, model second.

The model could summarize when the evidence packet was small and direct. But the system had to reject output when it:

- missed returned rows;
- failed to cite evidence;
- invented unsupported URLs or facts;
- repeated itself;
- echoed prompt instructions;
- drifted beyond source rows.

The fallback answer from cited rows was often more trustworthy than the generated prose.

## What Failed

### Small LLM as planner

Small models produced malformed JSON, repeated questions, bad table choices, and weak plans. Even when they generated valid output, they selected the wrong source or relationship when multiple domains shared words like "search", "watch", or "product".

Conclusion: the model should not own query planning. Deterministic routing and contracts should narrow the task first.

### Small LLM as memory writer

Memory-first approaches failed because they tried to turn raw corpus observations into durable personal knowledge too early.

Bad durable-memory candidates included:

- one-off coding prompts;
- assistant-derived context;
- programming fragments;
- source diagnostics;
- UI/data terms;
- generic repeated nouns;
- task-specific sentences rephrased as stable user traits.

After stricter filters, real exports often produced no useful durable memories. That is better than hallucinating, but it means durable memory cannot be the first product milestone.

### Graph communities without typed evidence

Generic community graphs created labels from recurring tokens and schema artifacts. That made graph retrieval look structured while still being semantically weak.

Conclusion: graph traversal is only valuable after source-backed typed facts exist. It should not be built from raw term recurrence.

### Embeddings alone

Local embeddings helped when fused with lexical and structural signals. Alone, they were too easy to pollute:

- semantically nearby but wrong source family;
- right source but wrong field;
- broad activity rows outranking precise evidence;
- multilingual ambiguity where the correct hit and unrelated hit were both plausible.

The safe pattern is hybrid retrieval with field-aware reranking and citation checks.

### Broad synthesis

Questions like "What are my strongest interests?" or "Summarize activity across all sources" failed because they require compiled source summaries, topic rollups, activity rollups, and cross-source support. A row lookup path cannot answer them well.

The right behavior before those artifacts exist is to say there is not enough verified evidence.

## Why Kuzu Was Most Promising But Still Failed

Kuzu was promising because it made the model choose among meaningful local relationships instead of raw chunks. But the current graph was not rich enough.

| Failure | Why it happened | What the next system should do |
| --- | --- | --- |
| Shopping prompts selected media contracts | The wording "search then action" matched multiple domains | Gate contracts by source intent and required entity coverage |
| "Rated but not saved" returned saved+rated rows | The graph had no anti-join/negation contract | Detect unsupported negation and refuse or compile an explicit anti-join |
| "Returned/refunded" returned purchase rows | Purchase status semantics were absent | Model status fields or refuse status questions without evidence |
| Samsung SSD queries paired related USB-C products | Product matching used broad term overlap | Create product-intent nodes or stricter search-to-purchase relationships |
| Broad interests and recent activity failed | No topic/activity rollups existed | Compile source summaries and topic/activity nodes before broad synthesis |
| Correct rows got weak summaries | Small LLM coverage and citation discipline were weak | Keep row rendering primary and reject incomplete summaries |

Kuzu is the right substrate only when the graph contains the semantics the user needs. Without that, the small model falls back to guessing.

## Next Direction

### Build an evidence engine, not a chatbot

The next system should be organized around this product contract:

```text
local private data
-> source shape and field-role understanding
-> source-backed evidence cards
-> typed graph relationships where known
-> source-tree summaries where unknown
-> lexical plus optional semantic candidate retrieval
-> rank fusion and field-aware reranking
-> cited evidence segment
-> small model as bounded formatter/summarizer
-> deterministic verification and fallback
```

The small model should only see compact evidence. It should not scan raw corpora, create durable memories directly, or decide unsupported operators.

### Use LocalMode or LlamaIndex.TS for scaffolding

LocalMode and LlamaIndex.TS are promising, but only as scaffolding:

| Layer | Likely direction |
| --- | --- |
| Browser-local provider and model state | LocalMode |
| RAG abstractions, retrievers, query engines | LlamaIndex.TS |
| Typed relationship substrate | Kuzu |
| Local embeddings/classifiers/rerankers | Transformers.js or equivalent browser runtime |
| Correctness policy | Custom evidence engine |

The correctness policy should stay explicit:

- source IDs;
- citations;
- source-shape gates;
- field-role scoring;
- relationship contracts;
- unsupported-operator refusal;
- deterministic fallback;
- eval traces.

### First useful proof

Do not rebuild all prototypes. Prove one narrow vertical slice:

1. Import mixed local data.
2. Identify source shapes and field roles.
3. Build source-backed evidence cards.
4. Build one typed relationship graph for a rich source family.
5. Add one relationship contract with explicit refusal rules.
6. Retrieve cited rows.
7. Render rows as the primary answer.
8. Let the small model summarize only from those rows.
9. Reject the summary if it misses evidence, invents facts, or ignores citations.

Good first question family:

```text
Which products did I search for and then buy?
Did I search for Samsung SSD before buying one?
What did I buy from Apple?
What products did I return?
```

This family is small enough to test, but it exercises the hard parts: positive joins, entity constraints, no-row answers, unsupported status semantics, and fuzzy source matching.

### Evaluation gates

Every result should record:

- the route chosen;
- whether a contract was selected or refused;
- selected evidence rows or segments;
- forbidden-hit count;
- final answer;
- citation coverage;
- whether deterministic fallback was used.

Pass criteria should prefer honest refusal over unsupported synthesis.

## Final Verdict

Keep the lesson, not the prototypes.

The best next system is not vector RAG in a browser. It is a local evidence engine:

```text
schema-aware storage
typed graph relationships
source trees
hybrid retrieval
strict reranking
cited rows
small LLM as optional summarizer
deterministic fallback
```

Kuzu remains the most promising substrate from these trials. LocalMode and LlamaIndex.TS are promising ways to reduce boilerplate in the next implementation. The tiny browser LLM should be treated as a helper behind hard boundaries, never as the source of truth.
