from pathlib import Path
import os,json,hashlib,subprocess,zlib,struct,datetime
R=Path('/srv/android/asus-gpio28-lifecycle-full-kernel-20261107-r1');B=Path('/srv/android/asus-bmc156-full-kernel-r1');K=R/'kernel';O=R/'out';E=R/'evidence'
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});os.nice(10)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def artifact(p):return {'bytes':p.stat().st_size,'sha256':sha(p)}
checks=[]
def check(n,v):
 assert v,n
 checks.append(n)
def nodes(data):
 h=struct.unpack_from('>10I',data);pos=h[2];strings=data[h[3]:h[3]+h[8]];stack=[];out={}
 while True:
  t=struct.unpack_from('>I',data,pos)[0];pos+=4
  if t==1:
   end=data.index(0,pos);stack.append(data[pos:end].decode());pos=(end+4)&~3;out['/'.join(stack)]={}
  elif t==2:stack.pop()
  elif t==3:
   n,off=struct.unpack_from('>II',data,pos);pos+=8;name=strings[off:strings.index(0,off)].decode();out['/'.join(stack)][name]=data[pos:pos+n];pos=(pos+n+3)&~3
  elif t==4:continue
  elif t==9:break
  else:raise ValueError(t)
 return out
def cells(b):return list(struct.unpack('>'+str(len(b)//4)+'I',b))
s=json.loads((E/'build-status.json').read_text());check('all_real_compile_stages_exit_zero',s['status']=='complete' and s['exit']==0 and len(s['commands'])==4 and all(c['exit']==0 for c in s['commands']))
check('one_CPU_max_j1_native_AS_unlimited',len(s['affinity'])==1 and s['max_jobs']==1 and s['native_as']==[-1,-1])
image=(O/'arch/arm64/boot/Image').read_bytes();packed=(O/'arch/arm64/boot/Image.gz-dtb').read_bytes();z=zlib.decompressobj(31);raw=z.decompress(packed)+z.flush();dt=z.unused_data
check('complete_ARM64_Image_with_exact_appended_DTB',z.eof and raw==image and raw[56:60]==b'ARM\x64' and dt==(O/'arch/arm64/boot/dts/mediatek/asus-p00a.dtb').read_bytes())
check('embedded_config_equals_actual_resolved_config',subprocess.check_output([str(K/'scripts/extract-ikconfig'),str(O/'arch/arm64/boot/Image')])==(O/'.config').read_bytes())
check('actual_resolved_config_has_only_two_intended_symbol_deltas',json.loads((E/'config-delta.json').read_text())=={'CONFIG_AMP_AW8737S':{'before':'y','after':'n'},'CONFIG_ASUS_P00A_STOCK_SPEAKER_GATE':{'before':None,'after':'y'}})
old_dt=(B/'out/arch/arm64/boot/dts/mediatek/asus-p00a.dtb').read_bytes();new=nodes(dt);old=nodes(old_dt)
gates=[(n,p) for n,p in new.items() if 'asus,p00a-stock-speaker-gate' in p];check('one_explicit_codec_gate_profile',len(gates)==1)
gn,gp=gates[0];spec=cells(gp['extspkamp-gpio']);check('OF_singular_GPIO28_flags0',len(spec)==3 and spec[1:]==[28,0] and 'extspkamp-gpios' not in gp and b'mediatek,mt8163-soc-codec-63xx\0' in gp['compatible'])
controllers=[(n,p) for n,p in new.items() if p.get('phandle')==struct.pack('>I',spec[0])]
check('OF_own_MT8163_GPIO_controller',len(controllers)==1 and b'mediatek,mt8163-pinctrl\0' in controllers[0][1]['compatible'] and 'gpio-controller' in controllers[0][1] and cells(controllers[0][1]['#gpio-cells'])==[2])
usb=[n for n,p in old.items() if 'usb_dpn_sel-gpio' in p]
def phandles(tree):return {cells(p['phandle'])[0]:n for n,p in tree.items() if 'phandle' in p}
old_handles=phandles(old);new_handles=phandles(new)
check('unchanged_USB24_binding',len(usb)==1 and all(cells(old[n]['usb_dpn_sel-gpio'])[1:]==cells(new[n]['usb_dpn_sel-gpio'])[1:]==[24,0] and old_handles[cells(old[n]['usb_dpn_sel-gpio'])[0]]==new_handles[spec[0]] for n in usb))
check('unchanged_USB24_controller_properties',all({k:v for k,v in old[n].items() if k!='pinctrl-0'}=={k:v for k,v in new[n].items() if k!='pinctrl-0'} and [old_handles[c] for c in cells(old[n]['pinctrl-0'])]==[new_handles[c] for c in cells(new[n]['pinctrl-0'])] for n in usb))
usb_pins=[n for n in old if '/usb-dpn-sel-pin' in n]
check('unchanged_USB24_pinctrl_semantics',bool(usb_pins) and all({k:v for k,v in old[n].items() if k not in ['phandle','linux,phandle']}=={k:v for k,v in new[n].items() if k not in ['phandle','linux,phandle']} for n in usb_pins))
check('charging_DT_opt_in_still_absent',b'asus,allow-battery-charging' not in dt and b'asus,allow-battery-charging' not in old_dt)
# All meaningful non-audio DT properties must be preserved. Phandle numbers may legitimately be renumbered by dtc.
removed=sorted(set(old)-set(new));changed=sorted(n for n in set(old)&set(new) if old[n]!=new[n]);added=sorted(set(new)-set(old))
# Record actual small DT differences for inspection, without inferring physical behavior.
(E/'dt-delta.json').write_text(json.dumps({'removed_nodes':removed,'added_nodes':added,'changed_nodes':{n:{p:{'before_hex':old[n].get(p,b'').hex(),'after_hex':new[n].get(p,b'').hex()} for p in old[n].keys()|new[n].keys() if old[n].get(p)!=new[n].get(p)} for n in changed}},indent=2,sort_keys=True)+'\n')
# Exact selected source pins, including all delivered patch destinations.
for row in json.loads((E/'pre-post-pins.json').read_text()):check('source_postimage_'+row['path'],sha(K/row['path'])==row['after']['sha256'])
for p,v in json.loads((E/'unchanged-selected-sources.json').read_text()).items():check('unchanged_selected_'+p,sha(K/p)==v['baseline'])
# Inspect actual linked symbol names; do not claim absence of a macro can alone prove no pulse path.
symbols=subprocess.check_output(['aarch64-linux-gnu-nm',str(O/'vmlinux')],text=True);names={l.split()[-1] for l in symbols.splitlines() if l.split()}
audio_symbols={}
for rel in ['sound/soc/mediatek/mt_soc_audio_8163/mt_soc_codec_63xx.o','sound/soc/mediatek/mt_soc_audio_8163/built-in.o']:
 text=subprocess.check_output(['aarch64-linux-gnu-nm',str(O/rel)],text=True)
 selected_names={l.split()[-1] for l in text.splitlines() if l.split()}
 for n in ['switch_mode_delay','switch_mode_lock','mt_soc_get_dts_config']:check('excluded_AW_audio_activation_symbol_'+rel+'_'+n,n not in selected_names)
 audio_symbols[rel]=[l for l in text.splitlines() if any(n in l for n in ['p00a_gate','codec_state_mutex','codec_registration_mutex','UpdateHeadsetGainLocked'])]
(E/'audio-symbols.json').write_text(json.dumps(audio_symbols,indent=2)+'\n')
# Whole-kernel generic name switch_mode_delay belongs to accdet.c, not the codec.
file_owner=None;collision=[]
for l in subprocess.check_output(['readelf','-Ws',str(O/'vmlinux')],text=True).splitlines():
 c=l.split()
 if len(c)>=8 and c[3]=='FILE':file_owner=c[-1]
 if len(c)>=8 and c[-1]=='switch_mode_delay':collision.append({'file':file_owner,'entry':l.strip()})
check('generic_switch_mode_delay_is_accdet_not_audio',len(collision)==1 and collision[0]['file']=='accdet.c')
(E/'symbol-name-collision.json').write_text(json.dumps(collision,indent=2)+'\n')
check('excluded_AW_named_symbols',not any('aw873' in n.lower() for n in names))
check('lifetime_and_gate_symbols_linked',all(any(x==n or x.startswith(n+'.') for x in names) for n in ['mt8163_codec_state_mutex','codec_registration_mutex','p00a_gate_lock','UpdateHeadsetGainLocked','SetAnalogSuspend','OpenAnalogHeadphone']))
(E/'selected-linked-symbols.txt').write_text('\n'.join(l for l in symbols.splitlines() if any(x in l for x in ['p00a_gate','codec_state','codec_registration','UpdateHeadsetGain','SetAnalogSuspend','OpenAnalogHeadphone']))+'\n')
# Confirm baseline anchors have not changed. These are the only baseline artifact rehashes.
for p,h in [('.config','10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2'),('arch/arm64/boot/Image.gz-dtb','e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1'),('arch/arm64/boot/dts/mediatek/asus-p00a.dtb','a099d0538b270e23ec0d034b507eef9248252a3c459a11aa70edb6520bfd2b77')]:check('baseline_anchor_unchanged_'+p,sha(B/'out'/p)==h)
artifacts={p:artifact(O/p) for p in ['arch/arm64/boot/Image.gz-dtb','arch/arm64/boot/Image','arch/arm64/boot/dts/mediatek/asus-p00a.dtb','.config','vmlinux','include/generated/compile.h','include/generated/utsrelease.h','sound/soc/mediatek/mt_soc_audio_8163/mt_soc_codec_63xx.o','sound/soc/mediatek/mt_soc_audio_8163/AudDrv_Gpio.o']}
source=json.loads((E/'source-copy.json').read_text())['allocated_file_bytes'];owned=sum(int(subprocess.check_output(['du','-s','-B1',str(R/n)],text=True).split()[0]) for n in ['out','tmp','evidence','patches','scripts'])
check('owned_allocation_under_3GiB_including_96MiB_source_directory_allowance',source+owned+96*1024**2<3*1024**3)
r={'status':'COMPLETE_ARM64_KERNEL_COMPILE_PROOF','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'artifacts':artifacts,'config_delta':json.loads((E/'config-delta.json').read_text()),'OF':{'codec':gn,'controller':controllers[0][0],'speaker_cells':spec,'USB':usb,'USB_pin_nodes':usb_pins},'owned_disk_bytes_upper_bound':source+owned+96*1024**2,'source_prefix':str(K),'output_prefix':str(O),'HAL_qualified':False,'hardware_tested':False,'product_integrated':False}
(E/'verification.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':r['status'],'Image.gz-dtb':artifacts['arch/arm64/boot/Image.gz-dtb'],'checks':len(checks),'owned_disk_upper_bound':r['owned_disk_bytes_upper_bound']}))
