set -eu
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,shutil,subprocess
source=Path('/var/tmp/asus-jwm-build.EdgPCC/asus-jwm')
expected='789dbb085e8485ff69b177cd8da8c4effe75028dfcdbf1cd4119a0959c910bc6'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)==expected
old=sha(Path('/usr/bin/jwm'))
dest=Path('/usr/local/bin/asus-jwm');assert not dest.exists()
with dest.open('xb') as f:f.write(source.read_bytes());f.flush();os.fsync(f.fileno())
dest.chmod(0o755);assert sha(dest)==expected
doc=Path('/usr/local/share/doc/asus-jwm');doc.mkdir(parents=True)
for name in ('LICENSE.jwm','jwm-workarea.patch'):shutil.copyfile(source.parent/name,doc/name)
version=subprocess.check_output([str(dest),'-v'],text=True)
assert 'JWM v2.4.6' in version
receipt={'status':'COMPILED_ON_TABLET_AND_STAGED_INERT','binary_sha256':expected,'packaged_jwm_sha256':old,'version':version,'build_directory':str(source.parent),'patch_sha256':sha(doc/'jwm-workarea.patch')}
Path('/run/asus-goodix/jwm-build-receipt.json').write_text(json.dumps(receipt)+'\n')
assert sha(Path('/usr/bin/jwm'))==old
print(json.dumps(receipt))
PY
apk del .asus-jwm-build
/usr/local/bin/asus-jwm -v
df -h /
