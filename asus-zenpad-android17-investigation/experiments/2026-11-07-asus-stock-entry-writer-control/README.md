# Stock entry writer control — STOP

Question: can R2's unchanged stackless pre-MMU retained-console writer be positively calibrated on the known-working stock RECOVERY kernel, allowing only an additive `asus,p00a` root compatible marker?

Status: **STOP: the extracted stock DT fails R2's fundamental memory-bank contract.** One local standalone AArch64 assembly and one focused actual-byte execution completed. No candidate, installer, isolated PLAN, installation or physical GO was produced. The VM was not started; no device, ADB, network, SSH, cloud, private inputs, full kernel build, reboot or subagent was used.

## Concrete obstacle

The pinned donor's `/memory@00000000/reg` is:

```text
0000000040000000 0000000020000000
base 0x40000000, size 0x20000000, end 0x60000000
```

R2 requires the exact base `0x40000000` and size `0x7d600000`, ending at `0xbd600000`. Its actual source at `source/asus_entry_text.S:559..570` decodes the 16-byte `reg`, compares the base, then compares the size and refuses on mismatch. Adding the permitted compatible marker cannot change that comparison. Changing the hardware memory property or relaxing this check is outside this unit's authorization. The requested explicit stop condition applies before placement, readback-slot work or packaging.

This is a refusal on the **packaged stock DT with the permitted marker added**, not a measurement of the physical stock handoff. LK may edit DT contents; this unit neither observes nor assumes a runtime bank rewrite. It does not claim that the actual installed RAM ends at `0x60000000`.

## One actual binary/ABI check

`source/asus_entry_text.S` is byte-identical to R2 SHA-256 `32f22ec90acd2fc6787a15589ada5c2a1d06117768b43cc8ab88051c11cbfc5a`. The header is also an exact R2 copy. Its old R2 UUID remains solely in this unshipped fixture; **it is not a fresh stock-control identity**. No new control UUID or production entry binary was created.

Apple clang assembled `qa/unit.S` once with `-target aarch64-none-elf`. `source/check_once.py` used the already installed local camera fixture Python environment for Unicorn/Capstone/pyelftools; nothing was installed. It relocated and executed the actual object, using the existing R2 synthetic `_text=0x40080000`, `_end=0x41280000`, valid synthetic OEM geometry, supplied CurrentEL=EL1 and SCTLR=0. These fixture extents are **not stock symbol addresses or a stock load/BSS proof**.

Exactly one case ran: the original extracted stock DT with root compatible changed from `mediatek,mt8163\0` to `mediatek,mt8163\0asus,p00a\0`. Every other property, token, node order, original compatible membership/order, memreserve bytes, string table and trailing bytes was preserved. Only required FDT size/string-block-position accounting changed. Stock DT is 62,482 bytes, SHA-256 `a627db960f72733f52e52426b553477153bcdaa5865a3127eb29a2a5df48d53d`; marker-only fixture is 62,494 bytes, SHA-256 `39b2a9a5aa4e6ce2edbd863e169a9dbee008737386ef6a80e8040fcfe0016f18`.

The decisive fixture instructions were:

```text
0x400809c8 10acafd2  mov x16, #0x7d600000
0x400809cc bf0110eb  cmp x13, x16       ; x13 = 0x20000000
0x400809d0 a11e0054  b.ne #0x40080da4  ; taken to writer end
```

Execution ended after 228,222 instructions with **zero stores** and the entire 0x80000-byte retained fixture unchanged. x0–x3, x18–x30 and SP were preserved. Static disassembly retained x4–x17/NZCV scratch restrictions, no BL/BLR, stack access or callee-saved writes, and the unchanged final `str w17,[x4,#0x38]; dsb sy` commit sequence. This establishes the specific DT refusal, not a positive writer calibration or actual stock-entry preservation.

Important outputs:

- `evidence/focused-check.json`: pins, exact failed comparison, preservation and limitations.
- `evidence/refusal-trace.disasm`: final actual instructions and observed register operands.
- `qa/unit.o`, `qa/unit.text.bin`, `qa/unit.disasm`: single compiled fixture and relocated actual bytes; assembly/check stderr are empty.
- `source/{stock.dtb,stock-marker-only.dtb,asus_entry_text.S,asus_entry_tag.h,check_once.py}`: exact inputs, allowed isolated DT edit and one-case driver.

## Stock bytes remain unmodified

The donor SHA-256 was independently checked as `dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427`; decompressed original raw Image was `db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a`. The unchanged ramdisk's helper was independently checked as `631a0aa5e72ee4110357ddac12bc5e5436ef3b1924cf64355f6fae99dc96d272`.

Pure stock `kallsyms.decode()` and actual disassembly confirmed the original raw offset 0 instruction `10000014` branches to stock VA `0xffffffc000080040` (physical `0x40080040` **if** loaded at `0x40080000`). The existing clear at VA `0xffffffc000f41564`, raw offset `0xec1564`, remains bytes `4924c597`, `bl 0xffffffc00008a688` (`__memset_io`). Neither was patched. No appended entry/return target, verified append bounds, stock BSS placement, readback wrapper, relocated production tag, changed raw Image spans, candidate/full-p10 hashes or installer diff exists. No later mapped-code slot was selected. These downstream steps were stopped at the demonstrated contract failure, rather than supplied as unproved patch instructions.

No candidate was packaged, so there was no public packaging check or installer PLAN to run, and no current `f547c8fd3819b01efef6a232197aa5670dcbe332a83edcbc20529b2a07a08e42` preimage admission to add. The parent installer, a49/R2 images, donor, BOOT/SYSTEM and all prior spikes remain unmodified. The helper, its nominal 60-second alarm/normal reset, watchdog and USB paths were not changed.

## Continuation boundary

The next smallest missing observable is **the exact `/memory@00000000/reg` bytes in stock's LK-delivered x0 FDT**, supplied as public evidence by the parent. A packaged value alone cannot prove what LK passes. No new instrumentation, device capture, future variant or build is authorized by this unit. Do not rewrite stock memory to satisfy the guard and do not relax R2's contract.

R2's physical result remains `UNKNOWN_NO_FRESH_ENTRY_TAG`; experiment 3 is not admitted. Even a future positive stock control would calibrate the writer at stock entry/handoff only, not actual 4.9 runtime DT-guard admission. Absence remains UNKNOWN. This bounded unit ends here.
