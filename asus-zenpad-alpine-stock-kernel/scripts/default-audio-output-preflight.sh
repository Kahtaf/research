set -eu
python3 - <<'PY'
from pathlib import Path
import json,re,subprocess,time,wave
assert Path('/proc/asound/card0/pcm0p/sub0/status').read_text().strip()=='closed'
for name in ('Ext_Speaker_Amp_Switch','Speaker_Amp_Switch'):
 assert ': values=0' in subprocess.check_output(['amixer','-c','0','cget','name='+name],text=True)
folder=Path('/tmp/asus-default-audio-preflight');folder.mkdir(mode=0o700)
with wave.open(str(folder/'silence.wav'),'wb') as w:
 w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000);w.writeframes(bytes(48000*2*2))
with (folder/'aplay.log').open('wb') as log:
 player=subprocess.Popen(['aplay','-q','-D','default',str(folder/'silence.wav')],stdout=log,stderr=subprocess.STDOUT)
 actual=False;params=''
 try:
  deadline=time.monotonic()+2
  while time.monotonic()<deadline and player.poll() is None:
   if 'state: RUNNING' in Path('/proc/asound/card0/pcm0p/sub0/status').read_text():
    actual=True;params=Path('/proc/asound/card0/pcm0p/sub0/hw_params').read_text()
   time.sleep(.02)
  result=player.wait(timeout=3)
 finally:
  if player.poll() is None:player.terminate();player.wait(timeout=2)
print(json.dumps({'aplay_exit':result,'default_reached_pcm0':actual,'actual_hw_params':params,'output':(folder/'aplay.log').read_text()}))
for name in ('Ext_Speaker_Amp_Switch','Speaker_Amp_Switch'):
 assert ': values=0' in subprocess.check_output(['amixer','-c','0','cget','name='+name],text=True)
assert Path('/proc/asound/card0/pcm0p/sub0/status').read_text().strip()=='closed'
print('SILENCE_ONLY_PREFLIGHT_COMPLETE; amp gates remain off, PCM closed')
PY
