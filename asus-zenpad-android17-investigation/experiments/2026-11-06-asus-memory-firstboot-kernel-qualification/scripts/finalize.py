"""Derive scoped acceptance from stored inspection, never contact the builder."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json

S = Path(__file__).resolve().parents[1]
R = S.parent

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(name,obj): (S/name).write_text(json.dumps(obj,indent=2)+'\n')

a=json.loads((S/'evidence/authorities.json').read_text())
d=json.loads((S/'evidence/remote-inspection.json').read_text())
s=json.loads((S/'evidence/remote-supplement.json').read_text())
checks=[]
def check(name,value):
    checks.append({'name':name,'pass':bool(value)})
    assert value,name

for k,v in a.items(): check('authority bytes '+k,sha(R/v['path'])==v['sha256'])
memory=R/'2026-11-06-asus-sdk37-lmkd-functional/artifacts/frozen'
export=a['memory_export']['data']['files']
bad=[k for k,v in export.items() if not (memory/k).is_file() or sha(memory/k)!=v['sha256'] or (memory/k).stat().st_size!=v['bytes']]
check('510 frozen memory payload hashes and sizes',len(export)==510 and not bad)
bmc=R/'2026-11-06-asus-bmc156-full-kernel'
full=a['physical_full']['data']
base=gzip.decompress((bmc/'evidence/r5-source-manifest.json.gz').read_bytes())
check('physical compressed baseline authority',sha(bmc/'evidence/r5-source-manifest.json.gz')==full['source_manifests']['r5']['compressed_sha256'])
post=json.loads(base)
delta=json.loads((bmc/'patches/pre-post-hashes.json').read_text())
post.update({p:v['after'] for p,v in delta.items()})
parent_canonical=hashlib.sha256(json.dumps(post,sort_keys=True).encode()).hexdigest()
check('reconstructed physical full postimage manifest',parent_canonical==full['source_manifests']['post']['canonical_json_sha256'])
check('remote manifest uses identical map; compact serialization differs from parent convention',digest(post)==s['physical_manifest']['canonical_json_sha256'])
check('exact manifest-selected physical source paths',all(post[p]==h for p,h in s['selected_physical_manifest_pins'].items()))
for k,v in d['artifacts'].items(): check('actual artifact '+k,v['matches'])
groups={}
for group,n,opts in [('firstboot',290,134),('memory',210,72)]:
    sources=d['sources'][group]
    config=d['selected_config'][group]
    check(group+' exact unique source selection',len(sources)==n and len({r['path'] for r in sources})==n)
    check(group+' actual source equality to both frozen pins and full physical manifest',all(r['equal_physical'] and r['matches_frozen_virtual'] and r['matches_frozen_physical'] and r['physical']==post[r['path']] for r in sources))
    check(group+' exact unique config selection',len(config)==opts and len({r['option'] for r in config})==opts)
    check(group+' actual physical config matches frozen selected values',all(r['physical']==r['frozen_physical'] for r in config))
    if group=='firstboot':check('firstboot all134 options equal',not d['selected_config_differences'][group])
    else:check('memory all72 values preserve exact frozen virtual selection',all(r['virtual']==r['frozen_virtual'] for r in config))
    groups[group]={'sources':n,'options':opts,'source_map_sha256':digest({r['path']:r['virtual'] for r in sources}), 'physical_source_map_sha256':digest({r['path']:r['physical'] for r in sources}),'virtual_config_selection_sha256':digest({r['option']:r['virtual'] for r in config}),'physical_config_selection_sha256':digest({r['option']:r['physical'] for r in config}),'config_differences':d['selected_config_differences'][group]}
expected=a['memory_config']['data']['differences']
check('only five documented memory differences', [{ 'name':r['option'],'virtual':r['virtual'],'physical':r['physical']} for r in d['selected_config_differences']['memory']]==expected)
check('historical terminal build receipt binds actual Image and config',s['historical_memory_build_status']['returncode']==0 and all(v['sha256']==d['artifacts'][k]['sha256'] for k,v in [('memory_image',s['historical_memory_build_status']['files']['out/arch/arm64/boot/Image']),('memory_config',s['historical_memory_build_status']['files']['out/.config'])]))
union={r['path']:r['virtual'] for rows in d['sources'].values() for r in rows}
rawdiff=d['whole_config_differences']
effective=[r for r in rawdiff if r['virtual'] not in ('n','absent') or r['physical'] not in ('n','absent')]
virtual_values=[r for r in effective if r['virtual'] not in ('n','absent')]
save('evidence/selected-source-pins.json',{'format':'SHA256 of UTF-8 json.dumps(map, sort_keys=True, separators=(comma,colon)); no trailing newline', 'groups':groups,'union_files':len(union),'union_source_map_sha256':digest(union),'union':union})
with (S/'evidence/whole-config-differences.tsv').open('w') as f:
    f.write('option\tvirtual\tphysical\tclassification\n')
    for row in rawdiff:
        kind='both disabled; representation only' if row['virtual'] in ('n','absent') and row['physical'] in ('n','absent') else 'effective value differs; outside selected equality unless listed'
        f.write('\t'.join([row['option'],row['virtual'],row['physical'],kind])+'\n')
save('evidence/virtual-non-disabled-differences.json',virtual_values)
save('evidence/verification.json',{'checks':checks,'checks_passed':len(checks),'memory_payloads_verified':len(export),'physical_post_manifest':{'parent_serialization':'json.dumps(map, sort_keys=True), UTF-8, no trailing newline','parent_sha256':parent_canonical,'compact_sha256':digest(post),'files':len(post)},'whole_config_difference_rows':len(rawdiff),'effective_value_difference_rows':len(effective),'disabled_representation_only_rows':len(rawdiff)-len(effective),'virtual_non_disabled_difference_rows':len(virtual_values)})

refs=[R/'2026-11-06-asus-android17-orchestration/NEXT-RUNTIME-INPUTS.md',R/'2026-11-06-asus-sdk37-lmkd-functional/report/REPORT.md',R/'2026-11-06-asus-sdk37-lmkd-functional/report/HANDOFF.md',R/'2026-11-06-asus-sdk37-lmkd-functional/evidence/parent-memory-acceptance.json',R/'2026-11-06-asus-genuine-service-runtime/REPORT.md',R/'2026-11-06-asus-genuine-service-runtime/HANDOFF.json',R/'2026-11-06-asus-genuine-service-runtime/evidence/parent-runtime-acceptance.json',R/'2026-11-06-asus-firstboot-parity-continuation/REPORT.md',bmc/'report/REPORT.md',bmc/'report/HANDOFF.md',bmc/'report/SOURCE-PINS.json',bmc/'patches/pre-post-hashes.json',R/'2026-11-06-asus-product-input-build-kit/scripts/remote.py']
save('evidence/reference-hashes.json',{str(p.relative_to(R)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in refs})
accept={'schema_version':1,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'ACCEPT_EXISTING_IMAGE_FOR_FUTURE_SELECTED_PARITY_FIRSTBOOT_FIXTURE_WITH_EXPLICIT_LIMITATIONS','pre_runtime_selected_gates_pass':True,'strict_72_option_byte_equality':False,'artifact_pins':d['artifacts'],'selected_parity':groups,'union_source_files':len(union),'union_source_map_sha256':digest(union),'physical_source_manifest_parent_canonical_sha256':parent_canonical,'virtual_only_source_adaptation':d['virtual_board_source'],'source_scope':'Exact manifest-selected files only, plus separately recorded GIC adaptation; no full-tree source equivalence audit','config_difference_evidence':'evidence/whole-config-differences.tsv','config_limitations':['DEBUG_PREEMPT=y virtual versus n physical changes debug checks and overhead; no timing equivalence','CMA_DEBUGFS, PREEMPTIRQ_EVENTS, PREEMPT_TRACER, ZRAM_MEMORY_TRACKING absent virtual versus explicitly n physical; disabled in both configurations','CMA enabled in both; virtual fixture has no physical board CMA reservation or board-driver working set','SCHED_DEBUG, SCHEDSTATS, SCHED_INFO, SCHED_MC and MTK_SCHED_RQAVG_KS/US differ outside selected72; no vendor scheduler equivalence','Crypto module/builtin/disabled selections, hardening, failure behavior, platform/driver and reserved-memory coverage differ outside selected gates; downstream capabilities require their own qualification'],'kernel_source_patch_required_for_scoped_reuse':False,'kernel_rebuild_required_for_scoped_reuse':False,'smallest_later_requirement_if_strict_debug_parity_requested':'In a new owned virtual kernel stage disable CONFIG_DEBUG_PREEMPT only, resolve config and build Image serially; repin all selected sources/options and repeat relevant memory and firstboot runtime checks. Do not change physical config, add fake disabled entries, or modify this existing candidate. No such build was performed.','runtime_evidence_inherited':{'eligible_pressure_recovery_cycles_passed':4,'protected_incompressible_overload':'failed/aborted; swap write failures; no recovery','full_android_gms_working_set':'unproved'},'future_official_capture_consumed':False,'future_fixture_built_or_run':False,'physical_GO':False,'physical_boot_verified':False,'whole_kernel_equivalent':False,'runtime_requalified_by_this_task':False,'remote_owned_receipts':['/srv/android/asus-memory-firstboot-kernel-qualification-20261106/inspection.json','/srv/android/asus-memory-firstboot-kernel-qualification-20261106/supplement.json'],'evidence_sha256':{p.name:sha(p) for p in sorted((S/'evidence').glob('*')) if p.is_file()}}
save('acceptance.json',accept)
contract={'schema_version':1,'state':'PREPARED_WAITING_FOR_SEPARATELY_OWNED_COHERENT_OFFICIAL_CAPTURE','kernel':{'image':d['artifacts']['memory_image'],'config':d['artifacts']['memory_config'],'physical_reference_image_sha256':d['artifacts']['physical_image']['sha256'],'physical_reference_config_sha256':d['artifacts']['physical_config']['sha256'],'selected_source_union_sha256':digest(union),'acceptance_sha256':sha(S/'acceptance.json'),'reuse_existing_kernel':True},'capture_admission':{'owner_supplied_only':True,'not_consumed_now':True,'require_terminal_build_receipt':True,'require_exact_reviewed_r8_profile':True,'reject_failed_build_and_old_r7_profile':True,'require_complete_groups_and_before_copy_after_hash_equality':True,'groups':['genuine installed service ELFs with actual implementation dependency closure, linker and namespaces','mandatory platform boringssl_self_test32 and boringssl_self_test64 exact official variants','selected signed com.android.runtime.apex and required bootstrap packages, actual package contents and trust/activation metadata','genuine generated system/system_ext/product properties plus aggregate official apexkeys metadata','one coherent compiled policy/CIL/context/VINTF/init/fstab group; generated service contexts and manifests']},'fixture_requirements':['Create a fresh owned fixture/input/run revision; preserve old failures and all existing sources/out/kits','Verify before/copy/after hashes against owner manifest; never follow host /apex symlinks as package contents','Retain genuine crypto self-test actions, bootstrap/post-data APEX waits, signed package bytes, verification/trust and final linker namespaces','Let hwservicemanager own ready/disabled properties, apexd own APEX readiness, and keystore own module-hash/crypto handoff; observer only reads','No fabricated sys.boot_completed, BPF readiness, service substitute, skipped wait or policy relaxation','Verify genuine SELinux enforcing state/SIDs, manager IPC positive and negative controls; exit0 alone is insufficient','For memory inclusion, retain prepared low-RAM configuration and review exact zram0 swap_block_device label in coherent context set; no allow-rule expansion','Require actual lz4 selection, mkswap/swapon, 512MiB logical zRAM with no backing device and PSI monitor registration before accepting lmkd; observe consumed properties','Keep one CPU/1GiB future service-fixture budget unless owner separately authorizes a stock-RAM memory runtime; do not label a 1GiB guest as stock-RAM qualification','Any fresh fixture must requalify runtime behavior with this kernel; old95a62a8 firstboot runs do not become c59e runtime tests'],'memory_input_pins':{'genuine_lmkd_sha256':'ff975915ad8d1f2882cf297c6fa312e144166d87b1251bf880eb6e890a34353d','label_candidate_sha256':'3c9be94080cd5d2b146bd52e325545bc7b27e86395413e16ae650d3895c2426c','label_candidate':'/dev/block/zram0 u:object_r:swap_block_device:s0','coherence_rule':'The future official daemon, policy and properties must be pinned from its capture; the old memory ELF/policy pins are evidence references, not permission to mix revisions. A changed daemon must be qualified again.','properties':{'ro.config.low_ram':'true','ro.config.per_app_memcg':'false','ro.lmk.use_new_strategy':'true','ro.lmk.use_minfree_levels':'false'},'ro_lmk_use_psi':'not read by accepted source; no fabricated setting','logical_zram_bytes':536870912,'compression':'lz4','dalvik_growth_limit':'192MiB prepared source only; ART unproved'},'future_acceptance_evidence':['actual serial, command, terminal status, all consumed input hashes','genuine crypto self-tests complete; actual signed APEX activation/trust/verity and final namespaces','genuine manager IPC and service-owned readiness under coherent enforcing policy','Keymaster and keystore functional outputs before downstream claims','actual lmkd SID/properties, PSI fd+EPOLLPRI membership and zRAM activation if included','no full Android/GMS working-set or physical GO inference from native success'],'prohibited_now':['capture copying or preparation','build or boot','device/ADB/root/keys/private calibration','product supervisor or lock inspection/mutation','active source/out mutation','cloud/process lifecycle work'],'physical_GO':False}
save('next-fixture-contract.json',contract)
print(json.dumps({'checks_passed':len(checks),'union_sources':len(union),'source_union_sha256':digest(union),'acceptance_sha256':sha(S/'acceptance.json'),'contract_sha256':sha(S/'next-fixture-contract.json')},indent=2))
