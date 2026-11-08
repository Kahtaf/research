# Implementation report: exact recovery deployment

Implementation complete for parent technical review. **No device contact, ADB/root/SSH/cloud/network operation, build, rescue protocol/activation, mode entry, reboot, physical GO or readiness claim.** All implementation and QA writes stayed inside this separate spike; no subagents were used. This is not independent review.

## Exact scope and reused behavior

The fixed 10,412,032-byte candidate is `5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f`; the entire 16,740,352-byte zero-padded p10 is `3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a`. Original recovery is `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`. Actual wrapped stock kernel, exact Android/MTK headers/layout and every padding byte are bound. The original build/session contract and target implementation are unchanged.

The target has original SYSTEM/BOOT roles (manifest `605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47`) and fixed original-recovery helper (`c5df268a9f0bdc31e01140a5378d404f9cb7b091b8ec50e5c2be992434089859`). Its public host flags do not disable target capabilities. This deployment profile makes no RAM-only/zero-record or bounded automatic-return attestation. Parent owns supervised manual entry/return separately.

`source/engine.py` reuses the stock Wi-Fi writer. Its only difference from original source SHA `34ed0079e7f9ca3b4edcab5d108fe29d330a653781c4ec5d67b8ca421daac0ab` is an import-only CLI guard; all engine methods/guards are unchanged. The adapter uses its fixed root envelope, recovery alias/node/geometry/stock identity, full staged-byte comparisons, full physical readback and exact inverse. It does not use or relabel the old diagnostic validator or observer. The inherited generic CLI is disabled in this copy. [Exact diffs](evidence/diffs/) include this guard, helper adaptation and all new adapter/profile lines.

## Guards and completion rules

PLAN_ONLY is the default. Actual contact requires truthful current supervision and nearby Power fallback plus an independently parent-reviewed code/profile contract for the exact run/phase. Templates contain false review/supervision and null times. Each fresh contract lasts at most 600 seconds, with a monotonic ceiling and wall-clock checks; each actual USB pin lasts at most 180 seconds. These are host authorization limits, not measured rescue timing or target auto-return claims. An expired host request cannot cancel on-device work.

The adapter obtains actual current healthy-stock USB inventory/properties/Enforcing/boot UUID/stopped recovery-autorepair evidence and requires the already-authenticated secure Wi-Fi endpoint. It shares the established existing device-mutation lock; it creates no substitute lock. Each UUID has exclusive pin-install/install/pin-restore/restore directories. No retries or resume. Physical topology and identity stay fixed; a new transport ID is allowed only between phases with a fresh complete stock observation. A changed boot ID within a phase stops commands. After any parent-owned manual return, removal needs a new current pin.

`root_dispatch.py` loads the hash-pinned original helper into a fresh isolated module. Only that module's subprocess/sys references are replaced. Every actual nested ADB request is authorized after evidence persistence and source checks, immediately before dispatch; deadlines are rechecked after potentially slow local reads. Candidate freshness stays checked through actual root write dispatch. UnicodeError, closed-stream errors, timeout, helper refusal/missing completion, identity loss and persistence failure latch terminal uncertainty. No later commands, including cleanup/inverse, are allowed. Returned and partial stderr are preserved in nested receipts; aggregate helper stderr is also journaled.

At most one candidate dispatch and one fixed-original inverse are admitted. Install requires actual full stock preimage, full staged stock and candidate bytes, then full candidate readback. Only a known completed candidate failure can take the single bounded inverse under the same still-valid guards. Restore requires a clean original install and its guarded stock-prerequisite and candidate-final captures, source/code linkage and fresh pin. It admits only exact candidate or already-original bytes; arbitrary unexpected recovery hashes are refused. Prior automatic inverse or uncertain/failed install cannot enter later restore.

Partition status begins unobserved/conservatively possibly modified, then records actual full captures. Restore errors retain existing modified state. Write intent consumed before dispatch is distinguished from a sent request; known pre-dispatch expiry preserves the last verified partition status. Only actual full original readback clears possibly-modified status. Cleanup and health are reported separately. Manual entry, rescue commissioning, stock return, restoration and hardware readiness are not conflated; this adapter never certifies the first three or hardware readiness.

The successful live install result additionally returns a receipt nonce whose SHA256 alone is journaled. Later removal contracts require that returned nonce. A visible clean journal after publication/fsync failure cannot reconstruct acceptance. The regression deliberately leaves a visible installed journal after simulated post-rename failure and subsequent storage loss; no nonce is returned, no later command occurs, and restore refuses.

## Offline verification and preservation

Final suite: **45 test methods, zero failures/errors**, audit hook installed before implementation/test imports, zero actual subprocess/fork/socket attempts. [Final receipt](evidence/offline-1794005245640926000/receipt.json) records exact code/test pins and modeled scenarios; its adjacent tests.txt records all cases. Cases cover exact new/old image admission; kernel/header/geometry/padding changes; remote alias/geometry failures; missing review/supervision/fallback/freshness; per-nested-request expiry and late completion; helper Unicode/closed/timeout/missing status; complete staged/readback corruption; one inverse; already-original with clean linkage; unexpected recovery refusal; source drift; lock contention; consumed run; USB topology/identity changes; capture tamper; lost publication and no later commands. Fixtures model command results/storage only. There is no hardware capture, boot, SELinux/domain, timing or durability proof.

[Offline CLI receipt](evidence/offline-cli.json): verify-local, plan, default install and default restore returned PLAN_ONLY/0; execute without gates refused/2. No device process was launched. All 16 tracked original public source/image/stock-recovery inputs remain byte-identical: [before](evidence/original-inputs.before.json), [after](evidence/original-inputs.after.json). No private calibration/key/preservation payload was opened. Local original recovery was only used as the explicitly permitted fixed stock input.

All earlier failures remain. The first runner import had a test syntax error. The first 31-case run found six assertions expecting a terminal exception from inherited no-op cleanup; the adapter now checks its terminal guard even for no-op cleanup. A later aggregate-stderr assertion omitted root staging progress legitimately routed to stderr; the assertion now checks all four preserved stderr fragments plus that progress. The final implementation passes all 45 cases; prior receipts are historical and do not match every later source revision.

The dispatch-fix current source pin is `771ff66017eac906e807b8be2b722a5b3f47d3df0cb6323488ef9902464c685a`. Its older reviewed-v1 snapshot is `067a357a60da9888578d76d9a0fb326d325b45825fc9e037cfd58353b81d94df`. The current source adds query-stderr preservation; they are not byte-identical. [Recorded comparison](evidence/reviewed-root-dispatch-equality.json) and [diff](evidence/diffs/prior-review-snapshot-to-current.diff) preserve this distinction. This implementation used the current source lesson and claims no inherited independent approval.

## Exact parent review pins

Code receipt SHA256: `5f20aece6bfa3ede3e937766ff390e6a575cbbc97759cbe52a3f8a09b68f5a72`. It is the canonical sorted JSON hash of the file-pin mapping below. [Full source receipt](evidence/source-receipt.json) includes external input pins. These pin the implementation, not physical approval.

| File | SHA256 |
| --- | --- |
| `profile.json` | `661d93cbc012d839429bb1b87431fb83b5f646833ee59d307e0e60461b7cda6f` |
| `source/adapter.py` | `3f52fcadb8417aafa1235391ae2bc27a8ebc149541caaf953ae6c5201073ffc2` |
| `source/engine.py` | `630c4aaadbb418dc0af1f5a00628b3ec16117bb165707b4d18794c124464a681` |
| `source/root_dispatch.py` | `38c8030193f32084b6549bf81f6e1d2f9428fb516a6853295eb1adb4208407bc` |
| `source/preserved.json` | `80475bab124d355255ce10d4224ffc89ac20b61ddc440d88303f5fa47638ba8c` |

Parent continuation: review these exact bytes, diffs, tests and [command sheet](COMMANDS.md). No affirmative execution flags or completed approvals are supplied. Parent retains all actual operations and manual decisions. Lost completion/transport is terminal; do not retry/reconnect, substitute another UUID, or infer completion/readiness from a visible receipt. No BCB/p20/p26/SYSTEM/BOOT write, rescue opcode, mode selection, reboot or TCP re-enable route exists in the adapter.
