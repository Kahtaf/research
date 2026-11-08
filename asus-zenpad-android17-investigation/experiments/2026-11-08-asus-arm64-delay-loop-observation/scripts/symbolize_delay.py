"""Offline bounded public summary. Supply only the parent's private decoded JSON."""
from pathlib import Path
import argparse,bisect,gzip,hashlib,json
R=Path(__file__).resolve().parents[1]
def summary(d):
 receipt=json.loads((R/'evidence/System.map-uncompressed.json').read_text());z=(R/'artifacts/System.map.gz').read_bytes();assert hashlib.sha256(z).hexdigest()==receipt['compressed_sha256']
 b=gzip.decompress(z);assert hashlib.sha256(b).hexdigest()==receipt['uncompressed']['sha256'] and b==(R/'artifacts/System.map').read_bytes()
 m=[]
 for l in b.decode().splitlines():
  p=l.split()
  if len(p)==3:m.append((int(p[0],16),p[2]))
 m.sort();addresses=[a for a,n in m]
 def name(a):
  if not a:return None
  j=bisect.bisect_right(addresses,a)-1
  assert j>=0
  start,n=m[j];return n+'+'+str(a-start)
 out=dict(status=d['status'],uuid=d['uuid'],map_verified=True,previous_statuses=d.get('previous_statuses'),target=d['target'],limits=d['limits'])
 if d['status']!='FINITE_DELAY_CAPTURE':out['reason']=d.get('reason');return out
 h=d['header'];join=d['join'];calc=d['calculation'];out['callers']={k:name(h[k]) for k in ['hook_caller','const_caller','delay_caller']}
 out['source_caller']=name(join['caller']);out['calculation']={k:calc[k] for k in ['xloops','lpj','HZ','product','cycles']} if h['state']>=2 else None
 out['milestones']=d['milestones'];out['interpretation']='Finite retained boundaries only; no source cause, permanent hang, IRQ history or elapsed-time conclusion.'
 # No raw kernel pointer/worker/psy/callback/physical identity in this output.
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--decoded',required=True,type=Path);a=p.parse_args();print(json.dumps(summary(json.loads(a.decoded.read_text())),indent=2))
