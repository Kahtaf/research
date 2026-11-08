exec(open('2026-11-06-asus-r8-continuation-kit/preparation/inspect_remote.py').read().split('script=r')[0])
r=m.run(r'''
from pathlib import Path
import shlex,json,hashlib,base64
F=Path('/srv/android/asus-reviewed-build-kit/r8-fixtures/wpa-r2');A=Path('/srv/android/lineage24')
def deps(n):return set(shlex.split((F/(n+'.d')).read_text().replace('\\\n',' ').split(':',1)[1]))-{str(F/(n+'.c'))}
before=deps('original');after=deps('candidate');assert before==after
pins=json.loads((F/'result.json').read_text())['dependency_sha256'];assert all(hashlib.sha256((Path(p) if Path(p).is_absolute() else A/p).read_bytes()).hexdigest()==pins[p] for p in after)
print(json.dumps(dict(original_and_candidate_dependency_sets_equal=True,shared_dependency_count=len(before),dependency_set_sha256=hashlib.sha256('\n'.join(sorted(before)).encode()).hexdigest(),all_recorded_dependency_hashes_still_match=True,object_base64=base64.b64encode((F/'candidate.o').read_bytes()).decode()),indent=2))
''');d=json.loads(r);import base64;Path('2026-11-06-asus-r8-continuation-kit/artifacts/wpa-sdk37-candidate.o').write_bytes(base64.b64decode(d.pop('object_base64')));Path('2026-11-06-asus-r8-continuation-kit/evidence/wpa-dependency-equality.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2))
