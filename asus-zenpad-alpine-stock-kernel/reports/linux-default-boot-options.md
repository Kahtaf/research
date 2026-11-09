# Linux default boot using the recovery slot

Status: offline analysis of the exact saved stock LK, 2026-11-08. No tablet operation, bootloader change or BCB mutation was performed by this investigation.

## Result

**The exact saved LK supports a `boot-recovery` command at byte 0 of para’s BCB on its ordinary boot-selection path. The command reader does not clear or rewrite it.** This is a strong basis for a reversible Linux default while leaving stock BOOT unchanged. Persistence over a real ordinary reboot and power-on remains a physical qualification gate; it has not been demonstrated by this read-only task.

Use a NUL-terminated `boot-recovery` in the 32-byte command field, with the recovery argument field empty. No `recovery` arguments or wipe request is needed by the reader. Do not use the old stale BCB snapshot as rollback.

## Exact binary evidence

The retained public LK is 418,048 bytes, SHA256 `c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765`. The independently saved 524,288-byte live LK partition is SHA256 `65b7783ea392334f530fe43a341415abf9a2b00358bd73697f940f5df287f348`: its entire public-image prefix is equal, with only zero padding after it. The existing earlier live/official receipt agrees. Identity was rechecked offline in this task.

Runtime base is `0x41e00000`; file offset = address − base + 512. Addresses below refer to that exact binary, not generic Android code. Generated disassembly includes literal pools decoded as instructions; only the manually followed paths below support the conclusions.

| Address | Verified behavior |
|---|---|
| `0x41e031a8` | Startup calls boot-selection function `0x41e03b70`. |
| `0x41e03bd0` | In ordinary selection after earlier special-mode checks, calls `0x41e06024`; nonzero returns immediately, preserving the selected mode. A preceding RTC-recovery check can also select mode 2 separately. |
| `0x41e06024–0x41e06030` | Wrapper calls BCB checker `0x41e05c20` and returns Boolean success. |
| `0x41e05c20–0x41e05c4a` | Allocates 0x1800 bytes; calls the misc/para reader; copies the first 0x440 bytes to a local buffer and frees the read buffer. |
| `0x41e04bec–0x41e04c10`, `0x41e04b1c–0x41e04b86` | Reader resolves string `para` and reads from partition-relative offset zero. |
| `0x41e05c4e–0x41e05c58` | `strcmp` of the beginning of that local BCB buffer against `boot-recovery` at `0x41e423d8`. Full string equality is required. `strcmp` itself was decoded at `0x41e25bf4`. |
| `0x41e05c5a–0x41e05c6a` | On match, stores 2 to RAM boot mode through pointer slot `0x41e652f4` → `0x41e68500`, returns 1. No write-to-para call, command clearing or mutation of the BCB occurs in this function or its wrapper. |
| `0x41e1de74`, table `0x41e1de78` | Boot-image dispatch uses a halfword table. Entry 2 computes `0x41e1e006`. |
| `0x41e1e006–0x41e1e058` | Supplies string `recovery` to the recovery header/payload loaders and rejoins normal handoff. Earlier exact-LK acceptance report traces this path further. |

The command-match path does not inspect the recovery arguments. It does not invoke the menu’s BCB writer. This means `boot-recovery` with empty arguments is distinct from the stale `recovery\n--wipe_data` request cleared earlier.

A **separate physical boot-menu branch** at `0x41e062c2–0x41e06310` zeroes a 0x440-byte local BCB, formats `recovery\n--wipe_data` at offset 64, and calls para writer `0x41e06034`. This precisely explains why a stale wipe argument can exist even with an empty command. Do not use that menu path as an assumed harmless way to make Linux default.

## Consumption and remaining uncertainty

The exact BCB reader and its immediate caller unequivocally leave the on-disk command untouched. Static analysis of this path therefore predicts that `boot-recovery` remains effective on later normal boots as long as the OS does not clear it. This task has not exhaustively proven that every unrelated LK descendant, platform reset condition or future OS version never changes para. A post-boot read and second ordinary reboot distinguish persistence cheaply.

The currently inspected project scripts contain BCB operations in preflight/deployment utilities; none of the reviewed Alpine runtime startup paths implements stock recovery’s normal BCB clearing. Inspect the exact deployed startup script again before the test, because the parent is actively changing it.

Supporting stock 3.18 source `drivers/watchdog/mediatek/wdk/wd_api.c:573–574` marks recovery in RTC on `reboot("recovery")`; `drivers/misc/mediatek/rtc/mtk_rtc_common.c:345–352` sets `RTC_FAC_RESET`. This is a separate reboot-reason mechanism. Source alone does not identify the exact compiled running function, and a successful `adb reboot recovery` does not qualify a persistent BCB default. No 4.9 behavior is used as evidence here.

## Smallest bounded physical experiment

Before a mutation, parent should verify the recovery capsule boots and provides authenticated LAN/USB control and a working stock-return action. Save the fresh first 2048 BCB bytes privately. Verify para still resolves to p12 and the pinned geometry; verify command and the relevant recovery argument bytes are empty. The retained cleaned 2048-byte baseline is entirely zero and has SHA256 `e5a00aa9991ac8a5ee3109844d84a55583bd20572ad3ffcd42792f3c36b183ad`; compare fresh state, rather than blindly writing a historical block.

The candidate change is **only command bytes 0–31**: ASCII `boot-recovery`, followed by NUL padding. Preserve every other byte. Keep recovery arguments empty; never add `--wipe_data`. Read back the complete 2048-byte BCB and prove that only the command field differs before an ordinary reboot.

Predicted positive: an ordinary reboot, without the `recovery` reboot reason, enters this known Linux recovery capsule; a fresh BCB read still has the command; a second ordinary reboot returns to Linux and retains a real SD-written service marker. A later power-off/on qualifies cold power-on separately. Predicted negative: normal Android boot, cleared BCB or lost Linux control. Read the BCB before inventing variants. Do not combine the first test with a capsule redesign or bootloader mutation.

## Exact rollback to stock normal boot

From authenticated Linux root, or stock Android root if already there, identify para by the already pinned partition map. Read its first 2048 bytes; verify that the only intentional default-selection change was the known 32-byte command. **Clear those 32 command bytes to zero and leave the rest unchanged**, after verifying the recovery argument area is still empty. Sync and read back; prove command is empty and no wipe arguments exist. Perform an ordinary reboot without a `recovery` reboot argument. Stock BOOT then remains the normal path, because BOOT has not been replaced.

If recovery arguments have changed, do not restore the original pre-cleanup snapshot: it contains the stale wipe request. Reconcile against the clean snapshot first. If an entire 2048-byte clean restore is proposed, it must be guarded by a fresh exact preimage comparison so unrelated new fields are not silently overwritten.

Clearing BCB restores ordinary Android selection; it does not restore the original recovery image. Restoring stock recovery is a separate already-backed-up action using the original image hash `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`. Never restore stock recovery while leaving `boot-recovery` or wipe arguments active. No LK, preloader, GPT, seccfg/security record or factory calibration change is needed for this approach.

## Reproduction and retained evidence

- `evidence/boot-control/exact-lk-identity.json`: fresh offline identity/pointer/table checks, no private payload.
- `evidence/boot-control/lk-recovery-disassembly.txt`: bounded decoding from pinned LK.
- `evidence/boot-control/lk-recovery-call-candidates.json`: string-reference leads; candidates alone are not semantic proof.
- `scripts/trace_lk_recovery.py`, `scripts/disassemble_lk_recovery.py`: read-only local analyzers; run with the retained boot-access-audit `.venv/bin/python` for Capstone. They write only evidence in this spike.
- `../2026-11-06-asus-custom-boot-path/evidence/lk-acceptance-review.md`: earlier exact-LK mode-2 image-loading and handoff analysis.
