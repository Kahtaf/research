# Stock scalar checkpoint control

Question: can a narrowly instrumented stock recovery record step167 during its normal reboot and have original Android read it back?

Status: **PACKAGED; parent review complete; physical installation and trial pending nearby Power-fallback availability.** No new kernel compilation, VM start or physical operation occurred. Exactly two instruction words change one diagnostic print into the existing kernel-owned step setter. Reset arguments and hardware/reset operations are preserved. Prior actual stock RAM-PID1 runtime evidence confirms the expected route; universal reachability is not claimed.

The initial conservative findings and the later evidence resolving them are preserved in `evidence/initial-findings.md` and `evidence/runtime-route.json`. This README describes the current packaged result. The original BOOT/SYSTEM/DATA remain untouched. Parent's current plan is in `evidence/parent-status.json`.

## Packaged control and evidence

Parent supplied `evidence/runtime-route.json`, a sanitized prior retained-log stack demonstrating this stock raw kernel's normal RAM-PID1 reboot reached `mtk_arch_reset_handle` → `arch_reset`. Parent clarified the semantic constraint: the CALL must follow preservation of live reset arguments; the x0 tag load may precede their stores because x0 was solely the log format argument. That resolves the initial gates for this bounded experiment. The original initial report is preserved verbatim in `evidence/initial-findings.md`.

Status now: **LOCAL PACKAGED, ISOLATED PLAN PASSED; NO PHYSICAL GO.** Exactly two instruction words changed:

| VA | Raw offset | Before bytes | After bytes | Meaning |
|---|---|---|---|---|
| 0xffffffc00080026c | 0x78026c | 00800d91 | e0148052 | final format-address add → mov w0,#0xA7 |
| 0xffffffc000800278 | 0x780278 | 4cf90a94 | 145dfa97 | BL printk 0xffffffc000abe7a8 → BL aee_rr_rec_fiq_step 0xffffffc0006976c8 |

The tag load only changes original log argument x0. Existing x2/x1 stack stores at270/274 execute before the new call. The shipped setter clobbers only caller-saved x0/x1/x2; the original handler reloads x2/x1 at27c/280, reconstructs w0/x1 at284/288 and invokes unchanged arch_reset at28c. The log return was unused. Stack, x29/x30 handling, watchdog/reset instructions and all other raw kernel words are unchanged. Actual after-disassembly is `evidence/patched-handler.disasm`.

One essential local packaging check (`source/package_control.py`) verified the two-word raw delta, exact complete donor ramdisk/helper/static AArch64 ELF preservation, exact appended DT, original gzip header and level9 compression, all header metadata/addresses/arguments except required kernel-size/ID changes, original MTK wrapper except payload length, and zero container/partition padding. No kernel compilation occurred. It specialized the failure-log installer only in image hash/full hash/length/profile and appended the current full p10 preimage `0b1a3c45751d688ba304743dc74e73f7030586c6fafece32eedf0da39c86455d`; execute/Transport/Guard and copied legacy adapters remain byte-identical. Original admissions remain.

| Output | Bytes | SHA-256 |
|---|---:|---|
| artifacts/candidate.img | 7745536 | ebc410fb95113d74c2b16fe7a56e398215b99fcad4f6c948946af49de7e07bc4 |
| artifacts/candidate.p10.raw | 16740352 | b403e999805fcbbc76b988100cad5c49f13f5ca33fb70e99b555d6292e2107db |
| decompressed patched Image | 16963568 | 980cc9b540b8dae7a428d2f2f0d8114e6173bac35a22dda2f2f40f3204b28056 |

One isolated installer `main()` PLAN passed. It substituted pinned public original.img for the private stock-input reader and made source-manifest checking a no-op **in memory only**, avoiding private backup/root-helper reads. The delivered installer retains those original readers and guards. Thus the isolated PLAN does not validate private backup/source manifests or fresh device state. See `evidence/install-plan.json`, `plan-isolation-receipt.json`, and `packaging-receipt.json`.

Parent command for its own supervised admission/installation workflow: `python3 2026-11-07-asus-stock-scalar-checkpoint-control/source/install.py` (PLAN); physical flags must follow the unchanged installer's CLI and parent supervision. No physical command was executed here.

Expected saved readback is **167 (0xA7)** after this control's normal reset. The expected route was observed previously, not guaranteed universally; route bypass is an allowed failed calibration. Setter initialized/current-pointer guards, write visibility/cache flush, reset retention, snapshot identity and saved-reader acceptance remain unknown until physical calibration. A missing tag establishes neither nonexecution nor a 4.9 failure location. A matching saved tag is a stock-based control result with an explicit two-word kernel delta, not unchanged-stock execution. Prior donor automatic return does not prove automatic return for this new image. Original BOOT/SYSTEM/DATA are untouched by this local work; the specialized installer targets recovery p10 only. Parent owns fallback and physical commissioning.
