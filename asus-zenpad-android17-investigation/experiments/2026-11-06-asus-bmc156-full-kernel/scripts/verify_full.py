from pathlib import Path
import os,json,hashlib,gzip,zlib,struct,subprocess,datetime
R=Path('/srv/android/asus-bmc156-full-kernel-r1');K=R/'kernel';O=R/'out';E=R/'evidence';B=Path('/srv/android/asus-build-continuation')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(10)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def cfg(p):
 d={}
 for l in p.read_text().splitlines():
  if l.startswith('CONFIG_'):k,v=l.split('=',1);d[k]=v
  elif l.startswith('# CONFIG_') and l.endswith(' is not set'):d[l.split()[1]]='n'
 return d
def extract(p):
 data=p.read_bytes();z=zlib.decompressobj(31);raw=z.decompress(data)+z.flush();assert z.eof
 dt=z.unused_data;assert dt[:4]==bytes.fromhex('d00dfeed') and struct.unpack_from('>I',dt,4)[0]==len(dt)
 return raw,dt
checks=[]
def check(name,test):
 assert test,name
 checks.append(name)
status=json.loads((E/'build-status.json').read_text());check('full_compile_exit_zero',status['status']=='complete' and status['exit']==0 and all(x['exit']==0 for x in status['commands']))
raw,dt=extract(O/'arch/arm64/boot/Image.gz-dtb');oldraw,olddt=extract(B/'build/arch/arm64/boot/Image.gz-dtb')
check('Image_equals_decompressed_payload',raw==(O/'arch/arm64/boot/Image').read_bytes())
check('DT_byte_identical_to_physical_r5',dt==olddt)
check('DT_equals_build_output',dt==(O/'arch/arm64/boot/dts/mediatek/asus-p00a.dtb').read_bytes())
check('charging_opt_in_absent',b'asus,allow-battery-charging' not in dt)
check('ARM64_Image_magic',raw[56:60]==b'ARM\x64')
header=dict(text_offset=struct.unpack_from('<Q',raw,8)[0],image_size=struct.unpack_from('<Q',raw,16)[0],flags=struct.unpack_from('<Q',raw,24)[0],file_bytes=len(raw))
oldheader=dict(text_offset=struct.unpack_from('<Q',oldraw,8)[0],image_size=struct.unpack_from('<Q',oldraw,16)[0],flags=struct.unpack_from('<Q',oldraw,24)[0],file_bytes=len(oldraw))
check('header_text_offset_flags_preserved',header['text_offset']==oldheader['text_offset'] and header['flags']==oldheader['flags'])
check('header_reserved_fields_preserved',raw[32:56]==oldraw[32:56] and raw[60:64]==oldraw[60:64])
check('Image_fits_allocated_header_size',len(raw)<=header['image_size'])
cfgbytes=subprocess.check_output([str(K/'scripts/extract-ikconfig'),str(O/'arch/arm64/boot/Image')]);check('embedded_config_matches_resolved',cfgbytes==(O/'.config').read_bytes())
new=cfg(O/'.config');old=cfg(E/'physical-r5.config');delta={k:{'before':old.get(k,'n'),'after':new.get(k,'n')} for k in old.keys()|new.keys() if old.get(k,'n')!=new.get(k,'n')}
check('only_four_config_changes',delta==json.loads((E/'config-delta.json').read_text()) and len(delta)==4)
check('exact_expected_resolved_config',sha(O/'.config')=='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2')
runtime=json.loads((E/'r5-runtime-source-preservation.json').read_text())['files'];check('282_runtime_sources',len(runtime)==282 and all(sha(K/p)==v['expected'] for p,v in runtime.items()))
r5cfg=json.loads((E/'r5-config-receipt.json').read_text());check('58_runtime_options',len(r5cfg['runtime_prerequisites'])==58 and all(new.get(p,'n')==v['expected'] for p,v in r5cfg['runtime_prerequisites'].items()))
check('16_network_options',len(r5cfg['network_core'])==16 and all(new.get(p,'n')==v['expected'] for p,v in r5cfg['network_core'].items()))
first=json.loads((E/'firstboot-combined-parity.json').read_text());check('290_firstboot_source_files',len(first['sources'])==290 and all(sha(K/v['path'])==v['combined_source_sha256']==v['r7_source_sha256'] for v in first['sources']))
check('134_firstboot_options',len(first['selected_config'])==134 and all(new.get(v['option'],'n')==v['combined']==v['r7'] for v in first['selected_config']))
base=json.loads(gzip.decompress((E/'r5-source-manifest.json.gz').read_bytes()));post=json.loads(gzip.decompress((E/'post-source-manifest.json.gz').read_bytes()))
actual={str(p.relative_to(K)):sha(p) for p in K.rglob('*') if p.is_file() and not p.is_symlink()}
check('complete_owned_source_manifest_unchanged',actual==post)
check('all_original_r5_source_files_unchanged',all(sha(B/'kernel'/p)==v for p,v in base.items()))
check('original_r5_config_unchanged',sha(B/'build/.config')=='067090e03ad762344308cebd0a71274d9943e299ded6707051ebfdc075dd045f')
check('original_r5_Image_unchanged',sha(B/'build/arch/arm64/boot/Image.gz-dtb')=='46895deb12ec94160ea5af0e85afa89c6de84971db126bb94c60cec1ec3ec401')
check('frozen_r2_kit_seal_preserved',sha(Path('/srv/android/asus-reviewed-build-kit/r2/inputs/kit-pins.json'))=='841581a33251c975d19329d03318fb1e43e94dbdfebddcac4cd7d1def742ad70')
check('kernel_release_preserved',(O/'include/config/kernel.release').read_bytes()==(B/'integration-r5/kernel.release').read_bytes())
# Parse the actual appended FDT including its reserve map and reserved-memory nodes.
h=struct.unpack_from('>10I',dt);pos=h[2];strings=dt[h[3]:h[3]+h[8]];stack=[];nodes={}
while True:
 t=struct.unpack_from('>I',dt,pos)[0];pos+=4
 if t==1:
  end=dt.index(0,pos);stack.append(dt[pos:end].decode());pos=(end+4)&~3;nodes['/'.join(stack)]={}
 elif t==2:stack.pop()
 elif t==3:
  n,off=struct.unpack_from('>II',dt,pos);pos+=8;name=strings[off:strings.index(0,off)].decode();nodes['/'.join(stack)][name]=dt[pos:pos+n];pos=(pos+n+3)&~3
 elif t==4:continue
 elif t==9:break
 else:raise ValueError(t)
def cells(b):return list(struct.unpack('>'+str(len(b)//4)+'I',b))
reservations=[];dynamic=[];pos=h[4]
while True:
 addr,size=struct.unpack_from('>QQ',dt,pos);pos+=16
 if not (addr or size):break
 reservations.append(dict(source='FDT reserve map',start=addr,end=addr+size))
for name,props in nodes.items():
 if name.startswith('/reserved-memory/'):
  if 'reg' in props:
   c=cells(props['reg']);assert len(c)==4
   addr=(c[0]<<32)|c[1];size=(c[2]<<32)|c[3];reservations.append(dict(source=name,start=addr,end=addr+size))
  elif 'size' in props:dynamic.append(dict(source=name,size=cells(props['size']),alignment=cells(props.get('alignment',b''))))
payloads=[dict(source='ARM64 allocated Image',start=0x40000000+header['text_offset'],end=0x40000000+header['text_offset']+header['image_size']),dict(source='unchanged maximum parent ramdisk placement',start=0x44000000,end=0x44400000),dict(source='unchanged parent DTB placement',start=0x4e000000,end=0x4e100000)]
regions=payloads+reservations
check('no_static_payload_reservation_overlap',all(a['end']<=b['start'] or b['end']<=a['start'] for i,a in enumerate(regions) for b in regions[i+1:]))
check('DT_fits_parent_allocation',len(dt)<=0x100000)
banks=[v for v in nodes.values() if v.get('device_type')==b'memory\x00'];assert len(banks)==1
ram=cells(banks[0]['reg']);assert len(ram)==4
ram_start=(ram[0]<<32)|ram[1];ram_end=ram_start+((ram[2]<<32)|ram[3])
check('static_payloads_within_RAM_bank',all(ram_start<=p['start']<p['end']<=ram_end for p in payloads))
symbols=subprocess.check_output(['aarch64-linux-gnu-nm',str(O/'vmlinux')],text=True)
required=['bmc156_probe','bmc156_get_data','bmc156_driver','bmc156_batch','bmc156_set_cali','acc_register_control_path','sensor_event_read','bpf_prog_load']
symbol_names={line.split()[-1] for line in symbols.splitlines() if line.split()}
for s in required:check('linked_symbol_'+s,s in symbol_names)
prior_symbols=json.loads((B/'integration-r5/symbols.json').read_text())
linked={l.split()[-1]:{'address':l.split()[0],'type':l.split()[1]} for l in symbols.splitlines() if len(l.split())==3}
check('18_r5_runtime_radio_charging_network_symbols',len(prior_symbols)==18 and all(k in linked and linked[k]['type']==v['type'] for k,v in prior_symbols.items()))
(E/'linked-required-symbols.json').write_text(json.dumps({k:linked[k] for k in list(prior_symbols)+required},sort_keys=True,indent=2)+'\n')
check('vmlinux_no_undefined_symbols',not subprocess.check_output(['aarch64-linux-gnu-nm','-u',str(O/'vmlinux')],text=True).strip())
check('ARM64_vmlinux_ELF',subprocess.check_output(['readelf','-h',str(O/'vmlinux')],text=True).find('AArch64')>=0)
(E/'linked-sensor-symbols.txt').write_text('\n'.join(l for l in symbols.splitlines() if any(s in l.lower() for s in ['bmc156','bma255','acc_register','sensor_event']))+'\n')
artifacts={}
for name in ['arch/arm64/boot/Image.gz-dtb','arch/arm64/boot/Image','arch/arm64/boot/Image.gz','arch/arm64/boot/dts/mediatek/asus-p00a.dtb','vmlinux','System.map','.config','include/generated/compile.h','include/generated/utsrelease.h']:
 p=O/name;artifacts[name]=dict(bytes=p.stat().st_size,sha256=sha(p))
record=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='COMPLETE_KERNEL_COMPILE_STATIC_PROOF',checks=checks,checks_passed=len(checks),artifacts=artifacts,header=header,physical_r5_header=oldheader,layout=dict(payloads=payloads,reservations=reservations,dynamic_reservations=dynamic,static_overlaps=False,runtime_placement_verified=False,static_ram_bank=dict(start=ram_start,end=ram_end)),config_delta=delta,source_manifests=dict(r5=dict(file='evidence/r5-source-manifest.json.gz',compressed_sha256=sha(E/'r5-source-manifest.json.gz'),canonical_json_sha256=digest(json.dumps(base,sort_keys=True).encode())),post=dict(remote_file=str(E/'post-source-manifest.json.gz'),canonical_json_sha256=digest(json.dumps(post,sort_keys=True).encode()),local_reconstruction='r5 complete manifest overlaid with patches/pre-post-hashes.json after values')),source_files=len(post),original_source_files=len(base),source_delta_files=len(json.loads((R/'patches/pre-post-hashes.json').read_text())),dt_byte_identical=True,charging_opt_in_absent=True,full_kernel_compiled=True,product_integrated=False,physical_tested=False)
(E/'full-verification.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print('PASS',len(checks),'full-kernel/source/config/DT/layout checks',artifacts['arch/arm64/boot/Image.gz-dtb'])
