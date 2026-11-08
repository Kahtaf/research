from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];E=R/'evidence';O=R/'output';S=R/'source'
I=json.loads((E/'identity.json').read_text());P=json.loads((E/'packaging-receipt.json').read_text());B=json.loads((E/'build-receipt.json').read_text());M=json.loads((E/'System.map-uncompressed.json').read_text())
assert json.loads((E/'focused-checks.json').read_text())['status']=='PASS'
assert json.loads((E/'production-check.json').read_text())['passed']
assert json.loads((E/'build-status.json').read_text())['kernel_builds']==1
assert json.loads((E/'plan-isolation-receipt.json').read_text())['actual_installer_main_calls']==1
vm=json.loads((E/'after.stdout').read_text());assert vm['id']=='8549823276971553556' and vm['status']=='TERMINATED' and not Path('/tmp/asuevent-1108').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs=['2026-11-08-asus-opus55-backstop-result/ASSESSMENT.md','2026-11-08-asus-opus55-backstop-result/OPUS-RESPONSE.md','2026-11-06-asus-product-input-build-kit/scripts/remote.py']
(E/'parent-input-pins.json').write_text(json.dumps({n:sha(R.parent/n) for n in inputs},indent=2)+'\n')
# Read-only qualification of functions already acquired from the one candidate ELF.
soc=(E/'linked-asus_p00a_soc_update.disasm').read_text();sample=(E/'linked-asus_p00a_battery_read_sample.disasm').read_text();bat=(E/'linked-BAT_thread.disasm').read_text()
assert '<asus_p00a_battery_read_sample>' in soc and '<asus_p00a_soc_update>' in bat
assert all(x in sample for x in ['mov\tw1, #0x5','mov\tw0, #0x6','<asus_p00a_pmic_adc>'])
assert json.loads((E/'linked-battery-literal.json').read_text())['exact_battery_literal']
(E/'CALLER-ELF-ADDENDUM.md').write_text('''# Qualification from the one built ELF

The pre-build eight-input inventory is preserved unchanged in CALLER-INVENTORY.md. The already acquired candidate ELF closes one compiled edge while leaving dynamic scheduling unproved: BAT_thread calls asus_p00a_soc_update at 0xffffff80088053e8; soc_update calls asus_p00a_battery_read_sample at 0xffffff80087ffa30 and 0xffffff80087ffdc0. read_sample sets w1=5 at 0xffffff80085c0200 and w0=6 at 0xffffff80085c0204, then calls asus_p00a_pmic_adc at 0xffffff80085c0208. Thus another compiled channel-6/five-sample route outside uevent is positively present. Included SOC source internals and runtime occurrence remain unexamined; charger indirect-route gaps in the pre-build inventory remain. No further source acquisition, build or suppression followed this check.
''')
proof='''# Source and candidate ELF proof

Five kernel source/header files changed in an isolated diagnostic fork; exact before/after hashes are in prepost.json and the complete patch in ../source/changes.patch. Removing only the omission branch restores the complete original production power_supply_uevent body. Removing only the boolean declaration plus begin/publish calls restores the complete original power_supply_changed_work body. The actual-body host harness verifies the matched-name NAME-only success, unchanged unmatched getter/allocation/free path and NAME failure, original property-error cleanup, actual post-return/unlocked publication, stale initialization and other-task rejection, single attempt and original changed/notifier/class/LED/wakeup cleanup. These mocks are bounded behavior controls, not physical timing evidence. An initial harness extraction matched the __-prefixed helper instead of the worker; the harness name boundary was corrected before the passing run, without a candidate-source change or additional kernel build.

The compiled power_supply_uevent emits NAME at 0xffffff80087fcf6c and branches away on error at 0xffffff80087fcf74. Its exact __pi_strcmp call at 0xffffff80087fcf88 compares against the literal at 0xffffff8008e37c88. Local decompression of the fetched Image independently confirms those bytes are battery\\0 (linked-battery-literal.json). The zero branch at 0xffffff80087fcf8c goes to 0xffffff80087fd110, the inlined omission recorder. That path increments the static omission counter, checks armed state/numeric owner, release-publishes the first scoped hit when eligible, sets return zero at 0xffffff80087fd19c or 0xffffff80087fd1a8, and goes to the normal epilogue. It bypasses allocation at 0xffffff80087fcf9c and the original property getter loop at 0xffffff80087fcff4. Unmatched supplies retain the original loop and free_pages/error paths. The source's standalone static battery_uevent_omitted was inlined, so its empty standalone disassembly is not mistaken for missing machine code. This compiler aliases strcmp as __pi_strcmp and uses ldxr/stlxr; the ELF check was aligned with those actual instructions. No production-source repair or second kernel build occurred.

The worker releases changed_lock/IRQs at 0xffffff80087fbc2c, retains class_for_each_device (0xffffff80087fbc74), LED updates and notifier (0xffffff80087fbcdc), and arms the single exact battery worker call at 0xffffff80087fbd0c. kobject_uevent(KOBJ_CHANGE) is actually called at 0xffffff80087fbd1c; its returned w0 is saved to w21 at 0xffffff80087fbd20 and passed in w1 to the publisher at 0xffffff80087fbd2c. The original changed_lock reacquisition follows at 0xffffff80087fbd5c. pm_relax remains at 0xffffff80087fbdb8 under the original conditions; original final unlock is 0xffffff80087fbdec. Thus new publication is after the real callback returns in the original unlocked gap, not after a property callback which this candidate bypasses. Source equality verifies cleanup/callback ordering unchanged.

A single static worker slot is armed once before its real kobject call. Numeric task ID stays internal; no raw pointer or user string is captured. Registration omissions increment the counter but cannot set the scoped first-hit flag. The exact omission branch can set that flag only in the owning task while armed. Publication claims state4->5 before context/refusal checks, verifies before<first<=after, and calls the calibrated direct writer at most once. No publication retry or rearm occurs. This avoids poisoning the record with a stale init flag. Counter wrap/context rejection/no callback/no return/no drain/trylock/full/reset remain UNKNOWN.

Publisher native code uses a 192-byte line buffer, with 224 bytes total frame including compiler state. It checks current context and DAIF before formatting; direct calls are only scnprintf, asus_retained_trace_write and compiler stack failure. The claim is before the context guards. There is no new clock/MMIO/readout, allocation, printk recursion or per-poll instrumentation. The writer itself is the unchanged existing bounded trylock/IRQ-save retained writer; it can refuse/drop. No outer lock/IRQ mask spans original callbacks. The sparse filter is identical after removing only the new fresh BUEV-prefix admission; old ASCII/length checks, admissions, devkmsg and disabled hot-area behavior remain. The existing entire asus_retained_trace_write/asus_devkmsg_boundary/trace_init/cap_init bodies are byte-identical.

Old finite pwrap source and battery_get_property drain source were frozen by the build receipt. The candidate native battery_get_property calls asus_p00a_battery_get_property at 0xffffff80088018f4 and the old asus_pwrap_backstop_publish at 0xffffff80088018fc, preserving its result. That drain was not moved or repurposed. Pwrap's finite budget, hardware, delays, clocks, WDT/SPM/protection and other workers were not edited. Cold devkmsg kernel/printk/printk.c was among the frozen sources. The public PMIC source/clock binding remains the parent's prior evidence, without a new transport audit.

One make -j8 Image.gz-dtb invocation completed, zero helper compiles and no clean. A metadata-only free-space check preceded ordinary independent cp -a --reflink=never copies; 70,890 regular files were checked for distinct device/inode pairs. Nested repositories were preserved and out/source plus stored dependency paths were relocated inside the fork. The scoped original base source/artifact hashes, inodes and mtimes remained unchanged. Build receipt records all objects rebuilt due to the shared identity/header dependencies; this is not a claim that only two objects recompiled. Genuine System.map.gz/uncompressed pin, config and Image were fetched; out/vmlinux stays remote.

Package proof preserves the ENTIRE wrapped ramdisk/helper byte-for-byte, resolved config, compiled and runtime hardware DT, short bootargs and initrd/guard/load geometry. Installer execute/Transport/Guard and adapters stay byte-identical; only artifact pins/size/profile and appended current physical preimage changed. The one actual PLAN used restricted public readers in memory; private stock/root source-chain checks remain pending for the parent. No delivered guard was relaxed. Decoder strict first-line/framing/control/raw/refusal rules remain, with a narrow new record parser and separate execution facts. All console fixtures here are labeled synthetic. No physical pass was manufactured.

Exact VM verified TERMINATED; only the owned /tmp/asuevent-1108 master was closed. No device/ADB/root/private targetlogs/factorycontent operation, install, reboot, trial, child or new cloud asset was used. STOP after this candidate.
'''
(E/'SOURCE-ELF-PROOF.md').write_text(proof)
contract=f'''# Battery uevent omission record v1

```text
ASUS49-BUEV run={I['kernel_uuid']} v=1 SKIP first=<u32> before=<u32> after=<u32> same_task=1 uevent_rc=<s32>
```

The exact name is `battery`, qualified from selected battery_common.c battery_main.psd with native getter/config binding. POWER_SUPPLY_NAME is emitted normally; its existing emission error is returned unchanged. The matched battery then omits its property getter loop and returns zero, without fake values. All other supplies, events, sysfs/thermal getters and charging/battery workers retain their paths. The RAM helper has no Android property-event consumers. This is a diagnostic source fork, not product integration.

The omission counter counts exact matched uevent branches, including registration-time events. `before` is read when the first eligible battery changed worker arms the slot immediately before its actual kobject call. `first` is set by the first omission on that same task while that slot is armed. `after` is captured after the owning kobject call returns. It can include concurrent omissions, so after-before is a total counter interval, not a per-worker multiplicity claim. Numeric task identity is used only internally and never published. Every valid record establishes at least that specific worker's omission and the fact its actual kobject call returned; `uevent_rc` is the actual returned integer, and may be an error despite the omission callback's zero. The record does not prove worker cleanup/C return/syscall exit/userspace resumption.

The state moves once through unused/preparing/armed/hit-writing/hit-published/publication-claimed. Claim precedes context checks. There is a single writer attempt, no retry/rearm. Counter overflow or no scoped hit prevents a record; no later worker drains a stale flag. Publication occurs in the original unlocked worker gap, before reacquiring changed_lock. The old post-property pwrap record drain is unchanged and can be bypassed by this omission.

The decoder requires the exact UUID/version/mode, a single full canonical record, u32 bounds, before<first<=after, same_task=1 and s32 return range, plus original entry-first framing and binding/calibration requirements. Stale/malformed/duplicate/unbound/torn or missing/undrained publication is UNKNOWN. It reports omission/kobject-return independently of frozen-helper compute, afterIRQ, alarm and finish facts. Raw/refusal inputs must be retained by the parent; no stockproc preamble stripping or alternate framing acceptance was added. Supplied fresh-boot and console references are attestations, not target observations by this decoder.

One parent trial only. Observed skip plus correct normal-policy 2M checksum and afterIRQ supports dependence on this changed workload/timing, not a unique mechanism or strict necessity/exclusion. A negative with observed skip weakens this uevent trigger; it cannot exonerate AUXADC, pwrap, other readers or reporting. No flag is UNKNOWN. Progress without a qualified skip record is non-causal. Fast 2M completion is not 30-second stability, and a nominal one-second alarm may not fire before normal completion. MMC/finish/return and sustained execution are separate facts. No automatic repeat, global readout suppression, fullflash or storage advance follows any result.
'''
(O/'RECORD-CONTRACT.md').write_text(contract)
commands=dict(parent_execute_reference_only=f'python3 -B {R}/source/install.py --execute',parent_decoder_reference_only=f'python3 -B {R}/scripts/decode_boundary.py PARENT_CONSOLE_PAYLOAD.txt --installed-full-sha256 {P["full_p10"]["sha256"]} --fresh-stock-boot-reference PARENT_FRESH_STOCK_BOOT --complete-console-reference PARENT_COMPLETE_CONSOLE',build=json.loads((E/'build-status.json').read_text())['kernel_command'],physical_commands_executed=False)
artifacts={n:dict(bytes=(R/'artifacts'/n).stat().st_size,sha256=sha(R/'artifacts'/n)) for n in ['candidate.img','candidate.p10.raw','Image.gz-dtb','resolved.config','System.map.gz','runtime.dtb','ramdisk.wrapped']}
handoff=dict(status='ONE_DIAGNOSTIC_CANDIDATE_DELIVERED_STOP_NO_TRIAL',identity=I,pins=P,artifacts=artifacts,genuine_System_map_uncompressed=M,remote_vmlinux=dict(path=I['remote_root']+'/out/vmlinux',**B['artifacts']['vmlinux'],left_remote=True),remote_kernel=I['remote_root']+'/kernel',remote_out=I['remote_root']+'/out',commands=commands,checks=dict(production_bodies=True,source_ELF_package_parser=True,kernel_builds=1,helper_compiles=0,isolated_actual_PLAN=1,candidates=1),vm=dict(id=vm['id'],status=vm['status'],owned_master_closed=True,channel='/tmp/asuevent-1108',TCP_fallback=False),physical_trial=False,other_reader='Linked BAT_thread -> soc_update -> read_sample -> AUXADC6/five samples remains; charger indirect routes not fully qualified',stop='Parent owns at most one separately bound physical trial. No repeat/variant/global suppression/product integration/storage advance')
(E/'handoff.json').write_text(json.dumps(handoff,indent=2)+'\n')
text=f'''# One battery uevent omission diagnostic — STOP

One candidate built and packaged, one incremental -j8 Image.gz-dtb invocation, zero helper compiles, one restricted actual PLAN. Focused production-body, source/ELF, frozen-package and parser controls passed. No device/ADB/root/private targetlogs/factorycontent access, install, reboot or physical trial. Exact VM ID8549823276971553556 verified TERMINATED; owned /tmp/asuevent-1108 master closed.

Candidate: [candidate.img](../artifacts/candidate.img), {P['candidate']['bytes']} bytes, SHA256 `{P['candidate']['sha256']}`.

Fullp10: [candidate.p10.raw](../artifacts/candidate.p10.raw), {P['full_p10']['bytes']} bytes, SHA256 `{P['full_p10']['sha256']}`.

Fresh kernel `{I['kernel_uuid']}`; profile battery-uevent-omit-v1, format1. Full current physical preimage `{P['base_full_p10']}` appended to the preserved installer set. Current physical candidate/source pins were user supplied and locally/remote baseline verified as scoped, not freshly observed on the tablet.

Only workload delta: inside actual power_supply_uevent, after original POWER_SUPPLY_NAME emission/error handling, exact psy->desc->name=="battery" skips its property getter loop and returns0. No fake property values or full-worker bypass. Actual source/ELF proves class callbacks/notifier/kobject/changed/pm_relax cleanup preserved. Sysfs, thermal, charging/battery/SOC workers, WDT/SPM/protection, clocks/delay/hardware and finite pwrap budget remain. New once-only evidence is armed on one battery worker's actual kobject call, set only by the exact omission branch in the same task, and published after that call returns with original locks released. The old property-callback pwrap drain remains where it was; this candidate does not rely on it.

Before-build [caller inventory](../evidence/CALLER-INVENTORY.md) used six source files plus config/genuine map. The [candidate ELF addendum](../evidence/CALLER-ELF-ADDENDUM.md) positively identifies a remaining BAT_thread -> soc_update -> read_sample -> AUXADC channel6/five-sample route. Thermal TEMP retains channel5/presence traffic. Charger indirect include paths remain an exact documented gap. No other caller was suppressed, and a negative result cannot exonerate AUXADC/pwrap/other readers.

Entire wrapped ramdisk SHA `{P['ramdisk']['sha256']}` and helper SHA `{P['init']['sha256']}` are frozen. Helper run `{I['helper_uuid']}`, control `{I['control_uuid']}` reused. Config SHA `{P['config']['sha256']}` identical. Compiled/runtime hardware DT, short bootargs, initrd0x44000000..0x4403e92a, guard0x4403f007 and load geometry preserved. Genuine Image loaded end {P['layout']['loaded_Image_end']}, safely below initrd. Installer execute/Transport/Guard and adapters identical; adb0755. The single restricted PLAN substituted only public readers in memory: private stock/root dependency validation remains parent-owned and delivered guards were preserved.

[Complete source diff](../source/changes.patch), [before/after hashes](../evidence/prepost.json), [source/ELF proof](../evidence/SOURCE-ELF-PROOF.md), [record/parser contract](RECORD-CONTRACT.md), [full pins and commands](../evidence/handoff.json), [PLAN limits](../evidence/plan-isolation-receipt.json).

Remote isolated kernel/out: `{I['remote_root']}/{{kernel,out}}`. Vmlinux stays remote, SHA `{B['artifacts']['vmlinux']['sha256']}`. Genuine uncompressed System.map SHA `{M['sha256']}`, {M['bytes']} bytes; compressed copy in artifacts. Metadata/free-space, independent full-copy, scoped base-freeze and compile receipts retained. Parent/nested repositories preserved; active product/build sources were not integrated.

Parent-only references, NOT executed here:

```sh
{commands['parent_execute_reference_only']}
{commands['parent_decoder_reference_only']}
```

Parent owns at most ONE exact readback/fresh stock boot/complete console trial and stock return, then STOP. Preserve original stockproc raw/refusals; the strict decoder still requires an honestly identified console payload with entry as first line. Missing/stale/refused/undrained record is UNKNOWN; progress without qualified omission is non-causal. A skip record proves the scoped omission and actual kobject return only, with return code recorded separately from compute/afterIRQ/alarm/finish. WRET remains pre-C-return.

Observed skip plus correct 2M/afterIRQ supports workload/timing dependence in this exposure, not a unique inner fault, strict necessity or exoneration. Negative with skip weakens this trigger but leaves AUXADC/other readers/reporting unresolved. Fast2M is not30sec stability; the alarm can remain unfired before normal finish. No repeat, another loop variant, global suppression, product shipping fix, fullflash or automatic storage advance.
'''
(O/'HANDOFF.md').write_text(text)
(R/'README.md').write_text('''# Battery uevent property readout control

Question: does omitting only the named battery's uevent property getter loop change this exposure while other power/thermal readers remain?

Status: **one diagnostic recovery candidate delivered; STOP**. One incremental kernel build (-j8), zero helper compiles, one restricted actual PLAN. Production-body/source/ELF/frozen-package/parser checks passed. No device access or trial. Exact VM verified TERMINATED; owned SSH master closed.

Important outputs: [candidate and handoff](output/HANDOFF.md), [record contract](output/RECORD-CONTRACT.md), [pre-build caller limits](evidence/CALLER-INVENTORY.md), [remaining native channel6 route](evidence/CALLER-ELF-ADDENDUM.md), [complete patch](source/changes.patch), [source/ELF proof](evidence/SOURCE-ELF-PROOF.md), [pins and commands](evidence/handoff.json).

Continuation: parent owns at most ONE separately bound physical trial and verified stock return, then STOP. Do not repeat build/package/PLAN/trial, suppress other readers, integrate product sources, or advance storage. Missing/stale/undrained evidence remains UNKNOWN. Fast2M is not30sec stability; even a positive supports workload dependence only. Read the handoff and parser contract before continuation.
''')
# Explicit artifact manifest; no outside/private file traversal.
paths=[p for n in ['source','scripts','artifacts','evidence','output'] for p in (R/n).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='artifact-manifest.json']+[R/'README.md']
(E/'artifact-manifest.json').write_text(json.dumps({str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in paths},indent=2)+'\n')
print(json.dumps(dict(status=handoff['status'],kernel_uuid=I['kernel_uuid'],candidate=P['candidate'],full_p10=P['full_p10'],vm=handoff['vm']),indent=2))
