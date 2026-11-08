#!/usr/bin/env python3
"""Replay actual SDK37 policy generation into a private snapshot with radio added."""
import pathlib,subprocess,shlex,hashlib,json,sys
R=pathlib.Path('/srv/android/asus-build-continuation');A=pathlib.Path('/srv/android/lineage24');rev=sys.argv[1];O=R/('policy-'+rev);O.mkdir();S=O/'source';S.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
needle='command = echo > out/soong/.intermediates/system/sepolicy/'+sys.argv[2]+'/android_common/newline'
command=None
with (A/'out/soong/build.lineage_p00a.9.ninja').open() as f:
 for line in f:
  if needle in line:
   command=line.strip().removeprefix('command = ')
   while command.endswith('$'):command=command[:-1]+next(f).lstrip().rstrip('\n')
   break
assert command,'Generation recipe not found'
(O/'original-command.txt').write_text(command+'\n')
tokens=shlex.split(command);begin=tokens.index('&&')+1;end=tokens.index('>',begin);argv=tokens[begin:end]
assert argv[0]=='prebuilts/build-tools/linux-x86/bin/m4'
newline=O/'newline';newline.write_text('\n');pins={};newargv=[str(A/argv[0])]
for t in argv[1:]:
 if t.endswith('/newline'):newargv.append(str(newline));continue
 if (A/t).is_file():
  p=S/t;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((A/t).read_bytes());pins[t]=sha(p);assert sha(A/t)==pins[t];newargv.append(str(p))
 else:newargv.append(t)
radio=O/'p00a_radio.te';radio.write_bytes((R/'product-device/radio/sepolicy/p00a_radio.te').read_bytes())
index=next(i for i,v in enumerate(newargv) if v.endswith('/roles_decl'))
newargv[index:index]=[str(radio),str(newline)]
conf=O/'policy.conf'
with conf.open('wb') as f:result=subprocess.run(newargv,stdout=f,stderr=subprocess.PIPE,cwd=S)
(O/'m4.stderr').write_bytes(result.stderr);assert result.returncode==0,result.stderr
check=[str(A/'out/host/linux-x86/bin/checkpolicy'),'-M','-c','30','-o',str(O/'policy.bin'),str(conf)]
if sys.argv[2]=='vendor_sepolicy.conf':check.insert(1,'-C');check[check.index(str(O/'policy.bin'))]=str(O/'policy.cil')
p=subprocess.run(check,capture_output=True);(O/'checkpolicy.log').write_bytes(p.stdout+p.stderr)
(O/'evidence.json').write_text(json.dumps({'generation_exit':result.returncode,'checkpolicy_exit':p.returncode,'m4_command':newargv,'checkpolicy_command':check,'inputs':pins,'radio_sha256':sha(radio),'active_sources_unchanged':all(sha(A/t)==h for t,h in pins.items())},indent=2)+'\n')
print('Policy',rev,'checkpolicy exit',p.returncode,(p.stdout+p.stderr).decode()[-6000:]);sys.exit(p.returncode)
