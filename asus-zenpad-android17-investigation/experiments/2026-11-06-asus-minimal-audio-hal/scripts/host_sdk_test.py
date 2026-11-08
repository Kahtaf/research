from pathlib import Path
import subprocess,os,resource,json
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
a=Path('/srv/android/lineage24');s=Path('/srv/android/asus-minimal-audio-hal-20261106');out=s/'out'
cmd=[str(a/'prebuilts/clang/host/linux-x86/clang-r584948b/bin/clang'),'-std=gnu11','-Wall','-Wextra','-Werror','-pthread','-I'+str(s/'src'),'-I'+str(s/'source/sdk37/external/tinyalsa_new/include')]
for d in ['hardware/libhardware/include_all','system/media/audio/include','system/core/libcutils/include','system/core/libsystem/include','system/logging/liblog/include','system/core/libutils/include','system/libbase/include']:
 cmd += ['-I'+str(a/d)]
cmd += [str(s/'tests/hal_contract_test.c'),str(s/'src/routes.c'),'-o',str(out/'hal_contract_test')]
r=subprocess.run(cmd,capture_output=True,text=True);receipt=[{'argv':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}];print(r.stderr)
if not r.returncode:
 r=subprocess.run([out/'hal_contract_test'],capture_output=True,text=True);receipt.append({'argv':[str(out/'hal_contract_test')],'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr});print(r.stdout,r.stderr)
(out/'hal-test.json').write_text(json.dumps(receipt,indent=2)+'\n');raise SystemExit(r.returncode)
