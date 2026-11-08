from pathlib import Path
import hashlib,json,stat,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent
sys.path.insert(0,str(R/'source'));import bootformat as b
p=json.loads((R/'evidence/packaging-receipt.json').read_text());c=json.loads((R/'evidence/compiler-receipt.json').read_text());plan=json.loads((R/'evidence/plan-isolation-receipt.json').read_text())
header,kernel,ram,tail=b.parse_image((R/'artifacts/candidate.img').read_bytes())
layout=dict(android_page_size=2048,android_header_u32_fields=list(struct.unpack_from('<10I',header,8)),kernel_offset=2048,kernel_bytes=len(kernel),ramdisk_offset=2048+b.align(len(kernel)),ramdisk_bytes=len(ram),ramdisk_payload_bytes=len(ram)-512,candidate_bytes=p['candidate']['bytes'],full_p10_bytes=p['full_p10']['bytes'],android_boot_id=header[576:608].hex(),MTK_kernel_name=kernel[8:40].split(b'\0')[0].decode(),MTK_ramdisk_name=ram[8:40].split(b'\0')[0].decode(),tail_bytes=len(tail),LK_contract='Both MTK wrappers retain 512-byte layout; chosen start/end describes compressed ramdisk payload after LK strips ramdisk wrapper; fixed load start 0x44000000',DT_selection='Exact prior packaged runtime DT tail from calibrated candidate; only existing 32-bit chosen/linux,initrd-end value edited in place. Compiled Image.gz-dtb artifact retained untouched; gzip stream/raw Image retained in candidate.')
(R/'evidence/layout-receipt.json').write_text(json.dumps(layout,indent=2)+'\n')
base=W/'2026-11-07-asus-linux49-calibrated-entry-build'
files=[*sorted((R/'source').glob('*')),*sorted((R/'scripts').glob('*.py')),W/'2026-11-06-asus-product-input-build-kit/scripts/remote.py',base/'source/install.py',base/'scripts/package.py',base/'source/arch/arm64/kernel/asus_entry_text.S',base/'source/arch/arm64/kernel/asus_entry_tag.h']
pins={str(f.relative_to(W)):dict(sha256=hashlib.sha256(f.read_bytes()).hexdigest(),bytes=f.stat().st_size,mode=oct(stat.S_IMODE(f.stat().st_mode))) for f in files if f.is_file()}
(R/'evidence/public-code-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
(R/'evidence/final-status.json').write_text(json.dumps(dict(status='READY_FOR_PARENT_SINGLE_PHYSICAL_TRIAL',pid1_run_uuid=p['pid1_run_uuid'],compile_attempts=1,compile_exit=0,compile_warnings=2,packaged_candidates=1,isolated_actual_PLAN_calls=1,device_or_ADB_access=False,private_payload_or_retained_log_access=False,cloud_lifecycle_or_resource_operations=False,remote_kernel_copy_or_build=False,remote_prefix='/srv/android/asus-linux49-ram-primitive-probe-20261107',VM='VM8549823276971553556',VM_left_running_for_parent_stop=True,physical_timer_storage_usb_result='NOT_OBSERVED'),indent=2)+'\n')
readme=f'''# RAM PID1 sleep and fixed MMC enumeration

Question: can a tiny PID1 on the physically proven Linux 4.9 kernel return from one relative 100 ms blocking sleep and enumerate MMC hosts/block nodes when PID1 bypasses USB entirely?

Status: **one candidate packaged; minimal static ELF/preservation checks and one isolated actual installer PLAN passed. No device access, installation, reboot or physical trial performed.** Functional sleep, storage and USB remain unqualified. Parent owns one physical recovery trial, interpretation, nearby Power fallback and VM stop. No subsequent unit is prepared.

Fresh PID1 UUID: `{p['pid1_run_uuid']}`. Every emitted helper record starts `ASUS49-PRIMITIVE run={p['pid1_run_uuid']}`. Kernel entry UUID remains `23cdb057-295c-4b42-9ade-a4324162ad02`; an old kernel entry marker is not fresh proof for this trial. Physical Linux 4.9/PID1 admission comes only from the parent-provided public `../2026-11-07-asus-linux49-calibrated-entry-trial/evidence/RESULT.json` and `sanitized-bootstrap-observations.txt`. No full retained log was read.

## Candidate and immutable inputs

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `artifacts/candidate.img` | {p['candidate']['bytes']} | `{p['candidate']['sha256']}` |
| `artifacts/candidate.p10.raw` | {p['full_p10']['bytes']} | `{p['full_p10']['sha256']}` |
| `artifacts/init` | {p['init']['bytes']} | `{p['init']['sha256']}` |
| `source/init.c` | {p['init_source']['bytes']} | `{p['init_source']['sha256']}` |
| `artifacts/initramfs.cpio.gz` | {p['compressed_initramfs']['bytes']} | `{p['compressed_initramfs']['sha256']}` |
| unchanged `artifacts/Image.gz-dtb` | {p['compiled_Image_gz_dtb']['bytes']} | `{p['compiled_Image_gz_dtb']['sha256']}` |
| unchanged `artifacts/resolved.config` | {p['config']['bytes']} | `{p['config']['sha256']}` |

`evidence/packaging-receipt.json` records the unchanged compressed kernel and raw Image hashes, DT hashes, wrapper/header changed offsets, helper hashes, static ELF result, exact command line and installer preservation. `evidence/layout-receipt.json` records essential Android/MTK offsets, sizes and boot ID. The static ELF is AArch64 ELF64 with no PT_INTERP or PT_DYNAMIC.

Only `/chosen/linux,initrd-end` changes in the prior packaged runtime DT. Every other DT token, reservation byte and header/structure/string layout remains byte-identical; hardware properties also match the compiled DT. Kernel gzip/raw bytes, compiled kernel/config artifacts, MTK kernel wrapper, bootargs and load addresses are unchanged. The initrd starts at `0x44000000`, ends at `{p['initrd']['end']}`, and measures {p['compressed_initramfs']['bytes']} compressed bytes **excluding** the 512-byte MTK ramdisk wrapper, per existing LK stripping contract. This is below 258055 bytes, so unchanged assembly exclusion `[0x44000000,0x4403f007)` remains a safe superset. Genuine newc cpio contains only root-owned `init` mode 100755 and `dev`, `proc`, `sys` directories mode 040755. No security policy, persistent tables or mounts are added.

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

Compiler: `{c['compiler_version'].splitlines()[0]}`; executable SHA-256 `{c['compiler_sha256']}`. Flags: `-static -Os -s -ffunction-sections -fdata-sections -Wl,--gc-sections -Wall -Wextra`. Exit 0, two ignored signal-handler write-result warnings retained, no failed compilation. `evidence/compiler-receipt.json` and `compile-dispatch.json` pin compiler/source/binary, command and transport. `scripts/compile_once.py` refuses reuse of the owned remote prefix.

Installer specialization is exclusively image/full hash, actual image size, profile and append supplied current full p10 `c89bedfba2bd8550580f394bb4774018523855b622851d563a56975746f99bb5`. `source/install.diff` is the exact diff from calibrated-entry-build. execute, Transport, Guard and all adapter/helper bytes remain identical. Helpers were copied using copy2; delivered `source/adb` is explicitly mode **0755**, recorded with its hash in `evidence/packaging-receipt.json` and `public-code-pins.json`.

Exactly one actual installer main PLAN ran in an audited process denying subprocess/network and private/device/root-payload reads. In memory only, stock input became the established public stock-header template SHA-256 `f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140`; source checks became an explicit public-code hash subset. Delivered guards/input readers are unchanged. Private stock backup and full preserved manifest/root-helper chain were deliberately not validated. `evidence/install-plan.json` and `plan-isolation-receipt.json` disclose substitutions and pin the public transport/adapter/engine dependencies. `public-code-pins.json` pins this unit's source/scripts and parent packaging/entry sources. No broad suite or helper emulation was run.

## Parent continuation

Review receipts and exact full p10, then use the existing parent physical procedure and fresh identity/preimage checks. Parent installer command, from `/OWNER_HOME/Documents/workspace/ideas`:

```sh
python3 -B 2026-11-07-asus-linux49-ram-primitive-probe/source/install.py --execute
```

The delivered installer performs the guarded install/readback phase and does not reboot. Parent owns the separate single recovery entry, bounded observation, return/stock verification and interpretation. Match **this PID1 UUID**, actual uname and operation boundary results; absent completion/hosts/cards is not success. Do not infer a timer/WD/driver fix. Preserve this candidate and logs; no repeated physical trial or next implementation is authorized here. Stop VM8549823276971553556 after this implementation handoff.
'''
(R/'README.md').write_text(readme)
paths=[R/'README.md',*sorted((R/'source').glob('*')),*sorted((R/'scripts').glob('*.py')),*sorted((R/'artifacts').glob('*')),*sorted((R/'evidence').glob('*.json')),*sorted((R/'evidence').glob('*.log'))]
(R/'SHA256SUMS').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(R))+'\n' for f in paths if f.is_file()))
print(json.dumps(dict(final_status='READY_FOR_PARENT_SINGLE_PHYSICAL_TRIAL',candidate=p['candidate'],full_p10=p['full_p10'],adb_mode=oct(stat.S_IMODE((R/'source/adb').stat().st_mode)),PLAN_calls=plan['actual_installer_main_calls']),indent=2))
