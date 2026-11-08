# Stock retained-report control

Question: can one fresh PID1 `/dev/kmsg` marker from the working stock SD-report
recovery candidate survive its normal 60-second reboot and appear in the next
stock `/proc/last_kmsg`?

Status: **one static ARM64 helper compiled; one stock candidate packaged;
actual installer passed default PLAN_ONLY. No deployment or physical trial.**
The supplemental Linux 4.9 checkpoint patch is staged and applies cleanly;
it has **not been compiled or built into a new kernel**. Physical retention
remains unproved. The earlier physical #1/#2 stock controls establish that
modified stock data executes, not that this new marker survives reboot.

Important outputs:

- `artifacts/candidate.img`: 7,798,784 bytes,
  SHA-256 `70ff1f297bc50f11802de20a6fa8734a413a78304409890a9394c682af73a70b`.
- `artifacts/candidate.p10.raw`: 16,740,352 bytes,
  SHA-256 `a0e4856da4138dd401461add3104005fca67cf495da1a605c02392244dd757f8`.
- `artifacts/init`: 773,504-byte static AArch64 ELF,
  SHA-256 `a4c3cd9110c69ba5aeba9ddaefd4150f8b5e9999c74d9f0fb2bfd702a2d4f5cb`.
- `source/init.diff`, `source/install.diff`: complete changes from the working
  SD helper and stock deployment adapter.
- `source/install.py`: preserved deployment adapter, default PLAN_ONLY.
- `source/early-retained-checkpoint.patch`: three-file supplement to the existing
  retained writer; SHA-256
  `2991e2f9fdab79af5d87783fec3f3e7f0721cb8911df9f172c355d272489643d`.
- `evidence/packaging-receipt.json`, `evidence/helper-compile.json`,
  `evidence/install-plan.json`, `evidence/next-trace-patch.json`,
  `evidence/stock-transport.json`, `evidence/stock-transport.disasm`, and
  `evidence/source-pins.json` record the actual artifacts and source contract.

The local delivery is below 32 MiB. Matching candidate/full-p10/patch bytes also
reside in `/srv/android/asus-retained-report-control-20261107`; remote readback
hashes are in `evidence/remote-delivery.json`. This task used only that new remote
prefix for writes, through the restored fixed `remote.py`. It did not change
cloud lifecycle or contact the separate runtime-network-parity prefix. The VM's
previously scheduled November 8 stop was not changed.

## One stock control

The basis is the physically working stock SD candidate `eccfc87f…` from
`2026-11-07-asus-stock-kernel-sd-control/artifacts/candidate.img`. Its complete
7,472,341-byte MTK-wrapped kernel remains byte-identical:
`b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880`.
The raw Image stays `db90ee7f…`; the appended 62,482-byte FDT stays
`77e2d8fb…`. Stock Android addresses, page size, bootargs, SD marker/binding,
exclusive PROBE.TXT creation, watchdog and 60-second normal reboot are preserved.
Only init changes inside the same five-entry ramdisk. Component lengths and
Android image ID are updated. No new bootarg or FDT change is introduced.

Immediately after the existing tmpfs/proc/sysfs mounts, before SD discovery,
PID1 sets the console threshold with `klogctl(8, NULL, 1)`, creates `/dev/kmsg`
**inside its private tmpfs** as character 1:11, validates the node/opened fd,
and makes exactly one 95-byte write:

```text
<0>ASUS-stock-retained-control-20261107-v1 1fd4c968-c0b4-49ab-851a-b0ea4c50c01d pid1 /dev/kmsg\n
```

The final `\n` above denotes one LF byte. The `<0>` prefix selects level 0;
threshold 1 allows it despite stock silent mode. It is a diagnostic severity,
not a panic request. No retry splits or duplicates a short/ambiguous write.
No /dev/mem access, raw RAM/header writes, internal block mount/write, OEM
recovery program or filesystem-repair behavior is added. The existing SD report
adds the literal marker plus level/node/open/write/close results. Success is:
`kmsg_level_rc=0`, all `kmsg_*errno=0`, `kmsg_written=95`, `kmsg_expected=95`.
These syscall results do not themselves establish an OEM-console write or
physical retention.

`PROBE.ID` stays exactly `dbbb6afb-dd70-4c35-961e-9c977d7164a8` plus LF.
The output remains `PROBE.TXT`; parent must preserve the existing #2 report and
establish fresh report absence using its established card workflow before the
single trial. This task did not inspect or prepare the card.

## Why this is a supported transport attempt

`evidence/stock-source-excerpts.txt` and pinned retained public source explain
`devkmsg_write`, syslog action 8, console filtering and `sram_log_save`.
The exact shipped binary independently confirms the relevant path:

- `memory_open` resolves the 32-byte minor-11 entry at `0xffffffc000b384d8`
  from `memdevs=0xffffffc000b38378`. Its fops are `0xffffffc000ad96f8`;
  the +56 write_iter pointer is `devkmsg_write=0xffffffc0000ed718`.
- `devkmsg_write` parses the priority's low three bits, retains LOG_USER for
  userspace, and calls `printk_emit` at `0xffffffc0000ed7c4`.
- syslog's level case at `0xffffffc0000edcb0..0xedcd8` validates 1..8, clamps
  to the minimum, and updates console_loglevel at `0xffffffc000fb0148`.
  `call_console_drivers.constprop.24` reads the same address at
  `0xffffffc0000eb904` and dispatches enabled console callbacks.
- The registered `ram` console at `0xffffffc001002c28` has flags 0x15:
  PRINTBUFFER, ENABLED, ANYTIME; it is not CON_CONSDEV. Its +16 write pointer
  is `ram_console_write=0xffffffc000697478`, which calls `sram_log_save`.
- The previous exact reader analysis proves the same fixed
  `0x44400000..0x44480000` ring is copied before stock initialization resets it,
  and served by stock `/proc/last_kmsg`. See the original retained-trace REPORT
  and `evidence/stock-reader.disasm` in that preserved sibling spike.

This establishes a source/binary-backed attempt using the stock logger's own
mapping, bounds, ring management and restart handling. It does not establish
that the return sequence preserves the marker. No fallback RAM writer or new
OEM header is fabricated if the trial fails.

## Parent continuation: exactly one physical control

The following first command was run here and returned PLAN_ONLY with
`device_contacted=false`. The other two commands are for root's later physical
trial; **neither was run here**. The installer does not reboot.

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-retained-report-control/source/install.py
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-retained-report-control/source/install.py --execute
/OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-retained-report-control/source/adb -s IP_REDACTED:5555 reboot recovery
```

Use the parent's existing device lock/preparation/normal-return collection path.
The installer retains execute(), Transport, full readback, shared mutation lock,
one bounded inverse, uncertainty-stop behavior and all prior allowed preimages
exactly; no new preimage is admitted. An unrecognized full preimage still stops.
The copied adb shim intentionally depends on the existing wifi-microsd legacy
adapter and pinned real adb; keep sibling spikes in place.

On the immediate new normal Android boot, root collects and preserves the
**complete** actual `/proc/last_kmsg` through its already established path, plus
fresh PROBE.TXT and exact boot/install identity. This task supplies no new
collection helper or root/device operation. Search the collected host text with:

```sh
rg -F 'ASUS-stock-retained-control-20261107-v1 1fd4c968-c0b4-49ab-851a-b0ea4c50c01d' /absolute/path/to/collected-last_kmsg.txt
```

A fresh exact marker in actual last_kmsg proves the stock userspace injection,
retention and reader path across this return. A fresh SD report with successful
95-byte write but no retained marker means that transport is still unproved;
do not infer Linux 4.9 nonexecution or immediately generate another candidate.
A reported syscall error narrows failure to that API step. No fresh SD report
leaves PID1/SD reporting unresolved even if normal Android returns. Marker
presence can prove retention even if SD reporting separately fails.

## Narrow Linux 4.9 follow-on

The existing e9 writer uses the same stock text/header ABI but bypasses console
filtering by hooking log_store. It checks DT, memory reservations, overlaps and
all expected OEM header relationships, then cleans payload and aligned size
commit to PoC. The stock control validates the stock-owned path only: it cannot
prove those 4.9 guards pass, that 4.9 reaches paging, or that LK supplies the same
live layout. No supported header-guard correction was established, so none is
weakened.

The supplemental patch calls its guarded initializer immediately after
`arm64_memblock_init()` and before `paging_init()`. At this point the source has
initialized fixmap slots, finalized/reserved initrd and reserved DT regions.
`early_memremap(0x44400000, 0x40000)` uses PAGE_KERNEL normal cacheable attributes,
matching the later linear map. 256 KiB is the existing per-slot limit; the whole
512 KiB ring is never mapped through one early slot. The identical original
DT/memblock/header guards still validate the **full** reservation first. Extra
bounds require the Linux-reason area and first marker to fit in the temporary
window; other layouts defer to the original post-paging path. Only already
validated Linux reason/text/header fields are changed, never PL/LK sections.

It publishes:
`ASUS-e9-retained-v2 00 arm64_memblock_init returned; before paging_init`.
The existing IRQ-safe trylock and PoC payload-before-size publication are
unchanged. The temporary trace pointer is cleared and mapping removed before
paging. After paging, the normal initializer rechecks the original guards and
the early record before preserving it and appending the v2 marker 01. The
original later checkpoints and printk hook remain. No assembly/register handoff,
bootargs, timer, CPU, driver, memory reservation or config changes are added.

The supplement's three input-file hashes are pinned in
`evidence/next-trace-patch.json`; they match the prior delivered writer files.
Apply it only to an independent copy of that retained-probe source, after pin
checks. Its baseline includes any already present timer correction; this patch
adds none. Example later **VM commands**, not executed here:

```sh
mkdir /srv/android/asus-retained-report-control-20261107/next-trace
cp -a /srv/android/asus-retained-trace-kernel-probe-20261107/kernel /srv/android/asus-retained-report-control-20261107/next-trace/kernel
patch --batch -p1 -d /srv/android/asus-retained-report-control-20261107/next-trace/kernel -i /srv/android/asus-retained-report-control-20261107/source/early-retained-checkpoint.patch
```

Root can then perform one isolated <= -j8 build with the unchanged resolved
config (`0fddb41316305c672b0afd0a64b2615c6dae3c5727f5ff4ead791272ff71b696`)
if the stock control establishes transport. No full 4.9 build, object compile or
new 4.9 candidate is claimed here. Marker 00 without 01 would establish progress
to before paging, while still allowing failure in paging, subsequent logger
revalidation or later retention. Absence still permits earlier failure or guard
refusal. This is a bounded observation step, not a diagnosed boot fix.

## Checks and scope

One helper cross-compiler invocation completed without warnings/errors. Focused
checks parsed the actual output image, verified static ELF, exact kernel/DT,
wrappers/header/CPIO, LK's selected FDT and all unchanged SD/lifecycle functions.
The report's conservative 724-byte bound fits its 1,024-byte buffer. The actual
installer ran default PLAN_ONLY once. The supplement was applied to disposable
source copies and compared to staged files, including preservation of original
safety predicates and append/cache/lock code. No new test framework, host fake
retention, emulated boot, repeated review suite or physical proof is claimed.
The empty retained_marker disassembly in QA records compiler inlining; it is
not used as behavioral evidence.

No device/card/ADB/root-helper contact, private logs/calibration/factory/DATA
access, other workers' process inspection/signals, active product/AOSP/kernel
mutation, cloud lifecycle operation or subagent occurred. Older source and
artifacts were read-only inputs. Reproduce packaging only with
`python3 -B scripts/build.py`; recompilation is unnecessary for this delivery.
`SHA256SUMS` pins the final public packet. Scripts and QA remain in this spike.

## Parent physical result — 2026-11-07

PASS: actual fullp10 installed/readback+cleanup verifieda1c59781..., singleUSBRecoveryreboot acknowledged, safe new normalboot67f346b3-dd66-4339-81eb-a5afd566a000. FreshSDreport recorded95bytekmsgwrite andallzeroerrno. Complete127644byte last_kmsg contains exactfreshmarker; SHA25d5f5a621f5c724fa31a2f05c9155e43390574c798d5d032e72ce424266f77f. Publicphysical-retention.json and physical-log-layout.txt record physicalproof. Firstcollectorfailed at offline get-serialno before rootcommands; preserved. TargetedTCPendpoint reconnect then fresh authenticatedidentity allowed newcollection; existingADBserver notreset. SDreportrootarchivedKMSG.TXT;PROBE.TXT absenceverified. This establishes stockretention/readertransport, not Linux4.9execution or its guardpass. Earliercheckpointpatch2991e remainsstageduntilseparatebuild.
