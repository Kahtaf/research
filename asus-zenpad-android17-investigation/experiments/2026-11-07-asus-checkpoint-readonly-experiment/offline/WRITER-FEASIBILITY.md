# Stock writer feasibility gate

2026-11-07, offline only. **No acceptable user-facing setter for fiq_step or another chosen retained scalar was established. Stop before that physical experiment.** Internal setter presence is insufficient. A separate console-text calibration has a concrete stock implementation path, but its live prerequisites remain unverified here.

| Mechanism | Result | Reason |
|---|---|---|
| Write `/proc/aed/reboot-reason` | FAIL | Reference fops contain open/read/llseek/release only; creation mode 0444. Shipped `aee_rr_proc_init` passes 0x124 (=0444) to proc_create_data. It exposes the saved diagnostic, not a setter. |
| Call fiq setter via ordinary AEE controls | NOT ESTABLISHED | Shipped setter exists, but all 21 aligned direct branches to it classify as `aee_stop_nested_panic`, `aee_wdt_dump_info`, `aee_wdt_atf_info`, `ipanic`, or `ipanic_die`. Reference caller paths agree. These are panic/watchdog paths, outside this experiment. |
| Ordinary reboot sets an identifiable fiq marker | NOT ESTABLISHED | No normal-reboot caller to fiq setter found. Kernel-owned initialized zero is not a unique chosen marker; a repeat saved zero would not calibrate retention. |
| Ordinary reboot sets saved reboot_mode | NOT ESTABLISHED | Shipped `aee_rr_rec_reboot_mode` exists, but the exact direct-branch scan found no callers. Reference source search finds definition/declarations, not a normal-reboot writer. Indirect calls/inlining cannot be ruled out by this scan, so no claimed exhaustive absence. |
| AEE debug proc controls | REJECTED | generate-oops/nested-ke/wdt intentionally invoke excluded failure paths. generate-kernel-notify dispatches reminders/warnings/exceptions to AEE; it is not a chosen fiq-field API and has other diagnostic/UI/reporting behavior. AEE device writes exchange report requests, not a retained-scalar setter. No state-changing diagnostic control is proposed. |
| `/dev/mem`, module or patch route | OUT OF SCOPE | Parent's symbol gate does not establish devmem implementation. No node creation, module loading/ABI work, bypass, patch or memory write is proposed. |
| Existing `/dev/kmsg` -> retained console text | CONDITIONAL ALTERNATIVE | Concrete public source and shipped writer/reader path below. This exercises a Linux-owned console ring, **not fiq_step or reason-record preservation**. Live availability, permissions, console admission and retention are still prerequisites. |

## Binary corroboration and scope

`writer_check.py` reads the same public original.img and pure existing kallsyms decoder as the preceding contract check. Exact original.img SHA-256 is `f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140`; decompressed shipped Image SHA-256 is `db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a`.

`writer-abi.json` records exact symbols and direct call locations. `writer-abi.disasm` records bytes and hashes of the few endpoint/write/read/restart functions. The direct-branch scan checks aligned words against the exact setter targets; it cannot exclude indirect invocation and may interpret data as instructions. Its actual matches classify into the source-supported failure functions above. This is a bounded feasibility check, not a full kernel audit. Public reference is 3.18.22 and shipped binary 3.18.35; endpoint conclusions distinguish source from shipped proof.

Normal restart functions examined: `kernel_restart` 0xffffffc0000c0e44, `machine_restart` 0xffffffc0000863dc, `arch_reset` 0xffffffc000800138 and `mtk_wdt_restart` 0xffffffc000800914. No chosen retained Linux scalar setter was established. Reboot-command branches involving RTC/recovery/bootloader flags do not provide the desired Linux-owned-field identity and are not proposed as substitutes.

## Smallest legitimate alternative and prerequisite

Use the existing stock text logging path **only after confirming live prerequisites read-only**. The concrete path is:

1. Existing `/dev/kmsg` writer: reference `drivers/char/mem.c` dispatches character minor 11 to `kmsg_fops`; `kernel/printk/printk.c` gives it devkmsg_write. Shipped `devkmsg_write` at 0xffffffc0000ed718 calls shipped `printk_emit` at instruction 0xffffffc0000ed7c4. It accepts a short caller-chosen text line through the normal logging API. Its prefix handling preserves a userspace facility, so this is an injected user log record, not a forged kernel-origin event.
2. Existing registered RAM console: reference ram_console has CON_PRINTBUFFER|CON_ENABLED|CON_ANYTIME, callback ram_console_write. Shipped early initializer registers it (previous `stock-fiq.disasm`). Shipped ram_console_write 0xffffffc000697478 calls sram_log_save at 0xffffffc0006974b8; shipped sram_log_save 0xffffffc000697340 updates the current ring. A FIQ guard or disabled/filtered console can prevent delivery.
3. Next stock saved reader: shipped ram_console_show 0xffffffc000697190 loads saved pointer global +8, validates header/layout and emits ring contents via seq_write. Shipped ram_console_late_init creates the read-only last_kmsg proc endpoint. The earlier contract check establishes snapshot-before-current-clear ordering.

Prerequisites: stock actually exposes accessible `/proc/last_kmsg` and existing writable `/dev/kmsg`; the ram console is registered/enabled; current console filtering admits the intended message level without changing settings; read-only inspection identifies the exact console and reader; and the pre-reboot log can independently show the fresh unique marker was accepted. Do not create device nodes, relax permissions/security, or toggle diagnostic modes to satisfy these prerequisites.

If those prerequisites hold, the smallest separate calibration is one short unique text record through that existing API, confirm its current log identity, one ordinary stock reboot, and exact-text search in the next saved last_kmsg snapshot. No kernel/module change is required. Do not prepare or execute it based on this offline report alone. A bounded record should be recent enough to avoid ordinary ring overwrite; successful current printk acceptance alone still does not prove that RAM-console bytes reached reset-stable storage. If the saved record is absent, report inconclusive: filtering, console disablement, ring wrap, header rejection, reset preservation or save/read failure remain possible. A successful record calibrates this stock text path and that reset only; it does not establish fiq scalar retention or any 4.9 execution.

If the existing stock text reader/writer or required admission evidence is unavailable, stop: the smallest prerequisite becomes a supported diagnostic interface or separately authorized instrumented kernel that exposes a bounded kernel-owned marker API and readback. That is a different experiment, not a module-force-load or arbitrary-memory fallback.

All previous offline outputs were preserved. Only new feasibility report/script/evidence files were written locally. No device, private file, network, SSH, VM, build, reboot or kernel/RAM mutation occurred.
