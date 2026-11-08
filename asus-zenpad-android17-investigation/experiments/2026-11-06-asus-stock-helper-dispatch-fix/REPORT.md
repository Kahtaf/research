# Checked nested root-helper dispatch

## Current r2 correction

Independent review in `../2026-11-06-asus-stock-helper-dispatch-review/REPORT.md`
confirmed the original three fixes. Parent then made its two smallest requested
corrections: HostIO classifies UnicodeError during subprocess text decoding as
uncertain transport, with an uncertain journal, and check_output forwards query
stderr to the helper's aggregate stream. AuthorizationExpired stays separate.
No new retry or inverse path was added. The reviewed previous source and its
pins are preserved in `evidence/reviewed-v1/`.

At 20:44:51 UTC, all 89 unit methods and five shell groups / 53 vectors pass.
The review's two decoding defect reproductions now assert terminal uncertainty,
no inverse after the uncertain entry guard, and a truthful modified-partition
flag during a failed pre-entry inverse. Query warnings are present in both
aggregate and nested evidence. Seven unchanged adversarial review methods also
pass, including 13 actual intent-expiry boundaries, in-flight completion and
16 entry-response shapes. See `evidence/verification-r2.json`,
`evidence/source-pins-r2.json`, and `evidence/adversarial-r2.json`.

The parent has inspected these narrow changed lines and the reversed concrete
reproductions. The next step is a freshly authorized preflight on stock Android;
no previous physical result is claimed for this revision. The description below
records the original reviewed implementation and remains applicable apart from
the explicitly corrected exception/stream behavior.

This new parent-owned revision addresses the three concrete findings from
`../2026-11-06-asus-stock-roundtrip-fixes-rereview/REPORT.md`. Earlier source,
tests, review and runtime evidence remain unchanged. No device operation or
live approval occurred.

## Changes

The new `root_dispatch.py` loads and executes the exact hash-checked original
root helper in a fresh module. Its original directory, identity, root-binary,
privilege, status-token and Enforcing-restoration logic stays byte-identical.
Only that module's subprocess and standard-stream references are replaced with
local adapters. Process-global modules, streams and arguments are not modified.

Each of the helper's 13 ADB requests now goes through the existing HostIO
dispatcher, which records intent and rechecks authorization immediately before
the actual subprocess call. This includes root-binary push/chmod and the root
request containing the fixed writer. Expiry propagates as AuthorizationExpired,
without becoming an inverse trigger. A root request already dispatched is not
interrupted by review expiry; its original shell EXIT trap remains in place.
If authorization expires before a following completion query, that query is
refused and no helper-level success is inferred from missing evidence.

The original per-ADB-request timeouts remain. The old helper process's outer
95-second subprocess timeout no longer bounds the in-process orchestration;
this is explicitly not a whole-helper or whole-trial runtime guarantee. No new
request may start after authorization expires. The 900-second trial admission
margin remains a margin rather than a proven trial duration bound.

Entry failure classification now compares raw bytes against only the audited
LF reply and its terminal CRLF transport form. The saved firmware string is
`reboot failed: %d\n`. Leading/trailing whitespace, absent newline, nonbreaking
space, duplicate lines and replacement characters are not normalized into a
known failure. Raw bytes remain in command journals; decoded text is display.

All non-expiry pre-entry inverse exception outcomes now retain the conservative
`partition_may_be_modified` fact, as the expiry branch already did. No retry,
additional inverse or broader writer target was introduced.

## Verification

Final replay at 2026-11-06T20:37:01Z:

- All 65 baseline tests passed. The old capture fixture was extended to answer
  the now-visible nested identity/staging requests and supply both genuine
  status-token shapes; no production guard was bypassed for it.
- All 12 regression tests passed, including padded entry responses and all
  three non-expiry pre-entry inverse exception variants.
- Three new nested-dispatch tests passed. They execute the unchanged actual
  helper with real HostIO intent/check logic and mocked OS effects. Expiry after
  each of 13 request boundaries prevents the next request. Actual Transport.write
  integration preserves the exact p10 guard/write and Enforcing EXIT trap.
- Five real host-shell groups / 53 synthetic parser vectors passed.
- A fresh PLAN_ONLY invocation validated fixed inputs and generated an
  unapproved contract. Every live review flag remains false.

Receipts and exact source/test pins are under `evidence/`. The original helper
and frozen writer stay unchanged and hash-checked. Unit suites deny actual
external/device execution; the shell tests run only synthetic host files. These
tests do not establish Android shell compatibility, root/runtime completion,
recovery entry, reset causation, physical return or restoration on hardware.

## Next action

Fresh independent review of this changed dispatch boundary and the concrete
old reproductions is required before the parent uses this unattended controller.
Review the isolated adapter, exception taxonomy, actual nested command journals,
entry byte shapes and truthful partial outcomes. Generate a new hash-bound
approval only after actual parent review and fresh preflight. Do not reuse an
earlier review template, source pins or results as execution approval.

The candidate remains exactly the repaired stock-kernel diagnostic, with only
recovery p10 and the exact original inverse in scope. No Linux4.9 or full-OS
capability is added. The user's forthcoming physical availability is not assumed;
supervised transport readiness is assessed separately against its own reviewed
source and current device state.
