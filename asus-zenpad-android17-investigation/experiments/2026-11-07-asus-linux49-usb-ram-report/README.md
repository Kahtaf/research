# Linux 4.9 PID1 USB RAM report

Question: can the unchanged quiet single-CPU Linux 4.9 kernel execute PID1 and expose its actual runtime identity through configfs USB mass storage, independently of the SD driver?

Status: **offline packaged; no physical GO or physical execution proof**. One serial static ARM64 C compile completed using the existing fixed SSH helper, in the fresh owned prefix `/srv/android/2026-11-07-asus-linux49-usb-ram-report-9342cbf1`. No device, ADB, USB, card, cloud API, private data, or active Android build was accessed. The fixed builder SSH was the sole remote access. No kernel/platform build was run.

Important outputs:

- `artifacts/candidate.img`: **7,976,960 bytes**, SHA-256 `6b8c2d1c41685c7592a4aa42cd809e070e8033c0226febb9137285ef4e379f5d`.
- Full zero-padded p10: **16,740,352 bytes**, SHA-256 `fbd4a68ea1d1794db939ec8a9c154b419ecfdd99924e2ca251411525649c3401`. This file remains on the builder; it was not fetched. The actual local compact image plus exact zero padding was independently hashed.
- `artifacts/init`: **597,856 bytes**, static AArch64 ELF, SHA-256 `d081c46dcf40684b35ec5f16bb4238b60662dd857a7211d46241e98f96ac872b`.
- `source/init.c`: actual compiled source; `source/package_probe.py`: offline packager; `scripts/build_remote.py`: bounded one-compile delivery script. The script deliberately refuses reuse of its existing remote prefix.
- `source/install.py` and `source/install.diff`: four literal specializations from the current 827d installer: compact SHA, full SHA, compact length and one appended preimage. `execute()` and `Transport` are byte-identical; `adb` and `legacy_adb.py` are exact copies. Inherited SD-related descriptions/profile names and authenticated ADB-TCP transport remain unchanged.
- `evidence/manifest.json`, `evidence/build-log.json`, `evidence/local-check.json`, `evidence/install-plan.json`: actual artifact hashes, compile result/resource bounds, local container/ELF checks and observed default plan output.

The prior compact image was verified as `827d338c1733665c5adb40daa4a20505ec9ca7e2e586decd6069e2299bf4e062`. Its actual prior public padded artifact was read and verified as `ad32e78548ec22d03685839858bcbccd163465125d4fe7c6b68f86dd19f65982`, now admitted by the installer along with inherited preimages.

Both actual kernel streams remain byte-identical:

- Decompressed Image: `43ee0529e371575bfaddb9de392b77a2279cb44bc60649fcd8d9a88b6e613b09`.
- Compressed Image: `6e445d5000ad1d8dba7dd947945f2db417c45800a6036b995340b9ffc3b57b6d`.

Header and DT bootargs remain exactly:

```text
androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1
```

The sole DT change is `/chosen/linux,initrd-end`, from `0x4404e898` to `0x4403e6a3`, matching the actual 255,651-byte wrapped ramdisk at `0x44000000`. Load addresses, page size, compiled Image, compressed Image, kernel wrapper, all other DT properties and all other Android header fields remain unchanged except required ramdisk size and Android ID. The ramdisk contains only static `/init` and empty `dev`, `ram`, `proc`, `sys`, `config` directories; it contains no device nodes, shell or command service.

PID1 requires `getpid()==1`, captures and validates actual `uname`, and derives both the report and product descriptor from that same runtime result. It creates a private mount tree, fresh tmpfs mounts, proc, sysfs and configfs. The only medium is a freshly created, single-link, regular tmpfs file `/ram/probe.img`, verified with `fstat` and `fstatfs`, then chmod 0444. It is a standard 1.44 MiB FAT12 volume with two 9-sector FATs, 224 root entries and data at byte 16,896. `PROBE.TXT` contains these ordered keys:

```text
run_id=<fresh constant below>
pid1=1
sysname=<actual uname.sysname>
release=<actual uname.release>
version=<actual uname.version>
machine=<actual uname.machine>
status=pid1_ram_report_ready
```

The placeholders above document the format; production code emits only actual runtime values. There is no prewritten expected kernel version or simulated report in the production binary.

The fresh configfs gadget is `g1`, configuration `c.1`, function `mass_storage.usb0`, LUN `lun.0`. It requires an initially empty LUN and sets and verifies `ro=1` **before** attaching the RAM file, checks it again before binding, and exposes no other functions. The LUN should reject host writes with write-protected / SCSI DATA PROTECT behavior. Device class is 0 (per-interface); the standard mass-storage function supplies interface class 8 / subclass 6 / protocol 0x50. No firmware, calibration, charging or radio service is activated by PID1. Kernel hardware initialization still occurs normally; this experiment does not claim zero hardware effects.

It selects only the unique actual entry in `/sys/class/udc`, retrying absence for at most 10 seconds and refusing multiple controllers. The parent expects vendor MTK `musb-hdrc`; that name is never hardcoded, and generic `MUSB_HDRCn` config is not treated as proof of vendor support. Built-in configfs/mass-storage support is based on the parent's exact e9 config statement; the active build/config was not inspected.

The SIGALRM reboot watchdog and monotonic lifecycle deadline cover setup and attempt reboot at 60 seconds from PID1 startup. Normal completion first unbinds the gadget. If the alarm interrupts setup, it attempts reboot directly and cannot resume setup if reboot returns. Automatic return is unproven for this candidate; the parent's known Power fallback remains required.

USB identity and minimal host-read acceptance for the parent:

- Run UUID: `9342cbf1-3bf0-44d4-b655-a1ca30146a99`.
- Serial: **`P499342cbf13bf044d4b655`**.
- VID:PID: **`0x0b05:0x4a49`**, distinct from ADB.
- Manufacturer: `ASUS RAM PID1 Diagnostic`.
- Product: **`ASUS-PID1:<actual uname.release>`**. Mac `system_profiler SPUSBDataType` observing the exact fresh serial and that runtime-derived product independently establishes PID1 descriptor execution, even if no FAT volume mounts. Record the actual suffix; do not substitute an expected 4.9 constant.
- If the RAM volume appears, read `PROBE.TXT` and require the exact fresh run UUID, `pid1=1`, ordered keys above, and a release matching the product suffix. Confirm the medium is reported read-only. No SD read or host write test is needed for this bounded acceptance.
- Missing USB enumeration or a missing mounted FAT volume does not alone prove the kernel failed to execute. Descriptor execution and FAT readability are separate observations. No physical acceptance was performed here.

Continuation: root owns all physical probes and transport decisions. The inherited installer defaults to local PLAN_ONLY, performs no reboot, and retains its authenticated ADB-TCP endpoint; this worker has not introduced a USB installer. Parent install command, **not executed by this worker and not a physical GO**:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-usb-ram-report/source/install.py --execute
```

Default local plan:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-usb-ram-report/source/install.py
```

Validation was limited to the actual boot container, static ELF, exact preserved components/adapters, minimal FAT geometry and source read-only attachment order, and the actual default plan. FAT mount and write refusal were not physically tested. Owned local files are about 8.3 MiB, below 32 MiB; builder outputs remain below 64 MiB. No broad tests or review pass were run.
