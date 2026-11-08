# Qualified narrow milestone — not execution approval

2026-11-06. Offline only. No device operation, real socket, metadata write, reboot, or flash performed by this research task.

## Pins and current result

- OEM `/system/bin/uncrypt`: 68,752 bytes, SHA256 `3f7e8c8ed7272540315eaef0af405a57ac701db121dd5c842a8b04be721b2671`; live parent capture byte-identical to prior stock extraction.
- OEM `uncrypt.rc`: 390 bytes, SHA256 `63b33e2a2271d0c598bca842d0e6b03564004ed1e0e2995e8dd8ed5616455e82`.
- Built static AArch64 client `artifacts/clear-bcb-client`: 3,240 bytes, SHA256 `ea4f875e95f6c0b331edbad1817a60b7ce3d8a988516db8ec247ecf801f29630`.
- 15 actual OEM instruction emulation cases passed: `evidence/oem-emulation.json`. External OS/libc calls and fstab text parsing stubbed; actual OEM `/misc` selector, clear dispatch, zero-buffer preparation, writer, write/read loops and result/ack path executed.
- 44 actual compiled client ELF cases passed: `evidence/client-tests.json`. Entire AF_UNIX/syscall peer is a virtual in-memory fixture; no real host/device sockets. Peak RSS 37,896,192 bytes, sequential single-worker tests. `evidence/client-build.json` pins source, toolchain and ELF; `evidence/client-disassembly.txt` is actual instruction-boundary output.

## Exact effect established

`argc=2, argv[1]=--clear-bcb` selects action 2 at `0x3f2c`; accepted socket dispatch branches at `0x4054` to `0x4224`, calls `0x6438`. This clears **0x440 = 1088 bytes**, including the entire OEM bootloader message, not only the changed twenty bytes. Buffer initialization: `0x6454` loads length 0x440, `0x6460` zero value, `0x646c` memset; `0x6478` calls writer `0x64a4`.

Writer rereads `/fstab.${ro.hardware}` and selects `/misc` using actual compiled selector at `0xba58`. Archived OEM `/fstab.mt8163` maps it to `/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/para`. Fstab SHA256 `9f22f786ac2fdbaa10d0d40a7f2a962a3c7008cd22c8c54d4c4454232a6bf46c` (2,187 bytes). The vendor MTD helper at `0x6de0` literally returns 2; no MTD path executes. `open` flags are `0x101001` = O_WRONLY|O_SYNC, no create/truncate/append. No seek: a new descriptor begins at offset 0. WriteFully supplies exactly 1088 zero bytes, then `fsync`, then `close`. Partial writes can leave a prefix altered. Fsync failure can occur after all bytes changed.

Clear does **not** read a command from the client. **Accepting the connection triggers the clear immediately.** It sends network-order 100 (`00 00 00 64`) or -1 (`ff ff ff ff`), then reads a 4-byte acknowledgement. Client sends four zero bytes for either recognized terminal status, then expects EOF. Daemon ignores status-send result and acknowledgement value/failure for its process exit result. There is no reboot, wipe, userdata/p20/cache open, ioctl, or fallback into setup/uncrypt on this selected path, subject to the live fstab/alias gates below.

## Mandatory parent gates before invoking anything

1. Fresh actual full 524288-byte preimage must hash `8d0cf5c87bcb4abe769f7e4dc2000d45827980b6c12fb792af7bbd0d195c0ef9`. The parent receipt `before-capture-ac7cd9c04571db33.json` says two fresh reads match and staging cleanup is verified. Research did not inspect private captures.
2. **Parent must compute, locally and without writing the partition:** `sha256(bytes(1088) + fresh_current[1088:])`. It must equal original `8c9e2c158ac95f152d08ea9de929ae36d054131ca4b10620890974ed831480ef`. Current aggregate only proves other bytes match original; it does not prove original bytes 84..1087 are zero. If candidate differs: STOP, no daemon call, no narrowed/custom/raw writer.
3. Live stock fingerprint, `ro.hardware=mt8163`, live `/fstab.mt8163` byte/hash match, exact rc/binary hashes; `/misc` unique mapping to para. Read-only verify para resolves to `/dev/block/mmcblk0p12`, major:minor 179:12, start sector 225576, size 1024 sectors of 512 bytes. Parent's `read_para.py` guards these identities.
4. Exclusive parent ownership; setup-bcb, uncrypt, clear-bcb all stopped before start, no system update/recovery caller, user nearby. Preserve the prior diagnostic approval/staging; use a new purpose-specific review and receipt. Do not alter SELinux, service definitions, or properties beyond this one known service-start request.
5. Stage and hash-check this exact client under parent control. Parent needs separately reviewed authorization for the metadata-clearing action. Nothing here grants it.

## Smallest intended invocation, only after gates and parent review

- Parent starts known stock init service exactly once: `setprop ctl.start clear-bcb` via already authorized on-demand root.
- Parent bounds the wait for `init.svc.clear-bcb=running` and socket availability. No connect probes. Verify setup-bcb/uncrypt still stopped. Inspect the one daemon's exact cmdline `/system/bin/uncrypt\0--clear-bcb\0`, executable identity and positive PID. The daemon is waiting at accept; starting alone is not the write trigger.
- Parent runs the pinned client exactly once with that daemon PID as its **sole** argument: `.../clear-bcb-client PID`. No commands, paths or partitions are accepted as client inputs. Client hardcodes `/dev/socket/uncrypt`, verifies a nonsymlink socket owned 1000:1000 mode 0600 before connect and unchanged inode after, then SO_PEERCRED PID=expected, UID/GID=0, and exact peer path. Older ASUS 3.18.22 kernel source initializes peer credentials at daemon `listen()`; this is a source reference, not a bit-identical stock 3.18.35 kernel proof. Post-connect checks cannot undo a write already triggered by accept.
- Client finite stages: connect 5s (one attempt), status 10s, ack 2s, EOF 2s; bounded EINTR loops. Parent transport watchdog should be bounded too, without automatic re-execution. Exit 0 means only status100 + ack sent + peer EOF + client close, **not full readback verification**.
- After any outcome, parent verifies daemon stopped, independently captures full para twice using its reader, checks expected old hash, and reconciles. No automatic retry, no reboot/diagnostic continuation on an unknown result. Matching preimage means not cleared; unexpected hash means stop. Matching old postimage proves intended byte restoration, but any transport/fsync anomaly still requires explicit reconciliation and review before continuing.

Remaining smallest parent inputs: candidate full-postimage hash and live fstab/path identity receipt. No Binder transaction number is asserted or guessed.
