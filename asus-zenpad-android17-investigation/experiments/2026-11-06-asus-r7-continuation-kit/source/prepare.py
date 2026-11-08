"""Prepare only this spike's copy of r3; never edits the ancestor."""
from pathlib import Path
import hashlib,json,shutil,difflib
R=Path(__file__).resolve().parents[1];B=R.parent/'2026-11-06-asus-sensors-bpf-build-kit-r3';F=R.parent/'2026-11-06-asus-sensor-board-path-fix'
def read(p):return json.loads(p.read_text())
def put(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for folder in ['inputs','tests']:
 shutil.copytree(B/folder,R/folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
for name in ['integrate.py','check_launch.py','build.sh','r3_inputs.py','verify_full_images.py','validate_completed_product.py','verify_product_r3.py','verify_google_payload.py','verify_google_transformed.py','verify_input_payload.py','verify_root_payload.py','seal.py']:
 shutil.copy2(B/'scripts'/name,R/'scripts'/name)
shutil.copy2(R.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py',R/'scripts/remote.py')
(R/'inputs/kit-pins.json').unlink()
shutil.copy2(B/'inputs/kit-pins.json',R/'inputs/r3-kit-pins.json')
shutil.copy2(B/'inputs/STAGED.json',R/'inputs/r3-STAGED.json')
shutil.copy2(B/'inputs/sensor-selection.json',R/'inputs/r3-sensor-selection.json')
shutil.copy2(F/'source/BoardConfig.mk',R/'inputs/sensor-BoardConfig.mk')
shutil.copy2(F/'source/sensor-board-path.patch',R/'source/sensor-board-path.patch')
obs=read(R/'evidence/initial-remote.json')
for name,value in obs['receipts'].items():put(R/'inputs'/('r6-'+name),value)
put(R/'inputs/prior-preservation-pins.json',dict(attempt_files=obs['attempt_files'],logs=obs['logs']))
shutil.copy2(R.parent/'2026-11-06-asus-r6-product-build/evidence/terminal-log.json',R/'inputs/r6-terminal-log.json')
put(R/'inputs/sensor-delta.json',dict(relative='sensors/BoardConfig.mk',before='0e012287927a5b8ac3733f7fcc28d5cdc0eb1d8f06e82e0ff6ad211fe2f72f90',after='9207c304761cf86afb423641534ed383e7f8dae613e64061e972d2f65832aa4d',old_line='P00A_ACCEL_BOARD_PATH := $(call my-dir)\n',new_line='P00A_ACCEL_BOARD_PATH := device/asus/p00a/sensors\n'))
s=read(R/'inputs/STAGED.json');s['product_after']['sensors/BoardConfig.mk']={'sha256':sha(R/'inputs/sensor-BoardConfig.mk')};put(R/'inputs/STAGED.json',s)
s=read(R/'inputs/sensor-selection.json');s['files']['BoardConfig.mk']={'sha256':sha(R/'inputs/sensor-BoardConfig.mk')};s['board_path_adjustment']='One exact reviewed assignment replaces unavailable my-dir; policy and manifest unchanged';put(R/'inputs/sensor-selection.json',s)
p=read(B/'inputs/plan.json');old='/srv/android/asus-reviewed-build-kit/r3';new='/srv/android/asus-reviewed-build-kit/r7';stage='/srv/android/asus-product-integration-staging/r7'
# Rebind own kit inputs only; every ancestor and original external pin stays intact.
for k,v in list(p.items()):
 if isinstance(v,str) and v.startswith(old+'/inputs/'):p[k]=v.replace(old,new,1)
p.update(run_root=new,revision='r7',staging=stage,prior_kit=old,prior_kit_seal=obs['r3_seal'],prior_revision='r6',prior_attempt=old+'/attempt',sensor_delta=new+'/inputs/sensor-delta.json',sensor_postimage=new+'/inputs/sensor-BoardConfig.mk',prior_pins=new+'/inputs/prior-preservation-pins.json',prior_integration=new+'/inputs/r6-integration.json',prior_staged_receipt=new+'/inputs/r3-STAGED.json',prior_sensor_receipt=new+'/inputs/r3-sensor-selection.json',staging_manifest=new+'/inputs/r7-staging-manifest.json',original_pids=p['original_pids']+[1546715,1548484],parent_contract='PLAN_ONLY default; exact terminal r6 parent acceptance required before one-shot r7 continuation; only one sensor BoardConfig source write; no physical GO')
p['external_pins'][old+'/inputs/kit-pins.json']=obs['r3_seal']
for rel,digest in read(B/'inputs/kit-pins.json').items():p['external_pins'][old+'/'+rel]=digest
put(R/'inputs/plan.json',p)
