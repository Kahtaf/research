# Stock entry writer positive control R2

Question: can the **same unchanged R2 pre-MMU writer**, running once at stock RECOVERY entry, expose its actual fresh UUID bytes through stock initialization and the retained console?

Status: **ONE CANDIDATE PACKAGED; one successful actual-binary/ABI preparation replay and one isolated installer PLAN passed. No physical/OS flash GO.** This is a continuation positive control within experiment 2. The full 4.9 R2 result remains `UNKNOWN_NO_FRESH_ENTRY_TAG`; no experiment 3 or additional 4.9 variant is admitted. No device, ADB, network, SSH, cloud, private input, full kernel build, VM startup, install, reboot or subagent was used. Only local standalone ARM64 assembly/link and public binary packaging occurred. All prior artifacts are unchanged.

Important outputs:

- `artifacts/candidate.img`: 7,747,584 bytes, SHA-256 `d0a680bac719cd303065d010bddbd60ff802dbbd6d33492cc9ebf0979658f5e0`.
- `artifacts/candidate.p10.raw`: 16,740,352 bytes, SHA-256 `80fe0f339e2a2d609e3f6a9583b4b8ca2f9104ccbb5810a0d25178475b4bc73f`.
- `evidence/packaging-receipt.json`: exact original/changed raw spans, appended bytes, entry/return/readback addresses, hashes, ABI observations, scope and limitations.
- `evidence/completion.json`: static placement, readback, console replay, callback reachability and PLAN receipts.
- `evidence/{install-plan,plan-isolation-receipt}.json`: exactly one isolated PLAN; delivered installer unchanged by the isolation.
- `source/{asus_entry_text.S,asus_entry_tag.h,entry.S,readback.S,control.ld,install.py,install.diff}` and `qa/control.elf`: actual sources, link and installer specialization.

Fresh control UUID: **`d58fbb99-4da1-47e1-98f2-d316bf05085a`**. The complete 234-byte tag is in `evidence/preparation.json`. It retains `ASUS49-ENTRY` and identifies this stock R2 control, donor and exact writer source. The assembly is byte-identical to R2 SHA-256 `32f22ec90acd2fc6787a15589ada5c2a1d06117768b43cc8ab88051c11cbfc5a`; only the tag header identity/provenance/length and stock relocations differ. EL/MMU/cache/FDT/OEM guards, scratch restrictions, stores, barriers and final commit are unchanged.

## Parent runtime admission

Parent observed normal working stock boot `f53fef38-8c1e-40f2-aa9a-1b149cda93a9`, root cells 2/2 and `/proc/device-tree/memory@00000000/reg = 0000000040000000000000007d600000`, bank `[0x40000000,0xbd600000)`. Copies of the public observation and explicit fixture admission are in `evidence/`. This is an **unflattened normal stock DT**, not direct pre-MMU x0 capture or the failed 4.9 runtime DT. It does not unconditionally establish who edited the property.

Exactly one successful preparation replay used the actual stock DT plus permitted compatible marker, with **only the memory reg overlaid from that observed runtime value**. The overlay is `qa/fixture-runtime-memory.dtb`, not candidate data. The delivered DT is `source/stock-marker-only.dtb`: original `mediatek,mt8163\0` membership/order followed by `asus,p00a\0`; **all other properties/tokens, hardware data, memreserve and trailing content remain original**, including the packaged `0x20000000` (512 MB) placeholder. Guard relaxation and candidate memory-property replacement did not occur. Qualification of the future physical control itself tests the runtime admission; no unavailable x0 capture is demanded before preparation.

## Exact stock placement

The public donor is `../2026-11-07-asus-stock-legacy-ram-usb-reporter/artifacts/candidate.img`, SHA-256 `dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427`. Its raw Image is 16,963,568 bytes, SHA-256 `db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a`.

Shipped head literals establish `_text = 0xffffffc000080000` (literal at `0x80228`), complete kernel mapping/reservation end `0xffffffc001335000` (`0x80230`), and BSS `[0xffffffc0010ad7f0,0xffffffc001330018)` (`0x80240/248`). These data symbols are not exposed by this stock kallsyms table; their concrete shipped literals and consumers, with matching public head.S context, are the proof rather than invented decoded symbol names. The original ARM64 header Image size `0x12b5000` equals end minus `_text` and stays unchanged.

Append begins **exactly after the original raw payload**, at BSS start `0xffffffc0010ad7f0`, physical `0x410ad7f0` for load `0x40080000`. Entry code is 3,496 bytes; its required R2 read-only parser strings and fresh tag follow. The entire append is 3,930 bytes, ending at VA `0xffffffc0010ae74a` / physical `0x410ae74a`, safely inside original BSS and original reserved kernel extent ending `0x41335000`. No cave or extra reservation is assumed. The early stock page-table clear starts at physical `0x41331000`, beyond this append. After return and MMU enable, the actual stock loop at `0x80270` clears the entire original BSS, including the now-dead append. Nothing calls the appended code/data later. Readback lives in original mapped text.

The pinned LK common decompression path passes destination from the Android header's kernel address and capacity `0x1c00000`; see `evidence/LK-decompression-bounds.disasm` and the prior pinned LK receipt. Candidate output is 16,967,498 bytes, ending well before that capacity, LK staging, initrd at `0x44000000`, retained console at `0x44400000`, and the original kernel end. The pinned last-DT-magic scan/tail rounding plus raw-inflate semantic packaging model passed. This model uses host zlib, not executed LK; it does not claim secure-monitor, actual x0/EL/cache state or hardware boot success.

Exact original raw replacement spans (little-endian bytes):

- Raw `0x0`, four bytes: original entry B `10000014` becomes `fcb54014`, branching to appended writer. Its final B returns to original stock stext VA `0xffffffc000080040` / physical `0x40080040`.
- Raw `0xec1564`, four bytes, VA `0xffffffc000f41564`: original `4924c597` BL `__memset_io` becomes `6c55dd97` BL wrapper `0xffffffc000696b14`.
- Raw `0x616b14`, 131 bytes, VA `0xffffffc000696b14`: readback code plus private seven-byte format replaces the beginning of the 352-byte `aee_rr_show_idvfs_ctrl_reg` diagnostic callback. The remaining 221 bytes and adjacent functions/data are untouched. Full before/after bytes are in the receipt.

These spans contain 139 original bytes, 122 of which differ. Every other original raw byte is identical; the only growth is the 3,930-byte append. Patched raw SHA-256: `d3a356a7c095cf68be1242873908bb5d33ce76477de75c8a5694ddd4fb8db067`.

## Actual incoming-text readback

Stock first validates and snapshots the incoming 0x80000-byte region, then overwrites current Linux offsets/counters and clears current Linux storage. The wrapper uses **saved global `0xffffffc001278568`**, so it reads the incoming snapshot even though current metadata has already been reset. A failed saved allocation skips logging and still clears.

Before printk it requires `off_console >= 0x400`, `off_console < 0x80000`, nonzero incoming size no greater than `0x80000-off_console`, and start=0 (the unchanged writer's nonwrapped incoming record). Precision is `min(incoming_size,234)`. It passes **saved pointer + incoming off_console** as x2 to the inline `\x011%.*s\0` format. UUID bytes are read from actual memory; the wrapper contains no constant UUID. The size/bounds checks prevent unbounded scans even without a NUL. A missing, malformed or wrapped incoming record can skip or produce nonmatching text; absence remains UNKNOWN.

The 48-byte aligned frame saves x29/LR and all original clear arguments x0/x1/x2. The wrapper writes no other callee-saved register. After the bounded printk it reloads those original arguments and calls original `__memset_io` at `0xffffffc00008a688`, then restores x29/LR/SP and returns. All branches, including NULL/invalid cases, converge on the original clear. No clear, normal reset or watchdog operation is skipped or removed.

The slot's only live absolute reference is `0xffffffc001002ef8` in the diagnostic callback table traversed by `aee_rr_reboot_reason_show`, reached through its proc open callback. The other occurrence `0xffffffc000c0a948` is the decoded kallsyms address table, with adjacent symbol values checked. There are zero external direct B/BL instructions into the slot. Matching public source uses the function only in that proc callback table. The preserved sole PID1 helper opens no `/proc/*` file and launches no other process; it never invokes this callback. The next normal Android reader runs the unchanged BOOT kernel. This slot reuse relies on that fixed RECOVERY helper scope; it is not suitable for a general-purpose interactive recovery.

Stock RAM console object at `0xffffffc001002c28` has write `ram_console_write = 0xffffffc000697478` and flags `0x15`, including **CON_PRINTBUFFER**. Actual `register_console` checks flags bit 0 at `0xffffffc0000ee4c0`, restores replay indices and invokes `console_unlock`. The printk at the wrapper runs before the original clear and before `register_console` at `0xffffffc000f41570`. Thus printk's own ring can replay those actual incoming bytes into the cleared current retained ring. Exact original printk, registration, RAM writer and snapshot bodies are retained as bounded disassembly; the earlier public mapping/reset evidence is copied. This establishes the intended binary path, not physical retention.

## One focused check and installer PLAN

Apple clang `-target aarch64-none-elf` assembled the two standalone files; the already installed Rust toolchain's `gcc-ld/ld.lld` linked `qa/control.elf` using `source/control.ld`. No fetch/install/full kernel build occurred. The linked ELF has no remaining relocation sections. A preliminary static tag extraction assertion was corrected to exclude R2's parser constants sharing `.init.rodata`; no candidate or replay had been produced at that point.

The single successful Unicorn pipeline executed the actual physical header B, linked unchanged writer and return to stock stext. It used the disclosed runtime-memory overlay, actual stock extents, explicit EL1/SCTLR=0 and synthetic valid OEM geometry. It preserved x0–x3, x18–x30 and SP; 241 retained-region stores included the actual 234-byte tag and unchanged commit/barrier sequence. Platform record bytes remained intact. It then executed stock's real incoming snapshot byte loop and geometry/counter instructions through the patched clear call. The wrapper passed **actual saved snapshot bytes** to printk, then the original clear arguments, with callee-saved registers, return LR and SP preserved. printk and memset were explicit local contract stubs that clobbered caller-saved registers to check the wrapper ABI. Kernel allocation/vmap, printk internals, actual console replay, reset and retention were not emulated. No broad test suite or second candidate followed.

Public packaging checks reparsed delivered candidate/full-p10 bytes, gzip/tail/container IDs, DT preservation, complete ramdisk/helper and zero padding. The helper remains exactly SHA-256 `631a0aa5e72ee4110357ddac12bc5e5436ef3b1924cf64355f6fae99dc96d272`; its 60-second alarm, normal reset, watchdog, USB behavior and all bootargs/addresses remain intact. BOOT/SYSTEM/DATA were untouched.

`source/install.py` specializes the readback-control installer only in candidate hash, full-p10 hash, actual image size, profile and appended allowed full preimage `f547c8fd3819b01efef6a232197aa5670dcbe332a83edcbc20529b2a07a08e42`. Reversing these substitutions reproduces the complete parent file. `execute`, `Transport`, `Guard`, adapters and all original admissions are byte-identical.

Exactly one isolated `main()` PLAN passed. In memory only, it substituted the pinned public original stock header template for `b.local_inputs`, and a no-op for `a.check_sources`, avoiding private backups/root-helper manifest reads. Delivered input readers and guards remain unchanged. This PLAN does not validate those private inputs, current device identity/health or a fresh physical preimage.

## Continuation boundary

Preparation is complete. **Do not rerun the one-shot build/check/PLAN scripts or create another candidate from this unit.** Parent owns its existing admission workflow, one supervised RECOVERY trial, physical fallback and subsequent normal-stock retained-console collection. The prepared installer defaults to PLAN:

```sh
python3 2026-11-07-asus-stock-entry-writer-control-r2/source/install.py
```

A matching fresh UUID from actual retained console would positively calibrate this writer's stock entry/handoff and text route for that trial. It would **not** prove actual 4.9 runtime DT admission. Missing/nonmatching text stays UNKNOWN. No further experiment, build, interface, bypass, module, panic or driver work is authorized here.
