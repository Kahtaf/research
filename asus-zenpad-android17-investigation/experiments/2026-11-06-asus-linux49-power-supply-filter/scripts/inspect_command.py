from pathlib import Path
import json
R=Path('/srv/android/asus-root-enabled-incremental-r1/host-r2/validation');d=json.loads((R/'r8-product-provenance.json').read_text())
for r in d['payloads']:
 if 'filterPowerSupplyEvents' in str(r):print(json.dumps(r)[:15000])
p=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106/inputs/object-source');print('CAPTURE',list(p.iterdir())[:8])
# Read existing generated graph text only; never invoke its engine.
p=Path('/srv/android/lineage24/out/soong/build.lineage_p00a.ninja');print('GRAPH_EXISTS',p.exists())
if p.exists():
 lines=p.read_text().splitlines();hits=[i for i,x in enumerate(lines) if 'filterPowerSupplyEvents.o:' in x or ('filterPowerSupplyEvents.c' in x and 'build' in x)]
 for i in hits:print('\n'.join(lines[max(0,i-2):i+10]))
