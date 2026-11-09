#!/usr/bin/env python3
"""One stock-route, -40 dBFS speaker probe; always return both amp gates off."""
from pathlib import Path
import array, fcntl, json, math, os, re, signal, struct, subprocess, time, wave

ROOT = Path('/tmp/asus-media-trial')
assert os.geteuid() == 0
assert Path('/etc/asus-alpine-ram-release').read_text().strip() == 'asus-alpine-stock-kernel-v1'
assert os.uname().release == '3.18.35'
lock = (ROOT / 'speaker.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

def control(name):
    result = subprocess.check_output(['amixer', '-c', '0', 'cget', 'name='+name], text=True, timeout=2)
    value = re.search(r'^\s*: values=(\d+)$', result, re.M)
    assert value, result
    return int(value[1]), result

def set_control(name, value):
    subprocess.run(['amixer', '-q', '-c', '0', 'cset', 'name='+name, str(value)], check=True, timeout=2)

for name in ('Speaker_Amp_Switch','Ext_Speaker_Amp_Switch','Audio_Amp_L_Switch','Audio_Amp_R_Switch','Headset_Speaker_Amp_Switch','Voice_Amp_Switch'):
    assert control(name)[0] == 0, 'Route is already powered: '+name
gain, gain_text = control('Audio_Speaker_PGA_gain')
speaker_class, class_text = control('Audio_Speaker_class_Switch')
assert "Item #1 '0Db'" in gain_text and "Item #1 'CLASSAB'" in class_text
# These controls exist only in CONFIG_MTK_SPEAKER's original driver branch.
# Loaded OF codec GPIO must match the direct-gate branch, not board pinctrl24.
codecs = [p for p in Path('/proc/device-tree').rglob('compatible') if b'mediatek,mt8163-soc-codec-63xx\0' in p.read_bytes()]
assert len(codecs) == 1
gpio = (codecs[0].parent / 'extspkamp-gpio').read_bytes()
assert len(gpio) == 12 and struct.unpack('>III', gpio)[1:] == (28, 0)
assert Path('/proc/asound/card0/pcm0p/sub0/status').read_text().strip() == 'closed'

samples = array.array('h')
for i in range(48000*3):
    t = i/48000-1
    envelope = min(1, t/.05, (1-t)/.05) if 0 <= t < 1 else 0
    value = round(327.67*max(0,envelope)*math.sin(2*math.pi*440*t))
    samples.extend((value,value))
assert max(abs(v) for v in samples) <= 328
wav = ROOT / 'speaker-minus40.wav'
with wave.open(str(wav), 'wb') as output:
    output.setnchannels(2); output.setsampwidth(2); output.setframerate(48000)
    output.writeframes(samples.tobytes())

def interrupted(signum, frame):
    raise RuntimeError('Interrupted '+str(signum))
for sig in (signal.SIGTERM,signal.SIGHUP,signal.SIGINT):
    signal.signal(sig, interrupted)

player = None
# Independent deadline survives loss of the SSH session or probe process.
guardian = subprocess.Popen(['/bin/sh','-c',
    'sleep 6; amixer -q -c 0 cset name=Ext_Speaker_Amp_Switch 0; amixer -q -c 0 cset name=Speaker_Amp_Switch 0'],
    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
result = {'status':'not-started','rate':48000,'channels':2,'tone_seconds':1,'tone_peak_dbfs':-40,'speaker_gpio':28}
try:
    set_control('Audio_Speaker_PGA_gain',1)
    set_control('Audio_Speaker_class_Switch',1)
    with (ROOT/'speaker-aplay.log').open('wb') as log:
        player = subprocess.Popen(['aplay','-q','-D','hw:0,0',str(wav)],stdout=log,stderr=subprocess.STDOUT)
        deadline=time.monotonic()+1
        while time.monotonic()<deadline:
            assert player.poll() is None, 'PCM playback failed before route enable'
            if 'state: RUNNING' in Path('/proc/asound/card0/pcm0p/sub0/status').read_text():break
            time.sleep(.01)
        else:raise AssertionError('PCM never reached RUNNING')
        result['hw_params']=Path('/proc/asound/card0/pcm0p/sub0/hw_params').read_text()
        set_control('Speaker_Amp_Switch',1)
        set_control('Ext_Speaker_Amp_Switch',1)
        time.sleep(.03)
        assert control('Speaker_Amp_Switch')[0] == control('Ext_Speaker_Amp_Switch')[0] == 1
        assert player.wait(timeout=4) == 0, 'aplay failed'
        result['status']='PCM_COMPLETED_PHYSICAL_AUDIBILITY_UNVERIFIED'
finally:
    # Do not use the misleading gain enum named Mute: the driver clamps it to0dB.
    errors=[]
    for name in ('Ext_Speaker_Amp_Switch','Speaker_Amp_Switch'):
        try:set_control(name,0)
        except Exception as error:errors.append(str(error))
    if player is not None and player.poll() is None:
        player.terminate();player.wait(timeout=2)
    for name,value in (('Audio_Speaker_class_Switch',speaker_class),('Audio_Speaker_PGA_gain',gain)):
        try:set_control(name,value)
        except Exception as error:errors.append(str(error))
    result['cleanup_errors']=errors
    result['amps_off']=all(control(n)[0] == 0 for n in ('Ext_Speaker_Amp_Switch','Speaker_Amp_Switch'))
    (ROOT/'speaker-result.json').write_text(json.dumps(result)+'\n')
    print(json.dumps(result),flush=True)
    # Keep the independent guardian armed until its fixed six-second deadline.
    if errors:raise RuntimeError('Audio cleanup needs attention: '+str(errors))
