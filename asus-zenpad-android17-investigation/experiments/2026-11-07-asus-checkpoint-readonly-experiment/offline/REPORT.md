# Offline checkpoint contract check

Completed 2026-11-07. Only named public local kernel artifacts, source, config and receipts were read. No device, network, SSH, VM, build, image creation, RAM access, reboot or private input was used. `check.py` emits small evidence only here; run with the existing `2026-11-05-asus-boot-access-audit/.venv/bin/python -B` from workspace root. No dependency installation.

| Contract question | Result | Evidence / limit |
|---|---|---|
| Existing shipped saved-fiq diagnostic reader | PASS | Public stock Image contains `aee_rr_show_fiq_step`, format ` fiq step: %u ` and call to `seq_printf`. This is an existing concrete reader, not merely a 3.18.22 source inference. |
| Shipped field ABI and setter | PASS | Reader loads u32 header `off_linux` at +0x2c, then u32 at saved-base + off_linux + 0. Setter zero-extends its argument to u8 and performs a **32-bit** store at current-base + off_linux + 0, gated by initialized flag and nonnull current pointer. Full stored field is u32; setter accepted values are 0..255. |
| Saved versus current state | PASS | Reader uses global 0xffffffc001278568; setter/current getter use 0xffffffc001278560. Shipped early initializer copies 0x80000 bytes into the saved allocation before resetting current layout/reason area. Thus reading current fiq is not equivalent to the saved reboot diagnostic. |
| Stock reset preservation or fresh checkpoint delivery | UNKNOWN | Static reader presence cannot establish that firmware/reset preserves the intended bytes, a future writer commits them, stock accepts the resulting header, or stock snapshot is from that attempted boot. |
| Latest 4.9 appended DT versus logger's listed static guards | PASS | Root includes `asus,p00a`; reserved-memory has cells 2/2 and empty ranges. Exactly one static reservation intersects [0x44400000,0x44480000): `ram_console-reserved-memory`, exact base/size, `mediatek,ram_console`, absent status (accepted), absent no-map/reusable. No other child `reg` intersects. |
| Runtime DT, memblock and OEM header guards | UNKNOWN | Appended DT is package data, not proof of actual 4.9 runtime DT. Dynamic reservation placement, map-memory/reserved-page checks, loaded kernel/FDT/initrd overlaps, OEM header validity and early-map bounds were not exercised. A current stock DT/header snapshot is not 4.9 runtime evidence. |
| Corrected Linux-owned-field initialization source identity | PASS (receipt/source) | Retained C SHA matches 8373…3348. It derives Linux layout from PL/LK geometry, resets start then size, assigns sz_buffer/off_linux/off_console/sz_console and clears Linux reason area. It does not require preexisting Linux-owned layout/ring fields on first initialization. Watchdog handoff receipt names this logger SHA, then packaging receipt preserves its raw Image/config. This is provenance evidence, not a fresh full binary implementation audit. |

## Exact shipped instruction evidence

See `stock-fiq.disasm` for raw bytes, function hashes and the small relevant functions (including initializer):

- `aee_rr_show_fiq_step` 0xffffffc000695368, Image offset 0x615368. At +0x10 `ldr w2,[x1,#0x2c]`; +0x18 `ldr w2,[x1,w2,uxtw]` when nonzero; `seq_printf` at 0xffffffc00069538c. Format resolves to 0xffffffc000e37a38.
- `aee_rr_rec_fiq_step` 0xffffffc0006976c8, Image offset 0x6176c8. `uxtb w0,w0`; initialized flag at current-global +0x24; `ldr w2,[x1,#0x2c]`; `str w0,[x1,x2]` at 0xffffffc0006976e8. No cache clean/barrier is present in this small setter itself; reset durability is not established by it.
- `ram_console_early_init` stores current pointer at 0xffffffc000f41444. It validates signature/header (invalid input can be zeroed); allocates 0x80000 bytes, stores saved pointer at global +8, and byte-copies that full region at 0xffffffc000f414e4..f414f4. It then writes current off_linux (+0x2c), off_console (+0x30 = off_linux+0x400), sz_buffer (+0x28), sz_console (+0x3c), zeroes counters (+0x34/+0x38), and clears current Linux region before setting initialized flag. Reader can therefore display an earlier saved snapshot while current state has been reinitialized. Allocation failure and invalid incoming headers remain relevant conditions.

The public 3.18.22 reference corroborates the names/layout (`struct last_reboot_reason` begins u32 fiq_step) but differs from shipped 3.18.35; shipped instructions above are the ABI evidence. The shipped initializer itself shows the 0x400 reason-to-console spacing.

## Pins

| Artifact | SHA-256 |
|---|---|
| stock original.img | f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140 |
| stock decompressed Image | db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a |
| latest4.9 candidate.img | cc367b543eebea476b15a9033648c9547e48c7ac02d8c42856b372623bffb265 |
| latest4.9 decompressed Image | e1f5bb0a417d1819773719ffa09d01c96884ac29363900e3a5c1a7f36b55c72c |
| latest4.9 appended DT | 94cdeca7ad226e1e34fc1d0abc3fc3f4806eef8b8d9aa3904cda1f92024639c0 |
| latest4.9 resolved.config | 708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1 |
| corrected retained C | 8373baa301650d2bf3befe547df11a3079e22c51aec8a207de64eae0f1bb3348 |

All exact source/decoder/receipt paths and hashes are in `evidence.json`; extracted reserved DT properties are in `latest49-dt.json`. Config has CONFIG_ASUS_P00A_RETAINED_BOOT_TRACE=y, CONFIG_OF_RESERVED_MEM=y, CONFIG_HAVE_MEMBLOCK=y and CONFIG_ARM64_4K_PAGES=y.

This establishes a concrete existing saved-value reader and no obvious mismatch in the enumerated static DT guards. It neither creates nor calibrates a checkpoint writer. A marker absent from RAM or the saved diagnostic never proves nonexecution unless writer execution/readback and reset retention are calibrated. No arbitrary RAM write is proposed.
