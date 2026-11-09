set -eu
python3 - <<'PY'
from pathlib import Path
import hashlib,json,os
app=Path('/usr/lib/firefox-esr');file=app/'asus-ffmpeg61.json';d=json.loads(file.read_text())
assert d['schema']=='asus-browser-ffmpeg61-v1' and d['status']=='installed-for-bounded-trial'
events=json.loads(Path('/tmp/asus-media-trial/private-bundle-browser-events.json').read_text())
proof=[e for e in events if e['phase']=='av-muted' and e['event']=='ten-second-result'][-1]
assert proof['time']>=9 and proof['totalFrames']>=230 and proof['error'] is None
for name,sha in d['files'].items():assert hashlib.sha256((app/name).read_bytes()).hexdigest()==sha
for name,sha in d['system_before'].items():assert hashlib.sha256(Path('/usr/lib',name).read_bytes()).hexdigest()==sha
d.update(status='qualified-decoding-on-stock-3.18.35',proof={'seconds':proof['time'],'video_frames':proof['totalFrames'],'dropped_frames':proof['droppedFrames'],'utility_sandbox':'seccomp2, private library maps verified','audibility':'separate physical gate'})
temporary=file.with_suffix('.new');temporary.write_text(json.dumps(d)+'\n');temporary.chmod(0o644);temporary.replace(file);os.sync()
print('QUALIFIED_PRIVATE_DECODER_MANIFEST_PERSISTED',json.dumps(d['proof']))
PY
