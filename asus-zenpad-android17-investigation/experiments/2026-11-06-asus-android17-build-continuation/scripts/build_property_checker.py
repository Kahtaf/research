#!/usr/bin/env python3
"""Build the unmodified SDK37 checker outside the active Soong output tree."""
import pathlib, subprocess, shutil, hashlib, json, re
R=pathlib.Path('/srv/android/asus-build-continuation');A=pathlib.Path('/srv/android/lineage24');O=R/'property-tools-r1';O.mkdir();(O/'lib').mkdir();pins={}
def freeze(src,dst):
    before=hashlib.sha256(src.read_bytes()).hexdigest();shutil.copy2(src,dst)
    assert before==hashlib.sha256(src.read_bytes()).hexdigest()==hashlib.sha256(dst.read_bytes()).hexdigest()
    pins[str(src)]=before
freeze(A/'system/core/property_service/property_info_checker/property_info_checker.cpp',O/'checker.cpp')
includes=[]
for rel,name in [('system/libbase/include','base'),('system/logging/liblog/include','log'),('external/selinux/libsepol/include','sepol'),('system/core/property_service/libpropertyinfoparser/include','parser'),('system/core/property_service/libpropertyinfoserializer/include','serializer')]:
    dst=O/(name+'-include');shutil.copytree(A/rel,dst);includes+=['-I'+str(dst)]
static=[]
for rel,name in [('external/selinux/libsepol/libsepol','libsepol'),('system/core/property_service/libpropertyinfoparser/libpropertyinfoparser','libpropertyinfoparser'),('system/core/property_service/libpropertyinfoserializer/libpropertyinfoserializer','libpropertyinfoserializer')]:
    dst=O/'lib'/(name+'.a');freeze(A/('out/soong/.intermediates/'+rel+'/linux_glibc_x86_64_static/'+name+'.a'),dst);static.append(str(dst))
pending=['libbase.so','liblog.so','libc++.so'];done=set()
while pending:
    name=pending.pop()
    if name in done:continue
    done.add(name);dst=O/'lib'/name;freeze(A/'out/host/linux-x86/lib64'/name,dst)
    for dep in re.findall(r'Shared library: \[([^\]]+)\]',subprocess.check_output(['readelf','-d',str(dst)],text=True)):
        if (A/'out/host/linux-x86/lib64'/dep).is_file():pending.append(dep)
C=A/'prebuilts/clang/host/linux-x86/clang-r584948b'
cmd=[str(C/'bin/clang++'),'-fuse-ld=lld','-std=c++17','-stdlib=libc++','-O2',*includes,str(O/'checker.cpp'),'-Wl,--start-group',*static,'-Wl,--end-group','-L'+str(O/'lib'),'-lbase','-llog','-Wl,-rpath,$ORIGIN/lib','-Wl,-rpath-link,'+str(O/'lib'),'-o',str(O/'property_info_checker')]
p=subprocess.run(cmd,capture_output=True);(O/'build.json').write_text(json.dumps({'argv':cmd,'exit':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode(),'inputs':pins},indent=2)+'\n');print(p.returncode,p.stderr.decode());assert p.returncode==0
