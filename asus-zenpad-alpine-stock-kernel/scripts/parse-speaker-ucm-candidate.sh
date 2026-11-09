set -eu
python3 - <<'PY'
from pathlib import Path
import json,re,subprocess
assert Path('/proc/asound/card0/id').read_text().strip()=='mtsndcard'
assert Path('/proc/asound/card0/pcm0p/sub0/status').read_text().strip()=='closed'
def controls():
 values={}
 for name in ('Audio_Speaker_PGA_gain','Audio_Speaker_class_Switch','Ext_Speaker_Amp_Switch','Speaker_Amp_Switch'):
  output=subprocess.check_output(['amixer','-c','0','cget','name='+name],text=True)
  match=re.search(r'^\s*: values=(\d+)$',output,re.M);assert match
  values[name]=int(match[1])
 return values
before=controls();assert before['Ext_Speaker_Amp_Switch']==before['Speaker_Amp_Switch']==0
root=Path('/tmp/asus-ucm-candidate/ucm2')
for file in root.rglob('*.conf'):
 assert not file.is_symlink()
 assert 'BootSequence' not in file.read_text(), 'No automatic boot sequence in this parser test'
env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','HOME':'/root','ALSA_CONFIG_UCM2':str(root)}
queries=[(['list','_verbs'],'HiFi'),(['list','_devices/HiFi'],'Speaker'),(['get','=PlaybackPCM/Speaker/HiFi'],'hw:0,0'),(['get','=PlaybackRate/Speaker/HiFi'],'48000'),(['get','=PlaybackChannels/Speaker/HiFi'],'2')]
results=[]
for query,expected in queries:
 result=subprocess.run(['alsaucm','-c','hw:0']+query,env=env,capture_output=True,text=True,timeout=5)
 print('UCM_QUERY',query,'EXIT',result.returncode);print(result.stdout);print(result.stderr)
 results.append(result.returncode==0 and expected in result.stdout)
 if result.returncode!=0:break
after=controls();print('MIXER_BEFORE',json.dumps(before));print('MIXER_AFTER',json.dumps(after))
assert before==after,'Parser changed mixer state'
assert len(results)==len(queries) and all(results),'UCM discovery/parser gate failed'
print('UCM_PARSER_AND_DISCOVERY_PASS; no verb or device selected, mixer state unchanged')
PY
