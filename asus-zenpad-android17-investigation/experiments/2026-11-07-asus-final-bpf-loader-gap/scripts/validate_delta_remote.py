from pathlib import Path
import hashlib,json,subprocess as s,shutil
O=Path('/srv/android/asus-final-bpf-loader-gap-20261107');T=O/'integration-apply-check';T.mkdir(exist_ok=False)
K=Path('/srv/android/asus-firstboot-runtime/kernel-cpuset-r1')
H=Path('/srv/android/asus-network-runtime/handoff-r1')
manifest=json.loads((H/'manifest.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt={'active_source_modified':False,'config_delta':{},'source':str(K),'before':{},'after_map_info':{},'after_all_four':{},'patches':{}}
for rel,pins in manifest['kernel_changed_files'].items():
 p=K/rel;actual=sha(p) if p.exists() else None
 assert actual==pins['baseline_sha256'],(rel,actual,pins)
 receipt['before'][rel]=actual
 if p.exists():(T/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,T/rel)
for n in manifest['kernel_patch_order']:
 patch=H/'patches'/n;expected=manifest['sha256']['patches/'+n];assert sha(patch)==expected
 receipt['patches'][n]={'sha256':expected}
 p=s.run(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=T,capture_output=True,text=True,timeout=5)
 receipt['patches'][n].update(exit=p.returncode,stdout=p.stdout,stderr=p.stderr);assert p.returncode==0
 assert 'offset' not in p.stdout and 'fuzz' not in p.stdout
 if n=='01-map-info.patch':
  receipt['after_map_info']={rel:sha(T/rel) for rel in ['include/uapi/linux/bpf.h','kernel/bpf/syscall.c']}
for rel,pins in manifest['kernel_changed_files'].items():
 receipt['after_all_four'][rel]=sha(T/rel);assert sha(T/rel)==pins['tested_sha256']
for rel,pins in manifest['kernel_changed_files'].items():
 p=K/rel;assert (sha(p) if p.exists() else None)==receipt['before'][rel]
receipt['all_four_match_qualified_and_physical_sources']=True
(O/'evidence/integration-apply-check.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
