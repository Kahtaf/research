# Earlier generic watchdog registration candidate

Question: do exact source prerequisites and actual ELF initcalls support registering the existing generic MediaTek watchdog driver earlier?

Status: **one single-file candidate, one actual kernel build (exit 0), one package, one isolated PLAN (exit 0). No installation or reboot.** Source and compiled-order evidence support this handoff candidate. Runtime probe timing and watchdog reset causality remain unproved.

Only `drivers/watchdog/mtk_wdt.c` changes. The `module_platform_driver` macro is expanded into its equivalent `mtk_wdt_driver_init`/`mtk_wdt_driver_exit` wrappers, with the init wrapper using `arch_initcall`. Module builds retain `module_init` behavior through the existing module.h mapping; `module_exit` is retained. Driver, probe, stop/start/restart, nowayout, unregister and every register-handling body are unchanged. [Exact patch](source/watchdog-initcall.patch), [before](source/mtk_wdt.before.c), [after](source/mtk_wdt.after.c).

Patch SHA256 `8c4aa7b6ffad2d7a2d4ccbbad4e3705854b09c0b9ae08d83934e008575927989`. Source before SHA256 `b4650c1d087bc2ef4e0e4161afc9dd54cb38901e98af16a1b2fc2e784f1d927b`; after SHA256 `d215d7e458eed74b98e0d165d753db4a41712051a0f6a258616b45761cff1320`.

Exact baseline source establishes these prerequisites:

- `do_basic_setup()` calls `driver_init()` before `do_initcalls()`; `driver_init()` initializes the platform bus.
- Default OF platform population runs at `arch_initcall_sync`, level 3s. The exact baseline DT contains `/soc/toprgu@10007000`, compatible with the generic driver's `mediatek,mt6589-wdt` binding. Earlier registration can bind as devices appear.
- Watchdog core explicitly supports early drivers using a statically initialized deferred registration list/mutex. `watchdog_register_device()` queues before core initialization; `watchdog_init()` initializes the device layer and drains the list at `subsys_initcall_sync`, level 4s.
- The active generic probe maps its DT resource, has no active IRQ request or clock-get dependency, and on this ASUS configuration (`DOUGLAS=n`, `GIZA=n`) calls the existing `mtk_wdt_stop()` before watchdog registration. That behavior is preserved.

See [source gate](evidence/source-gate.json) and [exact baseline source evidence](evidence/baseline-source-inspection.txt). Stock `core_initcall(mtk_wdt_get_base_addr)` only maps; this work makes no claim that stock stops the watchdog there.

Actual ELF evidence reads the 64-bit initcall pointers through ELF PT_LOAD mappings and checks level boundaries, rather than inferring order solely from macros. Baseline entry `__initcall_mtk_wdt_driver_init6` at `0xffffff8008f6d820` points to `0xffffff8008f2d94c`. The compiled candidate has only `__initcall_mtk_wdt_driver_init3`, at `0xffffff8008f6cc30`, pointing to that same function address. Candidate DT population entry is `0xffffff8008f6cc40` (3s); core watchdog entry is `0xffffff8008f6ce70` (4s). No old late watchdog entry remains. [Baseline table receipt](evidence/baseline-initcalls.json), [compiled table receipt](evidence/compiled-initcalls.json).

Actual outputs, all SHA256:

- [Image.gz-dtb](artifacts/Image.gz-dtb): 7711225 bytes, `a49b87313d35d803e3ffaa2be2c60a3c678ccbc46efd5831651d2bd44ae4ee03`.
- [Resolved config](artifacts/resolved.config): 126443 bytes, `708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1`; byte-identical to baseline, no config delta.
- [Candidate](artifacts/candidate.img): 7970816 bytes, `c83a4465dd209d7c2979b7b156e9d5bd8f350d81f121fa29e51579871e3a2cb4`.
- Full p10: 16740352 bytes, `81bc90ed8f8c25a291c8ffca205de94a0188b5cbab37379b3f667ad1ac42ba2d`. Saved/read-back hash verified on VM at `/srv/android/asus-early-watchdog-handoff-20261107/artifacts/candidate.p10.raw`; installer creates identical zero padding locally.
- [Installer](source/install.py): `9c4ef4eb43ad8a4f6de678479551afba2576064b7221dfe75b6f6034bd22f158`. [Minimal installer diff](source/install.diff).

Source was independently copied using `cp -a`, with selected independent inodes verified, a fresh out directory and fresh TMPDIR. Selected baseline hashes were preserved; there was no full-tree rehash. Only the generic watchdog source was edited. The logger remains `8373baa301650d2bf3befe547df11a3079e22c51aec8a207de64eae0f1bb3348`. The exact entire config preserves disabled `SERIAL_8250_CONSOLE`, `SERIAL_EARLYCON`, `SERIAL_CORE_CONSOLE`, and `SERIAL_8250_FSL`; normal 8250/MT6577 remain. Actual linked assertions confirm early UART symbols and `8250_early.o` remain absent.

One `make -j8 Image.gz-dtb` used `aarch64-linux-gnu-`, `LOCALVERSION=-g717bb3c9e13c-dirty`, unlimited RLIMIT_AS and no supervisor timeout. It exited 0 with no source fix/rebuild. Release remains `4.9.337-asus-p00a-experimental-g717bb3c9e13c-dirty`. Full source, out, and build log stay under `/srv/android/asus-early-watchdog-handoff-20261107`. Small actual build/config/receipt fetch totaled 7897542 bytes, below 32 MiB. [Build status](evidence/build-status.json), [build receipt](evidence/build-receipt.json), [input preservation](evidence/input-preservation.json), [log summary](evidence/log-summary.json).

Packaging uses the exact ramdisk from candidate `8298badb09d9e91ee584eb6e27baf2054e660bbc5640443e9212f484f6fd590b`: 255651 bytes, SHA256 `51e6d1dc0acb742522c69b29355d2d77d8ba73a3597fb8ad3354fa9f0c494e49`. Static init remains 597856 bytes, SHA256 `d081c46dcf40684b35ec5f16bb4238b60662dd857a7211d46241e98f96ac872b`. No C compilation. Existing SIGALRM/monotonic 60-second lifecycle, run `9342cbf1-3bf0-44d4-b655-a1ca30146a99`, serial `P499342cbf13bf044d4b655`, VID:PID `0b05:4a49`, and product `ASUS-PID1:<actual uname.release>` are byte-preserved.

The actual compiled gzip and raw Image are preserved. Compiled DT bytes equal baseline; only inherited chosen metadata is applied, yielding exactly the existing USB reporter's packaged DT. Initrd is `0x44000000..0x4403e4a3`, excluding the 512-byte wrapper. Header/chosen arguments remain `androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1`. Header changes only kernel size and required ID; kernel wrapper changes only payload length. [Packaging receipt](evidence/packaging-receipt.json), [VM actual readback](evidence/remote-package-readback.json).

Installer specialization updates actual hashes/profile (actual image length remains 7970816) and appends only observed full-p10 preimage `c1fe664108ee8e2ef24edc9f0b3249589dc227f0ee8502b63e224930ee7fa541`; all existing preimages remain. `execute()`, `Transport`, `Guard`, and legacy adapters are byte-identical to the current UART-fixed USB reporter installer. The append uses the supplied public observation for parent run `ffcb0e5d-a976-4723-9f17-133910fb75d9`.

Exactly one isolated actual installer `main()` PLAN passed. It replaced the private stock reader in memory with the pinned public current USB candidate for geometry checks and replaced source dependency checking with an in-memory no-op to avoid root-helper reads. An audit hook blocked private/device/root-helper opens, sockets and subprocesses. Delivered guards are unchanged. Private stock backups and root dependency hashes were **not** validated. [PLAN output](evidence/install-plan.json), [isolation receipt](evidence/plan-isolation-receipt.json). No `--execute` was run.

Continuation: root owns fresh USB identity absence checks and any separately authorized installation/trial. **User-nearby availability for Power fallback is PENDING.** Confirm that availability before any future physical trial. Automatic return is unproved: the earlier estimated 32.906–32.963 seconds versus nominal PID1 60 seconds does not identify a watchdog cause and may involve timebase or intentional return. No offline approval, physical GO, or fullOS GO is granted here. Keep BOOT/SYSTEM/DATA untouched. Do not rerun prepare/build/package/PLAN scripts; existing attempts are refused.

No subagents, device/card/ADB/root-helper/private-input access, cloud lifecycle/labels/disks/process operations, other-owner source/out changes, or AOSP mutation occurred. No broad suites, QEMU, independent reviews, or review loops. [Consolidated receipt](evidence/RECEIPT.json). `SHA256SUMS` pins local deliverables.
