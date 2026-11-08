# ASUS USB retained-log initialization

Question: does the diagnostic writer wrongly require firmware to initialize the Linux-owned retained-RAM fields before Linux can log?

Status: source-only correction staged; five focused host cases pass with AddressSanitizer and UndefinedBehaviorSanitizer. No kernel build, VM, network, device operation, image assembly, or active/frozen-input edit was performed. This removes an unjustified prerequisite; the actual firmware header at the failed entry is unobserved, and the cause of the hardware reset remains unknown.

The exact stock `mtk_ram_console.c`, lines 543–561, saves the previous buffer and then computes `off_linux` from the LK layout (or 512), sets `sz_buffer`, computes `off_console` and `sz_console`, and resets `log_start`/`log_size`. Its reader, lines 514–525, uses those fields to emit the previous console. Consequently, requiring those Linux fields to be usable before the new Linux writer initializes them can suppress every marker even when the firmware signature and layout pass. No firmware header contents are assumed or invented here.

Important outputs:

- `retained-linux-owned-initialization.patch`: change against the pinned prior writer only.
- `source/arch/arm64/kernel/asus_retained_trace.c`: complete staged corrected writer.
- `evidence/source-pins.json`: absolute input locations and SHA-256 pins for the stock source, previous writer, staged writer and patch.
- `qa/test_init.py`, generated `qa/host_init.c`, and `qa/results.txt`: reproducible host checks of the actual staged C with kernel/mapping stand-ins.

The patch retains the existing DT, full reserved-memory, memblock, kernel, initrd, FDT, firmware signature and PL/LK guards. It computes the Linux layout in 64-bit temporaries, retains the positive console-capacity guard, and validates the computed Linux reason/marker endpoints against the temporary 256 KiB mapping before any initialization. Only the header's six Linux fields and the already-existing Linux reason/marker destinations are written. The first 40 header bytes and PL/LK payloads are not initialized. The inherited 0x400 Linux reason size is unchanged; this is not a new ABI or reader.

After an early marker has committed, the linear-map handoff requires all four derived Linux layout fields, both expected counters and the exact early marker to remain intact before any write. A changed counter, layout field or marker is refused. A valid firmware layout that exceeds the early mapping remains untouched early and can initialize through the original linear fallback.

Readback/reset semantics: preserve the existing ordered counter reset (`log_start=0` cleaned before `log_size=0` cleaned), then publish and clean the derived metadata. This avoids introducing a `log_size < log_start` interval during counter reset: the stock reader subtracts those values. Payload stores still clean to PoC before the aligned size commit. Only the Linux reason block is zeroed; the console tail is not zeroed outside the temporary map. Zero size hides stale tail bytes. The header update is not an atomic transaction; a reset during initialization can leave incomplete metadata and no marker. Cache cleaning is not a guarantee against power loss, firmware erasure, or DRAM loss. Retention and stock-reader behavior across the actual next recovery trial remain untested.

Focused cases: zero Linux fields plus early-to-linear preservation; stale invalid Linux metadata/counters and ordered reset; signature/PL/LK/range refusals without writes; early mapping refusal plus linear fallback; committed-marker/metadata corruption refusal. Host stand-ins do not validate real DT parsing, cache maintenance, kernel integration, physical memory, or firmware survival.

Continuation: apply only this patch to an independent copy of the exact pinned previous writer, leaving existing inputs unchanged. Run `python3 qa/test_init.py` from this directory if needed. The separate authorized device workflow can then build/package and trial once, allow the normal stock return, and retrieve stock `last_kmsg` over ADB USB. A missing marker alone cannot establish where the attempted kernel reset or whether it entered this initializer.
