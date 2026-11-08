#!/usr/bin/env python3
"""Strictly check all adapted ELF files against their real direct core providers."""
import json
from pathlib import Path
import subprocess

T=Path('/srv/android/lineage24')
I=T/'out/soong/.intermediates'
source=T/'vendor/asus/p00a'
manifest=json.loads((source/'adaptation-manifest.json').read_text())
projects={
'libc':'bionic/libc/libc','libm':'bionic/libm/libm','libdl':'bionic/libdl/libdl',
'libstdc++':'bionic/libc/libstdc++','libc++':'prebuilts/clang/host/linux-x86/libc++',
'libGLESv1_CM':'frameworks/native/opengl/libs/libGLESv1_CM',
'libbinder':'frameworks/native/libs/binder/libbinder','libui':'frameworks/native/libs/ui/libui',
'libion':'system/memory/libion/libion','liblog':'system/logging/liblog/liblog',
'libhardware':'hardware/libhardware/libhardware','libz':'external/zlib/libz',
'libp00a_legacy_memory':'device/asus/p00a/lights/libp00a_legacy_memory',
'libutilscallstack':'system/core/libutils/libutilscallstack'}
for name in ['libcutils','libnetutils','libsync','libutils']:
 projects[name]=f'system/core/{name}/{name}'
private={Path(row['path']).name for row in manifest['files']}
rows=[]
for row in manifest['files']:
    rel=Path(row['path'])
    arch='android_arm64_armv8-a_shared' if 'lib64' in rel.parts else 'android_arm_armv8-a_cortex-a53_shared'
    command=[str(T/'out/host/linux-x86/bin/check_elf_file'),'--soname',rel.name,
             '--llvm-readobj='+str(T/'prebuilts/clang/host/linux-x86/clang-r584948b/bin/llvm-readobj')]
    missing=[]
    for needed in row['needed']:
        name=needed.removesuffix('.so')
        if needed in private:
            mod='p00a_legacy_'+name.replace('.','_').replace('-','_').replace('+','x')
            project='vendor/asus/p00a/'+mod
        else:
            project=projects[name]
        dep=I/project/arch/needed
        if not dep.is_file(): missing.append(str(dep))
        command.extend(['--shared-lib',str(dep)])
    command.append(str(source/rel))
    if missing:
        rows.append(dict(path=str(rel),exit_status=2,output='Not yet built: '+', '.join(missing),command=command))
        continue
    result=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    rows.append(dict(path=str(rel),exit_status=result.returncode,output=result.stdout,command=command))
print(json.dumps(dict(checks=rows,passed=sum(r['exit_status']==0 for r in rows),total=len(rows)),indent=2))
raise SystemExit(0 if all(r['exit_status']==0 for r in rows) else 1)
