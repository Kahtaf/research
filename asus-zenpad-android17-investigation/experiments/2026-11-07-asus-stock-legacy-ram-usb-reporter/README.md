# Stock-only legacy RAM USB reporter

Question: can the existing stock android_usb driver expose the guarded RAM-only
report without the physically measured configfs UDC write errno16 EBUSY?

Status: packaged; one fixed-builder compile passed without diagnostics, one
combined source/ELF/package preservation check passed, and one isolated actual
installer PLAN passed. **No physical or fullOS GO.** No device/root/ADB access,
private/calibration input reads, install/reboot, kernel build, active AOSP reads,
Linux4.9 variants, broad tests/review campaign, or subagents were used.

## Outputs

| Output | Bytes | SHA-256 |
| --- | ---: | --- |
| [candidate.img](artifacts/candidate.img) | 7745536 | `dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427` |
| [candidate.p10.raw](artifacts/candidate.p10.raw) | 16740352 | `80270c24e310b5dd2a8e1e9e21b35a2f3d39c87dc2db25271d97b7d85da733eb` |
| [init](artifacts/init) | 597952 | `631a0aa5e72ee4110357ddac12bc5e5436ef3b1924cf64355f6fae99dc96d272` |
| [init.c](source/init.c) | 18031 | `ce849e64db7a64da414bc96aa6287cde63fdc52504ea40d4c91802f744a445bd` |

[init.diff](source/init.diff) is the exact delta from the failure-logging C.
[install.diff](source/install.diff) changes only candidate pins, exact length,
profile, and appends current parent physical p10
`a647247d220a0a33fc23ee125744847b836f20908539d9f150054aa20f1ce20d`.
`execute`, `Transport`, `Guard`, format helpers and legacy adapters are preserved.
The original configfs spike and its inputs remain unchanged.

## Backend and contract

This is an explicit stock3.18.35-only alternate backend. It retains the guarded
private mounts (configfs mount no longer needed), original FAT/report bytes for
the same actual uname, USB identity0b05:4a49 / serial P499342cbf13bf044d4b655 /
manufacturer ASUS RAM PID1 Diagnostic / actual-uname-derived product,
bounded failure logging marker ASUS-RAM-FAILLOG-20261107-R1, and original
nominal60s alarm plus monotonic deadline.

Before any USB write it requires PID1, actual Linux/3.18.35/aarch64, sole exact
musb-hdrc.0.auto controller with exact observed android_usb uevent, fixed kernel
sysfs paths/ownership, sole empty LUN and fresh enable0/functions-empty defaults.
The normal Android mtp,ffs/enable1 observation is read-only evidence; it is not
an accepted fresh recovery state. Mismatch returns setup failure and keeps reboot.

Its first USB write is enable0, read back, then functions=mass_storage, read back.
It writes and checks the exact diagnostic identity, verifies empty LUN again,
sets ro1 and reads back before attachment, sets/checks nofua0 while empty, and
reopens/verifies the sole fresh private tmpfs regular root-owned0444 single-link
FAT against its original device/inode. It attaches only /ram/probe.img, verifies
path/ro/nofua/media/identity/disabled state, and only then enables1 and reads back.
No UDC core takeover, unregister, platform unbind, second gadget, ADB/shell USB
function, SD/eMMC access, or persistent mutation is added.

At failure/deadline mainline cleanup disables only after ownership was acquired
for its fully checked mass-storage identity/media; it rechecks ownership fields.
SIGALRM also writes0 through an enable descriptor preopened only after those
checks, using async-signal-safe write and fixed bounded stage logging, then the
existing reboot path. There are no Android services or other USB writers in this
RAM PID1. Signal disable write errors are held in RAM, like existing signal sink
errors; a failed reboot still never resumes setup. A failed pre-ownership setup
leaves any already-disabled partial configuration disabled until reboot and does
not clear or detach a preexisting medium.

[attribute-contract.json](evidence/attribute-contract.json),
[shipped disassembly](evidence/shipped-attribute-contract.disasm),
[symbol hashes](evidence/shipped-attribute-symbols.json), and
[public source excerpts](evidence/public-source-excerpts.txt) record the exact
payload basis. **No concrete attribute payload contract remains unresolved.**
The public ASUS GPL source differs from shipped code: source string stores
would truncate spaces, while shipped stores use bounded strlcpy; source CDROM
initialization also differs from shipped parameter setup. Shipped behavior was
used for these choices. Source hashes pin the local public reference bytes and
are not a claim of full source/binary equivalence. Runtime sysfs state, USB
visibility and report readability remain unproved; any guard mismatch refuses
setup. No equivalent Linux4.9 failure was proved or fixed.

## Package and limited checks

[packaging-receipt.json](evidence/packaging-receipt.json) proves use of pinned
known-working original.img SHA
f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140.
Actual raw Image, gzip stream, kernel wrapper, kernel lengths, Android header
addresses/page/arguments and all hardware DT properties are byte-preserved.
Only /chosen/bootargs initrd payload length changes to
`initrd=0x44000200,0x03fed5`; payload is261845 bytes, end-exclusive0x440400d5.
Other changes are needed replacement initrd bytes, wrapper payload length,
Android ramdisk size/ID and zero alignment padding. Six original cpio entries
remain; only init content changes. Fullp10 remains16740352 bytes.

[build-log.json](evidence/build-log.json) records one serial static AArch64 helper
compile in fresh own fixed-SSH prefix, CPU0, nice+10,512MiB address limit,
90s CPU/compiler bound,32MiB file limit and under64MiB owned output. No failed
compile occurred. Static ELF64/AArch64/no dynamic interpreter or dependencies,
source preservation, package round trip and preserved installer code passed in
one combined check; helper was never executed.

[install-plan.json](evidence/install-plan.json) and
[plan-isolation-receipt.json](evidence/plan-isolation-receipt.json) record one
actual installer main PLAN. In-memory substitutions used pinned public stock
header geometry and skipped dependency readers; audit guards rejected private
reads, subprocesses and sockets. Delivered installer unchanged. This does not
validate private backup/dependency hashes, live identity/preimage or USB runtime.
Do not repeat compile/check/PLAN just to continue the physical trial.

## Parent continuation

Parent owns one physical trial and every operation. Exact install command under
the parent's established fresh checks/authorization (not executed here):

```sh
cd /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-stock-legacy-ram-usb-reporter && python3 -B source/install.py --execute
```

Require full installedp10 readback `80270c24e310b5dd2a8e1e9e21b35a2f3d39c87dc2db25271d97b7d85da733eb` and verified cleanup before
one recovery entry; retain established Power fallback. The installer does not
reboot. Observe the same absent-before-run USB identity and read-only P49RAM /
PROBE.TXT, allow nominal60s return, verify Android return, then parent collects
retained marker-only public evidence. Expected stages: legacy.owner.verified,
legacy.disabled, descriptors.ready, lun.attach, legacy.enable, legacy.enabled,
setup.return.0. First event=fail identifies guard/syscall and errno; a missing
marker alone does not prove nonexecution. No physical/fullOS GO is implied.
