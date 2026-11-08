# Minimal readonly RAMUSB transition handoff

PLAN_ONLY. No device contact or deployment authorization. Exact code receipt:
`2d7aee39cdddb5867b0f755c926786d4adc50030c23d5d45a7f2f34e811fdead`.
Parent owns technical review, any affirmative contracts, live invocation, manual
entry, host observation and healthy stock return. No affirmative live gate was
created here. Test-only affirmative fixture values are labeled OFFLINE FIXTURE.

`source/engine.py` and `source/root_dispatch.py` are byte-identical to the reviewed
monotonic-fix spike. `evidence/diff-adapter.py.patch` is the complete adapter delta.
Profile metadata now describes a minimal stock-kernel/PID1/tmpfs/readonly-RAMUSB
discriminator; old RSC capabilities and helper pin are absent. Source guards keep
all old provenance pins and add the exact probe manifest, handoff, its declared
sources and the original adapter/test baseline. No original source/artifact changed.

Exact sole image: `2026-11-06-asus-minimal-ram-usb-probe/artifacts/candidate.img`,
7,759,872 bytes, SHA256
`535ad86471739967c0e68c058787cf2e5ac6bd844765b75d4bb576200a01d40e`.
Exact full p10 after zero padding: 16,740,352 bytes, SHA256
`7562b6168a3cd3f8a2ac4fe1a896f707eab992b2f9b32a1ffb9b1ea33683f596`.
The exact wrapped stock kernel remains
`b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`.

Only `/dev/block/mmcblk0p10` is a mutation target. Install reads the complete actual
p10 and accepts only original stock
`902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`
or known prior failed rescue
`3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a`.
It durably records `install_preimage_sha256` and `install_preimage_bytes` before
candidate dispatch. `check_install` verifies that exact recorded preimage against
the first actual captured bytes and guarded command/completion provenance, then
the exact new postimage and chronology. A stale receipt cannot substitute for the
current physical read. Original recovery restoration between trials is deferred.
The existing one-shot inverse remains the original stock image, even when the
preimage was prior rescue. Known completed candidate failure may enter that fixed
inverse; uncertain completion/deadline/source/USB invalidation remains terminal.
All existing contract expiry, host-boot-bound monotonic pin freshness, shared lock,
source checks, actual readback and live install completion-token linkage remain.

## Parent API and command interface

From this spike, offline commands (safe without live contract):

```sh
python3 source/adapter.py plan
python3 source/adapter.py verify-local
python3 source/adapter.py template --run-id "$RUN" --phase pin-install
python3 source/adapter.py template --run-id "$RUN" --phase install
python3 tests/run_tests.py
python3 scripts/reviewer_regressions.py
```

`template` emits false/unset review, supervision and time fields. The parent must
separately create/review fresh phase contracts beneath this spike, bound to the
exact profile/code receipt. No contract is supplied in this packet.

For the parent's later reviewed live driver, import the exact local adapter and
invoke the existing API only when all existing authorization requirements hold:

```python
# RUN: new canonical UUID owned by parent.
# PIN_CONTRACT and INSTALL_CONTRACT: separate parent-owned reviewed JSON Paths
# beneath this spike. No example affirmative values are provided here.
result = a.main(['pin-install', '--execute', '--run-id', RUN,
                 '--contract', str(PIN_CONTRACT),
                 '--supervised', '--physical-fallback-present'])
# Require successful live return, then use the same RUN immediately.
result = a.main(['install', '--execute', '--run-id', RUN,
                 '--contract', str(INSTALL_CONTRACT),
                 '--supervised', '--physical-fallback-present'])
```

Each returns a process-style exit code and prints JSON. Retain the actual live
stdout from successful install, including `install_completion_token`, through the
parent's protected driver; never reconstruct it from the visible journal.
A separate later restore, only if parent elects it, uses `pin-restore` then
`restore` with their separate reviewed contracts and that same live token in each
contract's `install_completion_token`. They still require fresh current stock USB
pin and healthy original Android, even though historical install linkage is valid.
No successful install authorizes manual entry or attests a probe report/return.

The parent must prepare read-only host observation and keep the supervised manual
entry observation window bounded to 60 seconds, with nearby physical Power/Normal
Boot fallback. The candidate's PID1 timer cannot extend that external window.
Full acceptance schema and limits remain in the probe's HANDOFF and
`evidence/host-acceptance.json`; the deployment adapter makes no report or Android17
claim. No automatic cleanup restoration between trials is added.

## Verification evidence

All 56 inherited/focused methods pass in
`evidence/offline-1794019658919323000/receipt.json`; all 9 inherited reviewer
regressions pass in `evidence/targeted-1794019660099452000/receipt.json`. Both
runners installed process/fork/network-denying audit hooks before imports; no
blocked events or actual subprocess/network operations occurred inside the runs.
Focused cases cover direct prior-rescue transition and check_install linkage,
actual original-preimage recording, rejected preimage-record tampering, unexpected
complete preimage rejection before writes, prior-rescue known failure to the fixed
stock inverse, prior-rescue uncertain completion with no later commands, and exact
minimal identity/dependency preservation. Existing cases cover image/header/kernel/
padding mutation, full readback mismatch, stale USB and deadlines, source drift,
shared lock, lost completion publication and inverse consumption.

The initial development run overlapped a profile metadata edit and correctly
failed closed on source drift. Its original evidence is retained; the final
frozen-source run above passed. No physical timing, USB report or durability
qualification is inferred from fixtures. `evidence/plan-only.json` is the audited
offline API result; `evidence/source-receipt.json` and `HANDOFF.json` bind the
reviewed code and final test receipts.
