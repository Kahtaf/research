"""Offline map-verified naming. Input numeric addresses stay parent-private."""
from pathlib import Path
import argparse,bisect,gzip,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--map',type=Path,default=ROOT/'artifacts/System.map.gz');p.add_argument('--decoded',type=Path);p.add_argument('--address',type=lambda v:int(v,0),action='append',default=[]);a=p.parse_args()
h=json.loads((ROOT/'evidence/map-local-verification.json').read_text());blob=a.map.read_bytes();data=gzip.decompress(blob)
assert hashlib.sha256(blob).hexdigest()==h['gzip']['sha256'] and hashlib.sha256(data).hexdigest()==h['uncompressed']['sha256'],'Wrong System.map'
syms=[];bounds={}
for line in data.decode().splitlines():
 parts=line.split()
 if len(parts)==3:
  addr=int(parts[0],16);bounds[parts[2]]=addr
  if parts[1] in ('T','t'):syms.append((addr,parts[2]))
syms.sort();keys=[x[0] for x in syms]
def name(addr):
 if not bounds['_text']<=addr<bounds['_etext']:return dict(symbol=None,assessment='UNKNOWN: outside mapped kernel text; no module map substitution')
 i=bisect.bisect_right(keys,addr)-1
 if i<0:return dict(symbol=None,assessment='UNKNOWN: no preceding text symbol')
 base,symbol=syms[i];return dict(symbol=symbol,offset=addr-base,assessment='numeric function snapshot at dispatch boundary; no function-body entry or causal proof')
results=[name(addr) for addr in a.address];target=None
if a.decoded:
 d=json.loads(a.decoded.read_text());identity=json.loads((ROOT/'evidence/identity.json').read_text());assert d['status']=='FINITE_WORK_CAPTURE' and d['uuid']==identity['run_uuid'],'Unadmitted capture'
 pairs={x['token']:x for x in d['pairs'] if x['entry_sequence'] is not None}
 for r in d['records']:
  if r['kind']==1:results.append(dict(sequence=r['sequence'],token=r['token'],pid=r['pid'],comm=r['comm'],pair_status=pairs[r['token']]['status'],return_sequence=pairs[r['token']]['return_sequence'],**name(r['function'])))
 target=dict(status=d['target']['status'])
 if d['target']['status']!='UNKNOWN':target.update(token=d['target']['token'],**name(d['target']['function']))
print(json.dumps(dict(map_verified=True,results=results,target=target),indent=2))
