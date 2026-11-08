from pathlib import Path
import base64,json,subprocess
from vm import R,channel
I=json.loads((R/'evidence/identity.json').read_text())
script='''from pathlib import Path
import base64,hashlib,json,subprocess
B=Path(BASE);K=B/'kernel';O=B/'out'
names=['kernel/printk/printk.c','include/linux/asus_retained_trace.h','arch/arm64/kernel/asus_retained_trace.c','arch/arm64/kernel/asus_entry_tag.h','drivers/char/mem.c','fs/read_write.c','kernel/printk/Makefile','arch/arm64/kernel/Makefile']
files={n:(K/n).read_bytes() for n in names}
for sym in ['devkmsg_write','log_store','asus_retained_trace_write']:
 files['elf-'+sym+'.disasm']=subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--disassemble='+sym,str(O/'vmlinux')])
files['base-symbols.txt']=subprocess.check_output(['aarch64-linux-gnu-nm','-n',str(O/'vmlinux')])
print(json.dumps({n:base64.b64encode(d).decode() for n,d in files.items()}))
'''.replace('BASE',repr(I['base_remote']))
p=subprocess.run(channel()+['python3 -B -'],input=script,text=True,capture_output=True);p.check_returncode()
pins={}
for n,v in json.loads(p.stdout).items():
 d=base64.b64decode(v)
 if n=='base-symbols.txt':
  d=('\n'.join(l for l in d.decode().splitlines() if any(s in l for s in ['devkmsg','log_store','vprintk_emit','printk_emit','kmsg_fops','memory_open','memory_fops','write_iter','vfs_write','__vfs_write','asus_retained_trace_write']))+'\n').encode()
 path=R/('source/base/'+n if '/' in n else 'evidence/'+n);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(d)
 pins[n]=dict(bytes=len(d),sha256=__import__('hashlib').sha256(d).hexdigest())
(R/'evidence/base-inspection.json').write_text(json.dumps(pins,indent=2)+'\n')
print('Exact baseline source and focused linked disassembly fetched; no vmlinux fetched')
