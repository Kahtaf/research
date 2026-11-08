#!/usr/bin/env python3
"""Independent local exact-ROM evidence, never invokes a device tool."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys,zlib,re
from elfaudit import ELF
S=Path(__file__).resolve().parents[2];W=S.parent
POLICY=W/'2026-11-06-asus-android17-os-rescue/artifacts/tools-final/policy_constraints'
def isolated(event,args):
 if event.startswith('socket.') or event in ('os.system','os.posix_spawn','os.exec'):raise RuntimeError('Offline audit: '+event)
 if event=='subprocess.Popen' and Path(args[0]).resolve()!=POLICY:raise RuntimeError('Only fixed read-only policy evaluator may execute')
sys.addaudithook(isolated)
def sha(b):return hashlib.sha256(b).hexdigest()
def cpio(b):
 p=0;out={}
 while True:
  h=b[p:p+110];assert h[:6]==b'070701';f=[int(h[6+i*8:14+i*8],16) for i in range(13)];sz,ns=f[6],f[11]
  assert 0<ns<4096 and sz<32*1024*1024
  name=b[p+110:p+110+ns];assert name[-1:]==b'\0';name=name[:-1].decode();p=(p+110+ns+3)&~3
  if name=='TRAILER!!!':break
  assert name not in out;out[name]=b[p:p+sz];p=(p+sz+3)&~3
 return out

def main():
 art=S/'artifacts/service';out=S/'evidence/service'
 backups=W/'2026-11-05-asus-boot-access-audit/artifacts/device-backup'
 b=(backups/'initial/boot.bin').read_bytes();assert b==(backups/'verify/boot.bin').read_bytes()
 ks,_,rs=struct.unpack_from('<III',b,8);ro=2048+((ks+2047)//2048)*2048;entries=cpio(zlib.decompress(b[ro+512:ro+rs],31))
 assert sha(b)=='7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316'
 assert entries['init']==(art/'boot-init').read_bytes()==(art/'recovery-init').read_bytes()
 assert entries['sbin/adbd']==(art/'boot-sbin_adbd').read_bytes()==(art/'recovery-sbin_adbd').read_bytes()
 assert entries['sepolicy']==(S/'artifacts/stock-boot.sepolicy').read_bytes()
 root=art/'root-rc';root.mkdir(exist_ok=True);rc={}
 for name,value in entries.items():
  if name.endswith('.rc'):
   assert '/' not in name;path=root/name;path.write_bytes(value)
   rc['/'+name]=dict(sha256=sha(value),bytes=len(value),artifact=str(path.relative_to(S)))
 system=json.loads((out/'oem-system-rc.json').read_text());rc.update(system['files'])
 hits={p:[dict(line=n+1,text=line) for n,line in enumerate((S/r['artifact']).read_text().splitlines()) if 'powerctl' in line] for p,r in rc.items()}
 hits={p:lines for p,lines in hits.items() if lines}
 assert set(hits)=={'/init.rc','/factory_init.rc','/meta_init.rc'},hits
 for found in hits.values():assert [r['text'] for r in found]==['on property:sys.powerctl=*','    powerctl ${sys.powerctl}']
 imports={p:[line for line in (S/r['artifact']).read_text().splitlines() if line.startswith('import ')] for p,r in rc.items()}
 k=b[2048:2048+ks];assert sha(k)=='b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880'
 raw=zlib.decompress(k[512:],31)
 versions=re.findall(rb'Linux version [^\x00]+\x00',raw);assert len(versions)==1
 banner=versions[0][:-1].decode();(out/'stock-kernel-banner.txt').write_text(banner)
 para=(backups/'initial/para.bin').read_bytes();assert para==(backups/'verify/para.bin').read_bytes()
 assert len(para)==524288 and sha(para)=='8c9e2c158ac95f152d08ea9de929ae36d054131ca4b10620890974ed831480ef'
 probes=[]
 for src,dst,cls,perm in [('adbd','powerctl_prop','property_service','set'),('shell','powerctl_prop','property_service','set'),('init','init','capability','sys_boot')]:
  source='u:r:'+src+':s0';target=('u:r:' if dst=='init' else 'u:object_r:')+dst+':s0'
  args=[str(POLICY),str(S/'artifacts/stock-boot.sepolicy'),source,target,cls,perm]
  p=subprocess.run(args,capture_output=True,text=True,timeout=10,check=True)
  assert p.stdout.startswith('allowed=1 reasons=0 ')
  probes.append(dict(argv=args,stdout=p.stdout))
 regions={'adbd':[(0x401948,0x401d40),(0x4022e8,0x402358),(0x440d30,0x440d34),(0x490130,0x490420),(0x49e218,0x49e230)],
          'init':[(0x4077f8,0x407b34),(0x42d448,0x42d9d0),(0x4a8c8c,0x4a8cbc),(0x410d54,0x411148),(0x4127f0,0x412920),(0x4087e0,0x40884c),(0x421f40,0x42207c)]}
 region_pins={}
 for name,ranges in regions.items():
  elf=ELF(art/('boot-init' if name=='init' else 'boot-sbin_adbd'));listing=[]
  for a,z in ranges:
   listing.append(f'REGION {a:x}-{z:x}\n'+elf.listing(a,z));region_pins[f'{name}:{a:x}-{z:x}']=sha(elf.bytes(a,z))
  (out/(name+'-dispatch-disassembly.txt')).write_text('\n'.join(listing))
 init=ELF(art/'boot-init');bcb_callers=[hex(i.address) for i in init.instructions() if i.mnemonic in ('b','bl') and i.op_str=='#0x421f40']
 assert bcb_callers==['0x408818']
 result=dict(status='EXACT_BINARY_STATIC_QUALIFIED_PENDING_PARENT_REVIEW',device_contacted=False,root_rc=rc,imports=imports,
   powerctl_triggers=hits,policy_checks=probes,policy_tool_sha256=sha(POLICY.read_bytes()),stock_kernel_banner=banner,
   normal_boot_init_sha256=sha(entries['init']),normal_boot_adbd_sha256=sha(entries['sbin/adbd']),
   sys_powerctl_label='u:object_r:powerctl_prop:s0',para_guard_sha256=sha(para),para_bytes=len(para),
   region_sha256=region_pins,bcb_writer_callers=bcb_callers,
   selected_entry=['adb','-t','FRESH_STOCK_USB_TRANSPORT_ID','reboot','recovery'],
   route=['adbd recovery argument bypasses sideload cache-writing branch','adbd property_set sys.powerctl reboot,recovery',
          'stock property context/constraints allow adbd request','nonpersistent sys.* property not persist.* path',
          'normal init.rc sys.powerctl trigger invokes powerctl builtin; separate factory/meta RC alternatives contain identical builtin only','do_powerctl selects ANDROID_RB_RESTART2 0xDEAD0003, target recovery, callback NULL',
          'android_reboot_with_callback syncs, reads mounts, requests sysrq remount-ro, dispatches syscall 142 RESTART2 recovery from init'],
   persistent_side_effects={'BCB_write_in_selected_route':False,'cache_command_write_in_selected_route':False,
       'standard_shutdown_sync_service_stop_remount_effects':True,'block_writes_by_controller':'only pinned p10 writer'},
   boundaries=['static exact-binary branch proof; no actual property request or PMIC/round-trip proof',
       'parent exclusive ownership excludes OTA/other writers; fresh hashes required for audited /init and /sbin/adbd',
       'fullpara preimage comparison avoids guessed BCB offset; no metadata cleared',
       'no first new-kernel trial authorized'])
 (out/'firmware-audit.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'rc_files':len(rc),'powerctl_triggers':list(hits),'kernel_banner':banner.strip()}))
if __name__=='__main__':main()
