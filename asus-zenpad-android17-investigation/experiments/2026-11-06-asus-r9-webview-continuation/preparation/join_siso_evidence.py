from pathlib import Path
import remote,json
s=r'''
from pathlib import Path
import json,hashlib,base64,datetime,sys
R=Path('/srv/android/asus-reviewed-build-kit/r9');O=Path('/srv/android/asus-reviewed-build-kit/r8');A=Path('/srv/android/lineage24');sys.path.insert(0,str(O/'scripts'))
from integrate import sha
from verify_product_r3 import log_entries
from compiler_channel import commands_for
state=json.loads((R/'evidence/selected-siso-state-v2.json').read_text());targets=set(state['selected_entries']);commands,_=commands_for(O,targets);joins=[]
for phase in ['host_init_verifier','bootimage']:
 folder=O/'attempt/native-evidence'/phase;receipt=json.loads((folder/'receipt.json').read_text());entries=log_entries(folder/'.ninja_log',targets)
 for line in (folder/'siso_metrics.json').read_text().splitlines():
  if not line.strip():continue
  metric=json.loads(line);target=metric.get('output')
  if target not in targets or target not in entries:continue
  node=state['selected_entries'][target];cmdhash=base64.b64decode(metric.get('cmdhash','')).hex()
  # Some targets have repeated metric attempts; only the persisted exact command hash joins.
  if cmdhash!=node['cmd_hash_hex']:continue
  joins.append(dict(output=target,phase=phase,phase_exit_code=receipt['exit_code'],phase_receipt_sha256=sha(folder/'receipt.json'),metrics_sha256=sha(folder/'siso_metrics.json'),step_id=metric['step_id'],frozen_ninja=entries[target],frozen_completed_compiler_commands=commands.get(target,[]),native_metric_command_hash=cmdhash,current_siso=node,output_digest_matches=node.get('digest',{}).get('hash')==node.get('current_sha256'),current_siso_mtime_matches_disk=node['mod_time_ns']==node.get('current_mtime_ns'),native_input_count=metric.get('inputs'),native_input_content_digests_recorded=False))
critical=['out/soong/.intermediates/system/bpf/loader/bpfloader/android_arm64_armv8-a/unstripped/bpfloader','out/soong/.intermediates/system/vold/libvold/android_arm64_armv8-a_static/obj/system/vold/model/PublicVolume.o','out/soong/.intermediates/system/vold/vold/android_arm64_armv8-a/unstripped/vold']
for t in critical:
 rows=[x for x in joins if x['output']==t and x['phase']=='host_init_verifier'];assert len(rows)==1 and rows[0]['output_digest_matches'] and rows[0]['current_siso_mtime_matches_disk'] and rows[0]['frozen_completed_compiler_commands']
r=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),r8_seal='f55aedf8ac9d2a513e3663230db0b9d802e72b5df512fc0db6b3714331a7efa4',current_state_sha256=state['source_state_sha256'],schema_version='siso/v1.5.8',joins=joins,critical_outputs=critical,closed_fact='Actual frozen r8 completed compiler commands/Ninja entries/metrics cmdhash join current Siso local output records and current output SHA256/mtime without inventing current Ninja rows.',remaining_gate='No execution-time transitive input content/root identity has been proven for these local actions: metrics record input counts; current Siso action digests are absent. Current global file hashes or newly frozen current graph cannot substitute for consumed input versions. Exact versioned dependency/toolchain/graph/rsp proof remains required, or parent must decide on further authoritative evidence. No cached execution is admitted.',cache_admitted=False)
with (R/'evidence/cache-provenance-gap.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/cache-provenance-gap.json').write_text(r);d=json.loads(r);print(json.dumps({k:v for k,v in d.items() if k!='joins'},indent=2));print('joined outputs:',len(d['joins']))
