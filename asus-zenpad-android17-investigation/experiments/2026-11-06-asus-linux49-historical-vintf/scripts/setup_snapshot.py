from pathlib import Path
import shutil,json,hashlib,base64
O=Path('/srv/android/asus-linux49-vintf-port-20261106');P=Path('/srv/android/asus-linux49-historical-vintf-20261106')
assert not P.exists();P.mkdir()
shutil.copytree(O/'baseline',P/'baseline');shutil.copytree(O/'inputs',P/'inputs')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
oldpins={str(p):h(p) for sub in ['baseline','inputs'] for p in (O/sub).rglob('*') if p.is_file()}
(P/'evidence').mkdir();(P/'evidence/frozen-before.json').write_text(json.dumps(oldpins,indent=2))
sources={}
for f in ['device/asus/p00a/device.mk','device/asus/p00a/manifest.xml','device/asus/p00a/BoardConfig.mk','device/asus/p00a/Android.bp']:
 p=Path('/srv/android/lineage24')/f;b=p.read_bytes();sources[f]={'sha256':h(p),'base64':base64.b64encode(b).decode()}
metadata={str(p.relative_to(P/'baseline')):{'sha256':h(p),'base64':base64.b64encode(p.read_bytes()).decode()} for p in (P/'baseline').rglob('*') if p.is_file()}
print(json.dumps({'sources':sources,'metadata':metadata,'oldpins':oldpins,'bytes':sum(p.stat().st_size for p in P.rglob('*') if p.is_file())}))
