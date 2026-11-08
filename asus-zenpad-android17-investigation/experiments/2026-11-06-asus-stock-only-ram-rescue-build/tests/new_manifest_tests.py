"""Actual shipped manifest and unmodified production parser/main_restore gate.
Only root/peer/lock and public virtual reads are linker-modeled. Stop at load_self.
No full SYSTEM/data file exists or is read. No test binary ships in the image.
"""
from pathlib import Path
import subprocess,tempfile,struct,json,hashlib
R=Path(__file__).resolve().parents[1]
cmd=['gcc','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-misleading-indentation','tests/manifest_admission.c','-o','artifacts/manifest_admission']
cmd+=['-Wl,--wrap='+n for n in ['open','fopen','getuid','geteuid','getsockopt','getsockname']]
p=subprocess.run(cmd,cwd=R,capture_output=True,text=True);assert p.returncode==0,p.stderr
m=(R/'artifacts/original-stock.manifest').read_bytes()
assert hashlib.sha256(m).hexdigest()=='605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47'
# Use the actual manifest extracted from the compressed core, not a fixture copy.
import sys
sys.path.insert(0,str(R/'source'));import bootformat as b
actual=b.parse_cpio(b.ungzip((R/'artifacts/core.cpio.gz').read_bytes())[0])['rescue.manifest'][3]
assert actual==m
off=112;records=[]
for i in range(2):
 end=off+52+struct.unpack_from('<I',m,off+48)[0]*32;records.append(m[off:end]);off=end
assert off==len(m)
def count(n,body):return m[:12]+struct.pack('<I',n)+m[16:112]+body
def mutate(data,at):x=bytearray(data);x[at]^=1;return bytes(x)
four=count(4,b''.join(records)+b''.join(struct.pack('<I',i+2)+rec[4:] for i,rec in enumerate(records)))
size=11331268096;chunks=(size+1048575)//1048576
five=four[:12]+struct.pack('<I',5)+four[16:]+struct.pack('<IIQ',4,26,size)+bytes(32)+struct.pack('<I',chunks)+bytes(32*chunks)
variants={'actual_two_role':actual,'zero_records':count(0,b''),'four_records':four,'five_records':five,
 'changed_original_system':mutate(m,112+16),'changed_original_boot':mutate(m,112+len(records[0])+16),
 'changed_system_chunk':mutate(m,112+52),'changed_cid_binding':mutate(m,16),
 'changed_role':mutate(m,112),'trailing_override':m+b'/dev/block/mmcblk0p20',
 'arbitrary_partition':mutate(m,112+4),'arbitrary_size_offset':mutate(m,112+8)}
rows=[]
for name,data in variants.items():
 with tempfile.TemporaryDirectory(dir=R/'artifacts',prefix='manifest-') as td:
  d=Path(td)
  for path,value in [('rescue.manifest',data),('proc/self/attr/current',b'u:r:p10_restore:s0\n'),('sys/fs/selinux/enforce',b'1\n'),('proc/swaps',b'Filename\tType\tSize\tUsed\tPriority\n')]:
   f=d/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(value)
  p=subprocess.run([str(R/'artifacts/manifest_admission'),td],capture_output=True,text=True,timeout=5)
  assert p.returncode==0,(name,p.stdout,p.stderr)
  result=json.loads(p.stdout);assert result['manifest_admitted']==(name=='actual_two_role'),(name,result)
  if name in ['actual_two_role','zero_records','four_records','five_records','changed_original_system','changed_system_chunk','changed_cid_binding']:assert result['parser_result']==0,(name,result)
  rows.append(dict(case=name,passed=True,manifest_sha256=hashlib.sha256(data).hexdigest(),**result))
(R/'evidence/manifest-admission.json').write_text(json.dumps(dict(passed=True,cases=rows,command=cmd,production_source_unchanged=True,scope='Native exact manifest admission only; root/peer/lock modeled; stop before load_self/identity/original-pair reads; no hardware proof'),indent=2)+'\n')
print('EXACT_MANIFEST_ADMISSION_PASS',len(rows))
