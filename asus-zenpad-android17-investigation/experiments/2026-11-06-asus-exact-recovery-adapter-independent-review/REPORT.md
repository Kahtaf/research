# Independent exact recovery adapter review

Review complete. **One P1 finding prevents a clean readiness result within the offline transport scope.** Parent owns the fix and all eventual physical actions. No implementation changes, execution approval, physical GO, commissioning, stock-return, or hardware-readiness claim is supplied.

## R1 — P1: clock rollback extends the USB pin past 180 elapsed seconds

Primary source: `source/adapter.py:179–184`, especially line 184. Related: `Guard.check` at lines 230–234, pin creation at lines 397–399, phase loading at lines 645–652, and actual nested dispatch at lines 327–330. These line numbers refer to the exact reviewed source, preserved in the snapshot.

`validate_pin` accepts only wall-clock age (`time.time() - created_at`). `Guard.end_mono` caps the phase contract, but does not cap pin age. The pin records no host monotonic timestamp. A backward wall-clock correction therefore lets an actually expired pin authorize a real nested helper mutation while the longer phase contract remains valid.

Concrete bounded reproduction, using unchanged production methods and the supplied typed storage/ADB fakes:

1. Create a pin at wall `2000000000`, monotonic `1000`. Give the phase a 590-second contract.
2. Run production setup, both full staging/readback checks, and a full original-p10 observation while the pin is fresh.
3. Advance monotonic time to `1200` (200 seconds elapsed), and wall time to `2000000100` (100-second net advance, representing a 100-second backward correction).
4. Call production `Transport.write('candidate')`. Its actual nested root-helper dispatch succeeds in the fixture, writing the exact full 16,740,352-byte candidate to the modeled p10. `guard.stopped` remains false. Contract time remaining is 390 seconds; pin wall age is 100 seconds; actual monotonic pin age is 200 seconds.

The failing assertion and every command/receipt remain in `evidence/targeted-1794005646847753000/test_pin_monotonic_age_expires_before_candidate_write/`. Its `observations.json` records the admitted candidate hash `3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a`.

A second regression uses production `usb_snapshot`, durable pin publication, journal completion and `load_pin`: the actual serialized pin is still accepted after 400 monotonic seconds when a clock correction leaves its wall age at 100 seconds. This is the same finding across phase boundaries, not a second issue. Evidence is in the adjacent `test_reloaded_pin_expired_monotonically_refused_before_commands/` directory.

Smallest parent fix: persist the pin's host monotonic creation time with a binding to that host clock epoch, and require both wall and monotonic age to remain within 180 seconds when loading the pin and at every actual nested dispatch boundary. Cap the active guard by the pin deadline as well as the contract deadline, including when `main` assigns a loaded pin after constructing `Guard`. Expiry must latch the existing terminal stop. Keep both regressions: anchoring only a new phase's deadline cannot reject a pin already stale before that phase starts. This extends the existing freshness guard; it requires no new deployment workflow.

## Exact reviewed bytes

Canonical sorted five-file JSON receipt: `5f20aece6bfa3ede3e937766ff390e6a575cbbc97759cbe52a3f8a09b68f5a72`.

- `profile.json`: `661d93cbc012d839429bb1b87431fb83b5f646833ee59d307e0e60461b7cda6f`
- `source/adapter.py`: `3f52fcadb8417aafa1235391ae2bc27a8ebc149541caaf953ae6c5201073ffc2`
- `source/engine.py`: `630c4aaadbb418dc0af1f5a00628b3ec16117bb165707b4d18794c124464a681`
- `source/root_dispatch.py`: `38c8030193f32084b6549bf81f6e1d2f9428fb516a6853295eb1adb4208407bc`
- `source/preserved.json`: `80475bab124d355255ce10d4224ffc89ac20b61ddc440d88303f5fa47638ba8c`

Candidate: `5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f`, 10,412,032 bytes. Full zero-padded p10: `3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a`, 16,740,352 bytes. Original: `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`. The intended block is `/dev/block/mmcblk0p10`, recovery alias, `179:10`, start 160184, 32696 sectors of 512 bytes.

Read REPORT.md, HANDOFF.json, COMMANDS.md, README.md, the full implementation and tests, pinned helper source, and supplied exact diffs. Independently regenerated and matched the bodies of the engine import-only, root-dispatch adaptation, adapter-addition and profile-addition diffs. Also read the preserved prior-dispatch comparison. No candidate build, target service, bootloader, PCM, or separate native work was re-reviewed.

## Verification and scope observations

The supplied 45 methods pass in the owned snapshot, with zero failures/errors and zero audit-blocked operations. The first snapshot run had one setup error because the old-image negative fixture was absent from the advertised 16 preservation inputs. Copied that one public negative fixture, recorded its pin, and reran successfully. Both logs are retained; that setup omission is not a software finding.

The independent suite has nine tests: seven pass, and two fail for R1, with zero errors. The script is `scripts/targeted_review.py`; it creates a fresh evidence directory per run. Its audit hook is installed before adapter/helper/test imports and blocks subprocess creation, exec, fork, process spawning and sockets. Actual implementation helper/device processes and network operations: zero. Only command results, clocks, files and block contents are modeled. Fixtures contain explicitly labeled synthetic contracts; they approve no physical action.

Passing additional cases exercise: contract monotonic expiry during actual nested binary staging; missing operation completion through production execute; failed candidate-completion publication stopping immediately with no inverse/cleanup; unhealthy stock after a known candidate failure preventing inverse; mismatching restore readback preserving modified status without retry; consumption of the single candidate and single fixed-original write; and isolation of production helper module references. Initial and final targeted failures are retained. The final receipt is `evidence/targeted-1794005646847753000/receipt.json`.

Within the inspected production paths, exact image hash plus Android/MTK layout, kernel/header and full padding checks admit the fixed candidate only. Local stock inputs are hash-bound. Root operations retain the fixed alias/node/device/geometry guards. Full staged-byte checks and full physical-read command/readback receipts precede success. The existing shared mutation lock encloses production phases. Parent code/profile/run/phase contracts, wall and monotonic contract expiry, current USB enumeration, stock identity and Wi-Fi identity/boot binding are present. R1 limits the claimed USB pin freshness.

The inspected state machine admits one candidate plus at most one fixed original inverse after a known completed failure, stops on uncertain completion, refuses unknown recovery during later removal, requires clean install/capture/source linkage and the live completion nonce, handles already-original removal, and retains conservative modified-partition flags. Supplied tests exercise lost nonce publication and a fresh removal pin with changed transport ID but unchanged physical topology. Actual supervision, manual entry/return, rescue commissioning, stock return and hardware status remain explicitly separate. No adapter path invokes rescue protocol, boot/reboot/mode entry, BCB/p20/p26 or SYSTEM/BOOT operations. The old diagnostic validator/observer are not adapter execution paths; no RAM-only or bounded-return attestation is reused.

These observations are not exhaustive correctness proofs. No real USB enumeration, authenticated Wi-Fi session, Android shell semantics, privilege/SELinux transition, device filesystem behavior, storage durability, physical readback, timing, candidate boot, manual return or hardware behavior was tested. Those unproved prerequisites are limits, not software findings. Candidate SYSTEM/BOOT capability and the fixed original-p10 helper remain as described by the independent build review; public host flags do not remove those capabilities.

## Preservation and continuation

All 51 pre-existing reviewed-spike files remain byte-identical, including source and tests. All 16 original public/fixed-stock inputs remain byte-identical. The extra old-image negative fixture is unchanged. Snapshot production code retains the exact five source pins. See `evidence/preservation.json` and before/after manifests. All review outputs are under this dated review spike; nested repositories were preserved. No private calibration/key inputs were accessed.

Parent: fix R1, regenerate source receipts and contract pins, and rerun both clock regressions plus the supplied suite against the new exact bytes in an offline guarded snapshot. A changed code receipt needs explicit new review linkage; this review does not authorize those future bytes. Readiness remains unresolved within the offline transport scope until the freshness gap is fixed. All eventual physical actions stay with the parent.
