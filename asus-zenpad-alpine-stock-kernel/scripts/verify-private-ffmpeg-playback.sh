set -eu
python3 - <<'PY'
from pathlib import Path
import hashlib,json,time,urllib.request
folder=Path('/tmp/asus-media-trial')
for _ in range(40):
 state=json.load(urllib.request.urlopen('http://127.0.0.1:8083/state',timeout=1));events=state['events']
 loaded=[i for i,e in enumerate(events) if e['event']=='loaded' and e['phase']=='loaded'];assert loaded
 events=events[loaded[-1]:]
 if any(e['phase']=='av-muted' and e['event'] in ('ten-second-result','error','play-rejected') for e in events):break
 time.sleep(.5)
else:raise AssertionError('No fresh AV result')
for e in events:
 if e['event'] in ('loaded','error','play-rejected','ten-second-result','ready'):print(json.dumps(e))
(folder/'private-bundle-browser-events.json').write_text(json.dumps(events)+'\n')
av=[e for e in events if e['phase']=='av-muted' and e['event']=='ten-second-result']
assert av and av[-1]['time']>=9 and av[-1]['totalFrames']>=230 and av[-1]['error'] is None,'Real muted A/V playback did not pass'
utilities=[]
for process in Path('/proc').iterdir():
 if not process.name.isdecimal():continue
 try:args=(process/'cmdline').read_bytes().split(b'\0')
 except FileNotFoundError:continue
 if args and args[0]==b'/usr/lib/firefox-esr/firefox-esr' and b'utility' in args:
  maps=(process/'maps').read_text();status=(process/'status').read_text()
  if '/usr/lib/firefox-esr/libavcodec.so.61' not in maps:continue
  assert 'Seccomp:\t2' in status
  assert '/usr/lib/firefox-esr/libavutil.so.59' in maps
  assert '/usr/lib/libavcodec.so.61' not in maps and '/usr/lib/libavutil.so.59' not in maps
  assert not any(name in maps for name in ('libgomp','libnuma','libjxl_cms','libsoxr','libx265'))
  (folder/('utility-'+process.name+'.maps')).write_text(maps)
  utilities.append(int(process.name))
assert utilities,'Live isolated utility decoder with private libraries not proved'
log=(folder/'browser-debug.log').read_text(errors='replace')
assert 'CRASHED_UTILITY' not in log and 'CRASHED_RDD' not in log and 'Decode error:' not in log
lines=[line for line in log.splitlines() if 'Utility' in line and any(s in line for s in ('FFmpegAudio','audio/mp4a','AAC'))]
assert lines,'No utility audio decoder evidence'
for line in lines[-12:]:print(line[:1200])
manifest=json.loads(Path('/usr/lib/firefox-esr/asus-ffmpeg61.json').read_text())
for name,sha in manifest['system_before'].items():assert hashlib.sha256(Path('/usr/lib',name).read_bytes()).hexdigest()==sha
print('REAL_AV_UTILITY_SANDBOX_PASS',json.dumps({'utility_pids':utilities,'seccomp':2,'private_libs_confirmed':True,'system_libs_unchanged':True,'result':av[-1]}))
PY
