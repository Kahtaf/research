"""Cross-check independent OEM bytecode anchors and emit parent-consumable facts."""
from pathlib import Path
import json,hashlib,struct
from dex import Dex
S=Path(__file__).resolve().parents[1];W=S.parent
methods=json.loads((S/'evidence/decoded-methods.json').read_text());get=lambda suffix:next(m for m in methods if m['method'].endswith(suffix))
stub=get('IRecoverySystem$Stub;->onTransact(ILandroid/os/Parcel;Landroid/os/Parcel;I)Z')
fields={f['name'].split('->')[1].split(':')[0]:f.get('initial_value') for f in stub['class_info']['fields']}
assert fields['TRANSACTION_clearBcb']==3 and fields['DESCRIPTOR']=='android.os.IRecoverySystem'
switch=next(r for r in stub['instructions'] if r['name']=='sparse-switch');assert switch['switch']['3']==0x49
branch=[r for r in stub['instructions'] if 0x49<=r['pc']<=0x5c]
assert [r['ref'] for r in branch if r['name'].startswith('invoke')]==['Landroid/os/Parcel;->enforceInterface(Ljava/lang/String;)V','Landroid/os/IRecoverySystem$Stub;->clearBcb()Z','Landroid/os/Parcel;->writeNoException()V','Landroid/os/Parcel;->writeInt(I)V']
proxy=get('IRecoverySystem$Stub$Proxy;->clearBcb()Z');by={r['pc']:r for r in proxy['instructions']};assert by[0x10]['literal']==3 and by[0x11]['literal']==0 and by[0x12]['ref']=='Landroid/os/IBinder;->transact(ILandroid/os/Parcel;Landroid/os/Parcel;I)Z'
clear=get('RecoverySystemService$BinderService;->clearBcb()Z');assert [r.get('literal') for r in clear['instructions'][:2]]==[0,0]
assert clear['instructions'][2]['ref'].endswith('->setupOrClearBcb(ZLjava/lang/String;)Z')
shared=get('RecoverySystemService$BinderService;->setupOrClearBcb(ZLjava/lang/String;)Z');by={r['pc']:r for r in shared['instructions']};assert by[8]['ref']=='android.permission.RECOVERY' and by[11]['ref'].endswith('->enforceCallingOrSelfPermission(Ljava/lang/String;Ljava/lang/String;)V')
assert by[0xe]['target']==0x29 and by[0x29]['ref']=='ctl.start' and by[0x2c]['ref']=='clear-bcb' and by[0x47]['target']==0x56
assert by[0x56]['ref'].endswith('->readInt()I') and by[0x5b]['ref'].endswith('->writeInt(I)V') and by[0x5e]['literal']==100
onstart=get('RecoverySystemService;->onStart()V');assert onstart['instructions'][0]['ref']=='recovery'
root=get('ActivityManager;->checkComponentPermission(Ljava/lang/String;IIZ)I');by={r['pc']:r for r in root['instructions']};assert by[6]['target']==12 and by[8]['literal']==1000 and by[12]['name']=='return'
for m in methods:
 assert not any('quick' in r['name'] for r in m['instructions']),'Unresolved optimized operand not acceptable'
queries=json.loads((S/'evidence/policy-queries.json').read_text())
assert all(r['exit_code']==0 and not r['source_permissive'] for r in queries['queries'])
expected_denials=[('u:r:shell:s0','u:object_r:ctl_default_prop:s0','set'),('u:r:uncrypt:s0','u:object_r:misc_block_device:s0','read'),('u:r:uncrypt:s0','u:object_r:block_device:s0','getattr'),('u:r:uncrypt:s0','u:object_r:para_block_device:s0','getattr')]
assert [(r['source'],r['target'],r['permission']) for r in queries['queries'] if not r['allowed']]==expected_denials
pins=[]
for m in methods:
 b=(S/m['file']).read_bytes();off=m['code']['code_offset'];n=16+2*m['code']['insns_size'];pins.append(dict(method=m['method'],file=m['file'],code_item_offset=hex(off),code_header_and_insns_bytes=n,sha256=hashlib.sha256(b[off:off+n]).hexdigest()))
(S/'evidence/method-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
for name in ['clear-attempt-reconciled.json','clear-attempt-quiescence.json','clear-prediction.json','live-fstab-identity.json']:
 (S/'evidence'/('parent-'+name)).write_bytes((W/'2026-11-06-asus-pending-recovery-request/evidence'/name).read_bytes())
uncrypt=W/'2026-11-06-asus-pending-recovery-request/source/uncrypt';native=hashlib.sha256(uncrypt.read_bytes()).hexdigest();assert native=='3f7e8c8ed7272540315eaef0af405a57ac701db121dd5c842a8b04be721b2671'
result=dict(status='OFFLINE_API_QUALIFIED_PARENT_EXECUTION_NOT_AUTHORIZED',service='recovery',interface='android.os.IRecoverySystem',method='clearBcb()Z',transaction=3,flags=0,method_arguments=[],parent_call='/system/bin/service call recovery 3',read_only_descriptor_transaction=1598968902,required_caller_uid=0,caller_context='u:r:shell:s0',server_context='u:r:system_server:s0',permission='android.permission.RECOVERY',permission_uid0_result='GRANTED by exact OEM ActivityManager bytecode',stock_policy_sha256=queries['policy_sha256'],stock_policy_control_result='system_server allowed; shell denied',native_service='clear-bcb',native_command='/system/bin/uncrypt --clear-bcb',native_binary_sha256=native,native_primitive_dependency='../2026-11-06-asus-exact-oem-clear-bcb-audit/REPORT.md',native_write_offset=0,native_write_bytes=1088,native_write_value=0,partition_bytes=524288,preimage_sha256='8d0cf5c87bcb4abe769f7e4dc2000d45827980b6c12fb792af7bbd0d195c0ef9',postimage_sha256='8c9e2c158ac95f152d08ea9de929ae36d054131ca4b10620890974ed831480ef',parent_prediction_confirmed=True,prior_attempt='direct shell ctl request denied; no client; no metadata change; reconciled',framework_internal_connect_attempts_max=30,framework_internal_connect_retry_sleep_ms=1000,framework_status_read_deadline=None,parent_api_retry_allowed=False,device_operations=False,metadata_writes=False,execution_approval=False,user_presence_assumed=False,remaining_parent_gates=['Fresh live descriptor matches exact interface','Current selected framework OAT/ODEX hashes and public/native/policy identities match','Fresh exclusive full preimage and predicted exact postimage','New parent approval for this API operation; user away is not permission','One Binder invocation only, authoritative result plus independent whole readback and quiescence'])
(S/'HANDOFF.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'static_cross_checks':'PASS','transaction':3,'interface':result['interface'],'method_arguments':[],'policy_queries':len(queries['queries']),'selected_methods':len(methods)}))
