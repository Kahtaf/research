from pathlib import Path
import shutil,subprocess,hashlib,json
R=Path(__file__).resolve().parents[1];A=R/'artifacts';D=A/'reproduction';D.mkdir();(D/'source').mkdir();(D/'scripts').mkdir();(D/'artifacts').mkdir()
for p in (R/'source').iterdir():
 if p.is_file():shutil.copyfile(p,D/'source'/p.name)
for name in ['assemble_core.py','assemble_final.py']:shutil.copyfile(R/'scripts'/name,D/'scripts'/name)
shutil.copytree(A/'core-inputs',D/'artifacts/core-inputs')
for name in ['core-input-metadata.json','base-header','base-kernel','base-wrapper','unarmed.manifest','restore-sepolicy','file_contexts.bin','rescue-proxy']:
 shutil.copyfile(A/name,D/'artifacts'/name)
flags=['-static','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-misleading-indentation','-Wl,--build-id=none']
commands=[['aarch64-linux-gnu-gcc',*flags,'-DP10_HANDOFF','source/rescue.c','-o','artifacts/os-rescue'],['python3','-B','scripts/assemble_core.py'],['aarch64-linux-gnu-gcc',*flags,'source/p10_restore.c','-o','artifacts/p10-restore'],['python3','-B','scripts/assemble_final.py']]
logs=[]
for cmd in commands:
 p=subprocess.run(cmd,cwd=D,capture_output=True,text=True,timeout=40);logs.append(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,p.stderr
names=['os-rescue','core.cpio.gz','p10-restore','candidate/UNARMED.img','candidate/UNARMED.p10.raw','candidate/helper.cpio']
sha=lambda b:hashlib.sha256(b).hexdigest()
for name in names:assert (A/name).read_bytes()==(D/'artifacts'/name).read_bytes(),name
assert (R/'source/core_binding.h').read_bytes()==(D/'source/core_binding.h').read_bytes()
(R/'evidence/reproduction.json').write_text(json.dumps(dict(passed=True,artifacts={n:sha((A/n).read_bytes()) for n in names},commands=logs),indent=2)+'\n')
print('FULL_CONTAINER_REPRODUCTION_PASS')
