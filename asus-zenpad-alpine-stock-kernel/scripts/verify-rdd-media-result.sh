set -eu
python3 - <<'PY'
from pathlib import Path
import json,subprocess,time,urllib.request
folder=Path('/tmp/asus-media-trial')
for _ in range(40):
 state=json.load(urllib.request.urlopen('http://127.0.0.1:8083/state',timeout=1))
 indices=[i for i,e in enumerate(state['events']) if e['phase']=='loaded' and e['event']=='loaded']
 assert indices
 events=state['events'][indices[-1]:]
 if any(e['phase']=='av-muted' and e['event'] in ('ten-second-result','error','play-rejected') for e in events):break
 time.sleep(.5)
else:raise AssertionError('No AV result')
(folder/'rdd-browser-events.json').write_text(json.dumps(events)+'\n')
for e in events:
 if e['event'] in ('loaded','error','play-rejected','ten-second-result','ready'):print(json.dumps(e))
av=[e for e in events if e['phase']=='av-muted' and e['event']=='ten-second-result']
good=bool(av and av[-1]['time']>=9 and av[-1]['totalFrames']>0 and av[-1]['error'] is None)
print('MUTED_AV_PLAYBACK_PASS',good)
roles=[]
for p in Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:a=(p/'cmdline').read_bytes().split(b'\0')
 except FileNotFoundError:continue
 if not a or a[0]!=b'/usr/lib/firefox-esr/firefox-esr':continue
 if b'rdd' in a or b'utility' in a:
  sec=[l for l in (p/'status').read_text().splitlines() if l.startswith('Seccomp:')]
  role='rdd' if b'rdd' in a else 'utility';roles.append({'role':role,'seccomp':sec});print('DECODER_PROCESS',p.name,role,sec)
logs=(folder/'browser-debug.log').read_text(errors='replace')
errors=[line for line in logs.splitlines() if 'CRASHED_UTILITY' in line or 'CRASHED_RDD' in line or 'Decode error:' in line]
print('DECODE_ERRORS',json.dumps(errors[-5:]))
print('RDD_FFMPEG_AAC_LOG_LINES')
for line in logs.splitlines():
 if 'RDD' in line and any(s in line for s in ('audio/mp4a','FFmpegAudio','AAC','Initialising FFmpeg')):print(line[:1000])
assert good,'Compatibility policy did not prove playback; inspect and remove if decoder remains broken'
assert any(r['role']=='rdd' and r['seccomp']==['Seccomp:\t2'] for r in roles),'RDD filter not verified'
assert not errors,'Decoder error remains'
PY
