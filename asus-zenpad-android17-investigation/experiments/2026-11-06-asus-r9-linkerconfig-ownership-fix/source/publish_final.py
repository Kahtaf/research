from pathlib import Path
import base64,hashlib,json,subprocess
from remote import BASE
R=Path(__file__).resolve().parents[1]
names=['README.md','REPORT.md','RUNTIME-ADDENDUM.md','HANDOFF.json','candidate/manifest.json','evidence/qualification-final.json','evidence/provider-ownership.html','source/qualify_final.py','source/finalize_docs.py']
files={n:{'base64':base64.b64encode((R/n).read_bytes()).decode(),'sha256':hashlib.sha256((R/n).read_bytes()).hexdigest()} for n in names}
pub=json.loads((R/'evidence/frozen-handoff-publication.json').read_text())
code='''from pathlib import Path
import base64,hashlib,json,os,datetime
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106')
os.environ['TMPDIR']=str(R/'tmp')
files=PAYLOAD
pub=PUB
for n,k in [('REPORT.md','report_sha256'),('namespace.patch','patch_sha256'),('pins.json','pins_sha256')]:
 assert hashlib.sha256((R/'frozen-namespace-handoff-v1'/n).read_bytes()).hexdigest()==pub[k]
for n,v in files.items():
 p=R/n
 assert p.is_relative_to(R) and '..' not in p.parts and 'frozen-namespace-handoff-v1' not in p.parts
 b=base64.b64decode(v['base64']);assert hashlib.sha256(b).hexdigest()==v['sha256']
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256']
logical=allocated=0
for p in R.rglob('*'):
 if p.is_symlink() or not p.is_file():continue
 st=p.stat();logical+=st.st_size;allocated+=st.st_blocks*512
budget=2415919104
assert logical<budget
result=dict(published_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),remote_prefix=str(R),files={n:v['sha256'] for n,v in files.items()},frozen_handoff_unchanged=True,owned_logical_bytes=logical,owned_allocated_bytes=allocated,budget_bytes=budget,no_active_source_or_out_writes=True)
(R/'evidence/final-publication.json').write_text(json.dumps(result,indent=2)+'\\n')
print(json.dumps(result))
'''.replace('PAYLOAD',repr(files)).replace('PUB',repr(pub))
r=subprocess.run(BASE+['python3 -'],input=code.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
if r.stderr: print(r.stderr.decode())
assert r.returncode==0,r.returncode
result=json.loads(r.stdout)
(R/'evidence/final-publication.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
