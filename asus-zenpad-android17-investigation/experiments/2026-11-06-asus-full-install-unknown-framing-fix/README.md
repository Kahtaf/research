# Terminal UNKNOWN journal framing

Question: can a recovered evidence sink publish an independently parseable terminal UNKNOWN record after an earlier write tore a JSON row?

Status: fixed and verified offline. All105 inherited flow cases and2 boundary methods pass; all204 final-run fake children were reaped. The2 original framing failures were reproduced first and preserved. This is an offline host journal correction; no device, network, source-image, build or cloud action is included. Original implementation and independent review remain unchanged.

Outputs: copied public host sources and tiny fake-peer tests, the original two production-path regressions, exact source delta and local QA evidence.

Continuation: retain poisoning before publication, possible-modification state, inode/no-follow/link/cap guards, original failure propagation and zero target requests after uncertainty. Missing runtime profiles and physical timing remain separate gates. This change grants no deployment or flash readiness.

## Framing contract

Terminal UNKNOWN publication starts with a newline before its JSON row. This creates a known boundary even when an earlier write stopped inside a row. The separator is part of the data passed through the bounded journal and consumes its byte capacity. Previously persisted torn bytes are retained for diagnosis.

Readers may skip blank separator lines. A valid final UNKNOWN row reports uncertainty only; it never authorizes a retry or proves a committed partition. A torn earlier row must never be ignored to promote a later SUCCESS into acceptance. Successful acceptance still requires the actual successful command completion and its intact, complete evidence. Failure to write, flush or fsync UNKNOWN returns false; the in-memory poisoned state remains authoritative and no durable-publication claim is made.

The closed-file recovery path uses the same publication function after the original inode/no-follow/link/count/cap checks. No permission, protocol, target, source profile, manifest, approval flag or timing budget changes are part of this correction.

Use `patches/unknown-framing.patch` against the reviewed complete host packet at exact source preimagea620a009…. This folder is a test/proof packet, not a deployed transport bundle; fixed source profiles were not recopied. Its copied ancestor `source/verify_handoff.py` is preserved reference code and is not this packet’s verifier. Run `python3 -B scripts/verify.py` for this unit. New code pins, final results and exact patch pre/post hashes are in evidence.
