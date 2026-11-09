#!/usr/bin/env python3
"""One unmuted ten-second playback check; caller must keep both amps off."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import argparse
import hashlib
import json
import os
import secrets
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--media', type=Path, required=True)
parser.add_argument('--sha256', required=True)
args = parser.parse_args()
media = args.media.read_bytes()
assert hashlib.sha256(media).hexdigest() == args.sha256
root = Path('/run/asus-browser-rw-audio')
root.mkdir(mode=0o700)
token = secrets.token_hex(20)
origin = 'http://127.0.0.1:8087'
state = {'pid': os.getpid(), 'status': 'running', 'events': []}
page = '''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ASUS browser audio routing check</title>
<style>body{font:24px sans-serif;margin:24px;background:#f6f3ed;color:#143c36}video{width:100%;max-width:640px}button{font:inherit;padding:20px}pre{font-size:17px;white-space:pre-wrap}</style>
<h1>Browser audio routing check</h1><p>The speaker route stays off during this check.</p>
<video id="v" playsinline controls src="/fixture.mp4"></video>
<p><button id="go">Run silent routing check</button></p><pre id="out"></pre>
<script>
const v=document.getElementById('v'),go=document.getElementById('go');let started=false;
function report(event,extra={}){const q=v.getVideoPlaybackQuality();const d={event,time:v.currentTime,paused:v.paused,muted:v.muted,volume:v.volume,totalFrames:q.totalVideoFrames,droppedFrames:q.droppedVideoFrames,error:v.error?{code:v.error.code,message:v.error.message}:null,...extra};document.getElementById('out').textContent=JSON.stringify(d,null,2);fetch('/state',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:'@TOKEN@',...d})}).catch(()=>{})}
v.muted=false;v.volume=.05;
v.addEventListener('error',()=>report('error'));
v.addEventListener('playing',()=>report('playing'));
go.onclick=async e=>{if(started||!e.isTrusted)return;started=true;go.disabled=true;report('trusted-play');try{await v.play();report('play-resolved');setTimeout(()=>{v.pause();report('result')},10000)}catch(e){report('play-rejected',{message:String(e)})}};
setInterval(()=>{if(started&&!v.paused)report('progress')},500);
setTimeout(()=>{v.pause();go.disabled=true;report('expired')},240000);
report('ready');go.focus();
</script>'''.replace('@TOKEN@', token).encode()


def save():
    temporary = root/'state.new'
    temporary.write_text(json.dumps(state)+'\n')
    temporary.replace(root/'state.json')


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, body, kind):
        self.send_response(200)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/':
            self.reply(page, 'text/html; charset=utf-8')
        elif self.path == '/fixture.mp4':
            self.reply(media, 'video/mp4')
        elif self.path == '/state':
            self.reply(json.dumps(state).encode(), 'application/json')
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', '0'))
        if self.path != '/state' or self.headers.get('Origin') != origin or not 0 < length < 8192:
            self.send_error(403)
            return
        value = json.loads(self.rfile.read(length))
        if value.pop('token', None) != token:
            self.send_error(403)
            return
        state['events'].append(value)
        state['events'] = state['events'][-100:]
        save()
        self.reply(b'{}', 'application/json')


save()
server = HTTPServer(('127.0.0.1', 8087), Handler)
server.timeout = .25
deadline = time.monotonic()+300
try:
    while time.monotonic() < deadline and not (root/'STOP').exists():
        server.handle_request()
finally:
    server.server_close()
    state['status'] = 'stopped'
    save()
