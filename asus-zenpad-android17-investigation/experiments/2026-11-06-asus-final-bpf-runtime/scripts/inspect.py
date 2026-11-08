from pathlib import Path
import json
R=Path('/srv/android/asus-root-enabled-incremental-r1/host-r2/validation');d=json.loads((R/'r8-product-provenance.json').read_text())
for k in ['bpf_classification','payloads','apex_archives','compiler_outputs','link_outputs']:
 v=d[k]; print(k, json.dumps(v)[:16000] if k in ['bpf_classification'] else (str(type(v))+ ' '+str(v)[:1300]))
print('APEX', [str(p.relative_to(R/'apex')) for p in (R/'apex').iterdir()])
for root in ['/srv/android/asus-network-runtime/source','/srv/android/asus-sdk37-platform-bpf-startup-20261106/source']:
 p=Path(root);print('SOURCE',root,[x.name for x in p.iterdir() if 'init' in x.name or 'probe' in x.name])
print('INIT_SOURCE',Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106/source/fixture_init_r2.c').read_text() if Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106/source/fixture_init_r2.c').exists() else 'absent')
