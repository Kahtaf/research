"""Check owned evidence relations only; no native engine or remote access."""
import json,hashlib,base64
from pathlib import Path
R=Path(__file__).resolve().parent;E=R/'evidence'
def read(n):return json.loads((E/n).read_text())
f=read('frozen-exact-commands.json');lin=read('relational-lineage.json');frozen=read('frozen-r8-selected.json');elf=read('selected-elf-identity.json');archive=read('archive-native-record.json');metrics=read('frozen-r8-selected-metrics.json');deps=read('selected-deps.json');checks={}
checks['frozen_first_phase_parent_pin']=frozen['host_init_verifier']['receipt_sha256']=='0e06bbee948f7413eaa0b54f6be95d8374750c0ece2646526864733ea6204660'
checks['frozen_full_phase_parent_pin']=frozen['bootimage']['receipt_sha256']=='06a73e6125819f5dd7e7449cbd95e1ac128beb483be6f5b194d5c7324933a2b2'
checks['frozen_file_pins']=all(v['matches_receipt'] for phase in ['host_init_verifier','bootimage'] for v in frozen[phase]['verified_files'].values()) and metrics['receipt_match']
checks['source_receipt_bound_before_build']=frozen['integration.json']['value']['active_source_postimages_sha256']==frozen['postimages.json']['sha256']
checks['selected_seven_native_digest_matches']=lin['all_selected_digests_match'] and len(lin['rows'])==7
checks['selected_seven_metric_cmdhash_matches']=lin['all_selected_frozen_metrics_match_cmdhash']
checks['five_exact_commands_plus_rsp_matches']=sum(r.get('command_plus_rsp_matches_native_state') is True for r in lin['rows'])==5
checks['selected_current_ninja_rows_absent']=lin['current_ninja_rows']==[]
checks['all_elf_aarch64']=all(v['e_machine']==183 for v in elf.values())
for name in ['bpfloader','vold']:
 vals=[v for k,v in elf.items() if k.endswith('/'+name)]
 checks[name+'_build_id_consistency']=len(vals)==3 and len({tuple(v['build_ids']) for v in vals})==1 and all(v['build_ids'] for v in vals)
a=archive['fs_state_entries'][0];path=archive['selected_paths'][0];m=next(r for r in f['metrics'] if r['value']['output']==path);artifact=archive['selected_files'][path]
checks['libvold_archive_native_digest_matches']=a['digest']['hash']==artifact['sha256']
checks['libvold_archive_frozen_cmdhash_matches']=a['cmd_hash_hex']==base64.b64decode(m['value']['cmdhash']).hex()
public=next(v for k,v in deps['targets'].items() if k.endswith('PublicVolume.o'))
checks['PublicVolume_dependency_record_key_matches']=public['mtime_ns']==public['output_mtime_ns'] and public['count']==1032 and 'system/vold/model/PublicVolume.cpp' in public['dependencies']
checks['selected_native_no_action_attestations']=all(r['native_state']['action'] is None for r in lin['rows'])
assert all(checks.values()),checks
qa={'checks':checks,'all_pass':True,'scope':'owned extracts only; no current native target validation or parent acceptance','evidence_files':{p.name:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(E.iterdir()) if p.is_file() and p.name!='QA.json'},'baseline_script_pins':{str(p.relative_to(R.parent)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((R.parent/'2026-11-06-asus-r8-continuation-kit/scripts').glob('*.py')) if p.name in ['compiler_channel.py','verify_product_r3.py','capture_build_evidence.py','continuation.py','integrate.py','r3_inputs.py','seal.py']}}
(E/'QA.json').write_text(json.dumps(qa,indent=2)+'\n')
print(json.dumps({'checks':checks,'all_pass':True},indent=2))
