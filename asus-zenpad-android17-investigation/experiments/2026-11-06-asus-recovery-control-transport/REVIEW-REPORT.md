# Recovery-only transport implementation review

Delivered a reviewable tool, not a flashed image or runtime result. Work was
confined to this spike. Required orchestration README, custom-boot REPORT and
exact-LK acceptance review were read first. Their conditional GO remains a
static justification for a supervised stock-kernel changed-ramdisk control;
this implementation adds no LK execution evidence.

## Actual offline evidence

Both complete original recovery backups were independently read locally and
matched 16740352 bytes and SHA256
`902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`.
The wrapped stock kernel/DTB is 7472341 bytes and SHA256
`b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`.
The unchanged root-helper source and its pinned mtk-su binary were hashed too.
See `evidence/local-input-verification.json` for exact paths and hashes.

All **26 offline tests passed**. The bounded standard-library suite uses fake ADB/root subprocess responses
and a byte-backed simulated recovery partition. It observes the requested write
destination/source set, resulting full bytes, statuses, and calls after loss.
Generated root scripts are syntax-checked locally with `/bin/sh -n`, never
executed against device paths. One local shell test removes all device guards
and runs only a failing subshell and printf to check real shell status behavior.
The fake candidate is intentionally nonbootable and is deleted after testing.

Actual test results are `evidence/offline-tests.txt` and the scenario-level
`evidence/offline-tests.json`:

- Wrong serial, fingerprint, sector count, start sector, partition number,
  major/minor, logical sector size, alias, current stock hash, staging bytes, or
  preexisting session: no simulated block-write attempt.
- Normal install: only `candidate → mmcblk0p10`, complete candidate bytes match,
  no restoration claim.
- Root write exit 5 after partial mutation, or exit 0 with mismatched full
  readback: `candidate → mmcblk0p10`, then exactly one
  `stock → mmcblk0p10`; final bytes equal the complete stock backup. Install
  still reports failure and never enables manual Recovery selection.
- Denied write with unchanged stock: candidate attempt only, followed by
  `install_failed_verified_already_restored`; no redundant stock write.
- Known repeated read error after candidate write with healthy Android: one
  exact stock inverse is attempted and verified. Transport uncertainty during
  the same phase would instead stop immediately.
- Timeout during write/readback, missing root status, or helper failure:
  candidate attempt only, no blind inverse/retry and no restoration claim.
  Timeout cases assert **zero further transport calls**.
- Android no longer boot-complete after a partial failure: no inverse dispatch.
- Failed inverse: candidate then one stock attempt, no retry or restore claim.
  Explicit restore write failure/mismatch: one stock attempt, unverified stop.
- Explicit restore of changed bytes: one stock attempt and exact full hash.
  Already-stock restore, including possible automatic stock repair: zero block
  writes and `verified_already_restored`.
- Failed final cleanup cannot grant the manual-Recovery gate. Verified partition
  evidence remains recorded separately from failed cleanup/health.
- Changed/rehashed kernel, wrong candidate/padding hash, unapproved manifest,
  wrong target and wrong reviewed-manifest hash are refused locally. Default
  PLAN ONLY is tested with all subprocess execution forbidden.

The real local shell status test observes operation exit **23** while the outer
wrapper exits **0**; the parser still reports 23. The tool deliberately carries
operation status in a unique required record, with the helper exit status used
separately to confirm helper/Enforcing completion. A missing/duplicate record or
nonzero helper exit is uncertainty. This avoids relying on legacy ADB shell exit
propagation or allowing `setenforce`/cleanup to turn a failed write into success.

## Remaining parent review points

1. Review the completed diagnostic source/image, unique marker, bounded return,
   RAM-only operation, lack of persistent mounts/writes or update/wipe behavior,
   MTK/header packaging and exact full-partition padding. Populate and hash the
   manifest only from that review. No actual candidate was accessed or approved
   by this task. Ensure it fits the narrow bounded-image profile documented in
   README; profile changes need another source review.
2. Review `source/recovery_control.py`, especially the generated root envelope,
   fixed `dd` destination, private staging and single-inverse logic. The existing
   helper remains the sole privilege path. The live stock shell's `stat` format,
   directory modes and `dd` behavior remain untested by this work; unsupported
   guards refuse. The existing helper imposes a 60-second root-session limit;
   timeout is uncertain and causes no automatic recovery action.
3. Arrange user presence, usable battery/USB, healthy authorized stock Android,
   and the physical Recovery/Normal Boot procedure. Confirm no concurrent writer
   on another host/tool. The offline plan cannot establish any of these facts.
4. Before manual Recovery, require the future execution run's full candidate
   hash, completed root/Enforcing checks, and cleanup/health evidence. A hash
   records a particular readback; later automatic stock repair can change the
   partition. The user/parent alone chooses boot modes. Preserve screen/marker
   evidence and distinguish LK acceptance from kernel/init/USB problems.
5. After manual Normal Boot, explicitly run the stock inverse even if Android
   may already have repaired recovery. Require `restored_full_hash_verified` or
   `verified_already_restored`, plus health/cleanup evidence. If transport was
   lost, parent must first assess the device/command state; do not infer that a
   timed-out writer stopped, retry blindly, or claim restoration. Existing
   sessions are refused. The separate restore session allows an intentional
   inverse after a stopped install without deleting the install's evidence;
   inspect any stale restore session before another attempt.

No full-disk backup, BROM/DA access, unlock, security-data modification or broad
security certification is introduced as a prerequisite. The known normal-stock
entry route remains the conditional recovery premise. This tool does not prove
that route will survive a new failed recovery boot, or that block writes and
custom recovery execution work on the tablet.
