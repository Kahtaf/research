#!/usr/bin/env python3
"""Immutable quiet AAC playback only; the separate prototype owns route gates."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import argparse
import hashlib
import json
import os
import secrets
import time

EXPECTED = '2b304ffa302593d2bd2df9f0164f59ceba408f777247ce78a7d41a3cd0fe8888'
ORIGIN = 'http://127.0.0.1:8088'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--media', type=Path, required=True)
parser.add_argument('--state', type=Path, required=True)
args = parser.parse_args()
blob = args.media.read_bytes()
assert hashlib.sha256(blob).hexdigest() == EXPECTED
args.state.mkdir(mode=0o700)
token = secrets.token_hex(20)
state = {'pid': os.getpid(), 'status': 'running', 'events': []}
HTML = '''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ASUS speaker lifecycle software check</title>
<style>body{font:24px sans-serif;margin:24px;background:#f6f3ed;color:#143c36}button{font:inherit;padding:24px}pre{font-size:17px;white-space:pre-wrap}</style>
<h1>Speaker lifecycle software check</h1><p>No tapping or device handling is needed.</p>
<button id="play">Play quiet three-second fixture</button><pre id="out"></pre>
<audio id="a" preload="none" src="/sound.m4a"></audio>
<script>
const a=document.getElementById('a'),b=document.getElementById('play');let episode=0;
a.muted=false;a.volume=.05;
function report(event,extra={}){const d={event,episode,time:a.currentTime,paused:a.paused,ended:a.ended,muted:a.muted,volume:a.volume,error:a.error?{code:a.error.code,message:a.error.message}:null,...extra};document.getElementById('out').textContent=JSON.stringify(d,null,2);fetch('/state',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:'@TOKEN@',...d})}).catch(()=>{})}
b.onclick=async e=>{if(!e.isTrusted||b.disabled)return;b.disabled=true;episode++;a.currentTime=0;report('trusted-play');try{await a.play();report('play-resolved')}catch(e){report('play-rejected',{message:String(e)});b.disabled=false}};
a.onplaying=()=>report('playing');a.onended=()=>{a.pause();report('ended');b.disabled=false;b.focus()};a.onerror=()=>report('error');
setInterval(()=>{if(!a.paused)report('progress')},100);setTimeout(()=>{a.pause();b.disabled=true;report('expired')},170000);report('ready');b.focus();
</script>'''.replace('@TOKEN@', token).encode()


def save():
    temporary = args.state/'state.new'
    temporary.write_text(json.dumps(state)+'\n')
    temporary.replace(args.state/'state.json')


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
            self.reply(HTML, 'text/html; charset=utf-8')
        elif self.path == '/sound.m4a':
            self.reply(blob, 'audio/mp4')
        elif self.path == '/state':
            self.reply(json.dumps(state).encode(), 'application/json')
        else:
            self.send_error(404)

    def do_POST(self):
        size = int(self.headers.get('Content-Length', '0'))
        if self.path != '/state' or self.headers.get('Origin') != ORIGIN or not 0 < size < 8192:
            self.send_error(403)
            return
        event = json.loads(self.rfile.read(size))
        if event.pop('token', None) != token:
            self.send_error(403)
            return
        event['server_monotonic'] = time.monotonic()
        state['events'].append(event)
        state['events'] = state['events'][-150:]
        save()
        self.reply(b'{}', 'application/json')


save()
server = HTTPServer(('127.0.0.1', 8088), Handler)
server.timeout = .2
deadline = time.monotonic()+180
try:
    while time.monotonic() < deadline and not (args.state/'STOP').exists():
        server.handle_request()
finally:
    server.server_close()
    state['status'] = 'stopped'
    save()
