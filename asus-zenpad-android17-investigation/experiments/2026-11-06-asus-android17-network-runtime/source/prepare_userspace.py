from pathlib import Path
import os
os.makedirs("/srv/android/asus-network-runtime/tmp",exist_ok=True)
os.environ["TMPDIR"]="/srv/android/asus-network-runtime/tmp"
import shutil,subprocess as s,json,hashlib
R=Path('/srv/android/asus-network-runtime');T=Path('/srv/android/lineage24');I=R/'inputs';H=I/'headers'
for rel in ['system/core/property_service','system/libbase','system/core/libcutils/include','external/libbpf']:
 d=I/'extra'/rel;shutil.copytree(T/rel,d,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git'))
for name,rel in {'libbpf.so':'external/libbpf/libbpf/android_arm64_armv8-a_shared_apex31/libbpf.so','libz.so':'external/zlib/libz/android_arm64_armv8-a_shared_apex31/libz.so'}.items():
 p=T/'out/soong/.intermediates'/rel
 if p.exists():shutil.copyfile(p,I/'root/system/lib64'/name)
F=T/'out/soong/.intermediates/packages/modules/Connectivity'
flags=list((F/'common/flags').rglob('com_android_tethering_readonly_flags.h'))
print('flags',flags)
if not flags:flags=list(F.rglob('com_android_tethering_readonly_flags.h'))
assert flags;shutil.copyfile(flags[0],I/'com_android_tethering_readonly_flags.h')
rc=T/'packages/modules/Connectivity/bpf/loader/netbpfload.rc'
d=I/'root/system/etc/init/netbpfload.rc';d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(rc,d)
# Host serializer uses actual Android serializer/parser and libbase source.
p=I/'extra/system/core/property_service';b=I/'extra/system/libbase'
cmd=['g++','-std=c++20','-include','algorithm','-include','cstring','-O2','-ffunction-sections','-fdata-sections','-Wl,--gc-sections',str(R/'source/make_properties.cpp'),*[str(p/'libpropertyinfoserializer'/f) for f in ['property_info_serializer.cpp','trie_builder.cpp','trie_serializer.cpp']],str(p/'libpropertyinfoparser/property_info_parser.cpp'),str(b/'strings.cpp'),'-I'+str(p/'libpropertyinfoserializer/include'),'-I'+str(p/'libpropertyinfoparser/include'),'-I'+str(b/'include'),'-o',str(R/'artifacts/make-properties')]
r=s.run(cmd,capture_output=True,text=True);(R/'evidence/property-compile.log').write_text(json.dumps(cmd)+'\n'+r.stdout+r.stderr);assert r.returncode==0,r.stderr
s.run([str(R/'artifacts/make-properties'),str(I/'root/property_info')],check=True)
