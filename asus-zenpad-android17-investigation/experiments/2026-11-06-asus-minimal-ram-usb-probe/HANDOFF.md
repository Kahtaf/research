# Minimal RAM probe handoff

**Offline candidate complete. No deployment, device contact or physical success.**

Candidate on this Mac: `artifacts/candidate.img`, 7,759,872 bytes, SHA256
`535ad86471739967c0e68c058787cf2e5ac6bd844765b75d4bb576200a01d40e`.

Full p10 on the VM at
`/srv/android/asus-minimal-ram-usb-probe-20261106/artifacts/candidate.p10.raw`:
16,740,352 bytes, SHA256
`7562b6168a3cd3f8a2ac4fe1a896f707eab992b2f9b32a1ffb9b1ea33683f596`.
It is exactly the candidate followed by zero padding. Only the small candidate
was copied to the Mac; the full partition image stays on the VM.

`evidence/manifest.json` pins source, input helpers, image, init, gzip and full p10.
`evidence/toolchain-pins.json` pins the existing compilers, compiler internals,
startup objects, static libraries, assemblers and linkers before/after building.

## Behavior and precautions

The unchanged wrapped stock kernel is
`b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`.
Original saved recovery header and MTK wrapper bytes are retained except component
lengths and Android SHA1 ID. No Android init, adbd, FunctionFS, properties,
SELinux policy/services, ueventd, shell, socket, network listener or restore helper
exists in the ramdisk. Its only entries are static ARM64 `/init`, `/dev`, `/proc`
and `/sys` directories. No policy is loaded and no Android security/readiness or
full OS claim is made. This is a stock-kernel/PID1/USB discriminator for progress
toward Android 17, not an Android 17 boot.

PID1 mounts a 1 MiB tmpfs at `/dev`, proc at `/proc` and sysfs at `/sys`, all
nosuid/nodev/noexec. It disables USB and verifies the LUN backing path is empty;
an unexpected path is a failure, never a path to clear or export. It sets
`f_mass_storage/bicr=0`, requires `lun/ro=1`, creates `/dev/probe.img` exclusively
without following symlinks, verifies the open descriptor is a single-link regular
file on tmpfs, writes a 65,536-byte FAT12 report, chmods it 0444 and verifies
size/mode. After attaching that sole constant path, it verifies the driver's
actual file path and `ro=1` again. Only `mass_storage` may be selected. Fixed
public descriptors replace serial/manufacturer/product; no unit serial is read.
It verifies `ro=1` immediately before enable. Every error returns to best-effort
USB disable and the bounded reboot lifecycle. There is no alternate gadget.

The FAT contains only a volume label and read-only `REPORT.TXT`: fixed fresh run
ID, PID1, four uname fields and a diagnostic status. Nodename/domainname, device
identifiers, credentials and storage contents are omitted. The reported status
means the RAM report was prepared; only observing the actual report establishes
the later gadget path. It does not attest to reboot success.

Normal path: absolute monotonic deadline 60 seconds from PID1 lifecycle start,
then best-effort USB disable and one `reboot(RB_AUTOBOOT)` request without a
recovery/bootloader argument. A separately armed SIGALRM attempts the same normal
reboot at 60 seconds even if setup blocks. A returning alarm reboot leaves PID1
paused; a returning normal-path reboot leaves it sleeping. This deliberately
requires parent Power fallback, not a reboot-success assertion. The bound begins
in PID1, not at boot-menu selection; it cannot cover a kernel hang before PID1.
No userspace block-device, mmc, data, misc, NVRAM, bootloader, charging, radio,
sensor or graphics write is implemented. Kernel boot/reboot and USB necessarily
operate hardware; this does not promise that a stock kernel never updates its
own boot accounting or retained crash state.

## Actual stock driver and config evidence

`inputs/stock-capability.json` is the parent's retained public stock observation
of the real `f_mass_storage/lun/file` path. It is not a new live probe.

`inputs/android.c`, `f_mass_storage.c`, `storage_common.c` and
`reference.defconfig` are pinned retained ASUS reference sources, **not claimed
byte-identical build inputs**. The reference defaults differ from the shipped
binary. The exact kernel has no embedded IKCONFIG, so an exact full `.config`
cannot honestly be extracted. Instead `evidence/kernel-contract.json` validates
all 70,337 kallsyms names/markers/token indices and records exact compiled API
functions, attribute modes/callbacks and hashes of small disassembled slices.
Those compiled facts, plus the retained real sysfs observation, establish the
needed built-in legacy driver support; they do not invent a configuration dump.

- `mass_storage_function_init` at `ffffffc00077fbc0` configures one removable LUN
  from parameters; `fsg_config_from_params` resolves the single empty file entry
  to one LUN. No physical backing path is installed by this code path.
- `mass_storage_bicr_store` at `ffffffc00077fd74` calls `fsg_bicr_store` at
  `ffffffc00076ecb8`. Its zero branch clears bit 3 (CD-ROM) and resets sector
  fields; readback reports the selected mode. This is why `bicr=0` is explicit.
- Actual `ro` attribute at `ffffffc001017b80` is mode 0644 with `ro_store`;
  the CD-ROM variant at `ffffffc001017bd0` is mode 0444 with no store callback.
  The probe accepts an already-1 immutable attribute, otherwise requires a
  successful set/readback. `fsg_store_ro` at `ffffffc00076f310` refuses changes
  with an open backing file and sets initially_ro and ro while closed.
- `fsg_lun_open` at `ffffffc00076ed98` tests initially_ro at byte 24 bit 0.
  With it set, it calls filp_open with ARM64 O_LARGEFILE|O_RDONLY (`0x20000`),
  not the `0x20002` writable branch. `fsg_show_ro` returns bit 1 for an open LUN.
- Actual `do_write` at `ffffffc00076b894` tests that same byte's bit 1 before
  the write path and branches to the write-protected response. The probe never
  asks the host to test a write. Directory read-only flags alone are not used
  as the USB write-protection guarantee.

## Offline verification

`evidence/build-log.json` records passing static builds, ELF readelf output,
production-body tests and real `fsck.fat -n -v` (exit 0). Tests invoke the actual
production setup/lifecycle/FAT functions with every external operation replaced
by in-memory RAM/sysfs fakes; no host mount, real sysfs write or reboot occurs.
They cover 67 injected lifecycle-through-setup syscall positions, partial RAM
writes, non-tmpfs/block/multilink backing descriptors, wrong PID, bad uname,
unexpected backing, immutable/mutable ro, loss of ro after attachment,
clock/watchdog failures, EINTR sleep and the watchdog reboot dispatch.

`evidence/independent-validation.json` independently parses container, both MTK
lengths, Android SHA1, original-header byte differences, page padding, single gzip
member, every newc entry, static ARM64 ET_EXEC/program headers/executable entry,
FAT BPB, both FATs, allocation chain and exact report schema. Wrapped ramdisk is
282,848 bytes; gzip is 282,336 bytes; expanded newc is 636,416 bytes. Its loaded
end `0x440450e0` fits below both the static 2 MiB initrd limit and ram-console
reservation. Actual runtime initrd bounds remain unknown.

Two independent compiler invocations produced identical init ELFs. Repackaging
from each ELF produced identical gzip/newc and image bytes. Resource evidence:
one CPU, 1 GiB address-space limit, finite command timeouts, around 28 MB of
owned VM files, well below 256 MiB. No full source or saved recovery image was
copied; only selected source/helper/header/wrapper material was staged and the
existing saved wrapped kernel was read in place. Originals remain unchanged.

## Parent-owned transition and physical test

This packet contains **no writer, approval flags, arbitrary-image option or
execute authorization**. Existing deployment code is still bound to the earlier
image and must not be bypassed. Parent separately reviews and binds this exact
new candidate, its full-p10 digest and source pins into its reviewed safeguards.
A fresh complete actual p10 preimage must be exactly one of:

1. Installed exact-5a61 full p10:
   `3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a`.
2. Original recovery full p10:
   `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`.

Both transitions have the sole new full-p10 postimage
`7562b6168a3cd3f8a2ac4fe1a896f707eab992b2f9b32a1ffb9b1ea33683f596`.
No BOOT/SYSTEM/data/misc/other partition transition is included. A stale prior
receipt is not proof of the current preimage. Parent retains its identity,
shared mutation lock, entry-state and complete write/readback/completion guards.
Original recovery restoration is deferred unless needed; it is not a prerequisite
or automatic cleanup step here.

For a separately authorized supervised trial, prepare host observation before
recovery entry, keep the cable attached and have the user beside Power. Bound
the observation to 60 seconds after manual entry; a delayed PID1 timer must not
extend the parent's own fallback window. Observe actual USB bus changes rather
than ADB inventory. No USB enumeration is inconclusive between early boot,
PID1 failure and a fail-closed gadget setup. Do not try another gadget or flash
Android17 on that result.

Accept a positive discriminator only when all of these are observed in that
same physical trial:

- Exact parent install/readback binding and fresh USB transition; mass-storage
  interface only, public serial `b8bfa53e-4142-4ec8-b603-8f25cb617e2e`.
- Capacity exactly 65,536 bytes; host reports device/LUN read-only (SCSI/media
  write protection), not merely a read-only filesystem mount. Prevent ordinary
  automount; use parent-owned read-only/noexec/nosuid/nodev access with no host
  write, repair, indexing or write-probe attempt. If host read-only status cannot
  be established, stop at raw read-only observation; do not mount writable.
- FAT12 with label `RAMPROBE`, a single `REPORT.TXT` file, no extra files, and
  exactly the seven fields in `evidence/host-acceptance.json`. Require fresh run
  ID, `pid1=1`, sysname Linux, release 3.18.35, machine aarch64, expected kernel
  version and status. This ID is public correlation, not authentication.
- Retain the actual report and host USB/read-only evidence. A report proves
  stock kernel → minimal PID1 → tmpfs → legacy USB path only.

Observe whether normal Android actually returns after the reboot attempt. If
it does not, use the established supervised physical Power/Normal Boot fallback
and verify healthy stock Android before any further device command. A timed
wait, disappearing USB device, logo or reboot syscall is not return proof.
The first successful report still does not prove Android17 or its security.

## Continuation

Only `scripts/local_driver.py build` reruns the bounded build in the existing
owned VM fixture. `setup` refuses an existing fixture. `fetch` retrieves only
public evidence/small ELF slices and the <16 MiB candidate, never padded p10.
Original input/kernel/toolchain hashes are checked; `evidence/manifest.json`
pins every staged source and helper. Preserve the reviewed evidence before any
future source change. Current task is complete; further work is the parent's
separate deployment review and physical test.
