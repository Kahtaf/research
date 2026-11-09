set -eu
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
app=Path('/usr/lib/firefox-esr');manifest=app/'asus-ffmpeg61.json'
d=json.loads(manifest.read_text());assert d['schema']=='asus-browser-ffmpeg61-v1'
assert set(d['files'])=={'libavcodec.so.61','libavutil.so.59'}
for name,sha in d['files'].items():
 path=app/name;assert path.is_file() and not path.is_symlink()
 assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
for name in ('libavcodec.so.61','libavutil.so.59'):(app/name).unlink()
manifest.unlink();os.sync()
print('EXACT_OWNED_PRIVATE_CODEC_FILES_REMOVED; restart owned browser to restore system selection')
PY
