#!/usr/bin/env python3
"""Loopback-only, fifteen-minute real-browser MP4 playback experiment."""
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path
import json, os, secrets, subprocess, time

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'state.json'
state = {'pid': os.getpid(), 'status': 'running', 'events': []}
TOKEN = secrets.token_hex(20)
last_speaker = 0
HTML = b'''<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ASUS media trial</title>
<style>body{font:24px sans-serif;margin:24px;background:#f6f3ed;color:#143c36}video{width:100%;max-width:640px;background:black}button{font:inherit;padding:20px}pre{font-size:17px;white-space:pre-wrap}</style>
<h1>Media playback trial</h1><p>Checking video decoding separately from sound.</p>
<video id="v" playsinline controls muted></video><p><button id="audio">Play quiet audio/video</button></p>
<p><button id="speaker">Play quiet speaker test</button></p><p id="speakerStatus">Speaker test uses a one-second quiet tone, then powers the route down.</p><pre id="out"></pre>
<script>
const v=document.getElementById('v'),out=document.getElementById('out');let phase='loaded',samples=[];
function report(event,extra={}){let q=v.getVideoPlaybackQuality();let d={phase,event,time:v.currentTime,duration:Number.isFinite(v.duration)?v.duration:null,readyState:v.readyState,networkState:v.networkState,paused:v.paused,ended:v.ended,muted:v.muted,width:v.videoWidth,height:v.videoHeight,totalFrames:q.totalVideoFrames,droppedFrames:q.droppedVideoFrames,error:v.error?{code:v.error.code,message:v.error.message}:null,...extra};out.textContent=JSON.stringify(d,null,2);fetch('/state',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}).catch(()=>{});return d;}
for(let e of ['loadedmetadata','playing','ended','error','waiting','stalled'])v.addEventListener(e,()=>report(e));
async function play(name,src,muted){phase=name;v.pause();v.src=src;v.muted=muted;v.volume=.15;report('start');try{await Promise.race([v.play(),new Promise((_,reject)=>setTimeout(()=>reject(new Error('play deadline')),5000))]);report('play-resolved')}catch(e){report('play-rejected',{exception:e.name+': '+e.message});return}await new Promise(r=>setTimeout(r,10000));report('ten-second-result');v.pause();}
document.getElementById('audio').onclick=()=>play('av-audible','media-with-audio.mp4',false);
document.getElementById('speaker').onclick=async()=>{const b=document.getElementById('speaker');b.disabled=true;document.getElementById('speakerStatus').textContent='Playing quiet tone...';try{const r=await fetch('/speaker',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:'@TOKEN@'})});const d=await r.json();document.getElementById('speakerStatus').textContent=d.amps_off?'Test finished; speaker route is off. Please report whether you heard the tone.':JSON.stringify(d)}catch(e){document.getElementById('speakerStatus').textContent=String(e)}setTimeout(()=>b.disabled=false,10000)};
report('loaded',{canMP4:v.canPlayType('video/mp4; codecs="avc1.42C01E"'),canAAC:v.canPlayType('audio/mp4; codecs="mp4a.40.2"')});
setInterval(()=>{if(!v.paused&&!v.error)report('progress')},1000);
(async()=>{await play('video-only','media-video-only.mp4',true);await play('av-muted','media-with-audio.mp4',true);phase='awaiting-audio-click';report('ready');document.getElementById('audio').focus()})();
</script>'''

def save():
    temporary = STATE.with_suffix('.new')
    temporary.write_text(json.dumps(state) + '\n')
    temporary.replace(STATE)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == '/':
            body, kind = HTML.replace(b'@TOKEN@',TOKEN.encode()), 'text/html; charset=utf-8'
        elif self.path == '/state':
            body, kind = json.dumps(state).encode(), 'application/json'
        elif self.path in ('/media-video-only.mp4', '/media-with-audio.mp4'):
            return super().do_GET()
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        global last_speaker
        length = int(self.headers.get('Content-Length', 0))
        if self.path not in ('/state','/speaker') or not 0 < length < 8192:
            self.send_error(400)
            return
        value = json.loads(self.rfile.read(length))
        if self.path == '/speaker':
            if self.headers.get('Origin') != 'http://127.0.0.1:8083' or value.get('token') != TOKEN or time.monotonic()-last_speaker<10:
                self.send_error(403)
                return
            last_speaker=time.monotonic()
            try:
                (ROOT/'speaker-result.json').unlink(missing_ok=True)
                result=subprocess.run(['python3',str(ROOT/'speaker-tone-trial.py')],capture_output=True,text=True,timeout=12)
                if not (ROOT/'speaker-result.json').exists():
                    raise RuntimeError('Speaker preflight refused: '+result.stderr[-500:])
                body=json.loads((ROOT/'speaker-result.json').read_text())
                body['probe_exit']=result.returncode
            except Exception as error:
                body={'error':str(error),'amps_off':False}
            state['speaker']=body
            save()
            encoded=json.dumps(body).encode()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(encoded)))
            self.end_headers();self.wfile.write(encoded)
            return
        state['events'].append(value)
        state['events'] = state['events'][-120:]
        save()
        self.send_response(204)
        self.end_headers()

server = HTTPServer(('127.0.0.1', 8083), Handler)
server.timeout = .5
save()
deadline = time.monotonic() + 900
try:
    while time.monotonic() < deadline and not (ROOT / 'STOP').exists():
        server.handle_request()
finally:
    server.server_close()
    state['status'] = 'stopped'
    save()
