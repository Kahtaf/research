# Fresh independent re-review of the parent stock-roundtrip fixes

**Verdict: one P1 remains at the nested root-helper dispatch boundary. Two P2 issues also remain in exact entry-response classification and failure-state reporting. This revision does not yet satisfy the requested per-device-command expiry contract.** The old unavailable-awk defect and the specific rc=1/closed and rc=-9 entry defects are fixed. The three original expiry reproductions now stop correctly, but the outer helper invocation is not the last device dispatch boundary.

This is an offline technical review, not implementation, approval, or a live GO. The parent owns all live operations and any subsequent decision. All existing parent files and live review flags are unchanged. Findings apply to the exact pins below, not a later revision.

## R1 — P1: a running helper can start the p10-writing ADB request after expiry

Locations: parent `source/service/transport.py:97–102`, frozen `2026-11-06-asus-recovery-control-wifi/source/recovery_control.py:305–315`, and pinned `2026-11-06-asus-wifi-device-access/scripts/root_shell_wifi.py:52–61`.

The adapter correctly authorizes after durable command intent and immediately before launching the Python root helper. The helper then performs its own sequence of ADB subprocesses without the callback or a deadline. Its identity checks and staging precheck precede separate `adb push`, `adb shell chmod`, and `adb shell timeout … mtk-su …` requests. The last request carries the generated p10 write. An expiry during the helper's precheck therefore does not prevent these new device commands.

**Reproduction:** `scripts/adversarial.py`, `test_nested_root_helper_starts_commands_after_expiry`. This imports the exact production transport and compiles the hash-checked, unchanged helper source; every subprocess and query is mocked under the existing audit denial hook. The fixture changes authorization to expired when the helper's initial staging precheck returns. Both outer authorization callbacks saw a valid window. After expiry the helper starts:

1. The root-binary push.
2. Its chmod request.
3. The root shell request containing `dd … of=/dev/block/mmcblk0p10`.
4. A getenforce completion query.

The simulated operation returns a successful `write_candidate` root status. The receipt records the four later requests and the two earlier authorization checks. No real process, helper, ADB request, or write ran. The captured script uses the production partition size and sector count, with fixture run/boot identities.

This finding concerns **a new ADB request**, not cancellation of an already dispatched block write or individual shell statements inside that in-flight request. Launching a host orchestration process before expiry does not prove that its later device requests were dispatched before expiry. Calling the whole helper one authorized in-flight operation would weaken the requested per-device-command rule and must not be described as enforcing it.

**Smallest correction:** make the helper's actual dispatches participate in the checked dispatcher, or use a narrowly scoped, independently pinned wrapper preserving the existing helper's identity, directory, privilege and Enforcing guards. Check authorization after recording intent and before each new ADB dispatch, especially the root shell request. Preserve expiry as a terminal, non-inverse-triggering result across that boundary. Let a root request already dispatched finish and retain its completion/trap evidence; do not kill it on expiry. The frozen writer engine need not change. Re-run this exact reproduction and repin any new helper/wrapper dependency.

## R2 — P2: unexpected entry-output shapes are normalized into the known-failure class

Location: parent `source/service/transport.py:63–66`; consequence at `controller.py:214–220`.

The clean-success check is strict: rc=0, zero stdout bytes, zero stderr bytes. Closed, killed, noisy-success and timeout cases now reach UNKNOWN and stop before TCP/inverse even after a verified new stock boot. However, the known-failure path still applies Unicode `.strip()` before comparing the response. It accepts arbitrary leading whitespace, extra blank lines, vertical tabs and even nonbreaking-space padding as the exact audited service failure.

**Reproduction:** `test_entry_shape_matrix_and_integrated_whitespace_escape` supplies rc=1, empty stderr, and stdout `b' \t\nreboot failed: -1\n\n\x0b'` to the actual adapter. It returns `explicit_service_failure`. The actual controller and frozen writer, with synthetic storage/observer effects, subsequently make one TCP call, write `['candidate', 'stock']`, and report `diagnostic_pass_stock_return_and_p10_restore_verified`. A separate nonbreaking-space vector is also accepted. The 11-vector matrix records exact input bytes as hex. Duplicate failure lines, negative status and failure text accompanied by stderr correctly remain UNKNOWN.

**Smallest correction:** classify raw bytes against a finite set of documented service reply shapes, allowing only justified terminal LF/CRLF differences. Keep the rc and empty-stderr requirements; do not strip arbitrary whitespace or decode replacement characters for the classification decision. Preserve raw response evidence. Add the padded responses above to the integrated UNKNOWN/no-TCP/no-inverse tests.

This is a narrow exact-shape defect, not a claim that those responses occurred physically. The original closed/-9 finding is resolved; its broader unexpected-shape requirement is not completely met.

## R3 — P2: non-expiry pre-entry inverse exceptions omit the modified-state flag

Location: parent `source/service/controller.py:249–250`.

The dedicated pre-entry `AuthorizationExpired` handler now preserves `partition_may_be_modified=install_started`. The adjacent handler for refusal, completed operation failure, uncertainty and OSError does not. A candidate can be fully installed, observer startup can fail before entry, and the inverse's initial safety snapshot can fail; the terminal state then omits the top-level modified-partition fact.

**Reproduction:** `test_nonexpiry_preentry_inverse_exceptions_omit_modified_state` uses observer behavior `not_ready` and injects uncertainty, refusal and completed failure separately at `restore-guard:snapshot`. Each result has `writes=['candidate']`, zero entry requests, `p10_restored=false`, outcome `preentry_refused_inverse_unverified_stop`, and no `partition_may_be_modified` field.

The nested `install_result` still records the successful installation, and the outcome is not a success. Evidence is therefore available to a careful parent inspecting the whole journal. The defect is inconsistent terminal reporting, not a demonstrated false restoration or further unauthorized command.

**Smallest correction:** include the conservative modified-state fact in this handler as in the adjacent expiry handler, retaining any already recorded stock-readback facts. Add the three exception variants; do not respond by adding another inverse or retry.

## Resolution of the three original findings

- **Old finding 1, missing awk: resolved in the reviewed source.** All nine uses are gone. The actual parser passes the original 53 real host-shell vectors with no utilities in PATH except a readlink fixture. An additional 21 synthetic cases exercise the complete metadata fragment, including standalone node-shape predicates, wrong aliases/geometry, dangling command links, recovery/cache symlinks, missing mount fields, duplicate final uevent keys without newlines, and malformed voltage. Stock shell/tool compatibility still needs the parent's fresh preflight; host `/bin/sh` is not Android's shell.
- **Old finding 2, rc=1/closed and rc=-9: resolved for those defects, with residual R2 above.** Actual-adapter/integrated regression cases enforce UNKNOWN observation-only behavior after new stock. The known-failure and clean-success paths still require a new boot before post-entry inverse; same-boot/USB-loss evidence cannot satisfy it.
- **Old finding 3, expiry dispatch gaps: partially resolved, R1 remains.** Expiry at candidate staging, completed candidate-write failure before the inherited inverse, and explicit restore staging now stops before the next guarded operation. Candidate/internal-inverse/explicit-inverse calls route through `GuardedTransport`; top-level staging, root-helper launch, cleanup, entry, tcpip and connect dispatches are checked. The nested helper's own requests remain outside that boundary.

`AuthorizationExpired` is deliberately independent of the frozen engine's Refused, OperationFailed, VerificationFailed and UncertainTransport classes and OSError. It is not caught by the engine's operation/inverse/cleanup handlers. The controller's dedicated expiry branch stops the observer and does not request an inverse. No hidden conversion of that exception into an inverse was found at those reviewed layers. The pre-entry expiry branch preserves the modified-state fact; R3 concerns its neighboring non-expiry branch.

The adapter retains returned stdout/stderr/status if expiry occurs during an already dispatched command. The next guarded command is refused. A verified stock readback survives expiry before later cleanup or metadata revalidation; incomplete work does not become the complete trial-success outcome. A final in-flight operation may complete with valid evidence after expiry if no subsequent command is required. Read-only pin/observer work is separately bounded and does not authorize a mutation.

Exclusive expiry (`now >= until`) and the 900-second admission margin are implemented. **The margin is not a full runtime bound.** Helper orchestration, command timeouts, installation, up to 420 seconds of observation, restoration and failure handling are not proven to fit inside 900 seconds. It does not close R1 or authorize post-expiry dispatch.

## Fresh checks, provenance and limits

Completed in this new spike:

- 65 baseline tests, zero failures/errors.
- 11 parent regression tests, zero failures/errors.
- Five parent shell groups / 53 vectors, all pass.
- Six fresh adversarial test methods: 11 entry shapes, one integrated response-shape reproduction, 25 writer-phase expiry points, seven actual outer intent/dispatch boundaries, the nested helper reproduction, three pre-entry inverse exception variants, and exception-taxonomy checks. All assertions pass; defect reproduction assertions confirm the defects rather than certify the safety condition.
- 21 additional real host-shell metadata/parser vectors, all pass; captured full helper script passes `/bin/sh -n` only.
- Seven fresh saved-ELF Unicorn cases pass using the existing local environment. Socket/property delivery, libc, OS, shutdown and mount effects remain named stubs. The shutdown-timeout fixture remains zero. These are instruction/stub-boundary evidence, not hardware or service-delivery proof.

`tests/service/` contains byte-identical copies of all four parent test files. `scripts/replay.py` imports production controller/transport/fixed/observer directly from the parent-fixes source before loading copied tests. The frozen engine is compiled from its hash-checked original bytes. Copies relocate test temporary files and receipts into this spike; production main was not invoked and no production evidence was overwritten. Fixture review booleans exist only in the original tests' temporary synthetic reviews, which are removed by teardown; no live review was authored or approved. Firmware replay executes the copied firmware test against the original saved public ELFs and writes only this spike's receipt.

`evidence/provenance.json` confirms all 34 original parent files are unchanged, all eight supplied source/test pins match, and the recorded PLAN_ONLY template exactly equals the current contract with every live flag false. `evidence/verified-contract.json` records all 30 contract source/evidence hashes and the template path/hash. This review did not rerun fixed-input image/para validation or inspect private backups; it checked the source/template bindings and existing public receipts. No full SYSTEM/data copies or rehashes were performed.

The generated helper script is a captured artifact for inspection and `-n` syntax checking only; **do not execute it**. Additional shell checks substitute synthetic files and mocked block-node, cat, ls and readlink boundaries. They verify parsing, predicates and fail-closed behavior, not real block identity or Android utility options. The inherited root helper, timeout, stat, ls, dd, sync, tar and staging semantics still depend on exact stock runtime behavior. No new external parser utility is introduced by the parent fix.

Initial review-harness failures are retained as `adversarial-initial.*` and `shell-adversarial-{initial,second}.json`: an overbroad assertion initially rejected permitted read-only pin/observer calls after expiry; shell mocks initially used an invalid function name and then the wrong positional argument. Only the new review harness was corrected. Final receipts distinguish the successful reruns; these initial failures were not production defects.

## Exact pins

Parent source/test SHA256:

```text
source/service/controller.py  e10c94de09279ec8a37b7344e3944124a9210e85e89c55b12b34eb0a7024c11e
source/service/fixed.py       66a59a241418c189a06243b17348a4c2cae433651517ac7c4b90d5ead4e34481
source/service/observer.py    db39847cbf81eaff77636fb5cde46e413d667dc64c24e30e689d292be38c7443
source/service/transport.py   d3c9fdcf5c378866e689b47905a73c95e2b234e119e1c47705519a7deb1be8fc
tests/service/test_faults.py  d9315a04ddd83bfa32a787fb5f2c49c818d6ced38e5899e4d951b77f217c10bd
tests/service/test_firmware.py ce78cc1156a5068f67ed8df1989660550122cdba409851ddd94373c7daacd740
tests/service/test_regressions.py b18169fca6dbd002dcfdb26a7fcdf2a2b73455ebb372172fe8035b0047e7cc34
tests/service/test_shell_guards.py a66ec3ed864617298f5098db84cdc36d439354542c7846b408e757db60594b9c
```

Frozen engine: `2026-11-06-asus-recovery-control-wifi/source/recovery_control.py`, SHA256 `34ed0079e7f9ca3b4edcab5d108fe29d330a653781c4ec5d67b8ca421daac0ab`.

Pinned helper: `2026-11-06-asus-wifi-device-access/scripts/root_shell_wifi.py`, SHA256 `684bbe346488dfd0e7dfce741b7547021f019d3749235e6208eb1c9766395f34`.

Scope remains the 8,654,848-byte diagnostic `7d74dfcaf4b2793453906799d721bfd95a401c564f6698b1c646e18bee918ea5`, padded p10 `6c6a3f534646ed30257c21c7d91be65ea1b8844ef6aa2d0bd3c11545f62db925`, wrapped stock kernel `b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`, and original p10 inverse `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`. No new4.9kernel or full-OS scope is assessed or enabled.

## Smallest parent next action

Fix R1 at the helper's nested dispatch boundary, tighten R2, and add the missing R3 terminal fact; then run these bounded offline reproductions and baseline suites, regenerate exact pins and an unapproved PLAN_ONLY contract, and review the changed boundary. No device operation is needed to resolve these findings. Keep live flags false while doing that work.

After the fixes qualify, the next technical step can be the parent's fresh preflight and, if its own current checks and authorization permit, one bounded test of this exact stock-only candidate and inverse. This report does not independently approve that step. The user's stock-only recovery authorization while away ends at **2026-11-06 23:03 UTC**, or the parent's earlier review expiry; nearby absence itself is not an extra stock-route blocker.

The earlier stock-kernel physical auto-return at roughly two minutes is useful prior evidence. It does not prove the repaired diagnostic plus the new service entry. Firmware stubs cannot establish physical readiness, PMIC clearing, timer/reset causation, or recovery from an early bootloader stall. Parent preflight must freshly establish the exact stock identities/USB topology, power/health, Enforcing, stopped autorepair, para/cache/firmware/RC/p10 checks and exclusive writer ownership. Preserve separate results for diagnostic validity, actual new-stock return, p10 restoration, cleanup and metadata revalidation. Requiring this repaired route to have already passed physically before its first authorized test would be circular; the outstanding blockers here are concrete offline defects.
