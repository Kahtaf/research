# Linux 4.9 minimal readonly RAMUSB transition handoff

PLAN_ONLY. Exact code receipt:
`2462a2ef11137852fbca68e89d22fce6ebd7dc4b48458ff38a88814f162b6ef3`.
No live action, affirmative contract, device contact or hardware-success claim.
The parent must complete the stock-kernel minimal PID1 trial before considering
manual entry of this separate Linux 4.9 candidate. Both profile and PLAN_ONLY
receipt explicitly carry `stockminimalPID1trial_required_before_manual_entry: true`.
This requirement is parent-owned; deployment does not authorize manual entry.

The complete source delta from the stock-kernel minimal transition is
`evidence/diff-adapter.py.patch`. `source/engine.py` and
`source/root_dispatch.py` remain byte-identical. Source guards retain every prior
pin and add the frozen Linux 4.9 delivery packet, manifest, source/input material,
exact compiled kernel and resolved configuration. Original spikes remain intact.

## Exact sole candidate and kernel binding

Candidate path: `2026-11-06-asus-linux49-minimal-ram-probe/artifacts/candidate.img`.
Size: 8,005,632 bytes. SHA256:
`5be0ed4cb9cb24a27853620a1a7870db63f5ba0eed75f587adf5c0850f5278a4`.
Zero-padded full p10: 16,740,352 bytes. SHA256:
`647b5865d4f63188b0a2e0f1c634b1b814ff0e44ecaa31963ea5c203e61d5ac3`.

The fixed wrapped kernel as actually parsed from this candidate is
`3d088a29baf17a1105134630a454995a2efbe70421f076981fe34ac20d3981b2`.
The new profile pins its exact header/layout and full header-page digest. The
former stock-kernel byte-equality condition is replaced by this exact new wrapped
kernel digest, while stock header address/page/legacy geometry checks remain.
The kernel-size field changes to its exact new value, independently pinned by
profile. There is no arbitrary path/hash/header/kernel option.

Local input `2026-11-06-asus-bmc156-full-kernel/artifacts/Image.gz-dtb` is bound to
`e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1`;
`artifacts/resolved.config` in that same spike is bound to
`10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`.
`verify_local` validates the actual fixed manifest and those actual local input
bytes. Preserved source pins bind the existing compiled Image/compressed stream,
DT changes, LK layout and reproduction proofs; this adapter does not recreate or
expand that frozen qualification. The original stock backup checks in the
unchanged engine remain mandatory for the single fixed original-only inverse.

## Exact actual preimages and retained safeguards

Only `/dev/block/mmcblk0p10` is a mutation target. Complete actual install preimage
must be one of these three exact full-p10 hashes:

| Actual preimage | SHA256 | Journal classification |
| --- | --- | --- |
| Original stock recovery | `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20` | `exact_stock` |
| Known prior failed rescue | `3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a` | `exact_prior_failed_rescue` |
| Stock-kernel minimal RAMUSB probe | `7562b6168a3cd3f8a2ac4fe1a896f707eab992b2f9b32a1ffb9b1ea33683f596` | `exact_stock_minimal_ram_probe` |

Each accepted install records actual `install_preimage_sha256/bytes` before
candidate dispatch. `check_install` verifies this binding against the first
actual captured bytes and guarded read command/result provenance, then verifies
exact full new postimage and write/readback chronology. The new namespace is
`exact-linux49-ramusb-<parent-run-UUID>-<phase>`; the probe's fresh public report UUID
is `801c68c4-841f-4ea4-9e9e-c608621839ca`. Parent live runs require new canonical UUIDs
and newly reviewed contracts; prior profile/code contracts cannot be reused.

All previous loaded-source checks, exact device/partition identity, shared mutation
lock, current physical USB plus already-connected authenticated Wi-Fi requirement,
wall and host-boot-bound monotonic expiry, dispatch-boundary checks, full physical
preimage/readback, live install return token and one-shot phase consumption remain.
Known completed candidate failure may use only the existing fixed original-stock
inverse. Uncertain completion/expiry/source or USB invalidation is terminal: no
further commands, automatic retry, inverse or cleanup. Original recovery restoration
between trials remains deferred and is not an automatic intermediate step.

## Exact parent API and command interface

From this spike, offline commands are:

```sh
python3 source/adapter.py plan
python3 source/adapter.py verify-local
python3 source/adapter.py template --run-id "$RUN" --phase pin-install
python3 source/adapter.py template --run-id "$RUN" --phase install
python3 tests/run_tests.py
python3 scripts/reviewer_regressions.py
```

Templates keep review/supervision false and time fields unset. No affirmative
live contract is supplied. Parent separately reviews the exact receipt/profile,
retains the stock-trial prerequisite, and owns fresh bounded phase contracts under
this spike, the live driver and any actual actions. The existing API arguments,
for later parent-owned execution only, are:

```python
# Use a fresh Python interpreter for this exact source path.
from pathlib import Path
import sys
SPIKE = Path('/OWNER_HOME/Documents/workspace/ideas/2026-11-06-asus-linux49-minimal-probe-transition')
sys.path.insert(0, str(SPIKE / 'source'))
import adapter as a
assert a.code_receipt()['sha256'] == '2462a2ef11137852fbca68e89d22fce6ebd7dc4b48458ff38a88814f162b6ef3'
# RUN: new canonical parent-owned UUID. PIN_CONTRACT and INSTALL_CONTRACT:
# separately reviewed parent-owned JSON Paths beneath this spike.
result = a.main(['pin-install', '--execute', '--run-id', RUN,
                 '--contract', str(PIN_CONTRACT),
                 '--supervised', '--physical-fallback-present'])
# Require successful actual live return, then use the same RUN promptly.
result = a.main(['install', '--execute', '--run-id', RUN,
                 '--contract', str(INSTALL_CONTRACT),
                 '--supervised', '--physical-fallback-present'])
```

The API prints JSON and returns a process-style exit code. Parent must retain the
actual successful live install stdout and its `install_completion_token` through
the parent's protected driver; a visible journal cannot reconstruct it. A later
optional parent-elected fixed original recovery restoration uses `pin-restore`
then `restore`, with separate fresh phase contracts containing that same live
token as `install_completion_token`. It still requires healthy original Android,
a new current stock USB pin and retained live install linkage.

Stock minimal PID1 trial completion is required before manual entry of this
candidate. Parent separately prepares read-only host observation and supervises
manual entry/return. Its 60-second observation window begins at manual entry and
is not extended by a delayed PID1 timer. The Linux 4.9 kernel's nominal 14-second
Power reset is unvalidated; the stock kernel's user-proven shorter hold is no 4.9
guarantee. Parent retains supervised physical 15–20-second Power/Normal Boot
fallback and verifies actual healthy stock Android before further commands.
Exact media/report acceptance and limits remain in the candidate's frozen HANDOFF:
65,536-byte mass-storage-only medium, actual host-observed media read-only state,
fresh public UUID and exact seven-field report/uname. The adapter reports no
physical GO, automatic return, Android17/security or hardware readiness.

## Offline verification

All 65 inherited/focused methods pass in
`evidence/offline-1794020665223066000/receipt.json`; all 9 inherited reviewer
regressions pass in `evidence/targeted-1794020666408526000/receipt.json`. Both
receipts bind the same exact final source receipt and test-file hashes. The
runners installed process/fork/network-denying audit hooks before implementation
imports; no blocked events or actual subprocess/network operations occurred
inside the runs.

Focused cases cover all three actual preimages and their distinct classifications,
complete preimage state/capture/check_install linkage, preimage-record tampering,
exact newly wrapped kernel/header/layout independent guards, previous candidate
rejection, full padding/readback and unexpected-preimage rejection, actual local
compiled input/config and manifest binding, new namespace/parent requirement and
unvalidated Power limit fields, third-preimage known failure using only the fixed
original inverse, and third-preimage uncertain completion with no later commands.
Inherited cases preserve expiry, USB/Wi-Fi, lock, source drift, completion-loss and
one-shot inverse behavior. The original-source/artifact preservation check passed.

`evidence/plan-only.json` is the audited offline API result.
`evidence/binding-receipt.json` records candidate/header/kernel/input/config pins;
`evidence/verified-original-input-pins.json` records the actual preserved inputs.
`evidence/source-receipt.json`, `HANDOFF.json` and `DELIVERY_PINS.json` bind this
reviewable packet. These are fixture/offline proofs, never physical timing, USB
report, boot-success or return qualification.
