from pathlib import Path
import hashlib,json,subprocess as s,zipfile,struct
O=Path('/srv/android/asus-final-bpf-loader-gap-20261107');E=O/'evidence';I=O/'inputs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
raw=Path('/srv/android/asus-radio-trigger-build-r4/system-partition.raw')
before=(raw.stat().st_ino,raw.stat().st_size,raw.stat().st_mtime_ns)
capex=I/'com.android.tethering.capex'
r=s.run(['/usr/sbin/debugfs','-R','dump /system/apex/com.android.tethering.capex '+str(capex),str(raw)],capture_output=True,text=True,timeout=15,check=True)
with zipfile.ZipFile(capex) as z:
 names=z.namelist();assert 'original_apex' in names
 apex=I/'com.android.tethering.apex';apex.write_bytes(z.read('original_apex'))
with zipfile.ZipFile(apex) as z:
 payload=I/'apex_payload.img';payload.write_bytes(z.read('apex_payload.img'))
out={'capex_sha256':sha(capex),'apex_sha256':sha(apex),'payload_sha256':sha(payload),'files':{}}
extract=I/'apex-extracted'
if not extract.exists():
 s.run(['/srv/android/lineage24/out/host/linux-x86/bin/fsck.erofs','--extract='+str(extract),'--no-preserve-owner',str(payload)],capture_output=True,text=True,timeout=20,check=True)
for rel,name in [('etc/bpf/mainline/offload.o','offload.o'),('bin/netbpfload','netbpfload')]:
 p=I/name
 p.write_bytes((extract/rel).read_bytes())
 out['files'][rel]={'sha256':sha(p),'bytes':p.stat().st_size}
out['offload_elf']=s.check_output(['readelf','-sW',str(I/'offload.o')],text=True)
out['offload_maps']=s.check_output(['readelf','-x','maps',str(I/'offload.o')],text=True)
for label,root in [('fixture','/srv/android/asus-firstboot-runtime/kernel-build-r7'),('physical','/srv/android/asus-bmc156-full-kernel-r1/out')]:
 root=Path(root)
 dis=s.check_output(['aarch64-linux-gnu-objdump','-dr','--disassemble=SyS_bpf',str(root/'kernel/bpf/syscall.o')],text=True)
 (E/(label+'-bpf-disassembly.txt')).write_text(dis)
 out[label+'_dispatch_comparisons']=[x for x in dis.splitlines() if any(v in x for v in ['cmp\t','cmp ','#0xe','#0xf'])]
 # Bind the selected Image's actual syscall instructions to the linked vmlinux,
 # rather than inferring binary behavior only from its current source directory.
 mp={x.split()[-1]:int(x.split()[0],16) for x in (root/'System.map').read_text().splitlines() if len(x.split())==3}
 vd=s.check_output(['aarch64-linux-gnu-objdump','-d','--disassemble=SyS_bpf',str(root/'vmlinux')],text=True)
 instructions=[]
 for line in vd.splitlines():
  f=line.strip().split()
  if len(f)>=2 and f[0].endswith(':') and len(f[1])==8:
   try:instructions.append((int(f[0][:-1],16),bytes.fromhex(f[1])[::-1]))
   except ValueError:pass
 image=(root/'arch/arm64/boot/Image').read_bytes()
 start=mp['_text'];matches=all(image[a-start:a-start+4]==b for a,b in instructions)
 out[label+'_binary_binding']={'image_sha256':hashlib.sha256(image).hexdigest(),'sys_bpf_address':hex(mp['SyS_bpf']),'text_address':hex(start),'instructions_compared':len(instructions),'all_syscall_instructions_match_Image':matches}
 assert instructions and matches
 (E/(label+'-linked-bpf-disassembly.txt')).write_text(vd)
assert before==(raw.stat().st_ino,raw.stat().st_size,raw.stat().st_mtime_ns)
out['raw_identity_unchanged']=True
(E/'bytes.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
