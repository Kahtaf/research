from pathlib import Path
import os,resource,json,hashlib,subprocess as s,zipfile,io,stat
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
O=Path('/srv/android/asus-final-bpf-runtime-20261106');O.mkdir(exist_ok=False);(O/'capture').mkdir();(O/'evidence').mkdir();(O/'scripts').mkdir()
R=Path('/srv/android/asus-root-enabled-incremental-r1/host-r2/validation');raw=R/'system-partition.raw'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def identity(p):
 st=p.stat();return dict(path=str(p),bytes=st.st_size,mode=oct(stat.S_IMODE(st.st_mode)),inode=st.st_ino,mtime_ns=st.st_mtime_ns,sha256=sha(p))
before=identity(raw);assert before['bytes']==3753902080 and before['mode']=='0o444' and before['sha256']=='04b4d81f486ce4a17609300c3f6d2f92cecc1938ee0f0e64019a29bd8c870785'
d=json.loads((R/'r8-product-provenance.json').read_text());commands=[]
def run(args):
 p=s.run(args,capture_output=True,text=True);commands.append(dict(argv=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0;return p.stdout
DB='/usr/sbin/debugfs'
def dump(img,path,dest):
 dest.parent.mkdir(parents=True,exist_ok=True);run([DB,'-R','dump '+path+' '+str(dest),str(img)]);assert dest.is_file(),path
payloads={}
for apex,a in d['apex_archives'].items():
 cap=O/'capture'/(apex+'.capex');dump(raw,'/'+a['path'],cap);assert sha(cap)==a['sha256']
 with zipfile.ZipFile(cap) as z:
  original=z.read('original_apex')
 with zipfile.ZipFile(io.BytesIO(original)) as z:
  payload=z.read('apex_payload.img')
 img=O/'capture'/(apex+'.img');img.write_bytes(payload);payloads[apex]=img
 print('APEX',apex,len(payload),payload[1024:1084].hex(),flush=True)
rows=[]
for row in d['bpf_classification']['rows']:
 path=row['install_path'];dest=O/'capture/root'/path
 if path.startswith('apex/'):
  _,apex,rel=path.split('/',2);dump(payloads[apex],'/'+rel,dest)
 else:dump(raw,'/'+path,dest)
 assert sha(dest)==row['current_sha256'],path
 rows.append({k:row.get(k) for k in ['install_path','current_sha256','kind','source_pins','native_command_hash','runtime_requalification_required','historical_runtime_tested_substitution_sha256']})
for path in ['system/bin/bpfloader','apex/com.android.tethering/bin/netbpfload']:
 dest=O/'capture/root'/path
 if path.startswith('apex/'):
  _,apex,rel=path.split('/',2);dump(payloads[apex],'/'+rel,dest)
 else:dump(raw,'/'+path,dest)
 print('LOADER',path,sha(dest),flush=True)
# Record completed host binding without consulting active source or output.
(O/'evidence/final-host-binding.json').write_text(json.dumps(dict(receipt_path=str(R/'r8-product-provenance.json'),receipt_sha256=sha(R/'r8-product-provenance.json'),bpf_classification=d['bpf_classification'],payloads=d['payloads'],link_outputs=d['link_outputs']),indent=2))
after=identity(raw);assert before==after
out=dict(raw_before=before,raw_after=after,objects=rows,loaders={str(p.relative_to(O/'capture/root')):dict(sha256=sha(p),bytes=p.stat().st_size) for p in (O/'capture/root').rglob('*') if p.is_file() and '/bin/' in str(p)},commands=commands)
(O/'evidence/capture.json').write_text(json.dumps(out,indent=2));print('CAPTURED',len(rows),'UNCHANGED_RAW',before==after)
