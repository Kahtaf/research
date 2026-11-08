# RAM PID1 sleep and fixed MMC enumeration

Question: can a tiny PID1 on the physically proven Linux 4.9 kernel return from one relative 100 ms blocking sleep and enumerate MMC hosts/block nodes when PID1 bypasses USB entirely?

Status: **one candidate packaged; minimal static ELF/preservation checks and one isolated actual installer PLAN passed. No device access, installation, reboot or physical trial performed.** Functional sleep, storage and USB remain unqualified. Parent owns one physical recovery trial, interpretation, nearby Power fallback and VM stop. No subsequent unit is prepared.

Fresh PID1 UUID: `b388b428-514d-49ee-949f-6b79317699bd`. Every emitted helper record starts `ASUS49-PRIMITIVE run=b388b428-514d-49ee-949f-6b79317699bd`. Kernel entry UUID remains `23cdb057-295c-4b42-9ade-a4324162ad02`; an old kernel entry marker is not fresh proof for this trial. Physical Linux 4.9/PID1 admission comes only from the parent-provided public `../2026-11-07-asus-linux49-calibrated-entry-trial/evidence/RESULT.json` and `sanitized-bootstrap-observations.txt`. No full retained log was read.

## Candidate and immutable inputs

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `artifacts/candidate.img` | 7972864 | `4dee477b7d1fc77ee8f04a2608a0805b199a82acf5ade23d8e447f54c4812343` |
| `artifacts/candidate.p10.raw` | 16740352 | `8e002fd9f9b7797470fd03d94da44c0f3479c6fdfefe00b8ecd1136bc53534fb` |
| `artifacts/init` | 597984 | `50a675a5a014dadca67d9ddfb1fc89fcfcef280ffb52c642e5496782c9c5f87d` |
| `source/init.c` | 6840 | `f3bbc220ec81a06a7aedd7ea31f0c332387dba4a56bfd48cf68809e9250a385c` |
| `artifacts/initramfs.cpio.gz` | 255220 | `f3f0eb0b87c238779ef375533f2d2efb884bbb69f28bcd28eaa095c43ad51d39` |
| unchanged `artifacts/Image.gz-dtb` | 7713482 | `97b7e1199d607f852bf52ff7766e8aa079fee92986cd3d473b765a45adbf45fb` |
| unchanged `artifacts/resolved.config` | 126443 | `708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1` |

`evidence/packaging-receipt.json` records the unchanged compressed kernel and raw Image hashes, DT hashes, wrapper/header changed offsets, helper hashes, static ELF result, exact command line and installer preservation. `evidence/layout-receipt.json` records essential Android/MTK offsets, sizes and boot ID. The static ELF is AArch64 ELF64 with no PT_INTERP or PT_DYNAMIC.

Only `/chosen/linux,initrd-end` changes in the prior packaged runtime DT. Every other DT token, reservation byte and header/structure/string layout remains byte-identical; hardware properties also match the compiled DT. Kernel gzip/raw bytes, compiled kernel/config artifacts, MTK kernel wrapper, bootargs and load addresses are unchanged. The initrd starts at `0x44000000`, ends at `0x4403e4f4`, and measures 255220 compressed bytes **excluding** the 512-byte MTK ramdisk wrapper, per existing LK stripping contract. This is below 258055 bytes, so unchanged assembly exclusion `[0x44000000,0x4403f007)` remains a safe superset. Genuine newc cpio contains only root-owned `init` mode 100755 and `dev`, `proc`, `sys` directories mode 040755. No security policy, persistent tables or mounts are added.

## Expected observation and bounds

1. Require actual getpid 1 before doing any setup. Create a fresh RAM-root char 1:11 node `/primitive-kmsg`, open with NONBLOCK/NOFOLLOW, then unlink. Refuse to open an existing node. Records include actual sink creation/open results, PID and actual uname fields.
2. Install SIGALRM and arm a nominal 10-second alarm. Mount only proc and sysfs, with operation begin/end, actual return and errno. The initial initramfs is already RAM; no block or persistent mount is made.
3. Log begin/end of CLOCK_MONOTONIC clock_gettime before sleep, one relative CLOCK_MONOTONIC clock_nanosleep request of 100000000 ns, its actual POSIX error-number return and captured libc errno, then begin/end of the post-sleep clock_gettime and delta if both samples succeeded. **No retries.** A successful sleep return proves blocking wake only; delta does not calibrate physical clock frequency.
4. Log begin/end for opendir, every readdir and closedir of `/sys/class/mmc_host` and `/sys/class/block`. Names only: at most 32 non-dot entries, 34 readdir calls, names shorter than 128 bytes. Limits are explicit records. No traversal into MMC card identity attributes.
5. For fixed `mmcblk0`, `mmcblk0p1`, `mmcblk1`, `mmcblk1p1`, log stat begin/end. Only when present, read `dev`, `size`, `removable`, `device/type` under `/sys/class/block`, with begin/end for open, a single read of at most 128 bytes, and close. A full buffer is flagged as possibly truncated. Missing nodes/attributes, timeouts and errors are observations. No block device opens, MMC mknod, storage mount/format/write, CID/serial/calibration/private reads, USB/configfs/gadget/UDC setup or child process exists in this helper.
6. Emit `stage=complete op=observation` after returning from the observation; consult actual earlier rc/errno to determine what worked. Block SIGALRM, cancel alarm, attempt normal reboot once. A returning reboot parks in pause forever. If blocking SIGALRM fails, park for the already-armed handler rather than race a second reboot attempt.

The log sink caps output at 768 records, each under 768 bytes, one nonblocking write per record; no write retry. Normal logging tracks sink write failure in RAM and reports it near completion if possible. If the sink is unavailable, records cannot survive reset. The alarm handler uses async-safe write and manual integer formatting, then the Linux reboot wrapper; if reboot returns it logs errno and parks. Its two ignored-write-result compiler warnings are preserved in `evidence/compile-1.log`. **SIGALRM uses the same kernel timers/interrupts and is not independent protection if those fail. Existing hardware reset and the parent's nearby Power remain fallback.** The unchanged kernel can still emit its existing USB/MMC probe diagnostics; this helper performs no USB setup.

## Build and review evidence

One remote C compile only, using the existing product-kit `remote.py` SSH transport to the already running VM. Owned prefix: `/srv/android/asus-linux49-ram-primitive-probe-20261107`, with separate source/tmp/artifacts/evidence directories. No remote kernel copy/build, RLIMIT_AS, cloud lifecycle/resource command or device access. Only source, binary, compile log and compiler receipt were fetched. VM remains ready/running for parent stop.

Compiler: `aarch64-linux-gnu-gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`; executable SHA-256 `cd90adc7801f4595267f61a5d25bd3a0c6beb2f9f1f107ab919a97a12972dc9a`. Flags: `-static -Os -s -ffunction-sections -fdata-sections -Wl,--gc-sections -Wall -Wextra`. Exit 0, two ignored signal-handler write-result warnings retained, no failed compilation. `evidence/compiler-receipt.json` and `compile-dispatch.json` pin compiler/source/binary, command and transport. `scripts/compile_once.py` refuses reuse of the owned remote prefix.

Installer specialization is exclusively image/full hash, actual image size, profile and append supplied current full p10 `c89bedfba2bd8550580f394bb4774018523855b622851d563a56975746f99bb5`. `source/install.diff` is the exact diff from calibrated-entry-build. execute, Transport, Guard and all adapter/helper bytes remain identical. Helpers were copied using copy2; delivered `source/adb` is explicitly mode **0755**, recorded with its hash in `evidence/packaging-receipt.json` and `public-code-pins.json`.

Exactly one actual installer main PLAN ran in an audited process denying subprocess/network and private/device/root-payload reads. In memory only, stock input became the established public stock-header template SHA-256 `f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140`; source checks became an explicit public-code hash subset. Delivered guards/input readers are unchanged. Private stock backup and full preserved manifest/root-helper chain were deliberately not validated. `evidence/install-plan.json` and `plan-isolation-receipt.json` disclose substitutions and pin the public transport/adapter/engine dependencies. `public-code-pins.json` pins this unit's source/scripts and parent packaging/entry sources. No broad suite or helper emulation was run.

## Parent continuation

Review receipts and exact full p10, then use the existing parent physical procedure and fresh identity/preimage checks. Parent installer command, from `/OWNER_HOME/Documents/workspace/ideas`:

```sh
python3 -B 2026-11-07-asus-linux49-ram-primitive-probe/source/install.py --execute
```

The delivered installer performs the guarded install/readback phase and does not reboot. Parent owns the separate single recovery entry, bounded observation, return/stock verification and interpretation. Match **this PID1 UUID**, actual uname and operation boundary results; absent completion/hosts/cards is not success. Do not infer a timer/WD/driver fix. Preserve this candidate and logs; no repeated physical trial or next implementation is authorized here. Stop VM8549823276971553556 after this implementation handoff.
