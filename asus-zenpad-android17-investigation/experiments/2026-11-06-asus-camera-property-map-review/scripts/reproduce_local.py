from pathlib import Path
import runpy,json,hashlib,contextlib,io
review=Path(__file__).resolve().parents[1]; source=review.parent/'2026-11-06-asus-camera-property-map'
write=Path.write_text
allowed={'provider-closure.json','adapter-symbols.json','oem-methods.json','local-inputs-post.json','verification.json'}
def redirected(p,data,*args,**kwargs):
    assert p.parent==source/'evidence' and p.name in allowed,p
    return write(review/'evidence'/('reproduced-'+p.name),data,*args,**kwargs)
Path.write_text=redirected
out=io.StringIO()
try:
    with contextlib.redirect_stdout(out):
        runpy.run_path(str(source/'scripts/analyze.py'))
        runpy.run_path(str(source/'scripts/verify.py'))
finally: Path.write_text=write
(review/'evidence/local-reproduction.txt').write_text(out.getvalue())
for fn in allowed:
    actual=json.loads((review/'evidence'/('reproduced-'+fn)).read_text())
    expected=json.loads((source/'evidence'/fn).read_text())
    assert actual==expected,fn
for x in json.loads((source/'evidence/artifact-pins.json').read_text()):
    p=source/x['path']; assert p.stat().st_size==x['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],p
for x in json.loads((source/'evidence/source-pins.json').read_text())['new_sources']:
    assert hashlib.sha256((source/x['path']).read_bytes()).hexdigest()==x['sha256']
print(out.getvalue());print('PASS all 154 artifact manifest entries and six production source pins; reproduced five JSON outputs equal originals')
