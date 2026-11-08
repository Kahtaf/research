# Offline prearmed SD frontend follow-up

Question: can a deliberately prepared SD bundle execute once without any
post-boot USB/Wi-Fi/UI channel, while retaining the existing writer guards and
making full-install recovery checking practical?

Status: implemented; focused host cases passed; updated static AArch64 frontend
and AArch64 daemon translation unit compiled. This is source/ARM64 build output,
not a packaged or physically qualified recovery container. The completed
`2026-11-07-asus-microsd-rescue-frontend` sibling is preserved. The parent's
reported FAT32/MBR card preparation is context only; no card, device, Wi-Fi,
private data, active build or platform tree was accessed here.

Outputs:

- `artifacts/sd_frontend.aarch64`: static AArch64 executable, 775736 bytes,
  SHA256 `0d7ad266bbe5fefc1ce7db8716d209ed3a6da3d4de124e1d99d84a4634d5e7cb`.
- `artifacts/rescue.aarch64.o`: compiled AArch64 daemon translation unit,
  40584 bytes, SHA256
  `7cd6d8c57767f409e06d8bf17ab8192ce11fb8aafb5f58eb6d7684693eaa07ee`.
  This object does not include P10_HANDOFF or link a helper/container.
- `source/sd_frontend.c`, `source/rescue.c`, `source/recovery_phase.h`:
  current implementation. `source/sd_mount.h` is unchanged from the SD sibling.
- `followup.patch`: combined frontend/daemon/guard delta against that completed
  sibling's source directory, with `patch -p1` from its root.
- `combined-daemon.patch`: original stock writer -> SD mount exception, run
  nonce and accepted phase proofs, including both new headers.
- `INTEGRATION.md` and `PROTOCOL.md`: exact offline contract and service notes.
- `evidence/build.json`, `evidence/artifact.json`: actual compiler/test output
  and executable/object/source hashes.

## Implemented behavior

No arguments remains PLAN and performs no reconciliation, report creation or
image mutation. Online `--execute` retains its exact live-run-bound card trigger
and independently supplied immutable `/rescue.recovery.sha256` comparison.
It remains an online provisioning profile; no self-referential embedded pin is
required by the separate offline profile.

Explicit `--offline-prearmed` reads immutable root-owned RAM `/rescue.sd.arm`,
exactly 64 lowercase hex plus LF, and requires this exact ordinary card file:

```
/mnt/rescue-sd/asus-rescue/execute.trigger
OFFLINE-PREARMED ASUSR002 <actual-RAM-manifest-sha256> <build-arm-id> install:2,4,3
```

The line ends with LF and has no angle brackets in an actual staged trigger.
Both fields are parent-supplied actual values. No arm ID or real trigger was
created here. The arm is a pairing ID, not a secret, signature, source admission,
or claim of adversarial authentication. It is independent of the daemon's
unpredictable live run nonce, so the parent can stage it before boot. Deliberate
rollback still requires a separately selected role and exact selection text,
`rollback:0:inverse:-1` or the chosen role/explicit inverse. There is no automatic
rollback selection.

The frontend obtains initial authenticated status, binds actual RAM manifest,
PID and run nonce, then **closes that connection before full-source preflight**.
After validating source bytes/trigger it durably creates O_EXCL `attempt.txt`
with UNKNOWN before reconciliation or target mutation. It reconnects and requires
the same PID AND run nonce before the opcode6 capture and image exchange. No
silently restarted daemon is admitted. Every later role connection also checks
the same instance. Existing attempt.txt prevents another execution even on a new
recovery boot with a different PID/run; nothing clears or resumes that report.
A failure after report creation consumes the attempt even if no target write
occurred. The parent must retain the evidence and make a separate reconciliation
decision; the service never deletes reports or retries.

Offline execution hashes all **16740352 actual p10 bytes** through authenticated
RSC1 opcode6 before any image mutation. Only after the complete capture passes
frame/chunk checks is its digest published in the RAM p10 baseline. The report
records the actual digest, byte count, runtime-stability binding and actual daemon
run. This exact baseline is supplied to every image reconciliation, and all five
phase-bound daemon recovery proofs compare actual bytes against it. No SD
recovery pin is accepted. Truncated/failed capture never establishes a baseline
or starts an image.

This is runtime stability binding. Parent MUST independently full-readback-verify
the exact admitted recovery before manual entry. The client neither proves that
parent action occurred nor independently admits the running recovery. It is not
equivalent to an independent pin against an adversarial concurrent p10 writer
before/during measurement. It adopts the accepted ordinary-writer invariant:
no concurrent reachable p10 writer in the integrated RAM graph, and no concurrent
fd-table rebinding. That invariant must hold through the terminal receipt.

The daemon session and recovery_phase.h match the accepted phase-proof bodies
exactly. Five full recovery samples remain per image: before reconciliation,
after the target scan, at activation, after whole-target verification, and at
commit. Per-chunk source hashing, identity/CID/GPT/Enforcing, target descriptor,
recovery descriptor/node/geometry/alias/holder/mount and manifest/pin/image/token
checks remain; the per-chunk full p10 hash is removed. A later mutation is detected
only if a later full proof observes its changed bytes. Transient changes and
changes after the last observed bytes are not guaranteed to be detected. Closed
fds/replacements changing the checked binding can be detected; equivalent
same-node open-file-description/flag substitution is not universally detected.
The independent review's precision limits are preserved, not strengthened here.

Normal five-role order remains SYSTEM role2 -> DATA role4 -> BOOT role3. Actual
RAM manifest authority, fixed image hashes and geometry, separate removable SD
identity, <=1MiB chunks, exact 355840-byte DATA tail, source rechecks, full target
readback and final op9/0x89 acceptance are unchanged. Any failed/unknown outcome
stops before a later role. No automatic inverse/retry/reboot is added. A stock
pair still cannot admit an Android17 install. The host bundle producer is
unchanged, defaults PLAN and creates no execution trigger or admission.

## Checks, bounds and continuation

Only focused checks ran: exact offline pairing/profile/selection; durable report
refusal after changed run; fresh connections accepting the same PID/run and
rejecting either change; complete production-size p10 capture versus missing
final frame; unchanged accepted session/header bodies and five-proof guard
semantics. The guard fixture uses a 16-byte ordinary file; the capture fixture
streams 16.7MB generated bytes and is not a device read. Existing broad suites,
independent reviews, kernel/platform builds and physical tests were not rerun.

Build prefix: `/srv/android/asus-microsd-offline-prearmed-20261107-impl1`, created
exclusively through the existing fixed remote helper. Compiles/tests were serial
on one CPU with a 512MiB address-space bound, 120 CPU-second process limit and
small output bounds. No other remote prefix/build/cache/log/lock was read or
changed. `scripts/build_remote.py` is exclusive one-shot staging; do not rerun
against that existing prefix.

For continuation, use INTEGRATION.md. Parent supplies actual image admissions,
arm ID, card staging and final init/policy/helper/container binding. The terminal
five-role helper admission is a separate staged input and was not changed or
compiled here. Remaining runtime gates are actual target static-libc execution,
enforcing labels/DAC/socket peer creation context, fixed SD mount/namespace,
report durability/capacity, storage/timing and the final no-concurrent-p10-writer
graph. No new readiness flag or generic approval/resume wrapper is introduced.
