#!/usr/bin/env python3
"""Stage the accepted networking handoff without touching a live kernel/AOSP."""
import pathlib,hashlib,shutil,subprocess,json,datetime
R=pathlib.Path('/srv/android/asus-build-continuation');H=pathlib.Path('/srv/android/asus-network-runtime/handoff-r1');K=R/'kernel';A=pathlib.Path('/srv/android/lineage24/packages/modules/Connectivity');O=R/'inputs/network-r1';O.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
expected='d6790e2efde8ddb11102f561b5c58129660be09d41f1bbfb66402f3865ef13dd';assert sha(H/'manifest.json')==expected
m=json.loads((H/'manifest.json').read_text());assert len(m['sha256'])==60
for rel,h in m['sha256'].items():
    p=pathlib.PurePosixPath(rel);assert not p.is_absolute() and '..' not in p.parts
    assert sha(H/rel)==h,rel
    if rel.startswith(('patches/','source/','connectivity-source/','evidence/')):
        q=O/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(H/rel,q);assert sha(q)==h
shutil.copyfile(H/'manifest.json',O/'manifest.json');assert sha(O/'manifest.json')==expected
assert m['connectivity_patch_order']==['11-network-policy-and-required-loader.patch']
for rel,item in m['kernel_changed_files'].items():
    p=K/rel;assert (sha(p) if p.exists() else None)==item['baseline_sha256'],rel
assert not set(m['kernel_changed_files']) & {'arch/arm64/configs/asus_p00a_defconfig','include/linux/cgroup-defs.h','kernel/cgroup.c','kernel/cpuset.c'}
C=R/'platform-connectivity';C.mkdir();before={}
for rel,item in m['connectivity_changed_files'].items():
    assert sha(A/rel)==item['baseline_sha256'],rel
    q=C/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(A/rel,q);assert sha(q)==item['baseline_sha256'];before[rel]=sha(q)
patch=O/'patches/11-network-policy-and-required-loader.patch'
subprocess.run(['git','-C',str(C),'apply','--check',str(patch)],check=True)
subprocess.run(['git','-C',str(C),'apply',str(patch)],check=True)
for rel,item in m['connectivity_changed_files'].items():assert sha(C/rel)==item['tested_sha256'] and sha(A/rel)==item['baseline_sha256'],rel
config=(R/'build/.config').read_text();assert 'CONFIG_FILE_LOCKING=y\n' in config
for n in ['DUMMY','VETH','NAMESPACES','NET_NS']:assert f'CONFIG_{n}=y\n' not in config,n
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest_sha256':expected,'handoff_payload_hashes_verified':60,'connectivity_before':before,'connectivity_after':{p:v['tested_sha256'] for p,v in m['connectivity_changed_files'].items()},'kernel_preimages_verified':m['kernel_changed_files'],'kernel_patches_applied':False,'active_aosp_changed':False,'virtual_config_copied':False,'file_locking_preserved_y':True,'whole_platform_loader_qualified':False,'boundary':m['boundaries'],'legacy_map_type_adaptations':{'tether_dev_map':'25 -> HASH1','local_net_note_op_cache_map':'LRU9 -> HASH1','loopback_access_cache_map':'LRU9 -> HASH1'},'local_access_lpm_maps':'both actual type11'}
(R/'evidence/network-staging.json').write_text(json.dumps(report,indent=2)+'\n');print('All60 handoff payload hashes verified; Connectivity11 staged with exact pre/post hashes. Live kernel and AOSP untouched.')
