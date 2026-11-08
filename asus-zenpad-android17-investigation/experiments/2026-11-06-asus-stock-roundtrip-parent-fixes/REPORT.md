# Parent fixes for the stock-only software recovery controller

All three findings from the independent review are addressed in a new spike.
The earlier implementation and its evidence remain unchanged. This delivery
does not approve a live test or claim a physical recovery round trip.

## Changes

1. Removed all nine unavailable `awk` calls from the new adapter. Cache mount
   and battery/USB fields use shell builtins with duplicate-key, canonical
   decimal and threshold checks. Metadata block-node checks remain explicit.
   Running the production parser exposed a shell `set -e`/AND-list issue;
   required threshold and node-shape predicates now execute separately.
2. Only an empty-output, empty-stderr, exit-zero entry process is classified
   as completion unconfirmed. The exact audited service-failure reply has its
   own classification. Closed, killed, timed-out and unexpected responses are
   UNKNOWN. A later observed stock boot does not authorize TCP reenable or an
   inverse after UNKNOWN entry.
3. Authorization is checked at every writer interface and immediately before
   actual subprocess dispatch, after durable command intent. This covers the
   inherited internal inverse, explicit inverse, root/staging/cleanup commands,
   entry request and TCP commands. Authorization expiry has an independent
   exception type so the frozen writer does not misinterpret it as a completed
   operation failure and start an inverse. Expiry is exclusive and new trial
   admission requires at least 900 seconds remaining. This is an admission
   margin, not a proven upper bound on whole-trial duration.

In-flight commands retain their completion evidence after expiry. No following
command starts. Verified stock readback remains recorded if later cleanup or
metadata checks cannot run. Expiry during the pre-entry inverse branch also
preserves the fact that recovery may already have been modified.

## Verification

At 2026-11-06T20:23:17Z, the final source passed:

- 65 baseline tests, including the inherited fault and transport-loss cases.
- 11 new regression tests covering the exact review reproductions, command
  intent/dispatch boundaries, TCP boundaries and truthful partial outcomes.
- Five shell test groups with 53 cases running the actual parser through
  `/bin/sh` with `PATH=/nonexistent` and a narrow readlink fixture.
- A new `plan` invocation: `plan_only_validated`, no device contact, all live
  review flags false.

Receipts, exact source pins and the diff are in `evidence/verification.json`,
`evidence/verified-source-pins.json` and `evidence/parent-fixes.diff`.
Per-suite logs preserve actual exit statuses. Earlier failed runs are retained.

The unit suites forbid external process/network execution; adapter processes
are mocked. Shell tests use real host POSIX shell execution with synthetic
files, not the tablet's shell, block nodes, root helper or battery. The unchanged
firmware emulations remain static evidence. No physical readiness follows from
these tests alone.

## Continuation

Request a new independent review of this revision, including shell emission,
exception paths and the frozen inherited writer. Parent must inspect the new
review, decide actual technical readiness and generate a fresh hash-bound
approval before any execution. Never copy old approval values or reuse an old
source contract. Use the new plan location in `evidence/verification.json`.

Only the fixed repaired stock-kernel diagnostic is accepted. This controller
must not become a Linux 4.9 probe or a full-OS writer. The global user-away
window ends at 2026-11-06T23:03:00Z; elapsed time does not establish nearby
physical fallback for any new-kernel test.
