# Checked dispatch inside the unchanged stock root helper

Question: can every nested ADB command participate in the actual authorization
check while preserving the pinned original helper's guards and status handling?

Status: the independent review confirmed the prior fixes and found a text-decoding
uncertainty gap plus a query-stderr omission. Parent corrected those two lines;
89 unit methods and five shell groups pass. No trial has run from this revision.
Source is copied from the reviewed parent-fixes revision; earlier sources and
evidence remain unchanged. The new bridge executes the exact hash-checked helper
with isolated I/O adapters, without replacing process-global modules or streams.

Continue with baseline/adversarial tests, new exact pins and unapproved plan,
then fresh review. This remains stock-only; no Linux4.9/fullOS writer is enabled.

See [REPORT.md](REPORT.md), [current verification](evidence/verification-r2.json),
[current source pins](evidence/source-pins-r2.json), and [original diff](evidence/changes.diff).
The independently reviewed previous source is preserved under
`evidence/reviewed-v1/`; its original receipts remain historical.
