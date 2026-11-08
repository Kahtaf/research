from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
p=json.loads((R/'evidence/packaging-receipt.json').read_text());i=json.loads((R/'evidence/identity.json').read_text());s=json.loads((R/'evidence/source-patch.json').read_text());b=json.loads((R/'evidence/build-status.json').read_text());a=json.loads((R/'evidence/linked-entry.json').read_text())
rows=[]
for name,key in [('Image.gz-dtb','compiled_Image_gz_dtb'),('resolved.config','config'),('candidate.img','candidate'),('candidate.p10.raw','full_p10')]:
 v=p[key];rows.append(f"| [artifacts/{name}](artifacts/{name}) | {v['bytes']} | `{v['sha256']}` |")
source_rows=[]
for name,v in s.items():source_rows.append(f"| `{name}` | `{v.get('before_sha256','absent')}` | `{v['after_sha256']}` |")
text=f'''# Linux 4.9 entry retained-console text checkpoint

Question: can a fresh uniquely tagged, stock-readable retained-console line establish physical 4.9 execution before the existing C logger, memblock, DT initialization, and MMU setup?

Status: **ONE CANDIDATE BUILT AND PACKAGED; final isolated installer PLAN passed. No physical execution or retention qualification, and no OS admission.** The only kernel build completed on its first attempt. The writer is deliberately strict: **the entire incoming runtime DT must equal the pinned packaged DT byte for byte. Every bootloader DT mutation, including a harmless one, refuses this entry writer.** Runtime DT equality has not been observed on the device. Missing text is always **UNKNOWN**, including when this strict guard refuses.

The actual run UUID is `{i['run_uuid']}`. The exact 340-byte newline-terminated checkpoint is in [identity.json](evidence/identity.json), [asus_entry_tag.h](source/asus_entry_tag.h), and the verified linked bytes. Its searchable prefix is:

```text
ASUS49-ENTRY run={i['run_uuid']} stage=stext-preargs
```

The tag records actual release `{a['release']}`, the exact selected baseline compiled kernel pin, full config pin, and expected runtime DT pin. The [packaging receipt](evidence/packaging-receipt.json) binds this actual tag to the final compiled kernel and candidate hashes below; the embedded baseline pin is not misrepresented as a self-hash of the modified kernel.

| Delivered artifact | Bytes | SHA-256 |
| --- | ---: | --- |
{chr(10).join(rows)}

The final [installer](source/install.py) is 9682 bytes, SHA-256 `{p['installer']['sha256']}`. [install.diff](source/install.diff) and [final-installer-delta.json](evidence/final-installer-delta.json) establish exactly five permitted substitutions: actual compact/full hashes, compact size, profile, and append supplied current p10 hash `{p['delta']['added_preimage']}`. Every original allowed preimage remains. `execute`, `Transport`, `Guard`, both adapters, and all other installer bytes remain unchanged from the failure-log package. The current preimage and boot ID `c62d7755-35bb-4e53-920c-e69d136043f7` are parent-supplied facts, not fresh observations here.

The exact source is the EARLY-WATCHDOG baseline `/srv/android/asus-early-watchdog-handoff-20261107/{{kernel,out}}`, whose compiled Image.gz-dtb is `a49b87313d35d803e3ffaa2be2c60a3c678ccbc46efd5831651d2bd44ae4ee03` and logger is `8373baa301650d2bf3befe547df11a3079e22c51aec8a207de64eae0f1bb3348`. One ordinary independent `cp -a` copy went into `/srv/android/asus-linux49-entry-text-checkpoint-20261107/kernel`; selected independent inodes and before/after hashes are in [source-copy.json](evidence/source-copy.json). There was no full-tree rehash. All old sources, out directories and images were preserved. Only the new source copy was edited. The complete [entry-text.patch](source/entry-text.patch) changes two existing files and adds three files; it includes the generated exact-DT byte data. Before/after source pins are:

| Kernel source path | Before SHA-256 | After SHA-256 |
| --- | --- | --- |
{chr(10).join(source_rows)}

The entry hook is at the first instruction of `stext`, the 4.9 baseline's primary entry routine, before its original `preserve_boot_args`, `el2_setup`, page tables and `__cpu_setup` calls. The existing EFI/MZ Image prefix still branches to this routine. The hook uses only x4–x17 and condition flags, reads x0 without changing it, leaves x1–x3, x18–x30/LR and SP untouched, makes no call, allocates no stack, and uses no mutable global or C/FDT/memblock function. Code and read-only references use the tree's position-independent `adr_l` sequence. Refusal falls through to original control flow.

Before the first retained store, the linked assembly checks current EL1 or EL2 and the corresponding SCTLR M=0/C=0, aligned and bounded physical FDT storage, no FDT overlap with kernel, retained region or exact initrd, and no kernel overlap with the retained region. It compares all 63745 runtime FDT bytes to [expected-runtime.dtb](source/expected-runtime.dtb), SHA-256 `{p['packaged_and_runtime_guard_DTB']['sha256']}`. Equality covers the header, total size, reservation map, strings, root identity, memory bank, reservations, chosen initrd, and command line. This is an actual runtime guard, not an assumption that a packaged DT is what firmware passed. It never follows runtime-controlled DT lengths/offsets; any mismatch exits without a retained write.

The exact reference DT admits root `asus,p00a`, memory `[0x40000000,0xbd600000)`, reserved-memory address/size cells 2/2, empty ranges, and exactly one fixed reservation intersecting `[0x44400000,0x44480000)`: `mediatek,ram_console`, base `0x44400000`, size `0x80000`, with no `no-map`, `reusable`, or `status`. There is no extra memreserve-map alias. Other fixed reservations, dynamic reservation policy, hardware properties and geometry are preserved. The compiled DT remains byte-identical to selected baseline, 63621 bytes / `{p['compiled_DTB']['sha256']}`. The packaged DT remains byte-identical to the failure-log package, including its established chosen metadata. These are different pinned blobs because existing packaging already supplies the reporter's chosen metadata; the entry guard uses the exact packaged blob.

OEM admission then requires signature `0x43474244`, matching 64-byte-aligned PL/LK mirrored offsets, nonzero payloads outside the 64-byte header, complete PL/LK extents inside the region, disjoint ordered nonempty PL/LK regions, and derived Linux space after all platform payloads. Arithmetic is widened from u32 to u64 before alignment/addition; excessive sizes and any insufficient text capacity refuse. Linux offset is `off_lk + 2*align64(sz_lk)` when `sz_lk != 0`, otherwise `0x200`. Console starts at that offset plus the unchanged `0x400` reason area. Prior Linux offsets/counters are not used as addresses. There is no fallback writer outside the fixed region and no PL/LK-header or payload modification.

Only Linux-owned header words at +0x28/+0x2c/+0x30/+0x34/+0x38/+0x3c and the bounded text bytes are written. The entry writer leaves the reason area and all other bytes untouched. It invalidates the old Linux ring by publishing start=0 then size=0 with intervening DSB SY; writes the payload; completes payload stores with DSB SY; publishes derived geometry; completes it with DSB SY; then commits the nonzero length at +0x38 and executes DSB SY. On admitted MMU-off/D-cache-off boot-ABI entry, the physical writer creates no dirty cache allocation and changes no mapping or cache state. This is not a new scalar or speculative global-cache-flush experiment.

[entry.disasm](evidence/entry.disasm) and [linked-entry.json](evidence/linked-entry.json) verify the actual 536 linked code bytes, Image branch/callsite, embedded tag and complete DT bytes, and register/stack/call restrictions. Link VAs are `stext = 0xffffff8008ef0000`, original argument-preservation call `0xffffff8008ef0218`, and checkpoint commit `0xffffff8008ef0210`. The commit bytes are `913800b99f3f03d5`, decoding to `str w17,[x4,#0x38]; dsb sy`. These are linked addresses and bytes, not observations from hardware.

The corrected existing C logger was traced and changed to authenticate this exact run's complete tag and derived incoming Linux layout after its original DT/memblock/mapping guards. It preserves admitted entry text rather than clearing it, appends the existing post-memblock marker, and authenticates both during the paging handoff. If the temporary mapping cannot hold the entry or combined prefix, it leaves the entry intact for the post-paging path to recognize. The old markers were not renamed into a false earlier milestone. All original C reservation/runtime DT checks remain.

[build-status.json](evidence/build-status.json) and [build-receipt.json](evidence/build-receipt.json) record the single complete command: `make -C <new kernel> O=<new out> ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ LOCALVERSION=-g717bb3c9e13c-dirty -j8 Image.gz-dtb`. It ran from `{b['started']}` to `{b['finished']}`, exited 0, used fresh out/TMPDIR, inherited unlimited RLIMIT_AS `[-1,-1]`, and had no artificial wall deadline. Full config bytes remain identical. [compiled-initcalls.json](evidence/compiled-initcalls.json) verifies the unchanged earlier watchdog registration/order, no duplicate, and absent early UART symbols/object; selected timer/UART/watchdog/setup/hardware-source checks are in the linked/source receipts. No timer, watchdog-stop, UART, charging, radio, audio, or hardware-config fix was introduced.

One [focused host positive/refusal set](evidence/focused-guard-check.json) exercised a synthetic valid OEM layout with deliberately invalid prior Linux fields, platform/reason-byte preservation, changed DT, MMU/cache enabled, overlap/bounds, signature, and size/mirror refusals. It is a host contract model, not hardware proof. Linked verification needed checker-only corrections for the unchanged EFI header, legitimate read of x0, and objdump tab formatting; these are disclosed in [verifier-correction.json](evidence/verifier-correction.json). No kernel source adjustment or rebuild followed compilation.

Packaging retains the failure-log candidate `cc367b543eebea476b15a9033648c9547e48c7ac02d8c42856b372623bffb265` / full p10 `0b1a3c45751d688ba304743dc74e73f7030586c6fafece32eedf0da39c86455d` as its donor contract. Wrapped ramdisk remains exactly 258567 bytes / `{p['wrapped_ramdisk']['sha256']}`; compiled init remains 597888 bytes / `{p['init']['sha256']}`. Reporter run `9342cbf1-3bf0-44d4-b655-a1ca30146a99`, existing configfs logging, nominal 60-second reboot, and parent Power fallback remain. Initrd payload is still `[0x44000000,0x4403f007)`, excluding the 512-byte MTK wrapper. Android/MTK load addresses, page sizes, bootargs and DT hardware geometry stay intact. Arguments remain `{p['cmdline']}`. Only kernel payload, required wrapper size, Android kernel size/ID, alignment and padded full p10 change.

The final delivered installer passed one actual isolated default `main()` PLAN, exit 0: [output](evidence/install-plan.json), [isolation receipt](evidence/plan-isolation-receipt.json). In memory only, `b.local_inputs` used the established pinned public stock header template and `a.check_sources` was a no-op to avoid private backup/root-helper reads. Audit hooks blocked private/device input opens, processes and sockets. All delivered guards remain intact. Private backup/source pins, identity and live preimage were not validated. An earlier isolated PLAN used a malformed 66-character preimage because `p10` was split incorrectly; it was superseded, preserved under [superseded-plan](evidence/superseded-plan/install-plan.json), and corrected before this final-source PLAN. [preimage-correction.json](evidence/preimage-correction.json) records the correction. Thus there were two isolated PLAN invocations in this spike, one against the final delivered installer, and zero physical actions.

Continuation belongs to the parent: perform one fresh full-stock-last_kmsg absence check for UUID `{i['run_uuid']}`, fresh identity/current complete p10 and fallback checks, then use the final installer under the existing physical authorization:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-linux49-entry-text-checkpoint/source/install.py --execute
```

Require installed full-p10 readback `{p['full_p10']['sha256']}` and cleanup before the single recovery entry. Observe the unchanged reporter/reboot path and Power fallback, return to stock, and collect the complete stock last_kmsg through the parent's established private-safe procedure. Match the fresh UUID and full stage/provenance line, not an old marker or scalar. A fresh physical tag would establish this admitted pre-MMU writer executed and its text survived that trial; it would not establish later boot or final OS admission. **Absent text remains UNKNOWN** because execution before refusal, runtime-DT mismatch, earlier failure, or retention loss are not distinguished. Do not weaken the guard or start another variant as part of this unit.

No device/ADB/private payload access, installs, reboot, physical claims, cloud lifecycle/resource operation, subagent, driver repair or extra kernel build occurred. SSH used only the exact existing `2026-11-06-asus-product-input-build-kit/scripts/remote.py`; credentials were not copied. Compact local delivery fetched only Image.gz-dtb, config and receipts/disassembly, never vmlinux or a full tree. The owned remote tree remains available on the running VM at `IP_REDACTED`; **the parent owns VM stop**. This implementation unit is finished.
'''
(R/'README.md').write_text(text)
