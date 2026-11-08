"""Read exact existing build symbols and narrow disassembly, with no remote writes."""
from pathlib import Path
import importlib.util, json
R = Path(__file__).resolve().parents[1]
E = R/'private/symbolization-lastpc'
rp = R.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py'
spec = importlib.util.spec_from_file_location('preserved_remote', rp)
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)
control = Path(json.loads((E/'ssh-control.json').read_text())['socket'])
assert control.is_socket()
remote.SSH = remote.SSH[:-1]+['-S',str(control),'-o','ControlMaster=no','-o','ProxyCommand=false']+remote.SSH[-1:]
script = r'''from pathlib import Path
import hashlib,json,bisect,subprocess,gzip,base64
r=Path('/srv/android/asus-linux49-retained-clock-capture-20261107-fef31ed4/out')
pins={'System.map':'6e6dbe763620e7701dd1a854f341ecec7b2346bc66c44e5cd6aedd093078d8a3','vmlinux':'903ed4f3197f8e0f9408ad65d4bde5c52b0d08a325e9447349622fb9b5245cd4'}
for n,h in pins.items():assert hashlib.sha256((r/n).read_bytes()).hexdigest()==h,n
rows=[]
for l in (r/'System.map').read_text().splitlines():
 p=l.split()
 if len(p)==3 and p[1] in ('t','T'):rows.append((int(p[0],16),p[2]))
rows.sort();addresses=[a for a,n in rows]
targets={'monotonic_caller':0xffffff800811f970,'raw_reader':0xffffff8008869160,'last_timer_callback':0xffffff800811e330,'interrupted_PC':0xffffff8008b673c4,'ktime_get_ts64':0xffffff8008123bc0,'cached_lastpc_clue':0xffffff8008695440}
result={'exact_build_pins_verified':pins,'read_only':True,'targets':{}}
for name,addr in targets.items():
 i=bisect.bisect_right(addresses,addr)-1;assert i>=0
 a,sym=rows[i];nexta=next((q for q in addresses[i+1:] if q>a),None)
 q=subprocess.run(['aarch64-linux-gnu-objdump','-d','--start-address='+hex(max(a,addr-32)),'--stop-address='+hex(addr+112),str(r/'vmlinux')],capture_output=True,text=True,check=True)
 result['targets'][name]={'address':hex(addr),'symbol':sym,'start':hex(a),'offset':addr-a,'next_text_symbol_address':hex(nexta) if nexta else None,'disassembly':q.stdout}
result['System_map_gzip_base64']=base64.b64encode(gzip.compress((r/'System.map').read_bytes(),mtime=0)).decode()
print(json.dumps(result))
'''
result=json.loads(remote.run(script))
import base64
(E/'System.map.gz').write_bytes(base64.b64decode(result.pop('System_map_gzip_base64')))
(E/'symbols.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:{n:v[n] for n in ['symbol','offset']} for k,v in result['targets'].items()},indent=2))
