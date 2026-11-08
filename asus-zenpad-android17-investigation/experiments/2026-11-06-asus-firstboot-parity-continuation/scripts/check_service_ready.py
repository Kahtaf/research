"""Read-only prerequisite recheck; does not build or start services."""
from pathlib import Path
import json,sys
R=Path('/srv/android/asus-firstboot-parity-continuation');T=Path('/srv/android/lineage24')
records=json.loads((R/'evidence/services-current.json').read_text())['records'];unready=False
for r in records:
 for e in r['edges']:
  output=e['output']; missing=[x for x in e['edge'].split()[3:] if x.startswith(('out/','prebuilts/')) and not (T/x).is_file()]
  ready=(T/output).is_file() and not missing;unready |= not ready
  print(json.dumps({'module':r['module'],'variant':r['variant'],'output':output,'output_exists':(T/output).is_file(),'missing':missing,'link_inputs_ready':ready}))
sys.exit(2 if unready else 0)
