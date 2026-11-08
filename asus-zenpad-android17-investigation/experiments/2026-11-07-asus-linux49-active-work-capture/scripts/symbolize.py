"""Offline active-function symbolization; raw inputs and output stay parent-local."""
from pathlib import Path
import argparse,bisect,gzip,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--map',type=Path,default=ROOT/'artifacts/System.map.gz')
p.add_argument('--address',type=lambda v:int(v,0),action='append',default=[])
p.add_argument('--decoded',type=Path,help='parent-private decode_switch JSON; symbolize current_func only')
a=p.parse_args()
h=json.loads((ROOT/'evidence/handoff.json').read_text());blob=a.map.read_bytes();data=gzip.decompress(blob)
assert hashlib.sha256(blob).hexdigest()==h['System_map']['gzip']['sha256'],'Wrong compressed map'
assert hashlib.sha256(data).hexdigest()==h['System_map']['uncompressed']['sha256'],'Wrong map content'
syms=[]
for line in data.decode().splitlines():
 parts=line.split()
 if len(parts)==3:syms.append((int(parts[0],16),parts[1],parts[2]))
syms.sort();keys=[x[0] for x in syms]
def symbolize(addr):
 if not addr:return dict(symbol=None,assessment='NULL function value: no active function at this seam only with valid worker-present flag; later work remains possible')
 i=bisect.bisect_right(keys,addr)-1
 if i<0:return dict(symbol=None,assessment='UNKNOWN: below map range')
 base,kind,name=syms[i]
 if kind not in ('T','t'):return dict(symbol=None,assessment='UNKNOWN: nearest map symbol is not text')
 return dict(symbol=name,offset=addr-base,assessment='own-worker active function snapshot only; no causal attribution')
out=[]
for addr in a.address:out.append(symbolize(addr))
if a.decoded:
 d=json.loads(a.decoded.read_text());assert d['status']=='FINITE_SWITCH_CAPTURE' and d['uuid']==h['capture_UUID'],'Unadmitted capture'
 for label,rows in [('ring',d['records']),('last_PID1_out',[d.get('last_PID1_out')]),('last_PID1_in',[d.get('last_PID1_in')])]:
  for row in rows:
   if row:
    sym=symbolize(row['current_func']) if row['worker_present'] else dict(symbol=None,assessment='No own-worker function snapshot available')
    out.append(dict(location=label,sequence=row['sequence'],worker_present=row['worker_present'],active_work_assessment=row['active_work_assessment'],**sym))
print(json.dumps(dict(map_verified=True,results=out),indent=2))
