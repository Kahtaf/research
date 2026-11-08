# Stock Linux offset control — scoped experiment 2

Question: does the parent-corrected Linux offset commit in the stock early hook, and does the complete fresh OEM text survive through the actual incoming snapshot readback?

Status: **one candidate packaged; focused actual-instruction replay and one isolated installer PLAN passed. No physical trial and no 4.9 build.** Parent owns one stock trial. Require both independent positives before admitting one 4.9 build with the staged parent correction. Any negative: stop and report; no additional calibration variant or driver fix.

The preceding physical trial established early magic `454559535452454e`, x0 `4e000000`, CurrentEL `8` (EL2), SCTLR `30c50830`, status `72` hex (114), under late UUID `ddfa517b-e809-45c8-83d9-a573403b3e68`; normal Android returned as `be73a526-a85c-4880-a9d6-6c2babd80aac`. This is the parent-supplied physical result, not a new measurement here. ID 114 formerly rejected derived Linux offset below 512 despite stock using a smaller derived offset when valid nonzero LK records exist.

## One package and pins

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `artifacts/candidate.img` | 7747584 | `adfcb88a77d9cab0648eed78a068961133d9b0dd08451d70736eb87ac46479b2` |
| `artifacts/candidate.p10.raw` | 16740352 | `ed054366765198d628f62086627a753daeae645cadf1d431be0e11315a649bbe` |
| Unmodified public donor image | 7745536 | `dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427` |
| Original raw stock Image | 16963568 | `db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a` |
| Patched raw Image | 16968578 | `4f53983442646e06aae97effe209ca954dfff08045e7e8f66f31780fba0d9867` |

Donor image byte count is recorded by the pinned source parser; the SHA is authoritative. Current full p10 preimage: `10c4c72da182f8164c238c27901b855e963eb1b5b66bb13827878f9f9c64370e`. Candidate full p10 is exactly **16740352** bytes, zero-padded after the Android image. Full before/after bytes and appended bytes are in `evidence/packaging-receipt.json`; source pre/post SHA-256 values and diffs are in `evidence/source-pins.json` and `evidence/*-*.diff`. `evidence/file-manifest.json` pins every delivered source, QA output and evidence file.

The instrumented writer differs from capture by exactly `.Laet_linux: cmp x14,#0x200` → `cmp x14,#0x40`. The default `mov x14,#0x200` remains unchanged. **ID 114 now means derived Linux offset <64**; all other IDs and conditions are unchanged (`evidence/failure-ids.tsv`). Complete PL/LK extent, alignment, nonoverlap, header and console-capacity checks remain. No new fix was invented.

The parent-corrected plain assembly SHA is `e56fffecd0f825439d3711ab931180d58a5a320e70ebb8b30fcc5e8442cd631d`; corrected C SHA is `76d9ff38bbf47995594a4795fe5af5b22f78b93fa91f6190bb4bbdf1c864721e`. Exact copies and `correction.patch` are in `source/future-4.9/`, **handoff only, unbuilt**. The OEM tag's `writer=` identifier is inherited R2 baseline identity; these source pins identify the applied correction.

## Actual dual observer and bounds

Fresh shared run UUID: **`3de99973-f225-47d8-9b0b-6d51a530ce40`**. Complete actual OEM tag, including its terminating newline (234 bytes):

```text
ASUS49-ENTRY run=3de99973-f225-47d8-9b0b-6d51a530ce40 stage=stext-preargs stock-control=LC donor=dc0b98e66798e3abc019f454921b1c84ff3ce58e356e26d0785e05b7714d3427 writer=32f22ec90acd2fc6787a15589ada5c2a1d06117768b43cc8ab88051c11cbfc5a
```

The tag is stored by the early writer. The late wrapper never prints a constant copy: it prints actual own-record fields first, then passes validated **saved incoming snapshot + off_console** to priority-1 `%.*s`, then calls original `__memset_io`. Saved global is VA `0xffffffc001278568`. It requires saved nonnull, `0x400 <= off_console < 0x80000`, `0 < size <= 0x80000-off_console`, start=0; precision is `min(size,234)`. It neither scans an unbounded string nor reads past the admitted snapshot. A short/partial text result is not complete-tag calibration.

At original clear BL VA `0xffffffc000f41564` (raw offset `0xec1564`), the wrapper uses the existing unused slot `[0xffffffc000696b14,0xffffffc000696c74)` (raw offset `0x616b14`, 352 bytes). Code is **152 bytes**, code+formats **274 bytes**, leaving **26 bytes** before the record. Record is fixed at offset **300**, VA `0xffffffc000696c40`, physical `0x40696c40`, length **40**; 12 bytes remain after it. The linker and packaging assertions prove nonoverlap. No active production slot or new BSS record was used.

The five little-endian u64 record fields are magic, original x0, CurrentEL, matching SCTLR (or sentinel), terminal status. Record is initially zero. Actual early magic is `454559535452454e`; terminal commit is `ffff`. Late format is exactly:

```text
ASUS-ENTRY-DIAG 3de99973-f225-47d8-9b0b-6d51a530ce40 magic=%016llx x0=%016llx el=%llx sctlr=%016llx status=%llx
```

A 48-byte aligned frame preserves original clear x0/x1/x2 and x29/LR/SP; x18–x28 are untouched. Both printk calls may clobber caller-saved registers. Original clear target is `0xffffffc00008a688`; original printk is `0xffffffc000abe7a8`. Early record capture, all terminal refusal IDs, and targeted `DC CVAC` publication are unchanged from capture (`evidence/cache-visibility.json`). Early boot x0–x3, x18–x30 and SP survive.

The Image entry B at raw offset 0 branches to appended VA `0xffffffc0010ad7f0` / PA `0x410ad7f0`, returning to PA `0x40080040`. Append ends at `0xffffffc0010aeb82` before original BSS stop `0xffffffc001330018`, within original Image reservation/LK capacity. No other original raw spans change. Stock callback table and kallsyms pointer values remain unchanged; inherited sole fixed-PID1 helper does not invoke the diagnostic proc callback. The exact prior unused-slot/callgraph proof and stock code excerpts are retained as `evidence/prior-r2-*` and `prior-*`.

Stock DT is byte-identical to capture's compatible-member-only `asus,p00a` marker DT; original 512MB placeholder and other properties stay. Runtime `0x7d600000` bank is a **replay fixture only**. Whole wrapped ramdisk SHA is `f2430b3e0ec09076e11654758e9c8a2e45f62f07208a79bc612095ae751c05e3`; helper remains `631a0aa5e72ee4110357ddac12bc5e5436ef3b1924cf64355f6fae99dc96d272`. No reporter compile, RAM-dump facility, same-boot helper change, normal BOOT/SYSTEM/DATA write, or clear/reset/watchdog change occurred.

## Focused local evidence

| Actual instruction replay | Record commit | Actual complete fresh OEM text read before clear |
|---|---|---|
| low-LK-offset | True | True |
| no-LK-fallback | True | True |
| LK-header-overlap | False | False |
| LK-platform-overlap | False | False |
| zero-early-record | False | False |

Low-LK derives `0xc0`; zero-LK falls back to `0x200`. Header overlap and PL/LK platform overlap refuse before any OEM store. All late cases print the actual record unconditionally and call the original clear with original arguments; adversarial printk/clear substitutes clobber x0–x17, and preserved ABI registers/LR/SP remain intact. `evidence/replay.json` retains exact fields, refusal tests, read pointers and actual snapshot bytes. Parser checks use those replayed bytes (`evidence/observer-contract.json`). MRS state is an EL2 fixture; DC addresses are checked without emulating coherence. Printk/clear are local ABI substitutes. **Host replay is not physical retention or 4.9 entry proof.**

The first interpreter attempt stopped at a missing Capstone import before replay/package; its stderr is retained as `qa/import-failure.stderr`. Existing local dependencies supplied the successful replay, without install. Standalone clang assembly and Rust-toolchain ld.lld linking only; no full kernel build.

## Parent command and readback contract

Exact parent install command, for the parent's already-guarded single physical stock-trial workflow (not executed here):

```sh
python3 /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-stock-entry-linux-offset-control/source/install.py --execute
```

Installer changes relative to capture are only candidate/full pins, size/profile, and appending current `10c4c72da182f8164c238c27901b855e963eb1b5b66bb13827878f9f9c64370e` preimage. `execute`, `Transport`, `Guard` and adapter source bytes are unchanged (host `source/adb` is packaged executable, mode 0755; see `evidence/adapter-mode.json`); substitutions are reversible to the capture installer. One isolated PLAN called actual `main()` once with a pinned public stock template and an **in-memory source-check no-op**, disclosed in `evidence/plan-isolation-receipt.json`. Delivered guards and original readers remain intact. This PLAN did not validate private inputs or device state.

After the parent's ONE stock trial and stock return, save the complete raw retained log separately and parse it locally:

```sh
python3 /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-stock-entry-linux-offset-control/source/parse_trial.py /absolute/path/to/complete-retained.log
```

Require both independently: (1) matching fresh diagnostic UUID plus actual early magic `454559535452454e` and terminal status `ffff`; (2) every byte of the complete 234-byte fresh OEM tag above present in the actual saved log, including newline. The parser reads log bytes, reports matched offsets, and never emits the expected constant as observed evidence. Numeric record fields parse as hex. Parent must establish complete capture and provenance; do not feed source/README/command transcripts as the log.

A late UUID alone, zero/missing magic, or `ffff` without complete actual OEM text is insufficient. A complete tag without the fresh valid commit record is independently insufficient. Preserve any negative evidence and stop; do not generate another control variant. Only dual-positive **stock calibration** admits one subsequent 4.9 build with the exact parent correction. This unit makes no 4.9-entry claim.

No device/ADB/network/SSH/cloud/private inputs/full kernel build/VM startup/install/reboot/subagents were used. Continue from the packaged pins; do not rerun assembly/replay/package/PLAN or start another variant.
