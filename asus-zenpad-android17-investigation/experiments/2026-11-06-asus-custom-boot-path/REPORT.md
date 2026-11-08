# Locked-unit custom recovery feasibility

**Decision: CONDITIONAL GO for one supervised stock-kernel/changed-ramdisk
recovery control, followed by restoring stock recovery.** There is no demonstrated
platform blocker preventing this experiment. There is also no demonstrated
custom execution on this exact tablet yet. This is not a full-ROM flash go.

The best concrete path is stock on-demand root, a bounded write to recovery,
and ordinary Recovery startup. The exact matching LK contains two relevant
verification checks whose returned failures do not stop the traced loading
path. This materially strengthens the case for the control; unlocking and
BROM investigation are unnecessary prerequisites for that experiment.

## New finding that changes the assessment

The exact LK has real signature verification. However, at `0x41e046d8` its
recovery header loader calls the lock-aware verifier, then at `0x41e046dc`
replaces the verifier's return with r7, the successful Android-header comparison
result. Earlier, the policy check at `0x41e1e222` routes a returned failure to a
store of red verified-boot state and rejoins the ordinary image loader. That
store is not a change of boot mode or an on-disk lock change.

The surrounding recovery path loads the payload and proceeds to the common
handoff. A normal returned verification failure can therefore plausibly show
Red State and still continue with a correctly packaged recovery. The regular
boot header has the same ignored-return pattern, but testing recovery first
preserves the known stock entry point.

This is a static inference about exact code, not successful execution. Detailed
addresses, limitations and reproducible checks are in
[evidence/lk-acceptance-review.md](evidence/lk-acceptance-review.md). No cipher,
parser exploitation, key generation or security-data change is proposed.

## Proven, contradicted and unresolved

| Assumption | Assessment and evidence |
|---|---|
| This unit is locked | Proven by saved `secure=yes`, `unlocked=no`, `unlock_ability=0` replies. Root does not imply unlock. |
| Ordinary temporary fastboot boot will work | Contradicted by the exact dispatcher registration forbidding it while locked. No need to send it. |
| Root access and reading recovery work | Proven by root-validation evidence, including independent block-read hashes. Actual recovery writes remain untested; root is the concrete candidate transport, not proof a write already works. |
| LK always halts when a changed recovery fails verification | Contradicted as a blanket interpretation of the traced checks: their returned failures are not enforced by the callers. A complete runtime boot is still unknown. |
| LK does no image verification | Contradicted. Both policy-controlled and later lock-aware verification exist. “Ignored failure” is more precise. |
| A stock kernel means the changed image retains stock authentication | False. A changed ramdisk changes authenticated image content. The control tests that change, without adding new-kernel risk. |
| Both backup copies are usable restoration sources | Proven locally: each is 16,740,352 bytes with the same SHA256, rechecked here. Previous root read independently matches. Actual rewrite/failed-boot recovery remains unproved. |
| Normal Boot / Power fallback is available | Previously demonstrated on this unit. Its success after this new recovery image fails remains a hypothesis the supervised roundtrip must test. |
| Independent fastboot entry is storage recovery | False. READY → FASTBOOT and normal reboot work; locked writes and BROM/DA restoration are not demonstrated. |
| Stock recovery provides an ADB rollback shell | Not established; the saved ramdisk has secure ADB, debuggable off and adbd disabled. Rollback uses stock Android root. |
| A historical Z380M custom boot proves our lock policy | No. The original Alpine author's logs prove another unit's DA writes/custom ramdisk, but omit LK lock state. The original TWRP thread remains inaccessible. |
| Generic seccfg unlock is the next useful step | No. The previous fixed-record/cipher analysis failed its validation. This test leaves security data untouched. |

Primary historical links and their provenance limits are recorded in
[evidence/primary-source-search.md](evidence/primary-source-search.md), including
[the original Alpine write/readback evidence](https://github.com/kaantcp/z380m-alpine/blob/7218a276f252a59874ab860683c061fa2b856519/evidence/01_stageA_printgpt_and_boot_write.txt).
No additional historical route with verified exact-firmware compatibility was
recovered. The useful new route evidence came from the exact LK itself.

## Exact partition and restoration source

Only **recovery**, GPT entry 10, Linux `/dev/block/mmcblk0p10`:

| Property | Exact value |
|---|---|
| Saved by-name alias | `/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/recovery` |
| First LBA / sector count | 160184 / 32696, with 512-byte sectors |
| Byte offset | `0x04e37000` |
| Byte length | `0x00ff7000` = 16,740,352 |
| End, exclusive | `0x05e2e000` |
| Restore SHA256 | `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20` |

The offset describes the verified GPT; it is **not** a recommendation to target
the whole disk with an offset writer. A future writer should use the checked
recovery partition node and refuse any other target or size.

Primary restoration file, relative to the ideas workspace:
`2026-11-05-asus-boot-access-audit/artifacts/device-backup/initial/recovery.bin`.
Independent second copy:
`2026-11-05-asus-boot-access-audit/artifacts/device-backup/verify/recovery.bin`.
Both contain the complete partition, including its tail. Keep the originals
private and unchanged; stage a verified copy for the parent's restore process.
No firmware scatter, another unit's image, or newly repacked stock image should
replace that exact restoration source.

Geometry comes from root-validation's `evidence/raw-gpt-verification.json` and
its observed by-name mapping, not the official firmware scatter. Current hashes
and paths are saved in [acceptance-facts.json](evidence/acceptance-facts.json).

Credible rollback is: physically return to **Normal Boot**, let the untouched
stock Android boot, use its existing authorized ADB/on-demand root, rewrite the
complete saved recovery partition, read it back, and require the hash above.
Keep boot, system, userdata, metadata, LK, both preloader areas and all security
partitions intact. The proposed control needs no persistent recovery request
in `para`/BCB: select Recovery with the physical boot menu. This reduces the
risk of repeatedly reselecting a failed recovery.

This is conditional recoverability, not a brick-proof claim. If Normal Boot
unexpectedly stops working, no demonstrated independent writer is available.
The already proven Power/menu and preloader-to-fastboot routes help regain
control, but neither fastboot enumeration nor the full OTA is a promised
recovery-only restore. The official full OTA also writes the preloaders.

## Cheapest discriminating supervised test

The diagnostic agent owns the image. Parent owns any writer and the hardware
session. This report supplies an offline plan only.

1. **Review the ready control.** Use the unchanged stock recovery kernel/DTB,
   stock-compatible Android header addresses/page size and MTK wrapper layout,
   plus a small changed ramdisk with a unique visible or readable marker.
   Verify kernel bytes against stock, image bounds and full-partition padding.
   Do not run stock recovery's update/wipe machinery. Diagnostic init must avoid
   block-device writes, filesystem mounts of persistent partitions, automatic
   updates and lock/security operations; its temporary mounts/logs stay in RAM.
   Give the control a bounded normal-reboot attempt, without writing a persistent
   recovery boot request. Physical Power/menu remains the independent fallback.
   A control lacking a credible marker/return is not ready.
2. **Confirm the supervised starting point.** User present; usable battery and
   USB; fully booted stock, authorized ADB and working existing root; physical
   Recovery/Normal Boot choices understood. Verify current recovery-node identity,
   size and stock hash against the saved values, and have the full restore copy
   and reviewed inverse procedure ready. The existing demonstrated fallback is
   the justification; do not demand proof of recovering from this same untried
   image before trying it. A stock-recovery/menu rehearsal is useful if the entry
   sequence is unclear, not a demand for BROM or full-disk certification.
3. **Perform one recovery-only installation, then read back before reboot.**
   Require the entire written partition to match the reviewed control hash.
   If writing is denied, stop: that is a transport result, not an LK acceptance
   result. On partial/mismatched writes, restore and verify stock immediately
   while Android is still running; do not proceed to Recovery.
4. **Select physical Recovery once.** Capture the screen from startup and observe
   the diagnostic's chosen USB/marker channel. Allow the LK warning delay plus
   the control's documented deadline, with a small fixed margin. Record any
   red/yellow state; red alone does not establish rejection. A unique RAM marker
   or a diagnostic transcript containing that build's identifier proves the
   changed ramdisk executed. USB enumeration alone is weaker evidence.
5. **Return and restore regardless of success.** Let the bounded reboot run or
   use the previously proven Power/Normal Boot fallback. In stock Android,
   regain root, restore recovery from the exact source, and verify the full hash.
   Check stock boot completion and expected stock state. Account for possible
   automatic stock recovery restoration on Android startup by reading its hash;
   do not disable that stock mechanism just to preserve the experiment.

This single intervention can answer both modified-ramdisk acceptance and
recovery-only restoration. There is no need to start with a full OS, TWRP,
new kernel, userdata migration, an unlock or BROM/DA writing.

## How to interpret the result

- **Unique marker, normal return, stock recovery hash restored:** this exact
  locked unit can execute a changed recovery ramdisk and the scoped stock return
  is demonstrated. Next, separately consider the same diagnostic with the changed
  kernel. A stock-kernel success does not establish 4.9 execution.
- **Marker, but return/restore fails:** acceptance is proven; recoverability is
  not. Do not expand the test to normal boot or system.
- **Explicit rejection before kernel entry, with verified image readback:** retain
  the exact screen/log and restore stock. This contradicts the permissive-path
  runtime hypothesis for that candidate/entry. It does not prove the entire port
  impossible or justify guessing at seccfg.
- **No marker, unexplained reset or black screen:** inconclusive. Restore stock;
  distinguish header/wrapper/init/USB failure from authorization using captured
  evidence and the unchanged stock kernel. Do not label it a signature failure
  or jump immediately to security changes.

**First parent action:** review the completed diagnostic stock-kernel control
and rerun `scripts/check_evidence.py` using the audit venv. If the control and
reviewed recovery-only restore procedure satisfy the conditions above, perform
that one supervised roundtrip. **CONDITIONAL GO.**
