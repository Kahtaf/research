# Physical Linux 4.9 startup gap

**No explanatory earliest-entry mismatch is proved.** One concrete early timer
DT/driver mismatch is present in the exact e9 binary, but the available physical
evidence does not show that execution reached it. It is not a justified boot-fix
candidate. The missing observation is an early execution record from this exact
4.9 recovery entry, before either SD or USB reporting depends on device drivers.

## Exact inputs and physical limit

The successful stock control's report records PID1=1, Linux 3.18.35, aarch64.
Its receipt pins image `eccfc87f…` and wrapped kernel `b0e5d48b…`. The original
public recovery `902b2f06…` contains that same wrapped kernel; this investigation
parsed it read-only. Receipt status labels written before the trials are not
substituted for the later physical observations.

The compiled input is `e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1`.
Its decompressed Image is `43ee0529e371575bfaddb9de392b77a2279cb44bc60649fcd8d9a88b6e613b09`.
The actual r2 image `291b824f…` contains that identical Image and embedded config
`10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`.
The embedded config equals the exported resolved config byte for byte.
The exact LK last-magic scan selects the FDT parsed here. r2 has initrd
`0x44000000..0x4403e4a3` and no header `initrd=` token.

r2's saved dispatch acknowledges one `adb reboot recovery` at 13:49:15 UTC.
The USB observer found no matching fresh identity. Stock Android's changed boot
ID was verified at 13:50:47 UTC. These facts neither establish 4.9 execution nor
identify its stopping point. The prior fixed-2-MiB and wrapper-offset premises
remain closed.

## Narrow hardware-contract result

The stock and e9 FDTs both describe MT8163/Cortex-A53, CPU IDs 0–3,
`enable-method="mt-boot"`, release address `0x40000200`, and legacy
`arm,psci`/SMC function IDs `0x84000001..04`. e9 preserves
`mediatek,mt8163` as its root fallback. Its embedded config enables
`CONFIG_MTK_PSCI`; `cpu_ops.c` includes `mt_cpu_psci_ops`, whose name is
`mt-boot`. The compiled Image contains `mt_psci_cpu_boot`, independently located
through its embedded kallsyms. A missing legacy CPU-method handler is not the
observed mismatch.

The architected timer remains 13 MHz with identical interrupt specifiers.
GIC-400 distributor/CPU-interface ranges and the MT8163 interrupt-polarity
controller also agree; changed phandle numbers resolve to their respective GIC
nodes. The compiled config enables their drivers and MT8163 clocks.

The static memory banks differ (stock's template has `0x20000000` bytes;
e9 has `0x7d600000`, both starting at `0x40000000`). The prior exact LK trace
already establishes runtime memory fixups. Without the final handed-off FDT,
this template difference is not evidence of the physical RAM map received by
Linux. ATF, ram_console and minirdump fixed ranges agree. No claim is made that
runtime memory initialization succeeded.

## One concrete mismatch: APXGPT rate comes from its bus input

The compiled e9/r2 FDT's `/soc/apxgpt@10008000` supplies inputs in this order:
`bus` (infracfg ID 6), `clk13m` (infracfg ID `0x46`), `clk32k` (topckgen ID
`0x60`). The driver binds through `mediatek,mt6577-timer` with
`CONFIG_MTK_TIMER=y`.

In `drivers/clocksource/mtk_timer.c:271`, it obtains **index 0** as `clk_src`
and then uses `clk_get_rate(clk_src)`. At lines 308–312 it programs GPT2 for
`TIMER_CLK_SRC_SYS13M` but registers that counter with the index-0 rate.
`clk-mt8163.c:476` defines index 6 as `infra_apxgpt`, parent `axi_sel`;
line 535 defines the separate `clk13m` as `clk26m / 2`.
Thus the selected clock object does not describe the programmed counter source.
The runtime AXI rate is unobserved; no numerical error factor is asserted.

This is present in the **actual compiled machine code**, not just an unused
source file: `mtk_timer_init` is at `0xffffff8008f42afc`. At
`0xffffff8008f42c30`, `w1=0`; `…2c34` calls `of_clk_get`; `…2c6c` calls
`clk_get_rate`, retaining the result in x26. `…2d54` selects source 0
(SYS13M), `…2d6c` calls `mtk_timer_setup`, and `…2d7c/…2d90` pass that retained
rate to `clocksource_mmio_init`. See [focused disassembly](evidence/e9-focused.disasm).

**Why this does not diagnose the boot gap:** this runs in `time_init`, after
entry, early DT/memory setup and IRQ initialization. No physical marker proves
those stages occurred. The architected timer's clocksource rating is 400 and
per-CPU clockevent rating 450; APXGPT's ratings are 300. Its wrong rate therefore
does not by itself prove that the boot timebase used it or that startup stopped.
No timer patch, build, or new trial image is proposed here.

## Smallest discriminating next step

Obtain **one retained early UART trace for the unchanged e9 recovery image**,
covering LK handoff and the first Linux output, if a known working UART capture
path is available. LK's already-audited default includes
`earlycon=uart8250,mmio32,0x11002000`, and the exact e9 config enables 8250
earlycon. Capture availability and actual UART output have not been established
here; silence on an unvalidated UART would not diagnose anything.

A fresh e9 Linux banner/early printk would establish execution beyond the
assembly entry; output through timer initialization would decide whether this
specific mismatch is even reachable in the failed attempt. A positive LK
handoff record without Linux output would still leave the secure-monitor/early
assembly boundary unresolved. The prior LK audit stops at SMC with entry in r1
and FDT in r2; actual AArch64 PC, EL, x0 and cache/MMU state remain unobserved.

If no validated early capture route exists, **that missing observation blocks
the startup diagnosis**. Another SD/USB-report package cannot resolve this
boundary merely by failing to report. No device operation or new trial was
performed or authorized by this research result.

## Evidence and continuation

[Input receipts](evidence/input-receipts.json),
[stock contract](evidence/stock-contract.json),
[e9 contract](evidence/e9-contract.json),
[r2 contract](evidence/r2-contract.json),
[binary symbol receipts](evidence/e9-symbols.json), and
[source receipts](evidence/source-receipts.json) retain the bounded inspection.
All 16 explicit source files fetched read-only from the supplied VM path match
their r5 source-manifest hashes; none is among the full-kernel source delta.
No cloud lifecycle/process inspection, build, dependency installation, device
access, private-folder contents, calibration/DATA/table access, or prior-artifact
mutation occurred. No subagents were used.

`scripts/compare.py` reproduces local artifact extraction.
`scripts/inspect_timer_binary.py` uses the existing boot-audit venv's Capstone
to reproduce only the retained compiled slices. `scripts/read_sources.py`
refetches only the explicitly listed source files; it is not needed to read
this packet. Continue from the missing execution observation, not another
speculative hardware change or product build.
