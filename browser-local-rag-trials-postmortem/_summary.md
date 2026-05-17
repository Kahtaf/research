Experiments with browser-local RAG demonstrate that private-data reasoning is effective only when structured as an evidence-engine problem rather than an open-ended model task. Success hinges on using a schema-aware substrate like [Kuzu](https://kuzudb.com/) to provide typed graph relationships that narrow the small model's focus to verifiable, cited facts. Future development should prioritize deterministic retrieval gates and source-tree navigation over freeform planning by underpowered local models.

*   Lexical retrieval proved to be a highly efficient baseline, achieving 100% recall on controlled facts with minimal memory overhead.
*   Small local LLMs (0.8B–3B) fail at query planning and memory writing but function well as bounded formatters for compact evidence packets.
*   Hybrid retrieval—combining BM25, schema-aware filtering, and relationship contracts—is necessary to prevent the context pollution common in vector-only RAG.
*   The project recommends moving toward structured scaffolding like [LocalMode](https://github.com/the-cryptic-company/localmode) to manage browser-local model state and orchestration.
