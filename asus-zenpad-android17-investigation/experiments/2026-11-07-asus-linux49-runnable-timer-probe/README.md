# One runnable PID1 timer observation

Question: while RAM PID1 stays runnable, does CLOCK_MONOTONIC advance, do arch_timer interrupt counts advance, and does an armed one-second SIGALRM arrive?

Status: **one helper compile and one candidate packaged; essential source/static-ELF/kernel/ramdisk/package checks and one isolated default PLAN passed. VM 8549823276971553556 is verified TERMINATED. No device/ADB command, installation, physical entry, or physical GO.** Parent owns all installation/reboot/physical work and nearby Power fallback. Stop after this candidate; no next variant.

Fresh helper identity: `ASUS49-RUNNABLE run=83cc6715-05b7-48be-aaff-44ea5186ba8a`. The kernel entry UUID remains `23cdb057-295c-4b42-9ade-a4324162ad02`; use the new helper identity for this observation.

Evidence basis: the requested public short-log files and latest polling-idle RESULT are copied and pinned under `evidence/`. Physical Linux 4.9 plus RAM PID1 are proven. Complete printk.devkmsg=on resolved the logging confounder. The earlier 76 records show uname, proc/sysfs mounts, initial MMC enumeration, CLOCK_MONOTONIC 0.665805999 and alarm(10) setup returned; the first unfinished operation was the 100 ms blocking sleep. nohlt reached the kernel and retained that boundary; normal low-power idle hardware entry is therefore unnecessary to reproduce it, while NO_HZ bookkeeping remains. Initial mmc0/mmc1 hosts without card block nodes are an early snapshot, not terminal storage failure. Candidate/stock timer DT agrees at 13 MHz with PPI 29/30/27/26; stock PPI30 has counts and PPI29 is zero. Saved PL reset32 meaning remains UNKNOWN. No thermal/watchdog/IRQ/frequency cause is asserted.

| Output | Bytes | SHA-256 |
|---|---:|---|
| candidate.img | 7974912 | `e8627d4f4d55f0a91cceb0bad493bec9a6a8ecdd3caccdc5508129ca3820375d` |
| candidate.p10.raw | 16740352 | `63431c259ed2c6051448912ea804b45a3aefa1b8bbbee24a77437ae669830be6` |
| init | 598000 | `7847d08b6084b7b3b6a15289be2637842dd7a3ccc510e8c91de541440c680769` |
| init.c | 10276 | `3d350bfafb200f6ae6c973a973a27f0e1a018a81826485688d1d776a1650f3ed` |
| initramfs.cpio.gz | 256127 | `58977711d5eff60bc641c31b9b86d33a5b26de4b7b44747a13ae84ae8f5a56d3` |
| Image.gz-dtb (preserved compiled baseline) | 7713482 | `97b7e1199d607f852bf52ff7766e8aa079fee92986cd3d473b765a45adbf45fb` |
| resolved.config | 126443 | `708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1` |
| runtime kernel gzip stream | 7649861 | `29437894a38cba034db136aa5ea3f1c930edf6ff6abcfc14a4dd652ceeebc491` |
| runtime raw Image | 17342976 | `60755a9910450cb0303157017ddb4f6ff08874fca32bf70298bb5a91d5450381` |

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

Preservation: `evidence/source-scope-receipt.json` replaces the old exact-reorder assertion with explicit unchanged helper bodies, exact extracted MMC body, exact unchanged main setup and declared new main tail, reviewed new-function pins and bounds/call checks. The compiled source SHA is bound through the compiler and package receipts. Static ELF64 AArch64 has no PT_INTERP/PT_DYNAMIC. The kernel gzip stream/raw Image, compiled kernel/config, all hardware DT tokens, DT reservations/header/structure, kernel MTK wrapper, all load addresses and exact short bootargs are preserved. Command line is `bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1 printk.devkmsg=on nohlt` (85 bytes), including nohlt and full printk.devkmsg=on in both header and chosen.

Only the helper/cpio changes, necessary ramdisk wrapper/header lengths and boot ID, and chosen/linux,initrd-end change. Current base end was 0x4403e1ff; new end is 0x4403e87f, start remains 0x44000000. Compressed payload 256127 bytes excludes the preserved 512-byte wrapper and remains below 258055; existing early exclusion 0x44000000..0x4403f007 is untouched. Cpio contains only root-owned init 100755 and dev/proc/sys directories 040755. Installer changes are hashes, actual image size, profile and exact current preimage addition; execute/Transport/Guard and adapters are byte-identical to polling-idle-probe. Adapters used copy2; source/adb remains 0755.

Compilation: one invocation of pinned `aarch64-linux-gnu-gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0` (SHA `cd90adc7801f4595267f61a5d25bd3a0c6beb2f9f1f107ab919a97a12972dc9a`) with inherited `-static -Os -s -ffunction-sections -fdata-sections -Wl,--gc-sections -Wall -Wextra`; exit 0, 0 warnings. The exact authorized VM/project/zone/id/labels/host were verified before start and after running. Unchanged product-kit remote.py SHA is c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab. Bounded readiness allowed 180 seconds; the third probe succeeded at 38.73 seconds, with first two SSH failures retained. Fresh remote prefix `/srv/android/asus-linux49-runnable-timer-probe-20261107-83cc6715` contains this helper and compile evidence only. Only helper/source echo/small receipts were fetched. One start/stop cycle ended in verified TERMINATED. No kernel/product build, cloud resource creation, SSH/firewall change or address-space cap.

The first package check stopped before payload generation on an inherited stale base-end assertion. `base-layout-correction.json` and `package-attempt-1.json` preserve the failure. The assertion was corrected to the exact parsed value in the already hash-pinned current base; one candidate was then generated with no helper change/recompile/guard change.

One actual installer main default PLAN passed in the inherited isolated public-reader harness: a pinned public stock header supplies geometry, and only explicit public code hashes replace the private/root dependency manifest check in memory. Subprocess/socket/private/device access was denied. Delivered installer guards/input readers were unchanged. Private stock backup and private/root-helper dependency chain were deliberately not validated; parent owns fresh checks. No emulation, broad tests or physical trial.

Continuation: review source/installer diffs, hashes and receipts. Parent install command from `/OWNER_HOME/Documents/workspace/ideas`, provided only and **not executed**:

```sh
python3 -B 2026-11-07-asus-linux49-runnable-timer-probe/source/install.py --execute
```

Installer performs the existing guarded install/readback and does not reboot. Parent owns fresh identity/preimage verification, separate physical entry, nearby Power fallback, bounded observation and verified stock return. Match the fresh helper tag, actual command line/uname and new complete public records. No physical GO is issued here. Preserve this spike; stop after this candidate.
