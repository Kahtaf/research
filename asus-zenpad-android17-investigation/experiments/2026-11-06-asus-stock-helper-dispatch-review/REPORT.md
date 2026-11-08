# Independent review of checked stock-helper dispatch

**Verdict: the three prior concrete findings are fixed, but one additional P2 exception-boundary defect remains. There is also a P3 stream-forwarding omission. Fix the P2 before treating this revision as technically ready for the parent's fresh preflight and one stock-only test.** This is offline review, not implementation, execution approval, or physical GO.

## R1 — P2: helper text-decoding errors escape the uncertainty boundary

Locations in `../2026-11-06-asus-stock-helper-dispatch-fix/`: `source/service/root_dispatch.py:25`, `source/service/transport.py:19–26`, and `source/service/controller.py:235–251`.

Every nested request now uses `HostIO.command(..., text=True)`. Python's subprocess text decoding can raise `UnicodeDecodeError` after dispatch, including when decoding stderr. HostIO catches timeout and OSError, but not UnicodeError. The exception bypasses the uncertain-result journal and the adapter's `O.Unavailable` conversion. UnicodeDecodeError subclasses ValueError, so the controller instead treats it as a guard/operation failure.

This matters specifically when moving the helper in process. Previously, an unhandled decoder exception inside the helper caused the helper CLI to exit unsuccessfully. The frozen parent's missing/disagreeing root-status check classified that result as uncertain. The fresh module now exposes the Python exception directly to the controller. The helper's byte-identical source alone does not preserve that process exception boundary.

Two new bounded reproductions pass their **defect-confirming** assertions:

- `test_repro_decode_error_after_install_triggers_inverse`: install succeeds in synthetic storage. The actual Transport/root-dispatch/helper chain runs for the entry guard. On nested request 12, the mocked OS boundary performs the real Python operation `b'\xff'.decode('utf-8')`, modeling subprocess decoding failure. The controller subsequently writes `['candidate', 'stock']` and reports `preentry_refused_stock_inverse_verified`, with zero entry requests. There is an intent but no `0012-result.json`. Thus uncertain root-request completion permits an automatic inverse. No hardware effect was simulated as proven completion of that failed root request.
- `test_repro_decode_error_escapes_preentry_inverse`: observer startup fails after a verified synthetic install; the inverse's initial safety snapshot invokes the real helper bridge. A query decoding failure escapes `run_trial` entirely. The durable state records the verified installation and restore intent but has no `partition_may_be_modified`; there is no nested result receipt. Production main's outer ValueError handler would write `refused_or_stopped` without adding that field. Main was not invoked for this reproduction.

These are fault injections, not evidence of non-UTF-8 replies on the tablet. They establish a reachable failure-policy difference at the new Python boundary. Authorization expiry itself is still propagated correctly.

**Smallest parent correction:** include `UnicodeError` in HostIO's existing uncertain-command exception handler around `subprocess.run`, retaining the uncertain journal and raising `O.Unavailable` with the original exception as cause. Transport already converts that to the frozen `UncertainTransport`; the controller then stops without inverse, or its pre-entry inverse handler retains the modified-state fact. Keep AuthorizationExpired separate. Do not classify decode errors as completed operation failure, replace invalid bytes to manufacture valid protocol text, or add retries. Reverse these two assertions into safety regressions: no stock inverse in the first case, and terminal modified-state reporting in the second. Re-pin and regenerate an unapproved template after the fix.

The literal three old R3 variants, plus VerificationFailed, O.Unavailable and OSError, all now retain the flag. The assertion that *all exceptions* do so is broader than the current implementation: the neighboring inverse handler still excludes ValueError/KeyError/TypeError. The concrete transport-decoding case above is sufficient to demonstrate the gap; it does not require catching arbitrary programming errors as recoverable failures.

## R2 — P3: check_output stderr is omitted from aggregate helper stderr

Location: `source/service/root_dispatch.py:29–34`.

The original `subprocess.check_output(..., text=True, timeout=12)` inherits stderr. The adapter captures it in HostIO but returns only stdout; it never writes query stderr to the helper's local stderr stream. `test_repro_query_stderr_not_forwarded` supplies a successful query with `QUERY_WARNING\n`. The per-request journal retains it, but the returned helper CompletedProcess has empty stderr.

This does not lose the nested evidence or bypass a guard. It does make the claimed stream preservation incomplete. **Smallest correction:** forward `result.stderr` to `helper.sys.stderr` in check_output before testing returncode/returning stdout. Preserve the current no-retry failure mapping. Add an assertion on the aggregate stderr. Precheck/chmod output and push stdout redirection are otherwise handled by the adapter's local streams.

## What is resolved and preserved

The old nested-dispatch R1 is fixed. I independently expired authorization while each of the 13 request intents was being durably saved. Each test stopped before that exact subprocess dispatch, with an `authorization_expired_before_dispatch` result. The old expiry-after-staging-precheck reproduction now makes nine requests, then refuses the push. Integrated controller/frozen-engine fixtures show no internal or explicit inverse on this exception.

An additional expiry injection during request 12, the root request, allows that request to return and records its result before refusing request 13. The original `trap 'setenforce 1' EXIT` remains in the actual script. There is no expiry-triggered kill, new root query, or inverse. A return after expiry is evidence of the dispatched request only; missing later Enforcing/status processing cannot become helper success.

Static inspection of the exact helper finds only `subprocess.check_output` in query and four `subprocess.run` call sites. They expand to endpoint query, six property queries, initial Enforcing query, directory precheck, push, chmod, root request and final Enforcing query. There is no Popen, os.system, subprocess alias, dynamic second import, or other device-process path escaping the adapter. Module top level only defines imports/constants/functions; the CLI main guard is not entered by exec. Transport intercepts exactly `[sys.executable, str(E.HELPER)]`; the frozen engine produces that argv.

The module is constructed from the same source bytes that were hashed. No global subprocess function, sys standard stream, or sys.argv is replaced. The exact original binary identity, private endpoint, serial/properties, directory/symlink/ownership/mode, root UID, helper token, writer token, device geometry and Enforcing guards remain. New probes reject wrong identity, failed precheck/push/chmod, failed final Enforcing, missing/duplicate/disagreeing completion and timeout. A genuine completed operation status 7 with helper status 0 still reaches the frozen root-status parser as 7; it is not confused with helper failure. The original helper, writer engine and root binary hashes match.

The old padded-entry R2 is fixed. Classification uses exact raw LF/CRLF bytes and exit status/empty stderr, independently of display `.strip()`. Sixteen fresh integrated vectors include both known terminal newline forms, clean completion, whitespace/NBSP padding, non-UTF-8 prefix/suffix, missing newline, duplicate text, closed, killed, noisy and unexpected responses. Every UNKNOWN result still observes the synthetic new stock boot but makes zero TCP calls and no inverse. Entry results and their HostIO receipts preserve the exact stdout/stderr hex. Text-mode nested commands currently have null hex fields; this review does not claim they retain original bytes.

The frozen p10 writer and old shell metadata predicates are unchanged. All copied 53 synthetic host-shell vectors pass. Host `/bin/sh` results do not establish Android shell/tool compatibility or actual block-node identity.

## Verification and provenance

- 65 copied baseline tests: pass.
- 12 copied regression tests: pass.
- 3 copied nested-dispatch tests: pass.
- 5 copied shell groups / 53 vectors: pass.
- 9 new adversarial methods: pass their assertions, including the explicitly labeled defect reproductions. Coverage includes 13 intent-expiry boundaries, two integrated nested-expiry cases, ten helper success/failure cases, 16 integrated entry byte shapes, six inverse exception classes, the two decoding reproductions, completed status 7 and query-stderr forwarding.
- All 37 original parent files are unchanged; all ten supplied source/test pins match. The existing final unapproved template matches the current 32-hash contract and every live flag remains false.

See `evidence/adversarial.json`, `evidence/adversarial.txt`, the four suite receipts, and `evidence/provenance.json`. `tests/service/` contains byte-identical parent test copies. Scripts import production modules directly from the reviewed source directory, not copies of production code. The existing audit hook forbids actual external/device process and network execution in the unit/adversarial suites. Only the separate synthetic POSIX-shell suite launches host shell processes. Test temporary directories, fixture journals and outputs are confined to this spike. Synthetic review booleans in the unchanged baseline fixtures are not live review approvals and are removed at teardown.

No device, network, USB/ADB/fastboot, root/writer/reboot, cloud, build, private backup, production edit or live controller operation occurred. Firmware replay was omitted because it is unchanged scope. No large firmware/storage image rehash was repeated. Source/helper/root-binary and contract evidence hashes were checked; no fixed-input image validation was rerun.

## Parent continuation and physical/runtime limits

Resolve R1 and the small R2 stream omission, rerun the bounded regressions, refresh exact pins and the unapproved plan/template, and review the changed lines. No live operation is necessary for those corrections. This report does not approve this revision for execution.

After those corrections qualify, the next technical step can be the parent's fresh preflight and one authorized stock-only test, conditional on its current checks: exact stock/USB/boot identities, power and health, Enforcing, stopped autorepair, para/cache/firmware/RC/p10 validation and exclusive writer ownership. A previous physical success of the newly repaired route is not required before its first authorized test; that would be circular. Diagnostic validity, actual new stock return, full p10 restoration, cleanup and metadata revalidation must remain separate observations.

Scope is only diagnostic `7d74dfcaf4b2793453906799d721bfd95a401c564f6698b1c646e18bee918ea5`, padded p10 `6c6a3f534646ed30257c21c7d91be65ea1b8844ef6aa2d0bd3c11545f62db925`, stock wrapped kernel `b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`, and original p10 inverse `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`. No new-kernel/full-OS capability is assessed or authorized here.

The per-request timeouts remain 12 seconds for queries/precheck/chmod, 20 for push and 75 for the root ADB request, whose device command still contains `timeout 60`. The previous outer 95-second subprocess timeout no longer bounds in-process helper orchestration. The 900-second admission margin is not a helper or trial runtime bound; multiple helper calls, local hashing/fsync, review checks, observation and inverse work have no demonstrated combined bound of 900 seconds. The 420-second observation window and diagnostic 120-second deadline do not prove hardware reset or return. No new checked request may begin at/after expiry; an already dispatched root request must retain its trap and must not be killed because authorization expires. Consequently restoration cannot be promised before authorization closes.

User authorization for the owned-tablet stock recovery route while away ends at **2026-11-06 23:03 UTC**, or the parent's earlier review expiry. Nearby availability around 20:43 UTC is not assumed to be actual presence. This is no physical GO. Prior stock-kernel return evidence and static/host fixtures cannot establish the new service's physical delivery, PMIC clearing, timer/reset causation, early bootloader-stall recovery or current readiness. The parent alone owns those live decisions and observations.
