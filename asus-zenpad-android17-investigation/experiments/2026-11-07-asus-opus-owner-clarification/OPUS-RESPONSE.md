Stripping the framing aside: this is an ordinary custom-kernel bringup on your own tablet, and I'm happy to reason about it as such. I'll answer plainly as Claude from the public evidence you supplied — I'm not running tools this turn, can't verify your hashes, and I'm reasoning fresh rather than reconstructing anything. I'm also not going to adopt the "an orchestrator will halt this on fallback / don't attribute 4.8's answer to 5.5" persona; it doesn't change the engineering, and I can't speak to what some previous invocation did.

## Diagnosis of your method

**What your facts actually establish (this is strong):** the recovery → kernel → standalone PID1 → USB/SD-report pipeline is fully proven *with the 3.18.35 kernel*, including custom-code execution (the UTS byte change) and a corrected stock-driver USB path. The EBUSY/`android_usb`-owns-`musb-hdrc` discovery correctly reclassified your earlier "no USB" as an instrument bug, not a kernel failure. Net effect: host, cable, media, ramdisk delivery, PID1, and the reporting channel are all controlled. **You have isolated the failing variable to exactly one thing: the 4.9 image itself.** That is real progress and most teams never get the controls this clean.

**The bad premises:**

1. **You blinded your best instrument.** `CONFIG_SERIAL_8250_CONSOLE=n`, earlycon off, `console=null` — removed on the strength of a "suspicious UART PC" whose capture epoch you yourself can't establish. For bringup that is exactly backwards. The LAST PC addresses (E) are uninterpretable (stock kallsyms on 4.9 addresses is meaningless, epoch unproven) and should not have driven a config decision.

2. **Your retained-RAM logger is not a trustworthy "did the kernel run?" oracle.** Read `asus_retained_trace.c`: it refuses silently unless the *runtime* FDT presents root `asus,p00a`, a `reserved-memory` node with exact `#address/#size-cells`, empty `ranges`, a child at exactly `0x44400000/0x80000`, compatible `mediatek,ram_console`, status okay, memblock reserved+mapped, no overlap — a long chain you have **never independently confirmed exists in the handed-off DT**. Any mismatch → `goto refuse`, zero bytes, kernel possibly running fine. So your flagship negative ("0 logger markers in 507 KB") is nearly uninformative. You half-flag this; it should be the headline.

3. **Source ≠ runtime, applied inconsistently.** You correctly say it for FDT/registers, then reason hard about the APXGPT clock (F) and watchdog (C/D) as if they were observed faults. Both occur *deep* in `time_init`/probe — long after entry — and you have no evidence execution gets there.

4. **You instrumented mile 20 before proving the runner left the start line.** configfs reporters, descriptor chains, retained loggers — all require the kernel to reach substantial C. You have *zero* evidence it reaches *any* C.

**What's actually missing:** one ground-truth observation of the *earliest* execution — did the CPU enter the decompressed kernel at all. Everything else is downstream of that unknown. Note the mechanism: on MediaTek, LK decompresses `Image.gz-dtb`; the kernel's `head.S` only runs *after* LK's decompress-and-jump. So "did any 4.9 instruction execute" cleanly separates an LK/handoff/load/header/decompression failure from an early-C failure — and you have nothing that distinguishes those two worlds.

## Three credible paths

**Path A — DT-independent assembly entry marker (differential, lowest dependency).** Add, as literally the first instructions of the 4.9 `head.S` entry (MMU off, D-cache off — so a raw `str` of a magic word to a *fixed physical address* plus a `dc civac` to push it to DRAM; `head.S` already documents these exact entry conditions), a write into the same `0x44400000` ram_console region stock preserves. Add a **second** magic word just before `start_kernel` (post-paging). No DT, no memblock, no console dependency.
- *Positive:* stock boot reads magic #1 back → 4.9 executed to entry. Both words → entry + MMU/paging survived, death is later.
- *Negative:* neither word despite a verified build → the kernel is never reached; LK handoff/load-address/header/decompression is the fault and all deep porting is premature.
- *Timebox:* one build + one recovery trial; ~half a day. *Verify offline first* by disassembling the built Image to confirm the stores sit at the entry and target the literal physical address. *Stop condition:* if the fixed-address write risks clobbering something stock needs, fall back to Path B.

**Path B — Re-enable earlycon, capture to persistent RAM (don't assume you need external UART).** Turn 8250/MTK earlycon back **on** and route printk into pstore/ramoops so the ring persists, then read it back through the proven stock path — no probe wires required. This directly challenges your "we need a UART route" conclusion: you don't need to *capture* the wire if early output lands in persistent RAM the stock kernel already reads.
- *Positive:* a 4.9 banner/early printk in the read-back buffer.
- *Negative but informative only if Path A already proved entry* — otherwise silence is as ambiguous as today.
- *Timebox:* one build. *Fallback:* if ramoops wiring is itself unproven on this tree, Path A is the cleaner first move.

**Path C — Early arch/DT-contract mismatch (deprioritize until A).** The real early-killer candidates for 3.18→4.9 on MT8163 are `setup_machine_fdt`/reserved-memory strictness and the image-header/`MIN_KIMG_ALIGN`/`__primary_switch` placement contract (4.9's `head.S` differs materially from 3.18's). The APXGPT clock (F) and watchdog (D) live *after* `time_init` and are **not** worth a patch yet. Do not build a blind matrix around them.

## The one best next step

**Do Path A.** Build one otherwise-unchanged 4.9 image with two fixed-physical-address magic-word stores (entry, and post-paging), **verify offline by disassembly before flashing**, then run a single recovery trial through your existing proven path. Unchanged kernel otherwise; one build; no new hardware.

**What it changes about the OS-flash decision:**
- *Entry word present* → you are running your own code; the problem is downstream and porting is worth continuing. Next move: re-enable earlycon (Path B) to localize the downstream death. A full Android 17 flash is still **not** justified until early userspace is reached.
- *Entry word absent, build verified correct* → the kernel never executes; the failure is LK/load/header/decompression, every driver/timer/watchdog hypothesis is moot, and a full flash has essentially zero boot chance. Pivot entirely to the boot wrapper/load-address/header contract — or treat Android 17 as not yet feasible.

Either outcome is the first fact that tells you whether you are even running your own kernel, which is the question all your other evidence silently assumes.

**On a later live USB read (none done here):** keep it to read-only, decision-relevant observations — the magic-word region contents at the fixed address, the fresh stock boot ID, and a confirmation the recovery entry was acknowledged. If a read fails, report the failure rather than inferring from its absence, and don't treat host metadata timing as execution timing.

One honest caveat: I can't confirm your build toolchain places the stores where intended — that's exactly why the offline disassembly check precedes the trial. That check is the cheap insurance that makes the negative result trustworthy.**Model fallback:** claude-opus-5-5[1m] declined this request (cyber); retried with claude-opus-4-8. The session will continue on claude-opus-4-8.