# Implementation handoff — offline only

The missing exact-candidate recovery transport is implemented. The 32-method
suite passes, including a complete emulated install → diagnostic observation →
stock return → stock inverse → journal-linked finalization. No target operation
was performed. This report does not authorize the first physical Linux 4.9 boot.

## Fixed scope and provenance

The accepted image is only the 8,880,128-byte
`UNTESTED-combined-linux49-ram-probe.img` in the build-continuation `probe-r2`
artifacts. Its SHA256 is
`48bb6efa1620cb380037e53b53cfa560e38cd23b95211c8634616ce94fd6ce48`;
zero-padded p10 SHA256 is
`25812e7dde39ec37e3f4c9438341cc29f2b2e7dce61e4b88d0886cd9dd075b16`.
The exact combined-r1 kernel input is separately checked:
`d4094bcff6c763af7f1c01ccd3d612a988f96de13f78b492b808cc76c0ac929f`.
Product kernel r3 has no accepted path or override.

`profile.json` carries the independent review's header, compressed Image,
original/packaged DT, permitted chosen-property changes, ramdisk gzip,
per-entry mode/owner/size/hash, policy/helper/public-key identity, diagnostic
marker and P00A49PROBE USB/ADB identity. Runtime local verification checks the
whole image and padded partition, combined input, header, packaged compressed
Image/DT and compressed ramdisk. Per-entry and DT semantic provenance comes
from the pinned independent review; this transport does not claim a second
independent parser/rebuild. The exact whole-image pin binds every packaged byte.

The independent review's static packaging PASS and original HOLD/F1/F2/F3 are
preserved verbatim under `evidence/reference`. The parent's corrected observer
is imported only after verifying SHA256
`75b1d96686a484e0eb5cfd73ec62976c394de1895e14ea45c83ea745d15f07ec`.
It is unchanged. The old Wi-Fi source's original SHA256 is
`34ed0079e7f9ca3b4edcab5d108fe29d330a653781c4ec5d67b8ca421daac0ab`.
The only change in its local copy is `BASE`, shown exactly in `base.diff`.
The stock-only validator is byte-for-byte unchanged and a negative test feeds
it the real frozen 4.9 image: it refuses the non-stock kernel.

## Implementation and execution boundaries

`source/probe_transport.py` provides PLAN_ONLY for every action unless
`--execute` is explicit. Live actions additionally require all of:

- Parent-reviewed exact code-bundle and profile digests, `--parent-reviewed`.
- Truthful `--supervised` and `--physical-fallback-present` attestations.
- A canonical UUID and a same-run exact-stock USB pin no more than 180 seconds
  old, tied to the pinned observer, candidate and physical topology. The current
  transport ID and identity must still match. Freshness is checked again before
  candidate dispatch after staging.
- The existing shared mutation lock, clean eligible prior phases, and a new
  exclusive phase directory. No resume/retry/endpoint/partition/image override.

The pinned root helper and binary are checked locally before every helper call;
helper success retains its own exact-stock identity, secure-ADB, UID/status and
Enforcing-before/after checks. All inherited geometry and bounded dd commands
remain. Before/after each helper call the adapter revalidates the physical USB
inventory. Health checkpoints also revalidate USB properties/Enforcing and the
fixed Wi-Fi endpoint's independent hardware identity. A changed USB transport
mid-operation stops as uncertainty, rather than silently repinning.

Candidate and stock are staged in a new per-run private directory with fresh
full staged readback. Only p10 is written; no reboot, boot selection, BCB/para,
other-partition or hardware-control commands exist. The known-failure stock
inverse is inherited. Across the run, either a failed install consumes the
inverse, or a successful install permits one later restore. A stock readback
before restore makes the inverse idempotent. Uncertain execution has no cleanup,
automatic inverse or further transport commands; incomplete/uncertain restores
also block later readback/finalization in that run.

## Observer integration

No parent observer edit is needed. Use the same UUID and original trial pin for
observer startup and install. Save the original pin: the install journal embeds
and hashes it. After stock returns, make a new same-run stock pin if the old pin
has expired or transport ID changed. Its physical USB topology must match the
trial. Restore/readback embeds that fresh pin and links the unchanged install
journal by digest.

Every full p10 capture records its source, size/hash, time, run, pin, session,
root-command file/hash and Wi-Fi pull-command file/hash. Command receipts cover
the complete host command journal. Finalization accepts only the fixed run's
actual restore/readback journal; checks chronology after observed stock return;
checks the completed pinned helper/guarded full-dd status and matching exact pull;
rechecks all command/file hashes; then delegates strict report/run/return/stock
checks to the unchanged observer. It also performs fresh USB+Wi-Fi stock checks.
No local backup-path input is exposed by this adapter. A copied backup with a
fresh timestamp cannot substitute for a missing reader/pull journal.

These are auditable host records, not cryptographically attested physical
origin. A privileged person could fabricate local evidence. Tests themselves
fabricate device responses intentionally, so their successful acceptance result
is explicitly offline proof of logic, never a physical capture. The parent must
retain the genuine live command journals and supervise actual return.

A normal stock boot alone never sets restoration verified. Final acceptance
retains the observer's four separate outcomes, unavailable optional readings,
unverified directory listings, and `hardware_ready=false`. The tool's
`manual_recovery_permitted` also remains false even after a verified install;
manual entry is exclusively the parent's separately supervised decision.

## Offline verification

32 test methods pass, including multiple fault subcases:

- Exact real image/components and both real fixed stock backups verified;
  candidate/kernel/profile/helper mutations rejected; old stock guard rejects r2.
- Full staging/install/partition readback, stock inverse, already-stock no-write
  restoration, additional read-only capture, end-to-end observer finalization.
- Known partial/mismatched writes and read failure: exactly one stock inverse;
  inverse/restore failures: no second attempt.
- Wrong serial, fingerprint, insecure ADB, permissive state, USB identity,
  topology/transport change, all sysfs geometry values, wrong alias, existing
  stage, wrong current p10, staged corruption and short reads.
- Stale/future/wrong-run/wrong-profile/wrong-observer pins, including pin expiry
  during staging; missing review/supervision/fallback/hash inputs.
- Wi-Fi loss, helper completion ambiguity and USB loss: no commands after
  uncertainty, no automatic inverse or cleanup.
- Real local advisory-lock contention, including CLI gating; phase replay;
  failed-install/prior-uncertain-restore follow-up refusal.
- Copied backup substitution, missing capture, reader run/profile/code-mode
  mismatch, pre-return reader, damaged capture/root-command binding, incomplete
  diagnostic observation and local file tampering cannot finalize.

Tests intercept every transport subprocess call with an in-memory model and
forbid actual Popen/check_output. No shell, helper, ADB, root, USB or target
commands run. Fixtures model generated command scripts and block/file bytes;
they cannot establish Android runtime permissions, radio/USB reliability,
charging behavior or Linux boot correctness. The base shell/helper is reused
from the previously tested implementation rather than claimed newly validated
on hardware. All temporary 16-MiB emulation files are deleted per test.

## Remaining gates / limitations

1. Parent must independently review the diff, exact profile/code receipt and
   concrete commands. These CLI attestations are statements by the operator,
   never evidence of their physical presence.
2. First physical 4.9 boot remains held until nearby fallback is actually ready.
   No static receipt, wall-clock arrival estimate or successful test changes that.
3. Both the finicky physical USB connection and fixed authenticated Wi-Fi must
   be available at each live phase. If stock reboot loses Wi-Fi, this CLI stops.
   Parent must separately regain the already-authorized transport; this code
   never enables it, scans, reconnects or kills/restarts the Mac ADB server.
4. Freeze code/profile/observer during an active run. A changed source digest,
   interrupted or uncertain operation is a deliberate stop requiring parent
   assessment. There is no generic emergency writer or forced retry here.
5. A failed diagnostic does not block a clean install's stock restore, but
   diagnostic acceptance remains failed. If observer collection has finished
   after an earlier restore, use the readback phase for a fresh post-return
   capture; do not substitute either backup.
6. The existing full local stock rollback READY receipt was read; it is static
   byte verification and says ready_to_flash=false. No system file was copied
   or rehashed here. This work only uses the two exact p10 backup copies.
7. The fixed staging paths can remain after a stopped operation. Preserve them
   and all evidence for parent assessment. No automatic cleanup is attempted
   after transport uncertainty. Local live evidence costs roughly a few hundred
   MiB per complete run, not a fullSYSTEM-sized copy.

All new files and QA output are in this spike. Existing sources, observer,
images, backups, nested repositories and parent spikes remain unchanged. No
network/cloud/SSH, device access, private calibration/private ADB key reads,
process inspection, build or source mutation outside the spike was performed.
