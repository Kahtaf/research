# Notes

## 2026-05-17

Task: consolidate the unstaged browser-local RAG experiments into one documentation-only research artifact that can survive deleting the prototypes.

Success criteria:

1. Capture what worked, what failed, and why.
2. Preserve the important product and architecture logic without preserving disposable implementation files.
3. Emphasize the best next direction: LocalMode or LlamaIndex.TS above a strict local evidence engine.
4. Keep only this folder as the intended artifact.

Initial consolidation:

- Created a report with the main thesis: browser-local private-data reasoning is viable as an evidence-engine problem, not as a tiny-LLM-does-everything problem.
- Captured the main Kuzu result: typed graph relationships were the most promising substrate, but the small LLM still failed on source intent, negation, status semantics, fuzzy matching, broad synthesis, and summary coverage.
- Captured the main retrieval result: lexical and schema-aware retrieval worked better than expected; embeddings helped only when fused with structure and field-aware ranking.
- Captured the main memory result: durable memories must be rare and source-backed; memory-first compilers either over-promoted junk or rejected nearly everything.

Revision after user feedback:

- Removed the previously requested narrative framing that was no longer useful.
- Removed discard instructions.
- Removed unhelpful appendices and low-level layout sections.
- Replaced implementation-oriented detail with extracted logic from the prototypes:
  - lexical baseline;
  - uploaded file-shape gate;
  - schema-guided JSON smoke;
  - memory-first graph compiler;
  - graph packet retrieval;
  - PageIndex-style source tree;
  - hybrid retrieval research;
  - Kuzu evidence engine;
  - Kuzu relationship contracts;
  - mobile model candidate pass;
  - browser/on-device support research.
- Inspected recent memory and Codex session logs from the last week for this research workspace.
- Added a session-derived learnings section covering:
  - rejection of English-only ranking tricks;
  - corpus-relative reranking;
  - source-local expansion after precise hits;
  - query-centered snippets;
  - hybrid retrieval instead of embeddings alone;
  - deterministic fallback;
  - deployed Kuzu import/graph green state vs WebLLM fresh-origin blocker.

Current intended artifact:

- `README.md`
- `notes.md`

No prototype implementation was copied into this folder.
No destructive file removal was performed.
