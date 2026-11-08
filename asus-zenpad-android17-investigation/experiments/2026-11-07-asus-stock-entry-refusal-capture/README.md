# Stock primary-entry refusal capture — experiment 2

Question: did the stock custom Image primary entry run, and which unchanged R2 guard refused?

Status: **one local candidate packaged, focused actual-instruction replay and one isolated installer PLAN passed; no physical trial.** Same working 3.18.35 stock kernel. Its early guard remains uncalibrated. No 4.9 failure inference follows. Parent owns one stock trial and actual readback; no next variant or anticipatory fix is part of this unit.

The prior physical control booted actual 3.18.35, provided read-only RAM USB, and returned automatically to stock boot `ce770280-d2ad-49ed-b5db-4471de4fdeac`. Its complete 150301-byte retained log had zero fresh R2 UUID/tag matches. This unit measures early entry/refusal directly rather than repeating that positive control.

Outputs:

- `artifacts/candidate.img`: 7747584 bytes, SHA-256 `5ec1fb9af889dfaaa383af416c1ed429c0d4f3d46d6cb1b2107057a9e79f92f6`.
- `artifacts/candidate.p10.raw`: **16740352 bytes**, SHA-256 `10c4c72da182f8164c238c27901b855e963eb1b5b66bb13827878f9f9c64370e`.
- Fresh late-line UUID: **`ddfa517b-e809-45c8-83d9-a573403b3e68`**.
- `evidence/packaging-receipt.json`: actual complete before/after patch bytes, appended bytes, pins, addresses and budgets.
- `evidence/failure-ids.tsv` and `.json`: every expanded refusal ID, original R2 source condition, actual branch and preceding test.
- `evidence/replay.json`, `cache-visibility.json`, `completion.json`, `install-plan.json`, `plan-isolation-receipt.json`: precise evidence and limitations.
- `source/{entry.S,asus_entry_text.S,readback.S,control.ld,check_capture.py,install.py,install.diff}`, `qa/control.elf`: actual implementation and linked bytes.

## Owned record and observation

The 40-byte initially zero record is VA `0xffffffc000696c40`, physical `0x40696c40` at the pinned load. It is within callback slot `[0xffffffc000696b14,0xffffffc000696c74)`, outside BSS and the appended executable. Layout is five little-endian u64 fields:

| Offset | Field |
|---|---|
| 0 | early magic `0x454559535452454e` |
| 8 | original x0 FDT pointer |
| 16 | actual CurrentEL encoding |
| 24 | corresponding valid SCTLR_EL1/EL2, or all-ones at other privileged EL |
| 32 | final refusal ID; `0xffff` after unchanged successful commit; zero before terminal diagnostic |

Capture precedes every original guard. SCTLR_EL1 is read only at EL1; SCTLR_EL2 only at EL2. EL3 uses the sentinel, then the unchanged guard refuses. No x0–x3, x18–x30, LR or SP is changed by early instrumentation. All original guard instructions/conditions and retained-memory stores remain; only refusal destinations go through private diagnostic stubs. The original tag is retained unchanged, including its prior R2 identity; the new diagnostic line is this unit's observable.

Every terminal path stores its exact ID, completes stores, performs targeted `DC CVAC` at record VAs +0/+16/+32, then `DSB SY`, before returning to physical `0x40080040`. This is clean-to-PoC, **not an invalidate or global flush**. It makes no C=0 assumption. Cache maintenance is line-granular, so unchanged neighboring bytes can also be cleaned. See the cache receipt for architectural access preconditions and the limits of local verification. At MMU-on entry the existing Image mapping must permit the record stores and maintenance; neither mapping permissions nor higher-EL interception are measured by this local replay. No firmware address, new physical reservation or OEM location is used for the diagnostic record.

At original clear BL VA `0xffffffc000f41564`, wrapper `0xffffffc000696b14` always loads the five **actual record fields**, then calls known stock printk `0xffffffc000abe7a8`. The line is `ASUS-ENTRY-DIAG ddfa517b-e809-45c8-83d9-a573403b3e68 magic=… x0=… el=… sctlr=… status=…`. It prints even when all fields remain zero. It then reloads original x0/x1/x2 and calls original `__memset_io` at `0xffffffc00008a688`, restoring callee-saved registers, LR and SP. It uses a 48-byte aligned frame. Callback code is 64 bytes, code plus format 179 bytes; record offset is 300, size 40, leaving 12 bytes at the slot end. Active instructions, format and record do not overlap. Original callback-table pointers are unchanged; the preserved sole helper never invokes this callback.

The original BSS append starts at `0xffffffc0010ad7f0`, ends at `0xffffffc0010aeb82`, and is used only before stock BSS clearing. Record and late code are original mapped text, so BSS clearing does not erase them. Original header/reservation/addresses/bootargs and stock DT marker are retained. RAM USB ramdisk is byte-identical; helper SHA-256 remains `631a0aa5e72ee4110357ddac12bc5e5436ef3b1924cf64355f6fae99dc96d272`. Original clear/reset/watchdog flow is retained. Normal BOOT/SYSTEM/DATA are untouched.

## Focused replay and interpretation

One focused local replay ran actual linked instructions for matching positive, EL2 MMU-on refusal, and wrong memory-bank size, then the actual patched BL and late wrapper for those records and an initial-zero record. Entry boot registers/SP and late callee-saved registers/LR/SP survived. All late cases printed actual fields and called the original clear contract with original arguments. MRS values are explicit fixtures. DC operands were checked, but actual cache behavior is not emulated. Printk and memset are explicit ABI-adversarial local contract substitutes; actual printk internals, console replay and retention were not emulated.

| Observed ID | Meaning |
|---|---|
| 1 | unsupported CurrentEL |
| 2 | SCTLR.M set |
| 3 | SCTLR.C set |
| 93 (`0x5d`) | memory/usable-memory bank size is not `0x7d600000` |
| 65535 (`0xffff`) | unchanged writer nonzero commit completed |

The complete exact FDT/OEM refusal table is in `evidence/failure-ids.tsv`; the replay obtained 65535, 2, and 93 respectively. Runtime-memory overlay is a disclosed fixture only. Packaged DT still has its original 512 MB placeholder; no guard was relaxed and no DT memory bank was changed.

A matching fresh late UUID **alone is not early proof**. Require actual magic `454559535452454e`, actual ABI fields and a mapped status. Zero magic independently proves the late observer ran but does not establish whether primary entry ran or whether its record survived. No late line leaves the observation route unestablished. The actual status, not an anticipated fix, decides the parent's next action.

## Installer and continuation

Installer differs from inherited R2 only in actual candidate/full-p10 pins, size/profile and appended allowed current full preimage `80fe0f339e2a2d609e3f6a9583b4b8ca2f9104ccbb5810a0d25178475b4bc73f`. Reversing those substitutions reproduces R2 exactly; `execute`, `Transport`, `Guard` and adapters remain identical. One isolated PLAN used the pinned public original stock header template and an in-memory source-check no-op to avoid private dependency inputs. Delivered readers and guards remain intact. This does not validate private backups, fresh device identity/preimage, actual entry state or hardware retention.

Do not rerun the build/replay/package/PLAN or create another variant from this unit. Parent owns its existing guarded workflow and **one stock trial**. No device/ADB/network/SSH/cloud/private input/full kernel build/VM startup/install/reboot/subagent was used. Only standalone ARM64 assembly/link, local replay and public binary packaging occurred.
