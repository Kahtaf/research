#!/usr/bin/env python3
import pathlib,subprocess,shutil,hashlib,json,re,os
R=pathlib.Path('/srv/android/asus-build-continuation');A=pathlib.Path('/srv/android/lineage24');O=R/'policy-tools-r1';O.mkdir();(O/'lib').mkdir();pins={}
def freeze(src,dst):
 before=hashlib.sha256(src.read_bytes()).hexdigest();shutil.copy2(src,dst);assert before==hashlib.sha256(src.read_bytes()).hexdigest()==hashlib.sha256(dst.read_bytes()).hexdigest();pins[str(src)]=before
for name in ['libsepol','libselinux']:shutil.copytree(A/('external/selinux/'+name+'/include'),O/(name+'-include'))
freeze(A/'system/sepolicy/tools/checkfc.c',O/'checkfc.c')
freeze(A/'out/soong/.intermediates/external/selinux/libsepol/libsepol/linux_glibc_x86_64_static/libsepol.a',O/'lib/libsepol.a')
pending=['libselinux.so'];done=set()
while pending:
 name=pending.pop()
 if name in done:continue
 done.add(name);src=A/'out/host/linux-x86/lib64'/name;dst=O/'lib'/name;freeze(src,dst)
 text=subprocess.check_output(['readelf','-d',str(dst)],text=True)
 for dep in re.findall(r'Shared library: \[([^\]]+)\]',text):
  if (A/'out/host/linux-x86/lib64'/dep).is_file():pending.append(dep)
cmd=[str(A/'prebuilts/clang/host/linux-x86/clang-r596125/bin/clang'),'-fuse-ld=lld','-O2','-I'+str(O/'libsepol-include'),'-I'+str(O/'libselinux-include'),str(O/'checkfc.c'),str(O/'lib/libsepol.a'),'-L'+str(O/'lib'),'-lselinux','-Wl,-rpath,$ORIGIN/lib','-Wl,-rpath-link,'+str(O/'lib'),'-o',str(O/'checkfc')]
p=subprocess.run(cmd,capture_output=True);(O/'build.json').write_text(json.dumps({'argv':cmd,'exit':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode(),'inputs':pins},indent=2)+'\n');print(p.returncode,p.stderr.decode());assert p.returncode==0
p=subprocess.run([str(O/'checkfc'),str(R/'policy-merge-r3/policy.bin'),str(R/'product-device/radio/sepolicy/file_contexts')],capture_output=True);(O/'checkfc-result.json').write_text(json.dumps({'exit':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode()},indent=2)+'\n');print('checkfc',p.returncode,p.stderr.decode());assert p.returncode==0
