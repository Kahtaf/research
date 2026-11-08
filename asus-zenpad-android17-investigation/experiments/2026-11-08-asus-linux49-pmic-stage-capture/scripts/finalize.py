from pathlib import Path
import json,hashlib,stat,sys,gzip
R=Path(__file__).resolve().parents[1];W=R.parent;B=W/'2026-11-07-asus-linux49-power-supply-phase-capture'
sys.path.insert(0,str(R/'scripts'));import decode_pmic as decoder
load=lambda n:json.loads((R/'evidence'/n).read_text());i=load('identity.json');p=load('packaging-receipt.json');m=load('System.map-uncompressed.json');checks=load('encoding-controls.json');build=load('build-status.json')
assert build['status']=='complete' and build['compile_attempts']==1 and build['compile_exit']==0
assert load('install-plan.json')['mode']=='PLAN_ONLY' and load('plan-isolation-receipt.json')['actual_installer_main_calls']==1
assert load('after.stdout')['status']=='TERMINATED' and load('after.stdout')['id']=='8549823276971553556'
assert not (R/'s').exists();assert 'exit' in (R/'evidence/master-exit.stderr').read_text() or (R/'evidence/master-exit.stdout').exists()
assert load('hook-abi.json')['status']=='PASS_SCOPED_LINKED_CALL_ORDER' and load('linked-capture.json')['status']=='PASS_SCOPED_SOURCE_AND_ACTUAL_ELF'
assert load('source-checks.json')['status']=='PASS' and load('semantics-control.json')['status']=='PASS' and checks['status']=='PASS'
for n in ['decode.py','decode_switch.py','decode_work.py','decode_power.py']:assert (R/'scripts'/n).read_bytes()==(B/'scripts'/n).read_bytes()
assert stat.S_IMODE((R/'source/adb').stat().st_mode)==0o755
assert p['admitted_current_full_p10']=='e4df271f2024c2abcfeac80475a074541255ae8318d86f77771a9e5684d93b0f'
assert p['preservation']['config_byte_identical'] and p['preservation']['entire_wrapped_ramdisk_byte_identical'] and p['preservation']['execute_Transport_Guard_byte_identical']
# Validate Python syntax without generating __pycache__, executing install again,
# contacting a target, or re-running a kernel build.
for folder in ['scripts','source']:
 for f in (R/folder).glob('*.py'):compile(f.read_bytes(),str(f),'exec')
for n in ['System.map.gz','Image.gz-dtb','resolved.config','candidate.img','candidate.p10.raw','runtime.dtb','ramdisk.wrapped']:
 d=(R/'artifacts'/n).read_bytes()
 if n in ['candidate.img','candidate.p10.raw']:assert dict(bytes=len(d),sha256=hashlib.sha256(d).hexdigest())==p['candidate' if n=='candidate.img' else 'full_p10']
# Exact commands are a handoff, never executed against any device by this worker.
commands=dict(PLAN=f'python3 -B {R}/source/install.py',parent_authorized_install_only=f'python3 -B {R}/source/install.py --execute',decode_pmic=f'python3 -B {R}/scripts/decode_pmic.py /absolute/path/to/parent-complete-console.txt --uuid {i["run_uuid"]} > /absolute/path/to/parent-private-pmic.json',public_summary=f'python3 -B {R}/scripts/symbolize_pmic.py --decoded /absolute/path/to/parent-private-pmic.json',kernel_build=build['command'])
for n in ['decode','decode_switch','decode_work','decode_power']:commands[n]=f'python3 -B {R}/scripts/{n}.py /absolute/path/to/parent-complete-console.txt --uuid {i["run_uuid"]}'
markers=[f'ASUS49-ENTRY run={i["run_uuid"]}',*[f'{name} uuid={i["run_uuid"]}' for name in ['A49CAP1','A49SW2','A49WD1','A49PS1','A49PM1']],'A49FAULT 0',*[f'A49{x}LOSS 0 guard=0 busy=0 admission=0 overflow=0' for x in ['S','W','P','M']],f'A49MGUARD BEGIN {i["run_uuid"]}',f'A49MGUARD END   {i["run_uuid"]}','VA49MH   <matching generation/metadata/tail>','VA49M 00..05 <576-byte ring rows>','VA49M 06 <fixed latest stage>','VA49M 07 <fixed latest present>','VA49M 08 <fixed latest ADC>','VA49M 09 <fixed latest prepare>']
handoff=dict(status='DELIVERED_ONE_DIAGNOSTIC_PMIC_STAGE_CANDIDATE_STOP',physical_GO=False,full_OS_GO=False,device_contacted=False,parent_owns_one_physical_trial=True,standing_eventual_manual_Power_fallback=True,run_uuid=i['run_uuid'],remote=i,VM=dict(project='PROJECT_REDACTED',zone='us-central1-a',instance='PROJECT_REDACTED',id='8549823276971553556',final='TERMINATED',own_master_closed=True),candidate=p['candidate'],full_p10=p['full_p10'],expected_current_full_p10=p['admitted_current_full_p10'],current_pin_source='Parent supplied latest physical full p10, not freshly observed by worker',System_map=m,config=p['config'],helper_uuid=p['helper_uuid'],ramdisk=p['ramdisk'],DT_compiled=p['compiled_DTB'],DT_runtime=p['runtime_DTB'],bootargs=p['bootargs'],initrd=p['initrd'],layout=p['layout'],charging_permission='ABSENT in actual compiled/runtime DT and unchanged from base',capture=dict(version='A49PM1',old_bytes=20544,appended_bytes=6208,combined_bytes=26752,ring_events=6,row_bytes=576,fixed_snapshots=['latest stage','present','ADC','prepare'],event_fields=decoder.FIELDS,codes=decoder.CODES,intervals=decoder.INTERVALS,protocol='protocol.md',old_protocols_decoders_byte_identical_except_UUID=True),checks=dict(base_gate='base-provenance-gate.json',source='source-checks.json',linked='linked-capture.json',ABI_order='hook-abi.json',ownership='ownership-proof.md',encoding='encoding-controls.json',semantics='semantics-control.json',preservation='preservation.json',packaging='packaging-receipt.json',PLAN='plan-isolation-receipt.json',compile_attempts=1,max_jobs=8,default_PLAN_calls=1,checker_corrections='checker-corrections.jsonl',compiler_corrections=0),commands=commands,expected_markers=markers,limits=decoder.LIMITS,no_automatic_retry_next_build_or_fullOS_GO=True,parent_consult_Large_before_further_guesses=True)
(R/'evidence/handoff.json').write_text(json.dumps(handoff,indent=2)+'\n')
(R/'evidence/exact-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
(R/'artifacts/SHA256SUMS').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name+'\n' for f in sorted((R/'artifacts').iterdir()) if f.is_file() and f.name!='SHA256SUMS'))
README=f'''# PMIC present / ADC / prepare stage capture

Question: which original primitive interval is last captured inside a strictly joined battery voltage-property invocation?

Status: **ONE diagnostic candidate built and packaged; STOP.** Parent owns one physical trial, complete retained-console interpretation, normal stock return and standing eventual manual Power fallback. No worker device/ADB/root/private factory/raw target-log contact, execute, physical/fullOS GO, automatic retry or next build.

- [candidate.img](artifacts/candidate.img): {p['candidate']['bytes']} bytes, SHA-256 `{p['candidate']['sha256']}`.
- [candidate.p10.raw](artifacts/candidate.p10.raw): {p['full_p10']['bytes']} bytes, SHA-256 `{p['full_p10']['sha256']}`.
- Fresh UUID `{i['run_uuid']}` across entry/clock/switch/work/power/PMIC metadata. Helper remains `{p['helper_uuid']}`.
- [System.map.gz](artifacts/System.map.gz): genuine VM build map, compressed SHA-256 `{m['compressed_sha256']}`. Local decompression: {m['uncompressed']['bytes']} bytes, SHA-256 `{m['uncompressed']['sha256']}`. [Uncompressed pin](evidence/System.map-uncompressed.json). vmlinux and out remain VM-only.
- [Handoff](evidence/handoff.json), [source pre/post pins](evidence/source-pins.json), [scoped diff](source/changes.patch), [actual source snapshots](source/base), [base provenance gate](evidence/base-provenance-gate.json), [base call flow](evidence/base-callflow.disasm), [linked candidate](evidence/linked-capture.json), [compiled order/ABI proof](evidence/hook-abi.json), [scoped disassembly](evidence/scoped-hooks.disasm), [preservation](evidence/preservation.json), [protocol and every stage code](evidence/protocol.md), [ownership/lock proof](evidence/ownership-proof.md), [checksums](artifacts/SHA256SUMS).

The accepted public physical evidence admitted all four older protocols without faults/loss and joined battery/PID119/work66/body61 at phase12 UEVENT_PRE to property89, enum66 batt_vol, callback battery_get_property. That callback's dispatch is pending through the finite capture; prior TECHNOLOGY/CAPACITY/CHARGE_FULL/CHARGE_COUNTER returned. The helper still stops after its initial0.650936307 direct SYS clock sample. These facts do not prove ADC entry, permanent hang, generic clock/scheduler failure, or provenance of the old cached ADC+340 PC. The parent's ASSESSMENT corrections govern interpretation.

Before any source edit, the actual exact-base pmic_battery.inc, battery_diag.c and pmic_mt6323.c were fetched with hashes and include/compiler/built-in/vmlinux provenance. All three C files and relevant functions match the supplied public reference byte-for-byte. The source was compared to linked ELF call flow, never byte-compared to ELF. Base prepare and measurement helpers inline, as do some nolock reads to regmap_read; existing error-only printk and compiler error-unlock duplication/countdown explain differences. Enum66 follows present before ADC(channel6,samples5). No invalidating source discrepancy was found. The candidate now leaves prepare standalone; this is ordinary compiler outlining, with its actual BL+4 parent call pinned.

Only pmic_battery.inc gains driver hooks, plus the existing recorder/header/tag. Present includes entry, readiness, existing read pre/post and status-only returns. ADC separates stay-awake and mutex acquisition, prepare call, VBUF, each sample's trigger0/1, udelay300, every poll read, taken sleep, ready/timeout, mutex-unlock, relax and return. Prepare separately captures original spin acquire, existing nolock delay/busy read/config, spin restore, taken sleep, poll/error/ready/timeout and return. No raw register/ADC/mV/present output or property value is recorded. No register operation, condition evaluation, range/error transform, loop count, delay, sleep, lock semantics or exported ABI changes. Removing hooks, local diagnostics and the sole static prepare-parent argument restores the original semantic token stream. [One host scenario](evidence/semantics-control.json) compares real base/candidate primitive order/counts, int status, synthetic output equality in memory and final lock/IRQ/wake state. [Actual linked CFG checks](evidence/hook-abi.json) bracket every relevant primitive exactly once per path, including duplicated compiler error-unlock paths.

A49PM1 appends6,208 guarded ASCII bytes after20,544 unchanged old bytes:26,752 combined. The actual OEM console capacity check precedes append writes, log_size and readiness. Six event rows plus fixed latest-stage/present/ADC/prepare snapshots retain caller-local tokens, actual PID/channel/sample/poll/status/context, direct source return-site identity and old clock/switch/work/PS anchors. Prepare inherits its actual ADC parent's identity. The independent nonblocking publication lock ends before each original primitive; there is no reverse lock edge. Atomic/IRQoff/preempt context alone is accepted. Fixed invalid-first/generation-tail/PoC-clean+dsb/valid-last publication, UUID guards, sticky loss/overflow and finite horizons are validated. No mapping, reservation or global active owner is added.

The new [decoder](scripts/decode_pmic.py) invokes the four byte-identical older decoders and joins fresh actual work/body/property tokens, PID, supply, named callback, enum, source caller, channel6/samples5 and time/anchor identities. Historical119/66/61/89 are not constants. A prepare substage must match its actual ADC parent. Unrelated generic present calls and overwritten/ambiguous contexts remain UNKNOWN for attribution; broad old property facts remain available. [Encoding controls](evidence/encoding-controls.json) use the actual extracted writers with deterministic host-only primitive/counter stubs: positive and pending intervals, nested calls, task interleaving, unrelated calls, wrap/out-of-horizon snapshots and torn/guard/loss negatives. These are synthetic controls, not physical evidence.

Exact base: `{i['base_remote_root']}/{{kernel,out}}`. Owned candidate: `{i['remote_root']}`. Source/out copied independently with `cp -a --reflink=auto`; [scoped frozen base](evidence/base-freeze.json) and [inode/repository preservation](evidence/repository-preservation.json) passed. No full-tree audit or Git mutation. One `make -j8 Image.gz-dtb`, one compile attempt, no compiler correction or alternate candidate. Two ELF checker scope corrections are preserved: local pm_init collided with kernel power's pm_init; it was resolved by actual recorder-object symbol name/size and linked caller. An intermediate inference that it was inlined was incorrect. No kernel source/build changed for these checker corrections.

Whole config SHA remains `{i['config_sha256']}`. Wrapped helper ramdisk, compiled/runtime DT, short bootargs, initrd geometry, load addresses, mappings and RDMA diagnostic skip remain exact. Actual charging DT opt-in remains absent. [Package receipt](evidence/packaging-receipt.json), [packager diff](source/package.diff), [installer diff](source/install.diff). Execute/Transport/Guard/adapters are byte-identical; only image/full hashes, profile, actual length and append of current full-p10 `{p['admitted_current_full_p10']}` change. adb remains0755. The current pin is parent-supplied, not freshly read by the worker.

[Exactly one isolated default PLAN](evidence/install-plan.json) passed. [Its receipt](evidence/plan-isolation-receipt.json) describes truthful public readers substituted only in memory; private stock/root dependency chains were not validated. Delivered guards and readers are unchanged. No target contact occurred.

Authorized VM PROJECT_REDACTED/us-central1-a/PROJECT_REDACTED, ID8549823276971553556, is verified [TERMINATED](evidence/after.stdout). One owned persistent SSH master handled readiness/build/fetch with ProxyCommand=false channel fallback disabled; only that master was closed. remote.py SHA remains c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab. No new cloud assets/disks/firewall/credentials, caps, arbitrary wall kill, AOSP/product/native work.

Parent commands (worker executed only the isolated PLAN; install does not reboot):

```sh
{commands['PLAN']}
# Parent's already-authorized one-trial recovery installation only:
{commands['parent_authorized_install_only']}
```

Decode only the parent's complete retained console; raw numeric identities stay parent-private:

```sh
{commands['decode_pmic']}
{commands['public_summary']}
```

[Exact commands and older decoder invocations](evidence/exact-commands.json), expected UUID/guard/loss/row markers and all stage codes are in handoff.json and protocol.md. Fresh helper/entry/full-p10 identity, complete-console collection, one boot/recovery/readback/stock-return procedure and eventual manual Power fallback remain parent-owned. No availability question or worker execute.

Continuation: deliver and STOP. A missing POST names only the finite PRE-through-POST interval, including ordinary preemption; especially spin/mutex unlock may schedule before the POST. Return markers precede C epilogues. No permanent hang/deadlock/holder/source cause follows from missing POST. Loss/torn/ambiguous/unjoined is UNKNOWN STOP. No automatic retry, next candidate/channel/fix, or fullOS GO; parent consults Large before further guesses.
'''
(R/'README.md').write_text(README)
print(json.dumps(dict(status=handoff['status'],run_uuid=i['run_uuid'],candidate=p['candidate'],full_p10=p['full_p10'],VM='TERMINATED',compile_attempts=1,isolated_PLAN_calls=1),indent=2))
