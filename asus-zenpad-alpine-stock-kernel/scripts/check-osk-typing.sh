set -eu
export DISPLAY=:0 XAUTHORITY=/run/asus-goodix/Xauthority
python3 - <<'PY'
from pathlib import Path
import json,subprocess,time,urllib.request
trial=Path('/tmp/asus-osk-trial');meta=json.loads((trial/'state.json').read_text())
assert meta['status']=='running'
assert meta['fixture']['activeElement']=='entry' and meta['fixture']['hasFocus']
subprocess.run(['xdotool','mousemove','110','1132','click','1'],check=True)
time.sleep(.7)
state=json.load(urllib.request.urlopen('http://127.0.0.1:8081/state',timeout=3))
print('AFTER_ACTUAL_ONBOARD_KEY_CLICK',json.dumps(state['fixture']))
assert state['fixture']['value']=='a' and state['fixture']['activeElement']=='entry'
def command(action):
 data=json.dumps({'action':action}).encode()
 urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8081/command',data=data,headers={'Content-Type':'application/json'}),timeout=3).read()
 time.sleep(.9)
command('done')
hidden=subprocess.run(['xdotool','search','--onlyvisible','--name','^Onboard$'],capture_output=True,text=True)
print('AFTER_NONEDITABLE_FOCUS_KEYBOARD_VISIBLE',bool(hidden.stdout.strip()))
command('focus')
visible=subprocess.run(['xdotool','search','--onlyvisible','--name','^Onboard$'],capture_output=True,text=True)
print('AFTER_INPUT_REFOCUS_KEYBOARD_VISIBLE',bool(visible.stdout.strip()))
assert hidden.returncode==1 and not hidden.stdout.strip()
assert visible.returncode==0 and visible.stdout.strip()
result={'onboard_key_delivered':'a','focus_preserved':True,'auto_hide_noneditable':True,'auto_show_input_refocus':True}
(trial/'typing-proof.json').write_text(json.dumps(result)+'\n')
print('AUTOMATIC_KEYBOARD_SOFTWARE_WORKLOAD_PASS')
PY
