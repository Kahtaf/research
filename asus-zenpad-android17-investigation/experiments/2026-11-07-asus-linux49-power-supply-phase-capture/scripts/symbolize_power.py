"""Map-verified public names only; raw pointer identities stay in parent's private decode."""
from pathlib import Path
import argparse,gzip,hashlib,json,bisect
R=Path(__file__).resolve().parents[1]
def symbolize(decoded):
 receipt=json.loads((R/'evidence/build-receipt.json').read_text())['artifacts']['System.map']
 packed=(R/'artifacts/System.map.gz').read_bytes();raw=gzip.decompress(packed)
 assert len(raw)==receipt['bytes'] and hashlib.sha256(raw).hexdigest()==receipt['sha256'],'genuine exact-build System.map mismatch'
 by={}
 for l in raw.decode().splitlines():
  p=l.split()
  if len(p)==3 and p[1] in 'tTwW':by.setdefault(int(p[0],16),[]).append(p[2])
 def name(address):
  if not address:return None
  return '/'.join(by[address]) if address in by else 'UNKNOWN_NOT_EXACT_BUILTIN_FUNCTION_ENTRY'
 out=dict(map_verified=True,map_uncompressed_sha256=receipt['sha256'],capture_status=decoded['status'],target=decoded.get('target'),callbacks=[],limits=['A symbol names a numeric pre-call snapshot, not driver-internal execution or causal proof.','Function addresses are omitted here. No target contact. UNKNOWN stops; one finite physical trial only.'])
 for r in sorted(decoded.get('records',[])+list(decoded.get('snapshots',{}).values()),key=lambda r:r['sequence']):
  if r['callback'] and not any(x['sequence']==r['sequence'] for x in out['callbacks']):
   out['callbacks'].append(dict(sequence=r['sequence'],pair_token=r['token'],pid=r['pid'],supply=r['name'],supplier=r['peer_name'] or None,phase=r['phase'],property=r.get('property'),callback=name(r['callback']),return_status=(r['result']-(1<<32) if r['result']&(1<<31) else r['result']) if r['code']==41 else None))
 if decoded['status']!='FINITE_POWER_CAPTURE' or decoded.get('target',{}).get('status')=='UNKNOWN':out['interpretation']='UNKNOWN_STOP'
 elif any(x['callback']=='UNKNOWN_NOT_EXACT_BUILTIN_FUNCTION_ENTRY' for x in out['callbacks']):out['interpretation']='UNKNOWN_SYMBOL_STOP'
 else:out['interpretation']='FINITE_BOUNDARY_ONLY_PARENT_INTERPRETATION'
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--decoded',type=Path,required=True);a=p.parse_args();print(json.dumps(symbolize(json.loads(a.decoded.read_text())),indent=2))
