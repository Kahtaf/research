from pathlib import Path
import subprocess as s,json,hashlib
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');R.mkdir(exist_ok=False)
for n in ['scripts','evidence','source','inputs','tmp']:(R/n).mkdir()
P=Path('/srv/android/asus-android-runtime-network-parity-20261107')
for f in ['kernel/bpf/syscall.c','include/uapi/linux/bpf.h']:
 p=P/'kernel'/f
 text=p.read_text();print('SOURCE',str(p),hashlib.sha256(p.read_bytes()).hexdigest())
 if f.endswith('syscall.c'):
  for key in ['static int bpf_prog_load','SYSCALL_DEFINE3(bpf,']:
   pos=text.index(key);print(text[pos:pos+4300])
 else:
  pos=text.index('union bpf_attr');print(text[pos:pos+3200])
raw=Path('/srv/android/asus-radio-trigger-build-r4/system-partition.raw')
p=s.run(['debugfs','-R','cat /system/vendor/etc/bpf/filterPowerSupplyEvents.o',str(raw)],capture_output=True,check=True)
assert p.stdout[:4]==b'\x7fELF';(R/'inputs/installed-filter.o').write_bytes(p.stdout)
print('INSTALLED',len(p.stdout),hashlib.sha256(p.stdout).hexdigest())
print('OWNED PRIOR FILTER FILES',s.run(['find','/srv/android/asus-linux49-power-supply-filter-20261106','-maxdepth','2','-type','f'],capture_output=True,text=True,check=True).stdout)
print('SCOPED LOCAL SOURCE REFERENCES')
