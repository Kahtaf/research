set -eu
python3 - <<'PY'
from pathlib import Path
import configparser,hashlib,json,os
stage=Path('/tmp/asus-private-ffmpeg61-stage');app=Path('/usr/lib/firefox-esr')
assert not Path('/run/asus-goodix/rotation-trial/REQUEST').exists()
assert not (app/'distribution/policies.json').exists()
config=configparser.ConfigParser();config.read(app/'application.ini');assert config['App']['Version']=='140.12.0'
assert not Path('/usr/lib/libavcodec.so.62').exists(), 'Newer preferred system codec needs a fresh review'
expected={'libavutil.so.59':'0554838b786e990a4155557fd1103c178adf54a7a143f4947917294f01e5fc36','libavcodec.so.61':'9435c2bd290a63b33d74dde2c366af9bf12bb2916ef47e637619e41caecbf96f'}
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
for name,sha in expected.items():
 target=app/name;assert not target.exists() and not target.is_symlink(), 'Refuse to replace any app file'
 assert digest(stage/name)==sha,name
 assert (stage/name).read_bytes()[:6]==b'\x7fELF\x02\x01'
 assert int.from_bytes((stage/name).read_bytes()[18:20],'little')==183
manifest=app/'asus-ffmpeg61.json';assert not manifest.exists()
system={name:digest(Path('/usr/lib')/name) for name in expected}
receipt={'schema':'asus-browser-ffmpeg61-v1','status':'installed-for-bounded-trial','source':'FFmpeg7.1.5 unpatched LGPL decoder-only','files':expected,'system_before':system,'firefox_version':config['App']['Version']}
backup=Path('/mnt/alpine-sd/2026-11-08-asus-alpine/private/firefox-before-private-ffmpeg61')
backup.mkdir(mode=0o700);(backup/'receipt.json').write_text(json.dumps(receipt)+'\n')
for name in expected:
 temporary=app/(name+'.asus-new');assert not temporary.exists()
 temporary.write_bytes((stage/name).read_bytes());temporary.chmod(0o644);temporary.replace(app/name)
manifest.write_text(json.dumps(receipt)+'\n');manifest.chmod(0o644);os.sync()
assert all(digest(app/name)==sha for name,sha in expected.items())
assert all(digest(Path('/usr/lib')/name)==sha for name,sha in system.items())
print('PRIVATE_FFMPEG61_INSTALLED_VERIFIED; exactly two new app libraries, original system hashes unchanged')
PY
