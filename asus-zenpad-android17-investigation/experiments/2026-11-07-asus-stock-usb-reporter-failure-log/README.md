# Stock USB reporter: one failure-logging revision

Question: Which existing reporter operation fails on one subsequent stock-kernel
boot after the exact stock control reached PID1 and attached the RAM-file path
but produced no observed USB descriptor?

Status: packaged locally; essential static source/ELF/package preservation check
passed; one isolated installer PLAN passed. **No physical or fullOS GO.** The
parent owns all fresh device checks, installation, recovery entry, observation,
return, and retained-log collection. This spike performed no device access,
private/calibration reads, installation, reboot, kernel edits/builds, active
Android-build inspection, cloud lifecycle actions, broad tests, or delegation.

## Basis

Only the public
[`physical-result.json`](../2026-11-07-asus-stock-exact-usb-reporter-trial/evidence/physical-result.json)
and parent-supplied observations were used: stock 3.18.35, initramfs unpack
248K, PID1 execution around 2.115s, Mass Storage Function initialization around
2.121s, `/ram/probe.img` attachment request around 2.1216s, reboot around
70.9046s, and normal Android return. The raw private retained log was not read.
The exact failure remains unknown. These observations do not establish EBUSY,
nonexecution, or a kernel cause. No concrete preexisting source bug was
established by this limited preservation check; no functional fix was applied.

## Outputs and SHA-256

| Output | Bytes | SHA-256 |
| --- | ---: | --- |
| [`candidate.img`](artifacts/candidate.img) | 7741440 | `cd3cf35840129247e93b7df899d8948d811745c48e156935f9bcdd937dee0dd2` |
| [`candidate.p10.raw`](artifacts/candidate.p10.raw) | 16740352 | `a647247d220a0a33fc23ee125744847b836f20908539d9f150054aa20f1ce20d` |
| [`init`](artifacts/init) | 597888 | `f410df21053fcac5f418c7d64749f19bae7921e5cc13f5c37fe5f9e99268752d` |
| [`init.c`](source/init.c) | 13725 | `c559ab35f75761bcd7a4e9c96154d2ee99453d80d9d3222fbe85d3d1cef86895` |

Important evidence:

- [`init.diff`](source/init.diff): exact delta from the requested existing C.
- [`packaging-receipt.json`](evidence/packaging-receipt.json): hashes, preservation assertions, exact changed offsets, and limitations.
- [`install.diff`](source/install.diff): only five substitutions from the current stock-control installer.
- [`install-plan.json`](evidence/install-plan.json) and [`plan-isolation-receipt.json`](evidence/plan-isolation-receipt.json): one actual installer `main()` PLAN, no transport calls.
- [`build-log.json`](evidence/build-log.json): successful corrected compile, no warnings/errors.
- [`compile-1-build-log.json`](evidence/compile-1-build-log.json), [`compile-1-init.c`](evidence/compile-1-init.c), and [`compile-1-attempt.json`](evidence/compile-1-attempt.json): preserved first failure.

## Exact implementation delta

The sole reporter revision adds bounded stage/error logging with fixed marker
`ASUS-RAM-FAILLOG-20261107-R1`. After arming the existing watchdog and establishing
its existing monotonic deadline, it creates `/reporter-kmsg` as a character node
major 1, minor 11 on the initial RAM root, opens it
`WRONLY|CLOEXEC|NOFOLLOW|NONBLOCK`, and unlinks the node. The descriptor remains
open through the original `/dev` tmpfs mount with `MS_NODEV`. No device node is
opened from that mounted `/dev`, and no persistent mount or file is added.

Records cover entry, the four public actual-uname fields (`sysname`, `release`,
`version`, `machine`), setup milestones, failing syscall operation and path,
numeric syscall errno, guard/comparison failure, setup return, disable, deadline
reboot and SIGALRM reboot. `put` distinguishes open/write/short-write/close;
`equals` distinguishes open/read/bound/close/mismatch. No actual UDC name,
attribute readback, device identity, calibration, hostname, domainname, or private
value is logged. Guard failures and successful short I/O use errno 0 because
they have no failing syscall errno. `clock_nanosleep` logs its returned error
number. Logging preserves the interrupted operation's errno.

Normal logging has at most 64 records of at most 511 bytes each. The SIGALRM
handler adds at most two records of at most 160 bytes each, uses only bounded
local formatting/arithmetic and `write`, and keeps the existing nonreturning
pause path if reboot returns. Logging performs no write retries. An 8192-byte
RAM fallback records unavailable-sink errors; signal-path sink errno is held in
RAM. If the kernel-log sink cannot open or accept writes, RAM-only failure
evidence cannot survive reboot. The parent trial must establish actual marker
retention through stock `/proc/last_kmsg`; static checks cannot prove it.

All 40 original setup operations retain their arguments and order. Original
short-circuit guards, fresh-gadget requirement, RAM-file checks, read-only-before-
attachment/binding order, sole mass-storage function, unique-UDC policy (including
its existing bounded absence wait), FAT construction/report bytes for the same
uname, exact USB identity, nominal 60-second watchdog/deadline, and disable/reboot
behavior are retained. No legacy gadget disabling, UDC takeover, extra retry,
extra USB function, block access, or speculative repair was added.

## Exact package and installer delta

The pinned public stock image is
`2026-11-07-asus-stock-kernel-version-control/artifacts/original.img`, SHA-256
`f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140`.
Its raw Image, original gzip stream, 512-byte kernel wrapper, kernel length,
Android header load addresses/page/arguments, and every hardware DT property are
byte-preserved. No 4.9 command line or kernel source is imported.

The six initramfs entries remain `init`, `dev`, `ram`, `proc`, `sys`, `config`;
only `init` content changes. The compressed initrd payload is **258055 bytes
(`0x03f007`)**, excluding its 512-byte wrapper. The wrapped ramdisk is 258567
bytes, up 2916 from the stock reporter control. The DT `/chosen/bootargs`
initrd-length token changes from control `initrd=0x44000200,0x03e4a3` to
`initrd=0x44000200,0x03f007`; payload end-exclusive is `0x4403f207`. No
`linux,initrd-start/end` properties are added. Exactly four bytes of the wrapped
kernel change against the control, at offsets 7470023–7470026, solely within that
length token. The kernel wrapper and all DT offsets/lengths remain exact.

Other package changes are required ramdisk-wrapper payload length, Android
ramdisk size/header ID, replacement gzip/cpio/init content, and zero alignment
padding. The candidate grows 4096 bytes from the control; full p10 stays
16740352 bytes. Exact offsets and before/after hashes are in the receipt.

[`source/install.py`](source/install.py) specializes the current stock control
only in candidate SHA, full-p10 SHA, exact image length, profile, and appending
the parent-reported current preimage
`039c5a52d9ac04fd515c2081c455066057d1503d6979fc81a5b2c70712bc7dba`.
`execute`, `Transport`, `Guard`, all other installer text, `adb`, and
`legacy_adb.py` remain byte-identical. That supplied current hash was not freshly
observed by this spike.

## Build and limited verification

The first permitted serial static AArch64 compile failed because this builder's
`-Werror` rejects three ignored logging `write()` results even with `(void)`
casts. The user explicitly authorized one corrected compile. Those logging
results are now consumed and failed signal-path writes retain their errno in
RAM. The second compile succeeded without diagnostics. Both attempts used the
fixed SSH definition from the requested build kit, each in a fresh owned
`/srv/android/2026-11-07-asus-stock-usb-reporter-failure-log-*` prefix. Only this
helper was compiled. Each compile used one CPU, nice +10, 512MiB address-space
limit, 90s CPU/compiler timeout, 32MiB per-file limit, no core dumps, and under
64MiB owned files. No process-count caps or other-job actions were used.

The one essential combined check in [`scripts/build.py`](scripts/build.py)
validated source preservation, static ELF64 AArch64 with no interpreter/dynamic
dependency, compiled-source and init hashes, exact stock preservation,
gzip/cpio round trip, initrd bounds, full padding, and installer/adapter delta.
It did not execute the helper or emulate the kernel.

The one isolated PLAN substituted only, in memory, the pinned public stock
header template for `b.local_inputs` and a no-op for `a.check_sources` to avoid
private stock/root dependency readers. The delivered installer was unchanged.
Audit guards prohibited private/device reads, subprocesses and sockets. The
PLAN passed, but **did not validate private stock backup, root dependency/source
hashes, live identity, live preimage, USB behavior, or retained-log availability**.
Those remain with the parent. No additional test suite or review was run.

## Parent continuation: one stock trial

1. Under the parent's existing physical authorization, perform the established
   fresh identity/preimage checks and use this spike's pinned installer. Its
   install entry point is `python3 -B source/install.py --execute` from this spike
   directory; it does not reboot. Require full installed-p10 readback SHA
   `a647247d220a0a33fc23ee125744847b836f20908539d9f150054aa20f1ce20d` and verified
   cleanup before one recovery entry. Preserve the established Power fallback.
2. Observe that single boot for the unchanged USB identity `0b05:4a49`, serial
   `P499342cbf13bf044d4b655`, and read-only `P49RAM/PROBE.TXT` if exposed. Allow the
   nominal 60-second reboot path and confirm Android return.
3. Collect retained stock `/proc/last_kmsg` through the parent's established
   private-safe procedure, then publish only marker lines and a public outcome.
   The first `event=fail` before `setup.return.-1` should identify the operation,
   path and errno. Distinguish later disable failures from the setup failure.
   `setup.return.0` plus `udc.bound` without host visibility is a different
   observation. A missing marker alone cannot establish nonexecution or a kernel
   cause, especially if the sink was unavailable or retention failed.

Do not re-run the compile, package check, or PLAN merely to continue the parent
trial; the scripts have one-attempt guards. Retain the artifacts/evidence and
continue from the single observed failure rather than speculative functional
changes.
