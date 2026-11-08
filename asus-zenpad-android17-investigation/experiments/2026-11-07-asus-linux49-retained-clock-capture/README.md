# Retained kernel clock checkpoint

Question: which selected monotonic read, architectural counter read, or actual timer event callback last entered without a matching captured completion, with timekeeper sequence, returned raw counter, callback and interrupted-PC metadata?

Status: one real kernel candidate built, packaged and checked. VM **TERMINATED**, exact ID `8549823276971553556`. No device/ADB/private payload/raw target-log access, physical GO, driver fix, second candidate, or subagent. Parent owns installation, reboot, Power fallback, fresh retained-log collection and interpretation. This unit stops here.

## Delivered candidate

- `artifacts/candidate.img`: 7976960 bytes, SHA-256 `666404b22886baab96ccd7b09ae258a9e65ecacbd674e1d70ae929b1083cdfce`.
- `artifacts/candidate.p10.raw`: 16740352 bytes, SHA-256 `4b474d6e714871dcefbba9510ff3d25f66e13147171ae39b0fa670c7cd70402e`.
- Genuine compiled `artifacts/Image.gz-dtb`: SHA-256 `1baa4bd8ea91477eb0592bc51d2d25a4cab8afe94c3c0014f98e2d4b222fbd90`.
- Capture/entry UUID: `fef31ed4-f62b-4f2a-8cc8-8f5a6c96dbdb`. The unchanged helper retains UUID `f0c3c82c-d639-4d8a-90f2-155fd4224ceb`; it is not standalone freshness evidence.
- Config SHA-256 `708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1` is byte-identical. The existing `CONFIG_ASUS_P00A_RETAINED_BOOT_TRACE` bool gates the capture; no config change.

The supplied current **complete p10** `e4afdc3542ecfbc5a4105ab6eb9d5b9f78ff614c2455b8e0b8dee5932e7ad3f4` is appended to `INSTALL_PREIMAGES`. It was not freshly read here. Existing stock/prior admission remains. `execute`, `Transport`, `Guard`, all transport/engine dependencies, `bootformat.py`, `fdt.py`, and adapters remain byte-identical. The `adb` adapter was copied with `copy2` and remains mode 0755. Installer delta is only candidate hash, full-p10 hash, actual candidate length, profile and the appended current preimage; see `source/install.diff`.

The entire wrapped ramdisk is byte-identical (256984 bytes, `df6406bd884126190ce05c26f097f9d84a36c64e332286fa5aee6225670857d3`), including the direct-syscall helper. The compressed payload remains 256472 bytes. Runtime DT is byte-identical to the current hard-single-CPU candidate, and the newly compiled hardware DT is byte-identical to the frozen compiled DT. Addresses, reservations, MTK wrappers apart from necessary kernel payload length, initrd `[0x44000000,0x4403e9d8)`, and existing early guard exclusion through `0x4403f007` are preserved. Exact short arguments in Android header and DT:

```text
bootopt=64S3,32N2,64N2 build_version=3 console=null nr_cpus=1 printk.devkmsg=on nohlt
```

Actual ARM64 `Image.image_size` is 18841600 bytes, including BSS; the admitted loaded range is `[0x40080000,0x41278000)`, clear of initrd and console. Android/LK page, wrapper, boot ID and offset evidence is in `evidence/packaging-receipt.json`. The entry tag's inherited `dt=94cde...` identifies the original calibrated-entry reference provenance, not a claim of current runtime-DT equality; current runtime and compiled DT identities are separately pinned in that receipt.

## Recorder and scope

The five changed kernel sources are in `source/` at their original relative paths. `source/changes.patch` and `evidence/source-pins.json` carry before/after identities. Changes are confined to the capture interface/logger, `ktime_get_ts64`, `arch_counter_read`, `timer_handler`, and fresh entry/capture identity metadata. Early assembly and its guards are unchanged.

After the original DT/memblock/OEM admission and post-paging marker, the logger aligns forward within the existing console, initializes **5952 fixed ASCII bytes** (192-byte header and fifteen 384-byte rows), cleans them to PoC, and advances normal append `log_size` once. Normal printk appends after this area. Entry/early markers, OEM PL/LK payloads and reason fields are not overwritten by the new capture. It uses the existing normal-cacheable mapping and IRQ-safe raw trylock. It adds no physical reservation, hardware access or block write. Uniform rows leave a few unused operation/context combinations; this keeps one small encoder/decoder and the entire area below 6 KiB rather than adding a second protocol.

Slot 0 is one **global PID1 task context**, independent of migration. Slots 1–4 are actual timer hard-IRQ contexts for logical CPUs 0–3. Each has three operation rows (kinds 0 monotonic, 1 counter, 2 timer callback), indexed `slot*3+kind`; unused combinations stay empty. A selected monotonic context means `current->pid == 1` outside interrupt context in `ktime_get_ts64`; it does not claim every caller is a userspace clock syscall. Its function field records the caller address for attribution. Nested counter reads are recorded only while a selected task-monotonic or actual timer-callback token is active. Timer callbacks are captured after the original interrupt-mask write, using the actual single-loaded callback pointer and `get_irq_regs()` PC when available. Counter code single-loads and calls the actual reader once; raw data is the returned value of that call. Original sequence begin/retry operations, counter/callback call counts and IRQ masking remain.

The recorder calls no timekeeping, counter-read, printk, sched_clock, allocator or scheduler. It does not add functional retry caps. Cache cleaning and diagnostic calls add overhead, so this is an intrusive checkpoint candidate, not a timing-neutral measurement.

Each operation gets a globally unique token containing a serial, operation kind and originating slot. Exit/update accepts only the matching active token. Task migration changes CPU metadata but keeps the same task token. Nested/reentrant use, unsupported CPU/context, NMI, trylock failure or token mismatch latches `A49FAULT 1` in a separate fixed header line, without waiting on the lock. The latch is monotonic; any captured loss makes unfinished-boundary interpretation UNKNOWN. Early unavailability gives no captured entry and remains UNKNOWN.

For each update the writer persists `!` first, then the entire row with equal leading/trailing update generations, then persists `V` as the commit. Reset during an update leaves a rejected row. A valid-looking older payload under `!` is still rejected. No timestamped printk or per-iteration append is used.

## Decode and acceptance

Parent, after obtaining the **complete console** through its established retained-reader route, run locally (keep captured addresses private):

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-retained-clock-capture/scripts/decode.py /absolute/path/to/parent-complete-console.txt --uuid fef31ed4-f62b-4f2a-8cc8-8f5a6c96dbdb > /absolute/path/to/parent-private-decoded.json
```

The host decoder does no device/network access. Require one exact fresh capture header, the fixed complete area, fault `0`, complete committed rows, matching update generations, valid operation tokens and consistent completion counts. A missing, truncated, invalid, empty or dropped record is UNKNOWN, never evidence of nonexecution. Any invalid/torn row or loss latch makes the whole area UNKNOWN for unfinished-boundary inference. Require this candidate's exact full-p10 readback and fresh entry/capture UUID before interpretation; source/host/ELF/PLAN checks establish no physical cause.

Every row contains seventeen fixed-width hexadecimal fields in this order: `update slot kind enter exit entries complete parent seq_enter seq_last stage raw function pc aux cpu_enter cpu_exit`. These are exposed by name in JSON. Task-monotonic stages are 1 immediately before `read_seqcount_begin`, 2 after it returns (the actual returned sequence), 3 immediately before original retry comparison, and 4 completed. Entry/stage-1/stage-3/exit sequence values are explicitly raw `READ_ONCE` snapshots, not a substituted functional seqcount operation. A snapshot need not equal the following/preceding functional operation's value. Counter and callback rows use stages 1 entered and 4 exited. Callback `aux` packs PC-available in the upper 32 bits and original timer access selector in the lower 32 bits. Counter function is the actual reader; callback function is the actual event handler. A zero unavailable PC never establishes where interruption occurred.

For a fresh complete row, `enter == exit`, matching token kind/slot and `entries == complete` means that operation completed. `enter != exit` and `entries == complete+1` identifies an entered operation with no matching **captured** exit. It is a boundary observation, not proof of duration, stagnation or cause. Counter `raw` always belongs to the **exit token**; on a new unfinished entry it remains the previous completed sample. Compare its parent token with the latest task/callback entry before attributing it to that parent. Completion counts show how many operations actually finished, including repeated retries/callbacks, without a time source; a single snapshot cannot prove wallclock stagnation.

`qa/row-examples.txt` gives exact fixed-width synthetic completed, unfinished and interrupted rows. `qa/decoded-valid.json`, `qa/decoded-interrupted.json` and `qa/decoded-loss.json` show their interpretation. Example: the valid synthetic task counter has one completed read with raw `0x123456789abc`; the latest synthetic task monotonic token has two entries and one completion, and that older counter's parent does **not** match the latest task entry. The interrupted replacement of that task row is rejected even though some previous fields look complete. The nested-entry example latches unknown. These are synthetic recorder-layout examples, not target logs.

The one essential acceptance unit, already passed, compiles the actual recorder body against small host stubs and exercises complete versus interrupted commit, preserved marker bytes, single append reservation, migration token matching, separate task/IRQ slots through CPU3, returned raw data and a nested-entry loss latch. `evidence/capture-layout-check.json` records the result. Re-running it is optional and overwrites only synthetic QA outputs:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-retained-clock-capture/scripts/check_layout.py
```

## Build, evidence and parent commands

One complete `make ... -j8 Image.gz-dtb` ran on the existing 64-GB VM, no new resource caps or product build. It passed first try, with 24 warnings preserved in `evidence/compile-1.log`; there were no compile errors. `evidence/build-receipt.json` pins the actual ELF, Image, config and generated release/version. `evidence/linked-capture.json` plus `capture-hooks.disasm` establish the actual monotonic hooks, one counter indirect call, and entry/exit hooks around one actual indirect callback in each of the four timer handler wrappers. `evidence/delivery-pins.json` pins this delivered source/scripts/package set. No full-tree rehash was used.

The original kernel/output/artifacts remain untouched. Independent source/output inodes were copied to `/srv/android/asus-linux49-retained-clock-capture-20261107-fef31ed4`; its large output and `vmlinux` stay on the VM for parent-only symbolization if needed. SSH used the same authenticated master, original key/known-host alias and `ProxyCommand=false` compiler/fetch channels; `remote.py` is unchanged. `evidence/lifecycle.jsonl` and `after.stdout` record identity/start/stop and final TERMINATED status. No firewall, credentials or cloud resources were changed.

Exactly one actual installer `main()` PLAN passed in the established isolated public-reader harness. It substituted only the pinned public stock-header template for private stock input and public code pins for the private/root-helper source chain, in memory. Delivered input readers and guards were not changed. Private backups and the full private manifest/root-helper chain were deliberately not validated. See `evidence/install-plan.json` and `plan-isolation-receipt.json`. This is not parent private-input or physical admission.

Exact **parent PLAN** command, using its existing private inputs and original guards:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-retained-clock-capture/source/install.py
```

Exact parent installation command, only within the parent's own physical-trial decision and established recovery/Power-fallback procedure:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-retained-clock-capture/source/install.py --execute
```

The installer performs full-p10 preimage/readback checks and does not reboot. No device operation was dispatched by this unit. Parent must collect the complete retained area, apply the freshness and decoder checks, and interpret only admitted rows. Stop after this candidate; there is no next hypothesis/build in this unit.
