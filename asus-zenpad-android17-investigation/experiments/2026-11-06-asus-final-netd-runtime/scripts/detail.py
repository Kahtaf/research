from pathlib import Path
import subprocess as s
N=Path('/srv/android/asus-network-runtime');F=Path('/srv/android/asus-final-bpf-runtime-20261106');O=Path('/srv/android/asus-final-netd-runtime-20261106');raw=Path('/srv/android/asus-root-enabled-incremental-r1/host-r2/validation/system-partition.raw')
for path in ['/system/etc/init/netbpfload.rc','/system/etc/source_apex_version','/system/etc/init/bpfloader.rc']:
 print('STAT',path,s.run(['/usr/sbin/debugfs','-R','stat '+path,str(raw)],capture_output=True,text=True).stdout)
 if path.endswith('.rc'):
  dest=O/'props'/path.lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True);r=s.run(['/usr/sbin/debugfs','-R','dump '+path+' '+str(dest),str(raw)],capture_output=True,text=True);print(r.stderr);print(dest.read_text() if dest.exists() else 'absent')
print('COMPILE', (N/'evidence/seed_properties-compile-r11.log').read_text()[:14000])
t=(N/'inputs/Connectivity/bpf/loader/NetBpfLoad.cpp').read_text();print('LOADER_END','\n'.join(t.splitlines()[1840:]))
print('PROPFINAL','\n'.join(x for p in (O/'props').rglob('*') if p.is_file() and p.suffix=='.prop' for x in p.read_text().splitlines() if x.startswith(('ro.product.board','ro.board.','ro.bpf.','ro.build.characteristics'))))
print('FROZEN_COMPILER',[str(p) for p in (N/'handoff-r1').iterdir()]);print('PROBE',s.run(['readelf','-d',str(N/'artifacts/loader_probe')],capture_output=True,text=True).stdout)
