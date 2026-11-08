# Terminal UNKNOWN record framing

Question: can a recoverable torn journal append hide a later successfully persisted terminal UNKNOWN record?

Status: parent one-line correction in an independent source copy; original lifecycle implementation and review remain unchanged. Actual direct API/CLI fake-peer regressions are reproduced before editing. No real device, ADB, root, network, image or contract is used.

Outputs: source/source_client.py, source diff/pins and before/after focused evidence.

Continuation: every UNKNOWN publication starts with a record separator newline, included in the existing journal byte cap. Empty separator lines may be ignored; torn earlier rows remain diagnostic evidence and prohibit successful-outcome acceptance. A completed terminal UNKNOWN line is independently parseable. A sink that never recovers still yields in-memory poison and a failed publication result, not a durable-record claim. Existing no-follow/inode/ownership/cap checks and no further protocol commands remain. Fresh independent review is required before adoption; hardware budgets remain unqualified and PLAN_ONLY stays default.
