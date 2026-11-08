from pathlib import Path
import json,hashlib,subprocess as s
A=Path('/srv/android/lineage24');src=A/'hardware/interfaces/health/utils/libhealthloop/filterPowerSupplyEvents.c';print('SOURCE',hashlib.sha256(src.read_bytes()).hexdigest())
R=Path('/srv/android/asus-root-enabled-incremental-r1/host-r2/validation');d=json.loads((R/'r8-product-provenance.json').read_text())
for cohort in d['compiler_outputs']:
 if 'filterPowerSupplyEvents' in json.dumps(cohort):print('COMPILER',json.dumps(cohort)[:21000])
for r in ['/srv/android/asus-sdk37-platform-bpf-startup-20261106/inputs','/srv/android/asus-network-runtime/artifacts']:
 print('FILES',r,[p.name for p in Path(r).iterdir()])
