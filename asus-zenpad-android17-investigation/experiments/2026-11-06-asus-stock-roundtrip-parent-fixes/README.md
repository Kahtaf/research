# Parent fixes for exact stock-only recovery control

Question: do shell guards, entry classification and authorization boundaries
meet the concrete independent review findings before any live test?

Status: parent fixes complete; offline suites and a new PLAN_ONLY run pass.
Fresh independent review remains pending; every live approval remains false. This revision
copies only the previous source/tests and preserves all previous evidence.
The fixed stock diagnostic, p10 inverse, endpoint, original writer engine,
root helper and user-away window remain unchanged. No device operations.

Review input: `../2026-11-06-asus-stock-roundtrip-independent-review/HANDOFF.md`.
The work replaces unavailable awk parsing with shell builtins, classifies failed
entry processes as unknown, and places review checks at new command dispatches,
including the inherited inverse. It does not interrupt an in-flight command on
expiry or infer success from USB loss. New regression evidence belongs here.

Continue with the new offline suite, generate a new unapproved plan, and obtain
a fresh independent review of these changed sources before parent execution.
Never reuse the old review template/source pins or turn this into a Linux4.9
trial. Parent alone owns any live preflight and bounded stock-only experiment.

See [REPORT.md](REPORT.md), [verification receipt](evidence/verification.json),
[source pins](evidence/verified-source-pins.json), and
[review diff](evidence/parent-fixes.diff). The recorded plan points to the fresh,
unapproved review template. No device or cloud operations occurred.
