from pathlib import Path
import os,resource,subprocess,json,hashlib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
a=Path('/srv/android/lineage24');s=Path('/srv/android/asus-minimal-audio-hal-20261106');out=s/'out';r=[]
def run(cmd):
 p=subprocess.run(list(map(str,cmd)),cwd=a,capture_output=True,text=True)
 r.append({'argv':list(map(str,cmd)),'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr});print(json.dumps(r[-1]))
for tool in ['assemble_vintf','host_init_verifier','secilc']:
 p=a/'out/host/linux-x86/bin'/tool
 if p.exists():run([p,'--help'])
run([a/'out/host/linux-x86/bin/assemble_vintf','-i',s/'staging/vintf/audio.xml','-o',out/'assembled-audio.xml'])
run([a/'out/host/linux-x86/bin/host_init_verifier',s/'staging/init/upstream-audio-service.rc.reference'])
# Public OEM binary metadata/disassembly only.
llvm=a/'prebuilts/clang/host/linux-x86/clang-r584948b/bin'
public=Path('/srv/android/asus-hardware-completeness-audit/public-selected/lib64_libaudiocustparam.so')
p=subprocess.run([llvm/'llvm-nm','-D','-C',public],capture_output=True,text=True)
print('DC_SYMBOLS\n'+'\n'.join(x for x in p.stdout.splitlines() if any(v in x for v in ['DC','Dc','Buffer','Gain','Record'])))
p=subprocess.run([llvm/'llvm-objdump','-d','--demangle',public],capture_output=True,text=True)
lines=p.stdout.splitlines();active=False;kept=[]
for line in lines:
 if '>:' in line:active=any(v in line for v in ['DCCalibration','DcCalibration','DC_Calibration','BufferDC','BufferDc'])
 if active:kept.append(line)
(out/'public-dc-disassembly.txt').write_text('\n'.join(kept)+'\n');print('DC_DISASSEMBLY_LINES',len(kept))
(out/'validation.json').write_text(json.dumps(r,indent=2)+'\n')
print('POLICY_INPUTS')
for p in (a/'out/soong/.intermediates/system/sepolicy').glob('*/*/*.cil'):
 if any(x in p.name for x in ['plat_sepolicy.cil','vendor_sepolicy.cil','mapping']):print(p,p.stat().st_size)
