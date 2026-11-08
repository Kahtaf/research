"""Small synthetic decoder controls only; never target evidence."""
from pathlib import Path
import copy,hashlib,importlib.util,json,uuid
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('strict_minimal_decode',R/'scripts/decode.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
p=json.loads((R/'evidence/packaging-receipt.json').read_text());i=json.loads((R/'evidence/identity.json').read_text());prefix='ASUS-MINPLAT run='+i['run_uuid']+' '
rows=['event=entry pid=1',p['expected_uname_record'],'event=scheduler policy=0 priority=0 nice=0','event=compute-begin iterations=2000000','event=compute-end iterations=2000000 state=2093acf8 checksum=4296231513146560']
for cycle in range(1,6):
 rows += [f'event=timer-before cycle={cycle} irq={cycle*10} monotonic={cycle*2}.000000000 requested_interval=1s',f'event=timer-return cycle={cycle} signal=SIGALRM irq={cycle*10+1} irq_before={cycle*10} monotonic={cycle*2+1}.000000000']
rows+=['event=success operation=five-timer-returns errno=0 next=normal-reboot']
header='ram console header, hw_status: 2, fiq step 0.\n';console=i['entry_tag']+'synthetic vendor line\n'+''.join(prefix+r+'\n' for r in rows);raw=(header+console).encode()
att=dict(installed_full_p10_sha256=p['full_p10']['sha256'],raw_sha256=hashlib.sha256(raw).hexdigest(),complete_console_reference='SYNTHETIC fixture only',console_capacity=523072,console_log_size=len(console.encode()),console_log_start=0,pre_trial_stock_boot_id='11111111-1111-4111-8111-111111111111',post_trial_stock_boot_id='22222222-2222-4222-8222-222222222222',stock_return_verified=True,stock_return_reference='SYNTHETIC parent attestation; no physical result')
assert m.decode(raw,att)['status']=='FUNCTIONAL_RAM_SEQUENCE_WITH_PARENT_ATTESTED_FRESH_STOCK_RETURN'
unknown={}
def check(name,data,a=None):
 if a is None:
  a=copy.deepcopy(att);a['raw_sha256']=hashlib.sha256(data).hexdigest()
  h=data.find(b'\n')+1;a['console_log_size']=len(data)-h
 result=m.decode(data,a);assert result['status']=='UNKNOWN',(name,result);unknown[name]=result.get('reason')
check('arbitrary_prefix',b'junk\n'+raw)
check('stale_kernel',raw.replace(i['entry_tag'].encode(),i['entry_tag'].replace(i['run_uuid'],'33333333-3333-4333-8333-333333333333').encode()))
check('mixed_helper_identity',raw.replace(prefix.encode(),prefix.replace(i['run_uuid'],'44444444-4444-4444-8444-444444444444').encode(),1))
check('failed_checksum',raw.replace(b'checksum=4296231513146560',b'checksum=4296231513146561'))
check('missing_timer_return',raw.replace((prefix+rows[6]+'\n').encode(),b''))
check('irq_no_growth',raw.replace(b'cycle=1 signal=SIGALRM irq=11',b'cycle=1 signal=SIGALRM irq=10'))
check('truncated',raw[:-1])
a=copy.deepcopy(att);a['console_capacity']=len(console.encode());check('saturation',raw,a)
a=copy.deepcopy(att);a['stock_return_verified']=False;check('stock_return_unproved',raw,a)
assert m.decode(raw,None)['status']=='UNKNOWN'
(R/'evidence/synthetic-complete-stock-proc.txt').write_bytes(raw);(R/'evidence/synthetic-parent-attestation.json').write_text(json.dumps(att,indent=2)+'\n')
assert (R/'evidence/synthetic-complete-stock-proc.txt').read_bytes()==raw
result=dict(status='STRICT_SYNTHETIC_DECODER_CONTROLS_PASS',complete_known_stock_proc_framing=True,positive_synthetic_only=True,unknown_controls=unknown,absent_attestation_unknown=True,raw_not_rewritten=True,no_target_input_or_physical_calibration=True)
(R/'evidence/decoder-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
