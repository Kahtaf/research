from pathlib import Path
import json,hashlib,struct,re
r=Path(__file__).resolve().parents[1];checks=[]
def check(ok,label):
 if not ok:raise AssertionError(label)
 checks.append(label)
def sections(p):
 d=p.read_bytes();check(d[:5]==b'\x7fELF\x01',p.name+' ELF32');check(struct.unpack_from('<H',d,18)[0]==40,p.name+' ARM')
 shoff=struct.unpack_from('<I',d,32)[0];ent,num,strings=struct.unpack_from('<HHH',d,46);sh=[struct.unpack_from('<10I',d,shoff+i*ent) for i in range(num)];s=sh[strings];names=d[s[4]:s[4]+s[5]]
 return {names[x[0]:].split(b'\0')[0].decode():d[x[4]:x[4]+x[5]] for x in sh}
rows=json.loads((r/'evidence/stock-compare.json').read_text());by={x['path']:x for x in rows}
check(by['/bin/cameraserver']['elfclass']==1,'stock cameraserver ARM32')
check(by['/etc/init/cameraserver.rc']['text'].startswith('service cameraserver /system/bin/cameraserver\n'),'exact configured server')
a=by['/vendor/lib/libcam.metadataprovider.so']['sensor_constructors'];b=by['/vendor/lib64/libcam.metadataprovider.so']['sensor_constructors']
check(len(a)==21 and set(a)==set(b),'identical 21 metadata constructors')
check(not any(s in n for n in a for s in ['OV5670','HM2051','OV2680']),'no newly matching ARM32 constructor')
for row in json.loads((r/'evidence/artifact-pins.json').read_text()):
 p=r/row['local'];check(p.stat().st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],'artifact '+row['local'])
s=sections(r/'fixture/abi-out/libp00a_camera_abi_probe.so');nums=struct.unpack('<35I',s['.rodata']);expected=[128,64,176,28,4,20,128,132,136,140,144,148,152,72,64,92,72,64,68,64,0,4,12,16,24,28,64,16,20,32,36,16,0x203,0x100,0x302]
check(list(nums)==expected,'all 35 C ABI constants')
s=sections(r/'fixture/cpp-out/layout.o');key=next(k for k in s if k.startswith('.rodata') and 'p00a_cpp_sizes' in k);check(struct.unpack('<4I',s[key])==(1784,96,8,20),'compiled C++ sizes 1784/96/8/20')
for row in json.loads((r/'evidence/compile.json').read_text()):check(row['returncode']==0,'C command success')
cmds=json.loads((r/'fixture/cpp-out/commands.json').read_text());check(all(x['rc']==0 for x in cmds),'C++ dep scan and compile success')
for row in json.loads((r/'evidence/compile.json').read_text()):
 if '-c' in row['argv'] or '-M' in row['argv']:
  check('bionic/libc/kernel/uapi/asm-arm' in row['argv'],'ARM UAPI includes');check(row['argv'].count('-target')==1,'single target')
check('10000000 0c000000 056910c0' in (r/'evidence/compat-layout.txt').read_text(),'OEM 16/12/ioctl c0106905')
check('14000000 10000000 056914c0' in (r/'evidence/compat-layout.txt').read_text(),'kernel49 20/16/ioctl c0146905')
ext=json.loads((r/'evidence/extended-closure.json').read_text());v=ext['vendor_libraries'];m=ext['modern_providers'];u=set().union(*(set(x['unresolved_against_vendor_union_and_found_sdk37']) for x in v.values()))
check(len(v)==82 and len(u)==19,'82 ELF closure/19 remaining names');check(sum(not x.get('missing',False) for x in m.values())==25,'25 modern providers');check(ext['vendor_total_bytes_read']==42768392,'bounded 42768392 bytes');check(not any(n in v for n in ['libui.so','libutils.so','libc.so','libbinder.so','libc++.so']),'no generic stock runtimes counted as closure solutions')
for x in json.loads((r/'evidence/abi-edges.json').read_text()):
 if x.get('text_file'):check(hashlib.sha256((r/x['text_file']).read_bytes()).hexdigest()==x['sha256'],'frozen source '+x['source'])
for p in [r/'README.md',r/'report/ARM32-ROUTE.md']:
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if not target.startswith(('https://','http://','#')):check((p.parent/target.split('#',1)[0]).exists(),'link '+target)
result={'status':'PASS','checks':len(checks),'items':checks,'boundary':'Offline evidence consistency and genuine compile artifacts only. No target execution or camera behavior.'};(r/'evidence/verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','checks':len(checks)}))
