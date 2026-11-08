from pathlib import Path
import subprocess,json
r=Path('/srv/android/asus-camera-property-map-20261106');f=Path('/srv/android/asus-camera-arm32-route/cpp-out/sdk37')
commands=[]
def run(a):
 p=subprocess.run(list(map(str,a)),cwd=r,text=True,capture_output=True,timeout=45);commands.append({'argv':list(map(str,a)),'cwd':str(r),'rc':p.returncode,'stdout':p.stdout,'stderr':p.stderr});(r/'host-commands.json').write_text(json.dumps(commands,indent=2));print('RC',p.returncode,p.stdout,p.stderr[:5000]);return p
flags=['-std=c++20','-O1','-g','-fno-exceptions','-ffunction-sections','-fdata-sections','-fno-strict-aliasing','-DHOST_OWNERSHIP_TEST','-Wno-attributes','-I'+str(r/'tests/host_include'),'-I'+str(r/'src'),'-I'+str(f/'system/core/libutils/include'),'-I'+str(f/'system/core/libutils/binder/include')]
sources=[r/'src/legacy_property_map.cpp',r/'tests/behavior.cpp',r/'tests/allocator.cpp',*[r/'backend'/x for x in ['VectorImpl.cpp','String8.cpp','SharedBuffer.cpp']]]
run(['/usr/bin/g++','--version'])
for mode,extra in [('native',['-fsanitize=undefined','-fno-sanitize-recover=all'])]:
 exe=r/('host-test-'+mode)
 p=run(['/usr/bin/g++',*flags,*extra,*sources,'-Wl,--gc-sections','-Wl,--wrap=malloc,--wrap=realloc,--wrap=free','-o',exe])
 if p.returncode==0:run([exe])
print('No Android provider ELF executed; host execution uses pinned upstream backend with frozen headers and stderr/fatal logging transport.')
