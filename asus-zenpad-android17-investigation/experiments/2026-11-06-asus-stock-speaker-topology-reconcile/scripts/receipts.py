import hashlib,json,os,platform,resource,re,struct
from pathlib import Path
from bounded import ROOT,run
from binary_evidence import fdt
W=ROOT.parent; H=lambda b:hashlib.sha256(b).hexdigest()
rows=json.loads((ROOT/'evidence/input-pins.json').read_text())
def cp(rel,dest):
 p=W/rel;b=p.read_bytes();out=ROOT/'inputs'/dest;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(b);rows.append({'path':rel,'copy':str(out.relative_to(ROOT)),'sha256':H(b),'bytes':len(b),'expected_sha256':None});return b
cp('2026-11-06-asus-stock-audio-topology/evidence/stock-topology.json','observations/stock-topology.json')
ready=json.loads(cp('2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback/READY.json','public-receipts/READY.json'))
audit=json.loads(cp('2026-11-06-asus-stock-firmware-restore-source/evidence/audit.json','public-receipts/firmware-audit.json'))
# Select the public hash entry only: no original backup content is opened.
pub=(ROOT/'inputs/stock-public/boot.img').read_bytes();count=16740352
padded=H(pub+bytes(count-len(pub)));assert padded=='7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316'
assert audit['zero_padded_boot_sha256']==padded and all(audit['padded_boot_matches_original_backups'].values())
(ROOT/'evidence/stock-boot-match.json').write_text(json.dumps({'public_boot_member_sha256':H(pub),'public_member_bytes':len(pub),'zero_pad_to_bytes':count,'padded_sha256':padded,'matches_prior_public_audit_of_two_original_backups':True,'original_backup_contents_opened':False,'current_running_kernel_measured':False,'scope':'offline matching to existing historical hash receipts, not a new device observation'},indent=2)+'\n')
# Mapping controls: validate actual image xrefs to literal OF property strings.
checks=[]
for label,base,refs in [('stock-public',0xffffffc000080000,{0xffffffc000ea7e10:b'mediatek,mt8163-soc-codec-63xx',0xffffffc000ea7e30:b'extspkamp-gpio'}),('bmc',0xffffff8008080000,{0xffffff8008d87d40:b'switch-mode-delay'})]:
 raw=(ROOT/'inputs'/label/'Image').read_bytes()
 for addr,want in refs.items():
  actual=raw[addr-base:addr-base+len(want)+1];assert actual==want+b'\0',(label,hex(addr),actual)
  checks.append({'image':label,'referenced_va':hex(addr),'file_offset':hex(addr-base),'literal':want.decode(),'exact_match':True})
(ROOT/'evidence/address-mapping-controls.json').write_text(json.dumps({'method':'ARM64 Image header text_offset=0x80000; _stext at image+0x1000; validate virtual-to-file mapping by actual disassembly OF string xrefs. ELF metadata wraps unchanged Image bytes, no instructions assembled or rebuilt.','controls':checks},indent=2)+'\n')
# Pinctrl ownership and consumers from actual DTBs.
own={}
for label,name in [('stock-public','appended.dtb'),('bmc','asus-p00a.dtb')]:
 nodes=fdt((ROOT/'inputs'/label/name).read_bytes());ph={struct.unpack('>I',p['phandle'])[0]:n for n,p in nodes.items() if 'phandle' in p}
 result={'gpio24_states':{},'consumers':{},'codec_nodes':{},'delay_nodes':[]}
 for n,p in nodes.items():
  if p.get('pins')==struct.pack('>I',0x1800):result['gpio24_states'][n]={k:v.hex() for k,v in p.items()}
  if any(b'mt8163-soc-codec-63xx' in v for k,v in p.items() if k=='compatible') or n.endswith('/audiosys@11220000'):
   result['codec_nodes'][n]={k:(v.rstrip(b'\0').decode(errors='replace') if k=='compatible' else v.hex()) for k,v in p.items()}
  if 'switch-mode-delay' in p:result['delay_nodes'].append(n)
  for k,v in p.items():
   if k.startswith('pinctrl-') and k!='pinctrl-names' and len(v)%4==0:
    refs=[ph.get(q) for q in struct.unpack('>'+str(len(v)//4)+'I',v)]
    if any(t and any(s in t for s in ['audexamp','usb-dpn']) for t in refs):result['consumers'][n+':'+k]=refs
   if k in ['extspkamp-gpio','usb_dpn_sel-gpio']:
    vals=list(struct.unpack('>'+str(len(v)//4)+'I',v));result['consumers'][n+':'+k]={'cells':vals,'controller':ph.get(vals[0])}
 own[label]=result
(ROOT/'evidence/gpio-ownership.json').write_text(json.dumps(own,indent=2)+'\n')
# Frozen source tree all references; no target/source mutation.
k=W/'2026-11-05-asus-p00a-power-port/sources/kernel'
run(['rg','-n','--glob','Kconfig*','(config|select|imply) (AMP_AW8737S|MTK_SPEAKER|MTK_LEGACY)',k],output='evidence/config-definitions-and-reverse-dependencies.txt')
run(['rg','-n','--glob','*.c','--glob','*.h','--glob','*defconfig','--glob','*.dts*','CONFIG_AMP_AW8737S|switch-mode-delay',k/'sound',k/'arch/arm64'],output='evidence/aw8737s-source-and-board-references.txt')
pre=(ROOT/'inputs/bmc/resolved.config').read_bytes();df=(ROOT/'inputs/bmc/asus_p00a_defconfig').read_bytes()
# Counterfactual for dependency accounting only; deliberately NOT staged as a proposal.
post=pre.replace(b'CONFIG_AMP_AW8737S=y',b'# CONFIG_AMP_AW8737S is not set');assert pre!=post
selected={}
for line in pre.decode().splitlines():
 if re.search(r'CONFIG_(SOUND|SND|SND_SOC|SND_SOC_MT8163|SND_SOC_MT8163_AMZN|MTK_SPEAKER|MTK_SND_SOC_NEW_ARCH|AMP_AW8737S|OF|MTK_LEGACY)(=| )',line):selected[line]=True
(ROOT/'evidence/config-accounting.json').write_text(json.dumps({'pinned_resolved_pre_sha256':H(pre),'defconfig_pre_sha256':H(df),'staged_post_sha256':H(pre),'staged_post_is_unchanged':True,'staged_changed_paths':[],'counterfactual_only_aw_off_sha256':H(post),'counterfactual_serialized':False,'counterfactual_changed_symbols':['CONFIG_AMP_AW8737S'],'counterfactual_resolved_by_olddefconfig':False,'reason_no_delta':'AW-off preserves internal function but loses OEM GPIO28 gate; fitted hardware and exact complete replacement not established. No enable/disable recommendation.','selected_resolved_lines':list(selected),'MTK_LEGACY_in_resolved_config':any('CONFIG_MTK_LEGACY' in s for s in pre.decode().splitlines()),'defaults':'Both MTK_SPEAKER and AMP_AW8737S default n. AW option has no direct dependency or select from MTK_SPEAKER; menu visibility inherited from SOUND/SND/SND_SOC. Both explicitly enabled by ASUS combined defconfig.','other_subsystems_changed':False},indent=2)+'\n')
limits={}
for sym in ['RLIMIT_AS','RLIMIT_CPU','RLIMIT_RSS']:
 r=getattr(resource,sym);old=resource.getrlimit(r)
 try:
  if sym=='RLIMIT_AS':resource.setrlimit(r,(1024**3,old[1]))
  limits[sym]={'before':old,'after':resource.getrlimit(r),'set_error':None}
 except (ValueError,OSError) as e:limits[sym]={'before':old,'set_error':str(e)}
(ROOT/'evidence/darwin-constraints.json').write_text(json.dumps({'platform':platform.platform(),'limits_probe':limits,'sched_setaffinity_available':hasattr(os,'sched_setaffinity'),'hard_single_cpu_affinity':'unavailable on Darwin; all work serial, no make/ninja/parallel workers, small clang invocations only','memory_constraint':'1 GiB RLIMIT_AS requested per child; Darwin does not offer Linux address-space enforcement semantics. No hard 1 GiB resident-memory guarantee claimed; small inputs (<20 MiB Image each), finite 64 MiB decompression bound, maximum one serial compilation; no full kernel or target build.','per_command_cpu_s':30,'per_command_wall_timeout_s':45,'max_output_file_bytes':128*1024**2},indent=2)+'\n')
(ROOT/'evidence/input-pins.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Public boot match, VA controls, GPIO consumers, config and Darwin receipts passed')
