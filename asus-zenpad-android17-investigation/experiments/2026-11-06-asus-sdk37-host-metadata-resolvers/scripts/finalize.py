from pathlib import Path
import ast,base64,hashlib,json
S=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n):return json.loads((S/'evidence'/n).read_text())
build=load('build.json');qa=load('qa.json');extra=load('extra-qa.json');cap=load('capture.json');abi=load('abi.json');audit=load('final-audit.json')
assert build['host_resolvers_built'] and qa['qualified'] and extra['extra_controls_passed'] and abi['compile_exit']==abi['run']['exit']==0
assert audit['final_audit_passed'] and audit['copies_verified']==147
assert audit['query_source_sha256']==sha(S/'scripts/query.py')
for n,v in audit['resolver_sources'].items():assert sha(S/'source'/n)==v
assert audit['qualified_tool_group_sha256']==cap['qualified_tools_sha256']
assert len(qa['checks'])==29
for row in build['copies']:assert row['before']==row['copied']==row['after']
for n,r in cap['resolver_elfs'].items():assert sha(S/'artifacts'/n)==r['sha256']==build['results'][n]['sha256']
for n,r in cap['source_snapshots'].items():assert sha(S/'source/sdk37'/n)==r['sha256']
native=qa['native_and_guard_receipts']
assert native['actual_override_consumption']['exit']==0
assert native['missing_override_native_fallback']['exit']==native['malformed_override_native_fallback']['exit']==0
assert native['corrupt_binary_text_fallback']['exit']==0
assert native['fourth_label_missing']['exit']==1 and not native['fourth_label_missing']['stdout']
for n in ['wrong-override-pin','missing-override','malformed-override','wrong-root','malformed-context','corrupt-binary','unadmitted-alternate-context','sidecar']:assert native['guard-'+n]['refused']
assert extra['checks']['wrong_context_guard']['refused'] and extra['checks']['cli-positive']['exit']==0 and extra['checks']['cli-wrong-pin']['exit']==2
assert qa['positive_query']['files'][0]['capability_xattr_v2_hex']is None
assert qa['positive_query']['files'][2]['capability_xattr_v2_hex']=='01000002c0000000000000008000000000000000'
assert cap['elf_metadata']['sdk37_capability_header_copy']['before']==cap['elf_metadata']['sdk37_capability_header_copy']['copied']==cap['elf_metadata']['sdk37_capability_header_copy']['after']
# Preserve previous accepted units: verify their actual local byte manifests, without SSH or kit reads.
previous={}
for directory in ['2026-11-06-asus-full-system-observer-preparation','2026-11-06-asus-sdk37-system-ext4-qualification']:
 root=S.parent/directory;manifest=json.loads((root/'artifact-manifest.json').read_text())
 for n,r in manifest.items():assert sha(root/n)==r['sha256'],'Previous artifact changed: '+str(root/n)
 previous[directory]=len(manifest)
for p in list((S/'scripts').glob('*.py'))+list((S/'tests').glob('*.py')):ast.parse(p.read_text())
result=dict(decision='GENUINE_SDK37_HOST_RESOLVER_TOOL_QUALIFICATION_PASS',scope='Reusable tools and synthetic metadata QA only',
            remote_root=build['remote_root'],resolver_elfs={n:{'sha256':r['sha256'],'bytes':r['bytes']}for n,r in cap['resolver_elfs'].items()},
            caller_source_pins={str(p.relative_to(S)):sha(p)for p in (S/'source').glob('*')if p.is_file()},
            query_script_sha256=sha(S/'scripts/query.py'),qualified_tools_sha256=cap['qualified_tools_sha256'],
            actual_sdk37_libraries=cap['qualified_tools']['libraries'],copy_receipts_sha256=cap['copy_receipts_sha256'],
            before_copy_after_verified=len(build['copies'])+1,primary_qa_checks=29,additional_controls_passed=True,
            abi=dict(override_header_bytes=16,capabilities_offset=8,prefix_offset=16,vfs_cap_v2_bytes=20,revision_effective='0x02000001'),
            prior_local_payloads_unchanged=previous,unique_storage_bytes=audit['final_unique_storage_bytes'],storage_cap_bytes=256*1024**2,
            actual_product_outputs_selected_or_captured=False,actual_SYSTEM_accessed=False,observer_image_built=False,
            production_metadata_group_claimed=False,production_admission=False,physical_GO=False,flash_ready=False,
            future_parent_contract='PARENT-CONTRACT.md')
(S/'acceptance.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'decision':result['decision'],'elfs':result['resolver_elfs'],'copies_verified':result['before_copy_after_verified'],
                  'previous_payloads_unchanged':previous},indent=2))
