# Stock checkpoint reset loss — bounded offline diagnosis

Question: why did the physically read-back current fiq value 167 become saved fiq 0 after the unchanged normal reset?

Status: **COMPLETE; no demonstrated Linux overwrite/reader mismatch and no supported missing-cache-clean diagnosis. Stop scalar variants; use the already physically validated retained-console checkpoint.** This analysis cannot distinguish selective firmware/reset-time loss from changes to the incoming Linux layout before the next stock snapshot. It does not establish a firmware culprit. No new candidate was built or packaged.

The parent’s public result is `CURRENT_WRITTEN_SAVED_NONMATCH`: exactly one current readback, 167, and saved fiq 0 on normal Android boot `c62d7755-35bb-4e53-920c-e69d136043f7`. The retained console contains the actual getter-derived `A7_READ=167` line. That proves the current setter/getter and this text checkpoint, not scalar preservation. Missing 4.9 text still cannot establish nonexecution. See `evidence/physical-selected.json`; raw console/private payloads were not opened.

## What the exact shipped binary establishes

All addresses below are VAs with prefix `ffffffc0`; raw Image base is `0xffffffc000080000`. Evidence files retain full addresses, little-endian instruction bytes and SHA-256 hashes.

**Current and saved layouts were traced separately.** The current global is `0xffffffc001278560`; saved is `0xffffffc001278568`. The setter at `0xffffffc0006976c8` checks the initialization flag at **global +0x24 = 0xffffffc001278584**, loads current, reads its u32 header +0x2c, then stores a u32 at current+that offset. The getter reads the same location. This is the Linux reason field, not a preloader/LK reason or watchdog register.

The initializer at `0xffffffc000f41350` maps physical `[0x44400000,0x44480000)` and installs current. It checks signature `0x43474244` and header geometry. Invalid signature/header branches to the whole-region `__memset_io` at `0xffffffc000f41474`, **before** snapshot; that would erase the retained text as well. No condition tests or clears a nonzero fiq specifically.

At `0xffffffc000f414cc`, it installs a newly allocated 0x80000-byte saved buffer; `0xffffffc000f414e4..f414f4` copies **every byte of the incoming region**, including its incoming header +0x2c and field. Only afterward does it derive the new current Linux offset: default 0x200, or `header[0x10] + 2*round_up_64(header[0x18])` when the nonzero-size/platform geometry matches `header[0x14]`. It writes current +0x2c, sets current +0x30 to Linux offset+0x400, and clears current from Linux offset through the end at `0xffffffc000f41564`. This later current clear cannot zero an already copied saved field. Platform header offsets +0x04/+0x08/+0x0c and +0x10/+0x14/+0x18 are distinct from Linux +0x2c; no equivalence between their records was assumed.

The next stock proc reader opens `aee_rr_reboot_reason_show` through the pointer at `0xffffffc0006aee68`. Its accepted-header callback table includes `aee_rr_show_fiq_step` at table entry `0xffffffc001002ca8`. That function loads **saved**, loads saved header +0x2c and reads saved+that offset; it does not reuse the newly computed current offset. `ram_console_show` likewise loads the same saved global, then uses saved +0x30/+0x34/+0x38 for the ring. The scalar and text have different subregions but a common snapshot. No Linux reader-offset correction follows from these instructions.

**Normal NULL reset resolves to the watchdog reset routine, not the similarly named keepalive routine.** After the patched notifier wrapper returns, the unchanged notifier calls `arch_reset` at `0xffffffc00080028c`. NULL takes the branch at `0xffffffc000800160` to `0xffffffc00080021c`, sets w21=1, logs/dumps the stack, then calls the watchdog table +0x20 with w0=1. The actual table entry at `0xffffffc00106bca0` is `wd_sw_reset` (`0xffffffc0007ffd40`), which calls `wdt_arch_reset` (`0xffffffc000800ac8`). `mtk_wdt_restart` is a separate keepalive implementation, not this callback.

`wdt_arch_reset` resolves the watchdog MMIO base and writes the restart/mode/software-reset registers. It contains no current/saved pointer access, Linux reason store, header rewrite or RAM-console clear. It executes **DSB ST** (`9f3e03d5`) at `0xffffffc000800b40`, `0xffffffc000800b70`, and `0xffffffc000800b8c`; the last precedes the software-reset store of 0x1209 at `0xffffffc000800b9c`. The ordinary printk RAM writer uses current header +0x30 for console bytes and +0x34/+0x38 for ring counters, not the Linux fiq field. These bounded paths expose no subsequent scalar overwrite. This is not a claim to have audited all asynchronous execution.

## Why a flush calibration is unsupported

The initializer passes **x3=0x02e0000000000703** to `vmap` at `0xffffffc000f413cc`. The protection flows unchanged through `vmap` into `vmap_page_range_noflush`, where it is ORed with the page frame and stored in the PTE (`0xffffffc00019a2c8..a2d8`). AttrIndx bits [4:2] are **0**.

`__cpu_setup` loads the literal at `0xffffffc000ad0a30`, bytes `00040c44ff000000`, and writes MAIR_EL1 at `0xffffffc000ad09fc`: **MAIR=0x000000ff440c0400, Attr0=0x00, Device-nGnRnE**. The setter uses this current vmap pointer; the text ring uses it too. These are concrete binary mapping attributes, not a conclusion from the word “SRAM” in `sram_log_save`. The physical retained area is DRAM-backed here; platform/SRAM diagnostic records are not interchangeable with this Linux area.

Thus absence of a cache-clean instruction in the tiny setter does **not** establish a dirty-cache persistence defect. The evidenced mapping is not a normal write-back mapping, and the later normal watchdog path already has store-completion barriers. Live page tables/aliases and firmware behavior were not inspected, so this does not prove universal cache correctness or reset retention. It does mean an extra BL to a global flush routine has no established target defect or safety justification in this diagnosis. **No flush routine/ABI or 48-byte wrapper proposal is recommended.** Physical slot capacity alone is not evidence that cache maintenance is appropriate.

## Exact pins and decisive bytes

The read-only script independently checked donor SHA-256 `dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427`, decompressed original Image `db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a`, readback candidate image `042c1a63a699f6a978c589341801580a5c4f46fde23832ad174f42c763940260`, and patched raw Image `610c7e459f8493ab668f59834c9db469e7a98b2e658a610d51ca6233c4cdcf91`. Parent full-p10 pin is `d6949069eaa498fcfbc27be707d01dffd7099992c5eb71e2c7c3926639851355`. Relevant initializer, mapping, setter/getter, arch/watchdog reset and saved-reader bodies are byte-identical between the public donor and readback candidate; documented wrapper/notifier edits are excluded from that assertion.

- Initializer: 576 bytes, SHA-256 `da7a041358995511c6028e3e2daa60eb7df7a2b03af5c117edf0a3ba133fc9c8`.
- Header validator: 176 bytes, SHA-256 `d91a3913c3e8d43791759182df6c8835a4e94a6400072d6daeada481bc9474ce`.
- `wdt_arch_reset`: 308 bytes, SHA-256 `896c1c9a752d2b1ecc581abe78210ae5fa04d3a7e445394008827714ccfb2d6c`.
- Saved fiq reader: 48 bytes, SHA-256 `8a0b7dd9bcfe10d8d2909e048f0ba6e87dcb084eb53a700764648760558b94dd`.
- Snapshot loop at `0xffffffc000f414e4`: `626a613802682138210400913f0042f181ffff54`.
- Reset barrier/trigger span at `0xffffffc000800b8c`: `9f3e03d5600e42f92141825200500091010000b9`.

`evidence/exact.json` contains exact byte spans, addresses, offsets and hashes. `core.disasm`, `mapping-reset.disasm` and `reader.disasm` contain the bounded function bodies. Public 3.18.22 source was not used to override the shipped 3.18.35 instructions.

## One next discriminator and stop boundary

**Abandon scalar retention for the next Android17-path checkpoint.** Parent should use one uniquely tagged, getter/execution-derived checkpoint through the already physically validated retained-console route at the earliest relevant 4.9 milestone, then inspect the next retained console for that exact tag. This moves the next discriminator onto a channel that just preserved actual stock execution across this reset. It is one future checkpoint experiment, not a repeat of the stock scalar trial or a flush variant. A positive tag proves reaching its emitting milestone; a missing tag remains inconclusive until that kernel’s writer/admission path is established. Stock text success does not itself validate a new 4.9 writer.

No more scalar variants, firmware investigation or hardware work follows from this spike. Parent decides and executes any physical next step. No device/network/SSH/private payload access, builds/compiles, VM startup, installation, reboot or subagent occurred. Original artifacts were read only. Reproduce the offline evidence from workspace root with:

```sh
2026-11-05-asus-boot-access-audit/.venv/bin/python -B 2026-11-07-asus-stock-checkpoint-reset-loss/source/diagnose.py
```
