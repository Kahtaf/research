from pathlib import Path
import subprocess as s,hashlib,struct,json
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');sha=lambda b:hashlib.sha256(b).hexdigest()
def sections(b):
 off=struct.unpack_from('<Q',b,40)[0];sz,num,idx=struct.unpack_from('<HHH',b,58);ss=[struct.unpack_from('<IIQQQQIIQQ',b,off+i*sz) for i in range(num)];strings=b[ss[idx][4]:ss[idx][4]+ss[idx][5]]
 return {strings[x[0]:].split(b'\0',1)[0].decode():b[x[4]:x[4]+x[5]] for x in ss}
a=sections((R/'inputs/installed-filter.o').read_bytes());b=sections(Path('/srv/android/asus-linux49-power-supply-filter-20261106/artifacts/postimage.o').read_bytes());d={n:dict(installed_sha=sha(v),qualified_sha=sha(b[n]) if n in b else None,equal=v==b.get(n),bytes=len(v)) for n,v in a.items() if n in ['skfilter/power_supply','critical','license','progs','bpfloader_min_ver','bpfloader_max_ver']};(R/'inputs/installed-insns').write_bytes(a['skfilter/power_supply']);(R/'evidence/elf-binding.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
for base in ['/srv/android/lineage24/system/bpf','/srv/android/lineage24/packages/modules/Connectivity','/srv/android/lineage24/system/libbpf']:
 p=Path(base)
 if p.exists():
  x=s.run(['grep','-R','-n','-E','bpf_prog_load|prog_name|union bpf_attr|BPF_PROG_LOAD',base],text=True,capture_output=True);print(x.stdout[:16000])
P=Path('/srv/android/asus-bmc156-full-kernel-r1/kernel')
for n in ['include/uapi/linux/bpf.h','kernel/bpf/syscall.c']:
 p=P/n;t=p.read_text();print('PHYSICAL',n,sha(p.read_bytes()))
 for key in (['union bpf_attr'] if n.endswith('.h') else ['#define BPF_PROG_LOAD_LAST_FIELD','SYSCALL_DEFINE3(bpf,']):
  i=t.find(key);print(t[i:i+1800] if i>=0 else 'KEY ABSENT '+key)
