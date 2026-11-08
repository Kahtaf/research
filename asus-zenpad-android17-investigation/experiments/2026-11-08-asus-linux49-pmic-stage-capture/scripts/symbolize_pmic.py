"""Genuine map-verified public PMIC stage summary, without pointer identities."""
from pathlib import Path
import json,gzip,hashlib,argparse
R=Path(__file__).resolve().parents[1]
def symbolize(decoded):
 receipt=json.loads((R/'evidence/build-receipt.json').read_text())['artifacts']['System.map'];raw=gzip.decompress((R/'artifacts/System.map.gz').read_bytes())
 assert dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())==receipt,'genuine exact-build map mismatch'
 syms={l.split()[2]:int(l.split()[0],16) for l in raw.decode().splitlines() if len(l.split())==3}
 linked=json.loads((R/'evidence/linked-capture.json').read_text())
 for n in ['battery_get_property','power_supply_changed_work','asus_p00a_pmic_present','asus_p00a_pmic_adc','p00a_pmic_prepare_adc']:
  assert syms[n]==int(linked['symbols'][n]['address'],16),'map/linked source identity mismatch'
 out=dict(map_verified=True,map_uncompressed_sha256=receipt['sha256'],capture_status=decoded['status'],target=decoded.get('target'),old_target_facts=decoded.get('old_target_facts'),snapshot_attribution=decoded.get('snapshot_attribution'),limits=decoded.get('limits'))
 out['interpretation']='FINITE_BOUNDARY_ONLY_PARENT_INTERPRETATION' if decoded['status']=='FINITE_PMIC_CAPTURE' and decoded.get('target',{}).get('status')=='JOINED_FINITE_PMIC_STAGE' else 'UNKNOWN_STOP'
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--decoded',type=Path,required=True);a=p.parse_args();print(json.dumps(symbolize(json.loads(a.decoded.read_text())),indent=2))
