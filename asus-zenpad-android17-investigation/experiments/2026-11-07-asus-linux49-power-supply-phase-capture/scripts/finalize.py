from pathlib import Path
import json,hashlib,gzip,re,stat,sys,difflib,copy
R=Path(__file__).resolve().parents[1];E=R/'evidence';B=R.parent/'2026-11-07-asus-linux49-work-dispatch-capture'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(E/n).write_text(json.dumps(d,indent=2)+'\n')
i=json.loads((E/'identity.json').read_text());p=json.loads((E/'packaging-receipt.json').read_text());linked=json.loads((E/'linked-capture.json').read_text());build=json.loads((E/'build-receipt.json').read_text())
assert json.loads((E/'after.stdout').read_text())['status']=='TERMINATED' and not (R/'s').exists()
assert sha(R.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')=='c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab'
for n in ['decode.py','decode_switch.py','decode_work.py']:assert (R/'scripts'/n).read_bytes()==(B/'scripts'/n).read_bytes()
for n in ['bootformat.py','fdt.py','legacy_adb.py','adb']:assert (R/'source'/n).read_bytes()==(B/'source'/n).read_bytes()
assert stat.S_IMODE((R/'source/adb').stat().st_mode)==0o755
assert sha(R/'artifacts/candidate.img')==p['candidate']['sha256'] and sha(R/'artifacts/candidate.p10.raw')==p['full_p10']['sha256']
assert json.loads((E/'install-plan.json').read_text())['mode']=='PLAN_ONLY'
assert json.loads((E/'encoding-controls.json').read_text())['status']=='PASS'
assert linked['status']=='PASS_SCOPED_SOURCE_AND_ACTUAL_ELF'
# Retain the exact failed recorder source alongside its compile log; this is
# compiler failure evidence, not an alternate packaged candidate.
s=(R/'source/arch/arm64/kernel/asus_retained_trace.c').read_text();bad=s.replace('(in_irq() ? 16 : 0)','(in_hardirq() ? 16 : 0)')
assert bad!=s
f=R/'source/failed-attempt-1/arch/arm64/kernel/asus_retained_trace.c';f.parent.mkdir(parents=True,exist_ok=True);f.write_text(bad)
assert sha(f)==json.loads((E/'dispatch-local.json').read_text())['uploaded']['kernel/arch/arm64/kernel/asus_retained_trace.c']
(E/'compiler-correction.patch').write_text(''.join(difflib.unified_diff(bad.splitlines(True),s.splitlines(True),fromfile='failed-attempt-1/asus_retained_trace.c',tofile='candidate/asus_retained_trace.c')))
# Actual linked ABI and source lifetime proof anchors.
dis=(E/'scoped-hooks.disasm').read_text()
def func(n):return dis.split('<'+n+'>:',1)[1].split('\n\n',1)[0]
def calladdr(n,name):
 m=re.search(r'^([0-9a-f]+):.*\bbl\s+[0-9a-f]+ <'+re.escape(name)+'>',func(n),re.M);assert m,(n,name);return '0x'+m[1]
f=func('power_supply_changed_work');assert 'sub\tx20, x0, #0x2e0' in f
ops={n:calladdr('power_supply_changed_work',n) for n in ['class_for_each_device','power_supply_update_leds','atomic_notifier_call_chain','kobject_uevent','pm_relax']}
abi=dict(status='PASS_SCOPED_LINKED_ABI_AND_ORDER',source_preservation='source-checks.json',disassembly='scoped-hooks.disasm',seam_neighborhoods='linked-seams.json',base_disassembly='base-hooks.disasm',named_work=linked['symbols']['power_supply_changed_work'],body_local=dict(frame_bytes=192,context='sp+0x18, caller-local 112 bytes; registers x19=work,x20=psy',changed_work_offset=736,original_flags='x21 saved/restored; false branch retains first flags; true branch reacquires final lock and stores returned flags in x21',return_checkpoint=calladdr('power_supply_changed_work','asus_capture_ps_step')),operations=ops,external=dict(frame_bytes=176,context='sp+0x18; supplier x19, consumer x20',supplied_by_call_once=True,existing_callback_guard_preserved=True,original_call='0xffffff80087f8408: blr x1; x0=x20; callback reloaded from consumer desc+56 after begin hook',return_checkpoint='0xffffff80087f841c: step code51, local context, no consumer/supplier dereference'),property=dict(wrapper=linked['symbols']['power_supply_get_property'],compiled_part=linked['symbols']['power_supply_get_property.part.0'],frame_bytes=192,early_returns='unmodified use_cnt<=0: initialized false=-EAGAIN, true=-ENODEV, before part.0 hook',original_call='0xffffff80087f8a84: blr x3; x0=x19 supply, w1=w20 property, x2=x21 val; desc+32 callback reloaded after begin',return_checkpoint='w0 copied to w3 then callee-saved x19; step code41 uses context sp+0x18 and property w20, no supply/val dereference; w19 returned unchanged',property_values_read_by_recorder=False),recorder=dict(raw_counter_reads=1,publication='independent raw_spin_trylock_irqsave -> ring + fixed snapshot + metadata -> raw_spin_unlock_irqrestore',no_original_operation_under_new_lock=True,no_new_lock_irqmask_preempt_disable_across_original_callback=True,allowed_calls=linked['recorder_calls'],context='pre-publication preempt_count, IRQoff, in_task, in_irq, in_serving_softirq; reject NMI/UP mismatch only, not nonzero preempt'),reservation=dict(old_bytes=15168,new_bytes=5376,combined_bytes=20544,linked_capacity_constant='0x503f, remaining bytes must exceed 20543',before_any_append_or_ready=True),physical_verified=False)
# First ps_step is not return checkpoint: bind exact code20 actual address.
abi['body_local']['return_checkpoint']='0xffffff80087f887c'
save('hook-abi.json',abi)
# Check map naming code on a clearly synthetic fixture with exact-build names.
from symbolize_power import symbolize
fixture=json.loads((E/'host-controls/missing-decoded.json').read_text());fixture=copy.deepcopy(fixture)
for row in fixture['records']+list(fixture['snapshots'].values()):
 if row['callback']:row['callback']=int(linked['symbols']['power_supply_get_property']['address'],16)
a=symbolize(fixture);assert a['map_verified'] and all(x['callback']=='power_supply_get_property' for x in a['callbacks'])
save('symbolizer-control.json',dict(status='PASS',source='synthetic host fixture only; callbacks replaced in memory with exact-build common getter entry for naming check',map_verified=True,uncompressed_sha256=a['map_uncompressed_sha256'],named='power_supply_get_property',numeric_function_addresses_emitted=False))
u=i['run_uuid'];base=str(R)
commands=dict(PLAN=f'python3 -B {R}/source/install.py',parent_authorized_install_only=f'python3 -B {R}/source/install.py --execute',decode_power=f'python3 -B {R}/scripts/decode_power.py /absolute/path/to/parent-complete-console.txt --uuid {u} > /absolute/path/to/parent-private-power.json',symbolize=f'python3 -B {R}/scripts/symbolize_power.py --decoded /absolute/path/to/parent-private-power.json',decode_clock=f'python3 -B {R}/scripts/decode.py /absolute/path/to/parent-complete-console.txt --uuid {u}',decode_switch=f'python3 -B {R}/scripts/decode_switch.py /absolute/path/to/parent-complete-console.txt --uuid {u}',decode_work=f'python3 -B {R}/scripts/decode_work.py /absolute/path/to/parent-complete-console.txt --uuid {u}')
from decode_power import CODES,FIELDS,LIMITS
markers=['ASUS49-ENTRY run='+u,'A49CAP1 uuid='+u+' rows=15 row=384 fields=17 header=192','A49FAULT 0','A49SW2 uuid='+u,'A49SLOSS 0 guard=0 busy=0 admission=0 overflow=0','A49WD1 uuid='+u,'A49WLOSS 0 guard=0 busy=0 admission=0 overflow=0','A49PS1 uuid='+u,'A49PLOSS 0 guard=0 busy=0 admission=0 overflow=0','A49PGUARD BEGIN '+u,'A49PGUARD END   '+u,'VA49PH   <matching generation/metadata/tail>','VA49P 00..07 <448-byte ring rows>','VA49P 08 <fixed latest body>','VA49P 09 <fixed latest property>','VA49P 0a <fixed latest external callback>']
h=dict(status='DELIVERED_ONE_DIAGNOSTIC_POWER_PHASE_CANDIDATE_STOP',physical_GO=False,full_OS_GO=False,device_contacted=False,one_parent_physical_trial=True,run_uuid=u,remote=i,VM=dict(project='PROJECT_REDACTED',zone='us-central1-a',instance='PROJECT_REDACTED',id='8549823276971553556',final='TERMINATED',own_master_closed=True),candidate=p['candidate'],full_p10=p['full_p10'],expected_current_full_p10=p['admitted_current_full_p10'],current_pin_source='parent-supplied physical current hash; not freshly observed by worker',System_map=json.loads((E/'System-map-verification.json').read_text()),config=p['config'],helper_uuid=p['helper_uuid'],ramdisk=p['ramdisk'],DT_compiled=p['compiled_DTB'],DT_runtime=p['runtime_DTB'],charging_permission='ABSENT in base; no DT/config permission introduced; entire DT bytes retained',initrd=p['initrd'],bootargs=p['bootargs'],layout=p['layout'],capture=dict(version='A49PS1',old_bytes=15168,appended_bytes=5376,combined_bytes=20544,offsets=dict(identity=0,metadata=64,sticky_faults=256,begin_guard=320,ring=384,latest_body=3968,latest_property=4416,latest_external=4864,end_guard=5312),ring_events=8,row_bytes=448,event_fields=FIELDS,codes=CODES,protocol='protocol.md',old_protocols_and_decoders_byte_identical_except_UUID=True),checks=dict(source='source-checks.json',linked='linked-capture.json',ABI='hook-abi.json',ownership='ownership-proof.md',encoding='encoding-controls.json',packaging='packaging-receipt.json',PLAN='plan-isolation-receipt.json',default_PLAN_calls=1,compile_attempts=2,compiler_corrections=1,compiler_failure_log='compile-1.log',successful_compile_log='compile-2.log',checker_corrections='checker-corrections.jsonl',max_jobs=8),commands=commands,expected_markers=markers,limits=LIMITS+['Standing owner/manual Power fallback belongs to parent; no availability question or target operation by worker.','No automatic retry, next variant, driver disable/fake, charging/thermal change, or fullOS GO.'])
save('handoff.json',h)
(R/'artifacts/SHA256SUMS').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted((R/'artifacts').iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
print(json.dumps(dict(status=h['status'],candidate=h['candidate'],full_p10=h['full_p10'],VM='TERMINATED',UUID=u),indent=2))
