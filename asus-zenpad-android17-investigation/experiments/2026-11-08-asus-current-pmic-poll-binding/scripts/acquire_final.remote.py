from pathlib import Path
import base64,hashlib,json,subprocess,re
B=Path('/srv/android/asus-devkmsg-return-boundary-20261108-e7acab50');K=B/'kernel';O=B/'out'
files={};details={}
nm=subprocess.check_output(['aarch64-linux-gnu-nm','-n','-S',str(O/'vmlinux')],text=True)
want=['_raw_spin_lock_irqsave','_raw_spin_unlock_irqrestore','fsl_a008585_read_cntvct_el0','arm64_1188873_read_cntvct_el0','pmic_mt6323_probe']
datawant=['pwrap_regmap_config','of_slave_match_tbl','of_pwrap_match_tbl','arch_timer_read_counter']
for line in nm.splitlines():
 a=line.split()
 if len(a)!=4:continue
 if a[3] in want+datawant:
  address,size=int(a[0],16),int(a[1],16);assert size<16000
  mode='-s' if a[3] in datawant else '-d'
  # PMIC probe's entry assigns the parent map; avoid unrelated init body.
  take=min(size,160) if a[3]=='pmic_mt6323_probe' else size
  b=subprocess.check_output(['aarch64-linux-gnu-objdump',mode,'--start-address='+hex(address),'--stop-address='+hex(address+take),str(O/'vmlinux')])
  files['evidence/elf/'+a[3]+('.data' if mode=='-s' else '.disasm')]=base64.b64encode(b).decode()
  details[a[3]]=dict(address=hex(address),symbol_size=size,inspected_bytes=take)
cmd=O/'arch/arm64/boot/dts/mediatek/.asus-p00a.dtb.cmd'
d=cmd.read_bytes();text=d.decode()
details['dt_cmd']=dict(path=str(cmd),bytes=len(d),sha256=hashlib.sha256(d).hexdigest(),lines=[dict(line=i,text=l) for i,l in enumerate(text.splitlines(),1) if i==1 or 'mt8163.dtsi' in l or 'asus-p00a.dts' in l or 'mt6323.dtsi' in l])
for n in ['arch/arm64/boot/dts/mediatek/asus-p00a.dtb','vmlinux']:
 p=O/n;st=p.stat();ent=dict(bytes=st.st_size,inode=st.st_ino,mtime_ns=st.st_mtime_ns)
 if p.name!='vmlinux':ent['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 details[n]=ent
print(json.dumps(dict(files=files,details=details)))
