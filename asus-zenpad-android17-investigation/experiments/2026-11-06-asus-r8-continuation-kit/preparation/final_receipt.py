exec(open('2026-11-06-asus-r8-continuation-kit/preparation/inspect_remote.py').read().split('script=r')[0])
r=m.run(r'''
from pathlib import Path
import json,sys,hashlib
R=Path('/srv/android/asus-reviewed-build-kit/r8');sys.path.insert(0,str(R/'scripts'))
from integrate import verify_pins,read,manifest,sha,write
from continuation import continuation_inputs,deltas
seal=verify_pins(R);assert seal=='f55aedf8ac9d2a513e3663230db0b9d802e72b5df512fc0db6b3714331a7efa4'
plan=read(R/'inputs/plan.json');rows=continuation_inputs(plan)
active=manifest(plan['device']);assert active==read(plan['r7_staged_receipt'])['product_after']
for rel,row in rows.items():assert active[rel]=={'sha256':row['before']}
stage=manifest(plan['staging']);old=read(plan['r7_staging_manifest']);diff={k:dict(before=old.get(k),after=stage.get(k)) for k in old.keys()|stage.keys() if old.get(k)!=stage.get(k)}
assert set(diff)=={'STAGED.json',*['product-device/'+r for r in rows]}
assert not (R/'attempt').exists() and not (R/'parent-review').exists() and not list(Path(plan['logs']).glob('full-build-r8.*'))
result=dict(kit_pins_sha256=seal,pinned_files=len(read(R/'inputs/kit-pins.json')),active_product_manifest_sha256=sha(R/'inputs/r7-STAGED.json'),active_product_is_exact_r7_preimage=True,source_preimages={rel:active[rel] for rel in rows},staging_files=len(stage),staging_manifest_sha256=sha(plan['staging_manifest']),staging_delta=diff,r7_preservation_sha256=sha(plan['r7_preservation']),r7_attempt_files=len(read(plan['r7_preservation'])['attempt_files']),authentic_r7_verbose_sha256=sha(R/'evidence/r7-native/verbose.log.gz'),r8_attempt_exists=False,r8_markers_exist=False,parent_acceptance_authored=False,global_lock_acquired=False,processes_polled=False,product_build_started=False,device_actions=False)
write(R/'evidence/final-receipt.json',result);print(json.dumps(result,indent=2))
''');Path('2026-11-06-asus-r8-continuation-kit/evidence/final-receipt.json').write_text(r);print(r)
