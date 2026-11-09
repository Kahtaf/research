#!/usr/bin/env python3
"""Bounded loopback AAC fixture. No native PCM playback or startup route writes."""
import argparse
import array
import fcntl
import hashlib
import http.server
import json
import math
import os
from pathlib import Path
import re
import secrets
import signal
import struct
import subprocess
import sys
import time
import wave

ORIGIN = 'http://127.0.0.1:8085'
AMPS = ('Ext_Speaker_Amp_Switch', 'Speaker_Amp_Switch')
ALL_AMPS = AMPS + ('Audio_Amp_L_Switch', 'Audio_Amp_R_Switch', 'Headset_Speaker_Amp_Switch', 'Voice_Amp_Switch')

def control(name):
    result = subprocess.check_output(['amixer', '-c', '0', 'cget', 'name='+name], text=True, timeout=2)
    value = re.search(r'^\s*: values=(\d+)$', result, re.M)
    if not value:
        raise RuntimeError('Unknown mixer response')
    return int(value[1]), result

def set_control(name, value):
    subprocess.run(['amixer', '-q', '-c', '0', 'cset', 'name='+name, str(value)], check=True, timeout=2)

def off():
    errors = []
    for name in AMPS:
        try:
            set_control(name, 0)
        except Exception as error:
            errors.append(str(error))
    if errors:
        raise RuntimeError('; '.join(errors))

def identity():
    assert os.geteuid() == 0
    assert os.uname().release == '3.18.35'
    assert Path('/etc/asus-alpine-ram-release').read_text().strip() == 'asus-alpine-stock-kernel-v1'
    assert Path('/proc/asound/card0/id').read_text().strip() == 'mtsndcard'
    codecs = [p for p in Path('/proc/device-tree').rglob('compatible') if b'mediatek,mt8163-soc-codec-63xx\0' in p.read_bytes()]
    assert len(codecs) == 1
    gpio = (codecs[0].parent / 'extspkamp-gpio').read_bytes()
    assert len(gpio) == 12 and struct.unpack('>III', gpio)[1:] == (28, 0)

def proc_stamp(pid):
    return Path('/proc/%d/stat' % pid).read_text().rsplit(')', 1)[1].split()[19]

def pcm_owner(args):
    # A PID alone is insufficient: pin process start time, executable and profile.
    assert proc_stamp(args.firefox_pid) == args.firefox_start
    assert str(Path('/proc/%d/exe' % args.firefox_pid).resolve()) == args.firefox_exe
    cmd = Path('/proc/%d/cmdline' % args.firefox_pid).read_bytes().split(b'\0')
    assert args.firefox_profile.encode() in cmd
    profile_lock = Path(args.firefox_profile)/'lock'
    assert profile_lock.is_symlink() and os.readlink(profile_lock).endswith('+'+str(args.firefox_pid))
    status = Path('/proc/asound/card0/pcm0p/sub0/status').read_text()
    if status.strip() == 'closed':
        return
    match = re.search(r'^owner_pid\s*:\s*(\d+)', status, re.M)
    assert match, 'PCM owner unavailable'
    owner = int(match[1])
    thread_status = Path('/proc/%d/status' % owner).read_text()
    tgid = re.search(r'^Tgid:\s*(\d+)$', thread_status, re.M)
    assert tgid and int(tgid[1]) == args.firefox_pid, 'Unexpected PCM owner'

def build(destination):
    destination.mkdir(parents=True, exist_ok=True)
    samples = array.array('h')
    for i in range(48000*3):
        t = i/48000-1
        envelope = min(1, t/.05, (1-t)/.05) if 0 <= t < 1 else 0
        value = round(327.67*max(0, envelope)*math.sin(2*math.pi*440*t))
        samples.extend((value, value))
    if sys.byteorder != 'little':
        samples.byteswap()
    wav = destination/'signal.wav'
    with wave.open(str(wav), 'wb') as out:
        out.setparams((2, 2, 48000, 0, 'NONE', 'not compressed'))
        out.writeframes(samples.tobytes())
    ffmpeg = '/opt/homebrew/bin/ffmpeg'
    subprocess.run([ffmpeg, '-v', 'error', '-y', '-i', str(wav), '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '128k', '-movflags', '+faststart', str(destination/'sound.m4a')], check=True)
    decoded = subprocess.check_output([ffmpeg, '-v', 'error', '-i', str(destination/'sound.m4a'), '-f', 's16le', '-acodec', 'pcm_s16le', '-ar', '48000', '-ac', '2', '-'])
    values = array.array('h', decoded)
    if sys.byteorder != 'little':
        values.byteswap()
    peak = 20*math.log10(max(abs(v) for v in values)/32768)
    assert -41 <= peak <= -39, peak
    receipt = {'source': 'synthetic only', 'rate': 48000, 'channels': 2, 'duration_seconds': 3, 'tone_seconds': 1, 'frequency_hz': 440, 'fade_seconds': .05, 'source_peak_dbfs': -40, 'decoded_peak_dbfs': peak, 'physical_audibility': 'unverified', 'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (wav, destination/'sound.m4a')}}
    (destination/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt))

def route(args):
    identity()
    lock = (args.state/'route.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    stamp = args.state/'last-arm'
    now = time.monotonic()
    if stamp.exists():
        assert now-float(stamp.read_text()) >= 20, 'Route cooldown'
    stamp.write_text(str(now))
    for name in ALL_AMPS:
        assert control(name)[0] == 0, 'Route already powered'
    gain, gt = control('Audio_Speaker_PGA_gain')
    cls, ct = control('Audio_Speaker_class_Switch')
    assert "Item #1 '0Db'" in gt and "Item #1 'CLASSAB'" in ct
    pcm_owner(args)
    # Two independent guardians are detached before any route mutation. Never cancel.
    for deadline in (6, 15):
        subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'guardian', '--delay', str(deadline)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True)
    def interrupted(signum, frame):
        raise RuntimeError('Route interrupted')
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGALRM):
        signal.signal(sig, interrupted)
    signal.alarm(15)
    try:
        set_control('Audio_Speaker_PGA_gain', 1)
        set_control('Audio_Speaker_class_Switch', 1)
        set_control('Speaker_Amp_Switch', 1)
        set_control('Ext_Speaker_Amp_Switch', 1)
        assert all(control(n)[0] == 1 for n in AMPS)
        print(json.dumps({'nonce': args.nonce, 'pid': os.getpid(), 'start': proc_stamp(os.getpid()), 'armed': True}), flush=True)
        time.sleep(5)
    finally:
        off()
        assert all(control(n)[0] == 0 for n in AMPS), 'Keep the selected class until amp shutdown succeeds'
        try:
            set_control('Audio_Speaker_class_Switch', cls)
        finally:
            set_control('Audio_Speaker_PGA_gain', gain)

HTML = '''<!doctype html><meta name="viewport" content="width=device-width"><title>Browser sound trial</title>
<style>body{font:24px sans-serif;max-width:650px;margin:12vh auto;padding:24px;background:#f6f5ef;color:#222}button{font:inherit;padding:30px;width:100%}pre{font:16px monospace;white-space:pre-wrap}</style>
<h1>Browser sound trial</h1><p>Play a short, quiet tone.</p><button id="play">Play browser sound</button><p id="status">Ready</p><pre id="telemetry"></pre><audio id="sound" preload="none" src="/sound.m4a"></audio>
<script>const a=document.querySelector('#sound'), b=document.querySelector('#play'), s=document.querySelector('#status');let generation=0;
let lastReport='';function report(){const d={currentTime:a.currentTime,ended:a.ended,error:a.error?{code:a.error.code,message:a.error.message}:null,muted:a.muted,volume:a.volume,generation};const text=JSON.stringify(d);document.querySelector('#telemetry').textContent=JSON.stringify(d,null,2);if(text!==lastReport){lastReport=text;fetch('/state',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':'TOKEN'},body:text}).catch(()=>{})}}
setInterval(report,200);b.onclick=async e=>{if(!e.isTrusted)return;const g=++generation,nonce=crypto.randomUUID();b.disabled=true;s.textContent='Preparing…';try{a.pause();a.currentTime=0;a.muted=false;a.volume=1;const r=await fetch('/arm',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':'TOKEN'},body:JSON.stringify({nonce})});const j=await r.json();if(!r.ok||j.nonce!==nonce||g!==generation||!j.armed)throw Error('Sound unavailable');await a.play();s.textContent='Playing quiet tone';}catch(e){s.textContent=e.message}finally{setTimeout(()=>{b.disabled=false},20000)}};a.onended=()=>s.textContent='Finished';a.onerror=()=>{s.textContent='Sound unavailable';report()};</script>'''

def serve(args):
    identity()
    args.state.mkdir(mode=0o700, parents=True, exist_ok=True)
    assert args.state.stat().st_uid == 0 and args.state.stat().st_mode & 0o077 == 0
    server_lock = (args.state/'server.lock').open('a')
    fcntl.flock(server_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    blob = args.media.read_bytes()  # Immutable bytes for the entire server lifetime.
    assert hashlib.sha256(blob).hexdigest() == args.sha256
    token = secrets.token_urlsafe(32)
    owned = None
    last = -100.0
    state = {'pid': os.getpid(), 'status': 'running', 'latest': None, 'events': [], 'arms': 0}
    def save():
        temporary=args.state/'state.new';temporary.write_text(json.dumps(state)+'\n');temporary.replace(args.state/'state.json')
    class Handler(http.server.BaseHTTPRequestHandler):
        def send(self, code, data, kind='application/json'):
            self.send_response(code); self.send_header('Content-Type', kind); self.send_header('Content-Length', str(len(data))); self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(data)
        def do_GET(self):
            if self.headers.get('Host') != '127.0.0.1:8085':
                return self.send(403, b'{}')
            if self.path == '/':
                return self.send(200, HTML.replace('TOKEN', token).encode(), 'text/html; charset=utf-8')
            if self.path == '/sound.m4a':
                return self.send(200, blob, 'audio/mp4')
            if self.path == '/state':
                return self.send(200, json.dumps(state).encode())
            self.send(404, b'{}')
        def do_POST(self):
            nonlocal owned, last
            if self.path not in ('/arm','/state') or self.headers.get('Host') != '127.0.0.1:8085' or self.headers.get('Origin') != ORIGIN or self.headers.get('X-CSRF-Token') != token:
                return self.send(403, b'{}')
            if self.path == '/state':
                length=int(self.headers.get('Content-Length','0'))
                if not 0 < length < 2048:return self.send(400,b'{}')
                data=json.loads(self.rfile.read(length));state['latest']=data;state['events'].append(data);state['events']=state['events'][-80:];save()
                return self.send(200,b'{}')
            try:
                length = int(self.headers.get('Content-Length', '0'))
                assert 0 < length <= 200
                nonce = json.loads(self.rfile.read(length))['nonce']
                assert isinstance(nonce, str) and re.fullmatch('[a-zA-Z0-9-]{16,64}', nonce)
                assert time.monotonic()-last >= 20 and (owned is None or owned.poll() is not None)
                last = time.monotonic()
                command = [sys.executable, str(Path(__file__).resolve()), 'route', '--state', str(args.state), '--nonce', nonce, '--firefox-pid', str(args.firefox_pid), '--firefox-start', args.firefox_start, '--firefox-exe', args.firefox_exe, '--firefox-profile', args.firefox_profile]
                owned = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=sys.stderr, text=True, start_new_session=True)
                import select
                assert select.select([owned.stdout], [], [], 4)[0], 'Arm timeout'
                ack = json.loads(owned.stdout.readline())
                assert ack == {'nonce': nonce, 'pid': owned.pid, 'start': proc_stamp(owned.pid), 'armed': True} and owned.poll() is None
                state['arms']+=1;state['last_route_pid']=owned.pid;save()
                self.send(200, json.dumps(ack).encode())
            except Exception:
                if owned is not None and owned.poll() is None:
                    owned.terminate(); owned.wait(timeout=12)
                self.send(409, b'{"error":"Sound unavailable"}')
        def log_message(self, fmt, *values):
            pass
    server = http.server.HTTPServer(('127.0.0.1', 8085), Handler)
    server.timeout = .25
    save()
    def stop(signum, frame):
        raise KeyboardInterrupt
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, stop)
    end = time.monotonic()+900
    try:
        while time.monotonic() < end:
            server.handle_request()
    except KeyboardInterrupt:
        pass
    finally:
        if owned is not None:
            if owned.poll() is None:
                owned.terminate()
            owned.wait(timeout=12)
            assert all(control(n)[0] == 0 for n in AMPS)
        server.server_close()
        state['status']='stopped';save()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['build', 'serve', 'route', 'guardian'])
    parser.add_argument('--state', type=Path, default=Path('/tmp/asus-browser-sound-trial'))
    parser.add_argument('--media', type=Path)
    parser.add_argument('--sha256')
    parser.add_argument('--destination', type=Path, default=Path('artifacts/browser-sound-trial'))
    parser.add_argument('--nonce')
    parser.add_argument('--delay', type=int, choices=[6, 15])
    parser.add_argument('--firefox-pid', type=int)
    parser.add_argument('--firefox-start')
    parser.add_argument('--firefox-exe')
    parser.add_argument('--firefox-profile')
    args = parser.parse_args()
    if args.mode == 'build':
        build(args.destination)
    elif args.mode == 'guardian':
        time.sleep(args.delay)
        identity(); off()
    elif args.mode == 'route':
        route(args)
    else:
        serve(args)
