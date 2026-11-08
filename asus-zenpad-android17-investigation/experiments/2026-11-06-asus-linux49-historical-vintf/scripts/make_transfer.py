from pathlib import Path
import base64,json
R=Path(__file__).resolve().parents[1];files={}
for p in (R/'candidate/device').rglob('*'):
 if p.is_file():files['candidate-source/'+str(p.relative_to(R/'candidate'))]=base64.b64encode(p.read_bytes()).decode()
for profile in ['p','q']:
 for p in (R/'upstream/s'/profile/'android-4.9').glob('*.decoded'):
  files['historical/'+profile+'/android-4.9/'+p.name.removesuffix('.decoded')]=base64.b64encode(p.read_bytes()).decode()
for name,source in [('kconfig_xml_fixup.py','upstream/s/tools/kconfig_xml_fixup.py.decoded'),('compatibility_matrix.4.xml','upstream/interfaces/compatibility_matrices/compatibility_matrix.4.xml.decoded')]:
 files['historical/'+name]=base64.b64encode((R/source).read_bytes()).decode()
s='''from pathlib import Path
import base64,json,hashlib
P=Path('/srv/android/asus-linux49-historical-vintf-20261106')
files='''+repr(files)+'''
pins={}
for rel,b64 in files.items():
 p=P/rel;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);b=base64.b64decode(b64);p.write_bytes(b);pins[rel]=hashlib.sha256(b).hexdigest()
assert sum(p.stat().st_size for p in P.rglob('*') if p.is_file())<256*1024*1024
print(json.dumps(pins,indent=2))
'''
(R/'scripts/transfer_candidate.py').write_text(s)
