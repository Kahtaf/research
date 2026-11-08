"""Write the handoff from completed essential checks; no device execution."""
from pathlib import Path
import hashlib,json,stat,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[1];W=R.parent
p=json.loads((R/'evidence/packaging-receipt.json').read_text())
c=json.loads((R/'evidence/compiler-receipt.json').read_text())
vm=json.loads((R/'evidence/vm-lifecycle.json').read_text())
plan=json.loads((R/'evidence/plan-isolation-receipt.json').read_text())
scope=json.loads((R/'evidence/source-scope-receipt.json').read_text())
assert c['exit']==0 and vm['final_status']=='TERMINATED' and vm['compile_and_small_fetch_completed']
assert plan['actual_installer_main_calls']==1 and not plan['device_contacted']
assert scope['source_sha256']==c['source_sha256']==p['init_source']['sha256']
assert p['compressed_initramfs']['bytes']<=258055 and p['initrd']['existing_guard_safe_superset']
warnings=(R/'evidence/compile-1.log').read_text().count('warning:')
sys.path.insert(0,str(R/'source'));import bootformat as b
h,k,ram,tail=b.parse_image((R/'artifacts/candidate.img').read_bytes())
layout=dict(android_page_size=2048,android_header_u32_fields=list(struct.unpack_from('<10I',h,8)),kernel_offset=2048,kernel_bytes=len(k),ramdisk_offset=2048+b.align(len(k)),ramdisk_bytes=len(ram),ramdisk_payload_bytes=len(ram)-512,candidate_bytes=p['candidate']['bytes'],full_p10_bytes=p['full_p10']['bytes'],android_boot_id=h[576:608].hex(),tail_bytes=len(tail),chosen_initrd_start=p['initrd']['start'],chosen_initrd_end=p['initrd']['end'],previous_current_chosen_end='0x4403e1ff',unchanged_guard_exclusion='0x44000000..0x4403f007',wrapper_stripped_bytes=512)
(R/'evidence/layout-receipt.json').write_text(json.dumps(layout,indent=2)+'\n')
status=dict(status='ONE_CANDIDATE_READY_FOR_PARENT_REVIEW_NO_PHYSICAL_GO',pid1_run_uuid=p['pid1_run_uuid'],helper_compile_invocations=1,compile_exit=c['exit'],compile_warnings=warnings,packaged_candidates=1,package_assertion_corrections_before_payload_generation=1,isolated_actual_default_PLAN_calls=1,device_or_ADB_commands=False,private_factory_or_raw_kernel_logs_accessed=False,remote_kernel_or_product_build=False,cloud_new_resources=False,resource_caps_changed=False,VM_id=vm['id'],VM_status=vm['final_status'],VM_start_stop_cycles=1,SSH_readiness_probes=vm['ssh_readiness_attempts'],physical_result='NOT_OBSERVED',saved_PL_reset32_meaning='UNKNOWN',next_variant=False)
(R/'evidence/final-status.json').write_text(json.dumps(status,indent=2)+'\n')
public=[W/'2026-11-06-asus-product-input-build-kit/scripts/remote.py',W/'2026-11-07-asus-linux49-ram-before-alarm-probe/source/init.c',*[W/'2026-11-07-asus-linux49-ram-before-alarm-probe/scripts'/n for n in ['compile_parent_once.py','package.py','plan_only.py']],*[W/'2026-11-07-asus-linux49-polling-idle-probe/source'/n for n in ['install.py','bootformat.py','fdt.py','adb','legacy_adb.py']]]
pins={str(f.relative_to(W)):dict(sha256=hashlib.sha256(f.read_bytes()).hexdigest(),bytes=f.stat().st_size,mode=oct(stat.S_IMODE(f.stat().st_mode))) for f in public}
(R/'evidence/public-code-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
rows=[]
for name,key in [('candidate.img','candidate'),('candidate.p10.raw','full_p10'),('init','init'),('init.c','init_source'),('initramfs.cpio.gz','compressed_initramfs'),('Image.gz-dtb (preserved compiled baseline)','compiled_Image_gz_dtb'),('resolved.config','config'),('runtime kernel gzip stream','compressed_Image'),('runtime raw Image','raw_Image')]:
 rows.append(f"| {name} | {p[key]['bytes']} | `{p[key]['sha256']}` |")
readme=f'''# One runnable PID1 timer observation

Question: while RAM PID1 stays runnable, does CLOCK_MONOTONIC advance, do arch_timer interrupt counts advance, and does an armed one-second SIGALRM arrive?

Status: **one helper compile and one candidate packaged; essential source/static-ELF/kernel/ramdisk/package checks and one isolated default PLAN passed. VM {vm['id']} is verified TERMINATED. No device/ADB command, installation, physical entry, or physical GO.** Parent owns all installation/reboot/physical work and nearby Power fallback. Stop after this candidate; no next variant.

Fresh helper identity: `ASUS49-RUNNABLE run={p['pid1_run_uuid']}`. The kernel entry UUID remains `23cdb057-295c-4b42-9ade-a4324162ad02`; use the new helper identity for this observation.

Evidence basis: the requested public short-log files and latest polling-idle RESULT are copied and pinned under `evidence/`. Physical Linux 4.9 plus RAM PID1 are proven. Complete printk.devkmsg=on resolved the logging confounder. The earlier 76 records show uname, proc/sysfs mounts, initial MMC enumeration, CLOCK_MONOTONIC 0.665805999 and alarm(10) setup returned; the first unfinished operation was the 100 ms blocking sleep. nohlt reached the kernel and retained that boundary; normal low-power idle hardware entry is therefore unnecessary to reproduce it, while NO_HZ bookkeeping remains. Initial mmc0/mmc1 hosts without card block nodes are an early snapshot, not terminal storage failure. Candidate/stock timer DT agrees at 13 MHz with PPI 29/30/27/26; stock PPI30 has counts and PPI29 is zero. Saved PL reset32 meaning remains UNKNOWN. No thermal/watchdog/IRQ/frequency cause is asserted.

| Output | Bytes | SHA-256 |
|---|---:|---|
{chr(10).join(rows)}

`SHA256SUMS` covers README, source, scripts, artifacts and evidence. `source/init.diff` and `source/install.diff` show the minimal changes relative to the inherited helper and current transport base.

The exact packaging base is polling-idle-probe candidate SHA `332ed4bef81b0529bad0b21642329c4b66af89ec7e7e17fba10750f963249765`. Its padded 16,740,352-byte p10 SHA `928efe92e7c8e617c571cd7512037be374d6c18815cb5303c37ae5e30465178d` is appended exactly to the existing admissions. This pin is supplied, not a fresh physical observation.

The helper preserves existing sink setup (O_NONBLOCK kmsg), actual getpid=1, uname, proc/sysfs-only mounts, and bounded MMC readers. Event records add phase=setup/before/observe/after/finish. Before the alarm it enumerates the same `/sys/class/mmc_host` and `/sys/class/block` names (32 non-dot entries, at most 34 readdir calls, names under 128 bytes), stats only mmcblk0/mmcblk0p1/mmcblk1/mmcblk1p1, and reads only dev/size/removable/device/type for present nodes using the existing once/max128 reader. It also reads only the two fixed public clockevent current_device paths with that reader.

Each before/after `/proc/interrupts` snapshot reads at most 32 KiB in eight calls of at most 4096 bytes, parses at most 256 complete lines and at most eight matching arch_timer lines, and accepts at most 16 CPU counters per matching line. It emits reconstructed numeric IRQ/counters/GIC/hwirq/name records only; no other interrupt lines, raw addresses or raw malformed text. It reports open/read/close errors, rejected arch_timer syntax, absent matches and byte/call/line/incomplete-tail bounds explicitly. A cap without EOF is conservatively possibly truncated. Compare counts by IRQ, GIC hwirq and CPU position. Snapshots bracket the loop plus setup/logging overhead, not an exact calibrated interval.

SIGALRM setup precedes observation. Its handler only sets volatile sig_atomic_t alarm_fired, attempts one async-safe write of a constant fired marker to the existing nonblocking sink, preserves errno, and returns. It never reboots, retries or formats output. Handler write completion is unchecked; the logged flag proves handler entry even if that marker is lost. Ordinary sink writes retain the inherited error tracker and 768-record/768-byte bound; the handler adds at most one marker for this one-shot alarm.

The successful observation path logs begin/end alarm(1), samples CLOCK_MONOTONIC initially, then repeatedly calls clock_gettime while runnable until observed delta >=1,500,000,000 ns or 2,000,000 iterations, whichever comes first. There is no sleep, yield, wait, fork or per-iteration log. It exits early on a clock error or counter regression. Final sample, sample validity, actual counter delta, iterations, stop reason, alarm flag and clock error are logged. On clock failure the final value retains the last successful sample; zero with sample-valid=0 is unavailable. Both samples use the same counter; this does not calibrate physical seconds.

After the loop the helper takes the second bounded timer snapshot and repeats the exact same MMC names/fixed metadata with phase=after, allowing later storage visibility to be observed. It then attempts SIGALRM block and cancellation, logs final alarm flag/completion/sink error, and attempts normal reboot once. A returning reboot parks using the inherited pause loop. Syscall begin/end records retain actual errors, including a block failure; a failed block does not trigger another reboot path. The loop's flag describes its completion point; alarm.final-flag can also reflect delivery during the later snapshots.

Expected decisive observations and limits:

- Increasing monotonic values establish counter progress while runnable. A counter-target stop establishes >=1.5 nominal counter seconds, not wall-clock accuracy.
- Increasing comparable arch_timer counts establish servicing recorded by those counters between snapshots. Counts alone do not prove that the PID1 alarm was delivered or identify a timer programming/routing defect.
- SIGALRM.fired or alarm_flag=1 proves this handler ran. Counter target plus changing counts plus flag=1 demonstrates runnable counter/timer/signal progress for this one unit; the earlier blocking-sleep path can still fail.
- Counter target with flag=0 records no handler by that point. Interpret together with actual samples, count deltas, final flag and errors; it does not independently calibrate the alarm or prove a hardware cause.
- Iteration-cap with delta <1 second and flag=0 is **not evidence of a missed alarm**. Frozen/small counter delta with a cap records bounded counter behavior only; no wall-clock duration follows from the iteration count.
- Missing after/complete records identify an unfinished observed boundary, subject to actual log delivery. No new mechanism or reset attribution follows. Later MMC presence/absence is a second snapshot only.

No persistent mount, block open or storage write occurs in the helper. No CID, serial, factory calibration, broad sysfs walk, USB setup or kernel/IRQ/clock/idle/watchdog/thermal patch. Parent Power fallback remains required: counter bounds do not bound a stuck syscall, and SIGALRM shares the timers/interrupts being observed. No independent timer protection is claimed.

Preservation: `evidence/source-scope-receipt.json` replaces the old exact-reorder assertion with explicit unchanged helper bodies, exact extracted MMC body, exact unchanged main setup and declared new main tail, reviewed new-function pins and bounds/call checks. The compiled source SHA is bound through the compiler and package receipts. Static ELF64 AArch64 has no PT_INTERP/PT_DYNAMIC. The kernel gzip stream/raw Image, compiled kernel/config, all hardware DT tokens, DT reservations/header/structure, kernel MTK wrapper, all load addresses and exact short bootargs are preserved. Command line is `{p['cmdline']}` ({len(p['cmdline'].encode())} bytes), including nohlt and full printk.devkmsg=on in both header and chosen.

Only the helper/cpio changes, necessary ramdisk wrapper/header lengths and boot ID, and chosen/linux,initrd-end change. Current base end was 0x4403e1ff; new end is {p['initrd']['end']}, start remains 0x44000000. Compressed payload {p['compressed_initramfs']['bytes']} bytes excludes the preserved 512-byte wrapper and remains below 258055; existing early exclusion 0x44000000..0x4403f007 is untouched. Cpio contains only root-owned init 100755 and dev/proc/sys directories 040755. Installer changes are hashes, actual image size, profile and exact current preimage addition; execute/Transport/Guard and adapters are byte-identical to polling-idle-probe. Adapters used copy2; source/adb remains 0755.

Compilation: one invocation of pinned `{c['compiler_version'].splitlines()[0]}` (SHA `{c['compiler_sha256']}`) with inherited `-static -Os -s -ffunction-sections -fdata-sections -Wl,--gc-sections -Wall -Wextra`; exit 0, {warnings} warnings. The exact authorized VM/project/zone/id/labels/host were verified before start and after running. Unchanged product-kit remote.py SHA is c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab. Bounded readiness allowed 180 seconds; the third probe succeeded at {vm['readiness_elapsed_seconds']:.2f} seconds, with first two SSH failures retained. Fresh remote prefix `/srv/android/asus-linux49-runnable-timer-format-fix-20261107-bee07d4f` contains this helper and compile evidence only. Only helper/source echo/small receipts were fetched. One start/stop cycle ended in verified TERMINATED. No kernel/product build, cloud resource creation, SSH/firewall change or address-space cap.

The first package check stopped before payload generation on an inherited stale base-end assertion. `base-layout-correction.json` and `package-attempt-1.json` preserve the failure. The assertion was corrected to the exact parsed value in the already hash-pinned current base; one candidate was then generated with no helper change/recompile/guard change.

One actual installer main default PLAN passed in the inherited isolated public-reader harness: a pinned public stock header supplies geometry, and only explicit public code hashes replace the private/root dependency manifest check in memory. Subprocess/socket/private/device access was denied. Delivered installer guards/input readers were unchanged. Private stock backup and private/root-helper dependency chain were deliberately not validated; parent owns fresh checks. No emulation, broad tests or physical trial.

Continuation: review source/installer diffs, hashes and receipts. Parent install command from `/OWNER_HOME/Documents/workspace/ideas`, provided only and **not executed**:

```sh
python3 -B 2026-11-07-asus-linux49-runnable-timer-probe/source/install.py --execute
```

Installer performs the existing guarded install/readback and does not reboot. Parent owns fresh identity/preimage verification, separate physical entry, nearby Power fallback, bounded observation and verified stock return. Match the fresh helper tag, actual command line/uname and new complete public records. No physical GO is issued here. Preserve this spike; stop after this candidate.
'''
(R/'README.md').write_text(readme)
paths=[R/'README.md',*sorted((R/'source').glob('*')),*sorted((R/'scripts').glob('*.py')),*sorted((R/'artifacts').glob('*')),*sorted((R/'evidence').rglob('*'))]
(R/'SHA256SUMS').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(R))+'\n' for f in paths if f.is_file()))
print(json.dumps(dict(status=status,candidate=p['candidate'],full_p10=p['full_p10'],compressed_initramfs=p['compressed_initramfs']),indent=2))
