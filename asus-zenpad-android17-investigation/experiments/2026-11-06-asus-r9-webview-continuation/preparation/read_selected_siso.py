from pathlib import Path
import remote,json
s=r'''
from pathlib import Path
import json,gzip,hashlib,sys,struct
R=Path('/srv/android/asus-reviewed-build-kit/r9');A=Path('/srv/android/lineage24');F=Path('/srv/android/asus-reviewed-build-kit/r9-fixtures')
gap=json.loads((R/'evidence/cache-gap.json').read_text());audit=json.loads((R/'evidence/actual-audit.json').read_text())
targets={x['output'] for x in gap['first']}|set(audit['cache_audit']['outputs'])
# Stream protobuf messages, exposing only exact selected native compiler outputs.
def vi(f):
 v=0;s=0
 while True:
  b=f.read(1)
  if not b:
   if not s:return None
   raise ValueError('Truncated varint')
  n=b[0];v|=(n&127)<<s
  if n<128:return v
  s+=7;assert s<70

def fields(data):
 import io
 f=io.BytesIO(data);r={}
 while True:
  tag=vi(f)
  if tag is None:return r
  num=tag>>3;wire=tag&7
  if wire==0:val=vi(f)
  elif wire==2:
   n=vi(f);assert n<1048576;val=f.read(n);assert len(val)==n
  elif wire==1:val=f.read(8)
  elif wire==5:val=f.read(4)
  else:raise ValueError('Unknown wire type')
  r.setdefault(num,[]).append(val)

def dig(data):
 if not data:return None
 d=fields(data);return dict(hash=d.get(1,[b''])[0].decode(),size=d.get(2,[0])[0])
result={};count=0
p=A/'out/.siso_fs_state';h=hashlib.sha256()
with p.open('rb') as f:
 for b in iter(lambda:f.read(1048576),b''):h.update(b)
state_hash=h.hexdigest()
with gzip.open(p,'rb') as f:
 while True:
  tag=vi(f)
  if tag is None:break
  n=vi(f);assert tag&7==2 and n<1048576;data=f.read(n);assert len(data)==n
  if tag>>3!=1:continue
  count+=1;d=fields(data);name=d.get(2,[b''])[0].decode()
  if name not in targets:continue
  result[name]=dict(mod_time_ns=fields(d[1][0]).get(1,[None])[0],digest=dig(d.get(3,[None])[0]),executable=d.get(4,[0])[0],cmd_hash_hex=d.get(6,[b''])[0].hex(),edge_hash_hex=d.get(9,[b''])[0].hex(),action=dig(d.get(7,[None])[0]),updated_time_ns=d.get(8,[0])[0],local=d.get(10,[0])[0])
  target=A/name
  if target.is_file():
   hh=hashlib.sha256()
   with target.open('rb') as inp:
    for b in iter(lambda:inp.read(1048576),b''):hh.update(b)
   result[name]['current_sha256']=hh.hexdigest();result[name]['current_mtime_ns']=target.stat().st_mtime_ns
r=dict(source_state_sha256=state_hash,entries_scanned=count,selected_targets=len(targets),selected_entries=result,scope='Selected output metadata only; no source key/calibration content read; cache untouched',cache_admitted=False)
with (R/'evidence/selected-siso-state.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
# Redact the exploratory prefix now that the actual schema is understood.
p=R/'evidence/siso-state-format.json';d=json.loads(p.read_text());d['out/.siso_fs_state'].pop('decoded_first128_hex',None);d['out/.siso_fs_state']['encoding']='gzip-compressed protobuf';p.write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/selected-siso-state.json').write_text(r);d=json.loads(r);print(json.dumps({k:v for k,v in d.items() if k!='selected_entries'},indent=2));print(json.dumps({t:v for t,v in d['selected_entries'].items() if '/unstripped/' in t},indent=2))
