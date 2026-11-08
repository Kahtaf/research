# Linux 4.9 minimal RAM probe — offline candidate

Actual isolated static ARM64 build and offline qualification are complete. **No device operations, deployment adapter, physical test or boot-success claim.** This candidate does not replace any frozen probe. Parent will finish the stock-kernel minimal PID1 trial before considering this separate Linux 4.9 candidate.

`artifacts/candidate.img` is 8,005,632 bytes, SHA256 `5be0ed4cb9cb24a27853620a1a7870db63f5ba0eed75f587adf5c0850f5278a4`.
The zero-padded 16,740,352-byte p10 image remains only at `/srv/android/asus-linux49-minimal-ram-probe-20261106/artifacts/candidate.p10.raw`, SHA256 `647b5865d4f63188b0a2e0f1c634b1b814ff0e44ecaa31963ea5c203e61d5ac3`. Only the small candidate and public evidence were fetched to the Mac.

## Runtime behavior

The ramdisk contains only `/init` and empty `/dev`, `/proc`, `/sys`, `/config` directories. PID1 mounts a 1 MiB tmpfs, proc, sysfs and configfs, each nosuid/nodev/noexec. There are no device nodes, Android init, shell, ADB, FunctionFS, policy, readers/writers for partitions, sockets, network listeners, modules or persistent filesystem mounts. No policy is loaded; neither the `enforcing=1` boot argument nor this probe establishes Android security or Android 17 readiness.

Setup requires exactly the public controller name `musb-hdrc`, an empty configfs gadget namespace, a newly created gadget and an empty initial UDC and LUN backing path. Unexpected controllers, gadgets, bindings or backing paths fail closed; they are never cleared for reuse. Only `mass_storage.ram` is created and linked once into one configuration. Fixed public descriptors include fresh run UUID `801c68c4-841f-4ea4-9e9e-c608621839ca`; no hardware/unit identifier is read.

Before attaching any file, PID1 sets and reads back `lun.0/removable=1`, `cdrom=0`, and `ro=1`. It creates only `/dev/probe.img` exclusively with O_NOFOLLOW, verifies a single-link regular empty file on tmpfs, writes exactly 65,536 bytes, chmods 0444 and verifies size/mode. It then attaches that sole constant path, verifies the driver's actual path and read-only state, creates the sole function symlink, rechecks read-only state and controller/binding, and binds UDC. The exact build source sets `initially_ro` through the `ro` attribute and opens this backing file O_RDONLY|O_LARGEFILE; its SCSI write path returns WRITE_PROTECTED. Filesystem attributes alone are not the media write-protection claim. No host write test is requested.

The FAT12 medium contains a volume label and a single read-only `REPORT.TXT`. Its seven fields are public run ID, PID1, sysname, release, version, machine and prepared status. Nodename/domainname, private identifiers, storage contents and calibration are omitted. The prepared status does not attest that USB enumeration or reboot occurred.

Normal lifecycle uses an absolute monotonic deadline 60 seconds from PID1 lifecycle start, including setup. At expiry it attempts UDC unbind and a normal `reboot(RB_AUTOBOOT)` without recovery/bootloader arguments. A separately armed SIGALRM attempts the same normal reboot if setup blocks; a returning watchdog reboot parks PID1 permanently, preventing resumed setup. Returning normal reboot leaves PID1 alive sleeping. These are attempts, not a guaranteed power/reset bound: pre-PID1 failure, kernel hang, uninterruptible operations or failed reboot may still require physical fallback. The timer starts in PID1, not at menu entry.

The unchanged kernel necessarily initializes hardware and executes its existing drivers and reboot path. This does not claim that the kernel never updates retained crash/boot accounting or makes internal hardware writes. No new hardware feature, charging opt-in, partition write or Android service is added.

## Kernel and LK package contract

The exact precompiled physical BMC156 kernel input is 7,716,897 bytes, SHA256 `e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1`; resolved config SHA256 `10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`. It already contains built-in configfs mass storage. There was no kernel/config compile or edit. Both compressed Image stream and the decompressed 17,345,024-byte Image remain byte-identical; decompressed Image SHA256 is `43ee0529e371575bfaddb9de392b77a2279cb44bc60649fcd8d9a88b6e613b09`.

Original recovery header and MTK KERNEL/RECOVERY wrapper templates are retained except reviewed header cmdline, component lengths and Android SHA1 ID. The reviewed 92-byte header is:

```
bootopt=64S3,32N2,64N2 build_version=3 androidboot.boot_devices=soc/11230000.mmc enforcing=1
```

There is no header or chosen `initrd=` override, including no inherited static 2 MiB token. This exact compiled input's original DT has no such token; the original stock header's permissive argument is replaced. Exactly three chosen properties change: bootargs and 32-bit `linux,initrd-start/end`. Source-proven LK strips the 512-byte ramdisk wrapper and relocates actual compressed payload to `0x44000000`; exact end is `0x44045319` (283,417 gzip bytes). All other DT properties and reservation bytes are preserved. `evidence/packaging-contract.json` checks Image.image_size, static RAM banks, fixed reservations, 1 MiB DT expansion envelope, all payload overlaps and the exact LK scanned-tail/rounding gzip model. Dynamic consys placement and runtime RAM/framebuffer fixups remain unobserved. The LK model uses host zlib, not execution of LK.

## Qualification and source binding

`evidence/manifest.json` pins every staged source/helper/input and final hashes. `evidence/external-input-preservation.json` pins the in-place exact build sources, compiled headers, configuration and kernel before/after compilation; `evidence/toolchain-pins.json` pins existing host/cross compiler internals, startup objects, static libraries, assembler/linker and validators before/after. `evidence/source-contract.json` records exact driver excerpts and truthful compiled uname expectations:

- sysname `Linux`; machine `aarch64`.
- release `4.9.337-asus-p00a-experimental-g717bb3c9e13c-dirty`.
- version `#1 SMP PREEMPT Fri Nov 6 21:17:56 UTC 2026`.

Two actual compiler invocations produce identical static AArch64 ET_EXEC ELFs with no dynamic/interpreter segment. Identical deterministic newc/gzip/image outputs follow. Tests compile the exact production C body with fake external operations; 101 lifecycle-through-setup failure positions, unexpected UDC/namespace/backing/binding, read-only loss, short RAM write, descriptor type/filesystem/link/mode/size violations, PID/uname failures, watchdog/clock errors, EINTR and watchdog reboot dispatch pass. The actual directory scanner additionally runs against owned ordinary test directories. No production init ELF is executed on a host or device. `fsck.fat -n -v` exits 0.

The independent validator parses header geometry/allowed byte differences, both wrappers, Android ID, zero padding, single gzip, each newc entry, actual static ELF program headers/entry, FAT BPB, duplicate FATs, allocation chain and report schema. It separately compares the packaged compressed/decompressed Image to the exact input and parses chosen metadata. `evidence/local-reproduction.json` records a Mac repack from the delivered ELF and local exact kernel that matches the image, cpio, gzip and padded p10 digest; all staged source pins match. The fixture report uses explicit fixture uname strings and is not a physical observation.

Build resource evidence is one CPU, 1 GiB address-space limit, finite compile timeouts, maximum 128 MiB owned files and about 28 MB actually retained. Only the owned `/srv/android/asus-linux49-minimal-ram-probe-20261106` prefix was mutated remotely. Existing sources/prebuilts/toolchains were read in place; no native AOSP/ninja/kernel build, full source/image copy, cloud lifecycle, process polling, private calibration/key read, device/USB/ADB/root call or transport change occurred. SSH uses the existing fixed helper and its private key path; key contents were never inspected or copied.

## Parent review and physical boundary

This packet carries no writer, arbitrary-image option, affirmative execution flags or physical GO. Parent separately reviews and binds this exact candidate/full-p10 digest and source pins into its safeguards, with a fresh actual complete p10 preimage and readback. Existing transport remains bound to its prior image; no bypass or frozen-probe replacement is included. Normal BOOT, SYSTEM, data, misc and every other partition remain preserved by this task.

Any later separately authorized supervised trial needs host observation prepared before entry, the cable attached and the user beside Power. Parent's own 60-second observation window starts at manual entry and is not extended by delayed PID1. Accept only a fresh mass-storage-only USB transition with the public run UUID, exactly 65,536-byte capacity, actual host-observed SCSI/media read-only status, FAT12 RAMPROBE and one REPORT.TXT matching all seven fields and the exact uname above. Avoid normal automount; parent uses read-only/noexec/nosuid/nodev observation without host repair, indexing or write probes. If media read-only cannot be established, stop at raw read-only observation. No USB appearance is inconclusive among boot failure, PID1 failure and fail-closed setup; do not switch gadgets or flash Android17 on that result.

A report proves only Linux 4.9 → static PID1 → tmpfs → configfs mass storage in that same physical trial. It does not prove full Android, Android security, normal reboot success, battery/charging or other hardware readiness. Actual healthy stock Android return is required after the reboot attempt; USB disappearance, a logo or elapsed wait is not return proof. The new 4.9 kernel's nominal 14-second Power reset is unvalidated; the stock kernel's approximately 5-second hold is user-proven and must not be treated as a 4.9 guarantee. Parent retains supervised 15–20-second Power/Normal Boot fallback if needed and verifies healthy stock Android before further device commands.

Continuation: `scripts/local_driver.py build` repeats the bounded isolated build. `setup` refuses an existing prefix; `sync` only restages this spike into its fixed owned prefix. `fetch` retrieves public evidence and the small candidate, never padded p10. Preserve evidence before source changes. Current remaining action is parent review and the earlier stock minimal PID1 trial, not deployment of this candidate.
