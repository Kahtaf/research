from pathlib import Path
import json,hashlib,subprocess as s,struct
O=Path('/srv/android/asus-final-bpf-loader-gap-20261107');E=O/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=Path('/srv/android/asus-genuine-service-runtime/inputs/kernel-r7/config')
new=Path('/srv/android/asus-network-runtime/handoff-r1/network.config')
def config(p):
 out={}
 for line in p.read_text().splitlines():
  if line.startswith('CONFIG_'):k,v=line.split('=',1);out[k]=v
  elif line.startswith('# CONFIG_') and line.endswith(' is not set'):out[line[2:-11]]='n'
 return out
a,b=config(old),config(new)
out={'selected_config_sha256':sha(old),'qualified_config_sha256':sha(new),'qualified_image_sha256':sha(Path('/srv/android/asus-network-runtime/handoff-r1/Image')),'config_delta':{k:{'selected':a.get(k),'qualified':b.get(k)} for k in sorted(a.keys()|b.keys()) if a.get(k)!=b.get(k)}}
for name,root in [('fixture','/srv/android/asus-firstboot-runtime/kernel-cpuset-r1'),('physical','/srv/android/asus-bmc156-full-kernel-r1/kernel')]:
 p=Path(root)/'kernel/bpf/syscall.c';lines=p.read_text().splitlines();idx=next(i for i,x in enumerate(lines) if x.startswith('SYSCALL_DEFINE3(bpf,'))
 out[name+'_syscall_source']={'sha256':sha(p),'first_line':idx+1,'text':'\n'.join(lines[idx:])}
bpf=Path('/srv/android/asus-network-runtime/inputs/Connectivity/bpf')
out['metadata_helpers']=[]
for p in bpf.rglob('*.h'):
 text=p.read_text()
 if 'bpfGetFdMapType(' in text or 'bpfGetFdMapInfo(' in text:
  lines=text.splitlines();indices=[i for i,x in enumerate(lines) if any(k in x for k in ['bpfGetFdMapType(', 'bpfGetFdMapInfo(', 'bpfGetFdKeySize(', 'BPF_OBJ_GET_INFO_BY_FD'])]
  out['metadata_helpers'].append({'path':str(p),'sha256':sha(p),'excerpts':[{'line':i+1,'text':'\n'.join(lines[max(0,i-8):i+24])} for i in indices]})
blob=(O/'inputs/offload.o').read_bytes();off=struct.unpack_from('<Q',blob,40)[0];ents,num,idx=struct.unpack_from('<HHH',blob,58);sects=[struct.unpack_from('<IIQQQQIIQQ',blob,off+i*ents) for i in range(num)];strings=blob[sects[idx][4]:sects[idx][4]+sects[idx][5]]
sections={strings[x[0]:].split(b'\0',1)[0].decode():x for x in sects}
maps=sections['.android_maps'];data=blob[maps[4]:maps[4]+maps[5]]
out['first_legacy_map_definition']={'name':'tether_error_map_def','section':'.android_maps','offset':0,'first_12_u32':list(struct.unpack_from('<12I',data)),'first_64_bytes_hex':data[:64].hex()}
# Fetch only public compact evidence, never previous DATA, COW or entropy inputs.
out['binary_dispatch_excerpts']={}
for label in ['fixture','physical']:
 lines=(E/(label+'-linked-bpf-disassembly.txt')).read_text().splitlines();needle='#0xe' if label=='fixture' else '#0xf';i=next(i for i,x in enumerate(lines) if 'cmp' in x and needle in x)
 out['binary_dispatch_excerpts'][label]='\n'.join(lines[max(0,i-4):i+17])
(E/'final-facts.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
