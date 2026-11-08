from pathlib import Path
import json,hashlib,subprocess,re,struct,zlib
from source_checks import check
R=Path('/srv/android/asus-selected-cntpct-delay-control-20261108-2ac3b1e4');B=Path('/srv/android/asus-arm64-delay-loop-observation-20261108-f3da846c');K=R/'kernel';O=R/'out';E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();i=json.loads((R/'source/identity.json').read_text())
assert json.loads((E/'build-status.json').read_text())['status']=='complete'
for n,v in json.loads((E/'source-pins.json').read_text()).items():assert sha(K/n)==v['after'] and sha(B/'kernel'/n)==v['before'],n
assert (O/'.config').read_bytes()==(B/'out/.config').read_bytes() and sha(O/'.config')==i['config_sha256'];assert (O/'source').resolve()==K
preserved=json.loads((E/'preserved-source-pins.json').read_text())
for n,v in preserved.items():assert sha(K/n)==sha(B/'kernel'/n)==v,n
for n in ['include/linux/power_supply.h','include/linux/power/asus_p00a_battery.h']:
 assert sha(K/n)==sha(B/'kernel'/n);preserved[n]=sha(K/n)
source=check(K,B/'kernel',i['run_uuid']);(E/'source-checks.json').write_text(json.dumps(source,indent=2)+'\n')
inodes={}
for n,v in json.loads((E/'base-freeze.json').read_text()).items():
 p=B/n;c=R/n;assert sha(p)==v['sha256'] and p.stat().st_ino==v['inode'] and p.stat().st_mtime_ns==v['mtime_ns'],n
 assert c.stat().st_ino!=p.stat().st_ino;inodes[n]=dict(base_unchanged=True,base_inode=p.stat().st_ino,candidate_inode=c.stat().st_ino,independent=True)
(E/'repository-preservation.json').write_text(json.dumps(dict(status='PASS_SCOPED_BASE_FREEZE_AND_INDEPENDENT_INODES',scope=inodes,copy='cp -a --reflink=auto kernel AND out including nested repositories',git_mutations=False,full_tree_audit=False),indent=2)+'\n')
nm=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(O/'vmlinux')],text=True)
rows=[x for l in nm.splitlines() if len(x:=l.split())==4];sized={x[3]:(int(x[0],16),int(x[1],16)) for x in rows}
objnm=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(O/'arch/arm64/kernel/asus_retained_trace.o')],text=True)
recorder_names={x[3] for l in objnm.splitlines() if len(x:=l.split())==4 and x[2].lower()=='t'}
for l in objnm.splitlines():
 x=l.split()
 if len(x)==4 and (x[3].startswith(('dl_','pm_','sw_commit','cap_init','trace_init'))):
  matches=[(int(y[0],16),int(y[1],16)) for y in rows if y[3]==x[3] and y[1]==x[1]];assert len(matches)==1,(x[3],matches);sized[x[3]]=matches[0]
def dump(a,z):return subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--start-address='+hex(a),'--stop-address='+hex(a+z),str(O/'vmlinux')],text=True)
names={'__delay','__const_udelay','__udelay','__ndelay','asus_p00a_pmic_adc','asus_p00a_pmic_present','p00a_pmic_prepare_adc','asus_p00a_battery_get_property','battery_get_property','power_supply_changed_work','trace_init','cap_init','__clean_dcache_area_poc','_raw_spin_trylock','_raw_spin_unlock_irqrestore'}
names|={n for n in recorder_names if n.startswith(('dl_','asus_capture_delay_')) or n.split('.')[0] in ['pm_record','asus_capture_pmic_step','sw_commit']}
dis={n:dump(*sized[n]) for n in names if n in sized and sized[n][1]}
(E/'scoped-hooks.disasm').write_text('\n'.join(dis[n] for n in sorted(dis)));(E/'delay-loop.disasm').write_text('\n'.join(dis[n] for n in ['__const_udelay','__delay','__udelay','__ndelay']))
def body(n):return '\n'.join(v for k,v in dis.items() if k.split('.')[0]==n)
def returns(d,t):return [int(m[1],16)+4 for m in re.finditer(r'^\s*([0-9a-f]+):.*\bbl\s+[0-9a-f]+ <'+re.escape(t)+r'>',d,re.M)]
adc=body('asus_p00a_pmic_adc');bat=body('asus_p00a_battery_get_property');co=body('__const_udelay');de=body('__delay')
assert len(returns(adc,'__const_udelay'))==1 and len(returns(co,'__delay'))==1 and len(returns(co,'asus_capture_delay_calc'))==1
constret=returns(adc,'__const_udelay')[0];constoffset=constret-sized['asus_p00a_pmic_adc'][0];assert constoffset==928
ls=adc.splitlines();j=next(j for j,l in enumerate(ls) if l.lstrip().startswith(hex(constret-4)[2:]+':'));near='\n'.join(ls[j-9:j]);assert '#0xa934' in near and '#0x13, lsl #16' in near
prereturns=returns(near,'asus_capture_pmic_step');assert prereturns==[sized['asus_p00a_pmic_adc'][0]+912]
vol=[]
for ret in returns(bat,'asus_p00a_pmic_adc'):
 lines=bat.splitlines();j=next(j for j,l in enumerate(lines) if l.lstrip().startswith(hex(ret-4)[2:]+':'));prior='\n'.join(lines[j-5:j])
 if 'w0, #0x6' in prior and 'w1, #0x5' in prior:vol.append(ret)
assert vol==[sized['asus_p00a_battery_get_property'][0]+468]
# The linked fixed callsite gate is an exact unique BL in this range, rather
# than an assumed inlining boundary. Both ABI callsites have original x0.
calcsite=returns(co,'asus_capture_delay_calc')[0];delayret=returns(co,'__delay')[0];assert sized['__const_udelay'][0]<=calcsite<delayret<sized['__const_udelay'][0]+256 and delayret<=calcsite+128
assert '__delay' not in co.split('<__const_udelay>:',1)[1].split('<__delay>')[0].split('asus_capture_delay_calc>')[0] # calc precedes call
assert re.search(r'\bmrs\s+x\d+, cntpct_el0',de) and re.search(r'\bmrs\s+x\d+, cntvct_el0',de) and re.search(r'\bblr\b',de)
assert re.search(r'\byield\b',de) # dynamic path count checked by route_proof.py
assert len(returns(de,'asus_capture_delay_begin'))==1 and '<asus_capture_delay_point>' in de and '\tisb' in de
# GCC may share arithmetic and branch tails; original xloops and the single
# LPJ load are retained as operands of calc before x0 cycles is passed on.
cmd=(O/'arch/arm64/lib/.delay.o.cmd').read_text();assert str(K/'arch/arm64/lib/delay.c') in cmd and '-O2' in cmd
assert 'cntfrq_el0' not in de and not re.search(r'\b(?:msr|smc|hvc)\b',de)
new={n:v for n,v in dis.items() if n.startswith(('dl_','asus_capture_delay_'))}
allowed={'__clean_dcache_area_poc','memcpy','memcmp','memset','__memset','__memcpy','__memcmp','cap_hex','__stack_chk_fail','_raw_spin_trylock','_raw_spin_unlock_irqrestore','sw_commit','pm_ps_field','__pi_memcmp','__pi_memcpy','__pi_memset'}
for alias,original in [('__pi_memcmp','memcmp'),('__pi_memcpy','memcpy'),('__pi_memset','memset')]:
 if alias in sized and original in sized:assert sized[alias][0]==sized[original][0],(alias,original)
calls={}
for n,v in new.items():
 assert not re.search(r'\bblr\b',v),'no indirect new recorder calls'
 for reg in re.findall(r'\bmrs\s+x\d+, (\w+)',v):assert reg in ['sp_el0','tpidr_el1','daif'],(n,reg)
 assert not any(t in v for t in ['cntvct_el0','cntpct_el0','cntfrq_el0'])
 targets=re.findall(r'\b(?:bl|b)\s+[0-9a-f]+ <([^>]+)>',v);calls[n]=sorted(set(targets))
 for t in targets:
  b=t.split('+')[0].split('.')[0];assert b in allowed or b.startswith(('dl_','asus_capture_delay_')), (n,t)
assert re.search(r'\bdsb\s+sy',body('__clean_dcache_area_poc'))
init=body('trace_init')+body('cap_init');assert 'dl_init' in init
pm=body('pm_record');assert '<dl_pmic>' in pm and pm.count('cntvct_el0')==1
# Read-only stable accessor provenance/config unchanged, optional activation unproved.
for n in ['arch/arm64/include/asm/arch_timer.h','arch/arm64/include/asm/timex.h','include/clocksource/arm_arch_timer.h']:assert sha(K/n)==sha(B/'kernel'/n)
raw=(O/'arch/arm64/boot/Image').read_bytes();assert i['tag'].encode() in raw
for tag in ['A49CAP1','A49SW2','A49WD1','A49PS1','A49PM1','A49DL2']:assert (tag+' uuid='+i['run_uuid']).encode() in raw
assert b'ASUS49-DIAG headless RDMA IRQ registration skipped' in raw
image_size=struct.unpack_from('<Q',raw,16)[0];assert image_size>=len(raw)
def unzip(p):
 d=zlib.decompressobj(31);r=d.decompress(p);assert d.eof;return r,d.unused_data
_,dt=unzip((O/'arch/arm64/boot/Image.gz-dtb').read_bytes());_,bdt=unzip((B/'out/arch/arm64/boot/Image.gz-dtb').read_bytes());assert dt==bdt
result=dict(status='PASS_SCOPED_SOURCE_ACTUAL_ELF',entry_identity=i,Image=dict(file_bytes=len(raw),image_size=image_size),symbols={n:dict(address=hex(a),bytes=z) for n,(a,z) in sized.items() if n in names},pmic_callers=dict(present_returns=returns(bat,'asus_p00a_pmic_present'),voltage_adc_returns=vol,prepare_returns=returns(adc,'p00a_pmic_prepare_adc'),prepare_inlined=False),delay_callers=dict(const_return=constret,pre_return=prereturns[0],calc_site=calcsite,delay_return=delayret,const_symbol=sized['__const_udelay'][0],actual_spin_body='__delay'),new_recorder_calls=calls,source_checks=source,preserved_sources=preserved,old_bytes=26752,append_bytes=2560,combined_bytes=29312,config_byte_identical=True,DT_byte_identical=True,hardware_DTB_sha256=hashlib.sha256(dt).hexdigest(),OOL_activation='UNPROVED',no_new_recorder_counter_reads=True,selected_domain=1,ABI='original exported __delay/__const_udelay/__udelay/__ndelay signatures unchanged',physical_execution=False)
(E/'linked-capture.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],delay_callers=result['delay_callers']),indent=2))
