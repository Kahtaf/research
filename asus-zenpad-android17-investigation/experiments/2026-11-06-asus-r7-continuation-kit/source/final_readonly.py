from pathlib import Path
import importlib.util,json
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('remote',R/'scripts/remote.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
code='''
from pathlib import Path
import hashlib,json,os,resource,sys
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1073741824,1073741824))
K=Path('/srv/android/asus-reviewed-build-kit/r7');sys.path.insert(0,str(K/'scripts'))
import integrate as i
p=i.read(K/'inputs/plan.json');i.verify_pins(K);i.revision_unused(p)
description=i.terminal(p,describe=True)
active=Path(p['device'])/'sensors/BoardConfig.mk'
source=Path(p['aosp'])/'build/make/core/soong_config.mk'
previous=Path(p['logs'])/'full-build-r6.vars'
oldvars=previous.read_text().splitlines()
lines=[]
for relative in ('system/sepolicy/build/soong/selinux.go','build/make/core/config.mk','build/make/core/board_config.mk'):
 config=Path(p['aosp'])/relative
 if config.is_file():
  lines.extend(dict(file=relative,line=n+1,text=line) for n,line in enumerate(config.read_text().splitlines()) if any(x in line for x in ('BOARD_REQD_MASK_POLICY','BOARD_PLAT_PUBLIC_SEPOLICY_DIR','BOARD_PLAT_PRIVATE_SEPOLICY_DIR','BOARD_SYSTEM_EXT_PREBUILT_DIR','BOARD_PRODUCT_PREBUILT_DIR')))
print(json.dumps(dict(kit_seal=i.sha(K/'inputs/kit-pins.json'),sensor_preimage=dict(path=str(active),sha256=i.sha(active),expected_preimage_matches=i.sha(active)=='0e012287927a5b8ac3733f7fcc28d5cdc0eb1d8f06e82e0ff6ad211fe2f72f90'),terminal_description=description,native_jobs=i.native_processes(p),lifecycle_lock_acquired_by_this_observation=False,actual_product_dumpvars_run=False,original_soong_config_sha256=i.sha(source),r6_vars_nonassignment_lines=[line for line in oldvars if '=' not in line],policy_make_lines=lines,attempt_exists=(K/'attempt').exists(),r7_markers=[str(p) for p in Path(p['logs']).glob('full-build-r7.*')],prior_attempt_preserved=True)))
'''
r=json.loads(m.run(code));(R/'evidence/final-readonly-state.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='terminal_description'},indent=2));print('description keys',r['terminal_description'].keys())
