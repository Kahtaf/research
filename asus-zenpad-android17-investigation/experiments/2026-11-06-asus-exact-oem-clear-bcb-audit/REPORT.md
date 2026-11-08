# Exact OEM clear-BCB audit

**Qualified narrow mechanism; parent-side gates remain.** The exact captured ASUS `uncrypt --clear-bcb` zeros **1,088 logical bytes at offset 0 of the fstab-selected `/misc` device**, calls `fsync`, and returns status over the init socket. The archived stock fstab selects `para` (p12). This is larger than the twenty-byte stale recovery argument. The action is suitable only if the parent independently proves that this entire zero span reconstructs the required original whole-para hash.

No device operation, actual socket, raw unit read, block-device access, metadata write, root operation, service start, reboot, flash, or approval was performed here. No subagents or active system/kernel/cloud changes. The parent retains all execution and approval authority.

## Exact inputs and provenance

All source snapshots are under `source/oem/`; `evidence/input-pins.json` records original paths and provenance.

| Input | Size | SHA256 / qualification |
|---|---:|---|
| Live OEM `/system/bin/uncrypt` | 68,752 | `3f7e8c8ed7272540315eaef0af405a57ac701db121dd5c842a8b04be721b2671`; identical to prior exact-stock extraction |
| Live `/system/etc/init/uncrypt.rc` | 390 | `63b33e2a2271d0c598bca842d0e6b03564004ed1e0e2995e8dd8ed5616455e82` |
| Archived stock boot `/fstab.mt8163` | 2,187 | `9f22f786ac2fdbaa10d0d40a7f2a962a3c7008cd22c8c54d4c4454232a6bf46c`; live byte/hash verification still required |
| Compiled fixed ARM64 client | 3,240 | `ea4f875e95f6c0b331edbad1817a60b7ce3d8a988516db8ec247ecf801f29630` |

The prior stock build.prop identifies `asus/WW_P00A/P00A_2:7.0/NRD90M/WW_P00A-V5.3.20-20180809:user/release-keys`, with display ID `NRD90M.WW_P00A-V5.3.20-20180809`. Parent supplied the corresponding currently running version. No live property queries were made by this task.

Parent receipt `before-capture-ac7cd9c04571db33.json` reports two 524,288-byte captures both equal to current hash `8d0cf5c87bcb4abe769f7e4dc2000d45827980b6c12fb792af7bbd0d195c0ef9`, staging cleanup verified, no clear requested and no block writes. Its private paths were not followed. The parent's read-only reader source was reviewed, not run: its guards identify p12, 179:12, start 225576, 1024 sectors, 512-byte logical sectors and the para symlink.

No matching OEM C++ source for the shipping uncrypt was asserted. The exact ELF and instruction execution are the decisive evidence. [AOSP Android 7 uncrypt source](https://android.googlesource.com/platform/bootable/recovery/+/android-7.0.0_r1/uncrypt/uncrypt.cpp) (blob `d7105a01f7c9bb352fb842f96a1cb95ee0572ec5`) is only a protocol/source-name reference; it does not establish this OEM binary's write span or a Binder transaction number. Attempts to fetch other generic writer/header references were unavailable and were not used as evidence.

The selected kernel source/header snapshots are from ASUS [Kernel_V4_7_0.zip](https://dlcdnets.asus.com/pub/ASUS/EeePAD/Zenpad/Z380M/Kernel_V4_7_0.zip), archive SHA256 `d8b9d77a7e8b5151c2b68c96e784842a25b167cf8a7044188e7044a5fdbcd41c`. **This is older Linux 3.18.22 source, not proof of the shipping 3.18.35 kernel build.** It supports interpretation of the AArch64 syscall/stat ABI and the `listen()` peer-credential expectation. A differing observed peer is a stop/reconcile condition, never a reason to weaken validation or retry.

## Exact instruction evidence

Addresses below are ELF virtual addresses, before runtime PIE load bias. `evidence/uncrypt-annotated.txt` includes instruction bytes, instruction boundaries, imported-call resolution from `.rela.plt`, and resolved literals. `evidence/oem-emulation.json` records executed PCs and each declared stub per case.

| Stage | Exact address evidence | Established behavior |
|---|---|---|
| Select clear | `0x3ec4–0x3f34`, especially `0x3eec`, `0x3f2c–0x3f30` | Exactly two argv entries and strcmp of `--clear-bcb` select action 2. Setup is action 1; uncrypt is action 0. |
| Initial fstab read | `0x3f34–0x3f8c` | `/fstab.` + `ro.hardware`, parsed by embedded `fs_mgr_read_fstab` at `0xb004`. Failure exits before accept. |
| Init socket | `0x3f98–0x4048` | Reads inherited `ANDROID_SOCKET_uncrypt`, sets FD_CLOEXEC, `listen(fd,1)`, one `accept4(...,SOCK_CLOEXEC)`. There is no daemon-level accept retry loop here. |
| Dispatch | `0x4050–0x4060`, `0x4224–0x4260` | Action 2 branches directly to clear, bypassing setup's length/command reads and uncrypt package processing. |
| Zero buffer | `0x6438–0x649c` | `w2=0x440` at `0x6454`, `w1=0` at `0x6460`, memset at `0x646c`; passes the entire buffer to writer at `0x6478`. |
| Resolve write path | `0x64a4–0x680c`, `0xba58–0xbb14` | Independently rereads `/fstab.${ro.hardware}`. Actual selector checks mount-point prefix and next slash/NUL boundary, returns first match. Writer takes `fstab_rec.blk_device` at offset 0; record stride 0x60, mountpoint at +8. |
| MTD dispatch | `0x680c–0x6884`, `0x6de0–0x6de4` | Vendor MTD function is exactly `mov w0,#2; ret`; always falls through to direct descriptor writer. No MTD erase/alternate write. |
| Open/write | `0x6884–0x68c0` | Flags `0x101001` (O_WRONLY | O_SYNC), no create/truncate/append. New fd's position is zero; no lseek/pwrite. `WriteFully(fd,zero_buffer,0x440)` at `0x68b8`. |
| Write loop | `0x7054–0x70cc` | Actual libc write attempts handle short writes by advancing pointer/remaining count; EINTR retries internally. Other errors return false. A zero-byte write would loop without progress: OEM has no deadline. |
| Durability/result | `0x68c4–0x68d8`, `0x69dc–0x6a98` | Calls `fsync` after complete write. `-1` means failure, even after bytes changed. Calls close; ignores close result. Returns boolean. |
| Status | `0x404c`, `0x4248–0x4260`, `0x4318–0x4334` | Network bytes `00 00 00 64` on success; `ff ff ff ff` on failure. Status-send return is ignored; real signal termination (for example SIGPIPE) is not modeled by the failure-return stub. |
| Ack and exit | `0x4ca4–0x4d1c`, read loop `0x6fcc–0x7050` | Reads four bytes, logs received native integer without validation, or logs read failure; closes accepted/listening fds. Exit code depends on clear result, not status/ack success. |

The actual archived fstab contains this entry:

```
/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/para /misc emmc defaults defaults
```

The writer does not use the `emmc` string as an independent safety check. Correct live fstab bytes and alias identity are essential: a changed fstab/alias could redirect the write. No OEM guard verifies partition size or the supplied preimage/postimage hash.

The full parser was also executed, not merely replaced with a hand-constructed record. It parses both fstab reads using the exact public text. While parsing `/data`'s `forceencrypt` flag, it opens `/sys/class/BOOT/BOOT/boot/boot_mode` read-only (`0x88000`) and reads up to three bytes. This only adjusts in-memory parser flags. With the exact stock fstab there is no `slotselect`; the slot-suffix rewrite branch is bypassed. The parser does not open userdata, its metadata/key location, or cache. The in-memory forceencrypt path string is not used for any data/key I/O in this operation.

## Logical write extent and exclusions

Successful logical write extent is precisely `[0,1088)`, all zero. `[1088,524288)` is not supplied to any write. This includes the 32-byte command, 32-byte status, the pending recovery argument, and the remainder of the OEM message buffer. It is **not** a 20-byte targeted clear, a 2 KiB generic BCB clear, or a whole-partition restore.

At block-layer/flash level this is not an atomic twenty-byte change: the span crosses sectors, writes may be split, and an I/O failure can leave a prefix changed. Physical flash write amplification is outside the logical-byte claim. Full independent post-readback is required.

For pinned clear argv plus pinned live fstab/alias, the reachable path has no factory-reset invocation, formatting, discard ioctl, user-data decryption, setup command read, package processing, property setter, or reboot call. `/data`, p20 metadata, and cache appear only as parsed fstab strings or unused constructor strings; there is no read/write of their block devices. The clear operation does not remove `/cache/recovery/command`; any existing cache-request condition remains the parent's independent diagnostic preflight concern. Logging may use normal platform log IPC in the real daemon; the offline emulator stubs logging and opens no socket.

## Verification and limits

`source/emulate_oem.py` runs original instructions with fixed synthetic memory. Sixteen cases passed: success, short writes, EINTR, open failure, total/partial write failure, fsync failure, status-send failure, ack EOF, arbitrary ack value, close failure, initial/writer fstab failure, missing misc, missing hardware, and full real OEM fstab parser success. The first fifteen stub fstab parsing with records from the archived text; the sixteenth executes both embedded parser and selector. All libc/OS operations are declared stubs; error-message formatting helpers are additionally stubbed for injected failures. No kernel/filesystem durability, live scheduling, SELinux access or real IPC success is claimed.

`source/test_client.py` executes the genuinely compiled static ARM64 ELF with a virtual AF_UNIX peer. Forty-four cases passed: normal/failure status, fragmented I/O, EINTR/EAGAIN/deadlines, wrong-endian/unexpected/short status, credential/path/inode/mode errors, ack failures, extra data, EOF timeout, bad arguments, and one-connect-only behavior. Unlisted syscalls fail the fixture, including block opens, command execution, properties and reboot. No Python socket or actual UNIX socket is created. `evidence/client-tests.json` records binary hash, exit codes, allowed syscall observations and measured peak RSS.

Build uses existing `/usr/bin/clang` plus pinned existing Rust `rust-lld`, one compilation then one link, no installs or Ninja. Existing Capstone/Unicorn virtualenv is reused read-only with bytecode writes disabled. Tests are sequential, one emulated CPU, one process, 45-second CPU limit per test program and bounded instruction/time budgets. Peak measured RSS is far below 1 GiB (client 37,896,192 bytes; OEM value in its receipt). macOS rejected address/data/RSS setrlimit requests; no hard 1 GiB address-space enforcement is claimed. Synthetic mapped memory is small and measured RSS is checked against the requested ceiling.

No Binder transaction mapping was established from compiled OEM framework code. `service check recovery` proves existence only. There is no `service call recovery 3` advice. The fixed stock service plus client is the chosen bounded route, per the parent's timing instruction.

## Smallest remaining evidence

Parent should provide only aggregates: (1) `sha256(bytes(1088)+fresh_current[1088:])` equals `8c9e2c158ac95f152d08ea9de929ae36d054131ca4b10620890974ed831480ef`, and (2) current public software/fstab/alias identity gates match. `source/predict_postimage.py` is a pure parent-side calculation with no file or device operations. Research does not need raw bytes.

If the candidate differs, the OEM operation is not qualified for this request: stop rather than narrow the writer, restore a partition, or factory reset. The parent's reviewed one-shot procedure and reconciliation rules are in [PARENT-PROCEDURE.md](PARENT-PROCEDURE.md). This research does not execute or approve it.
