#!/usr/bin/env python3
"""Fifteen-minute loopback page for the single reviewed CW landscape trial."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
import json, os, time

folder=Path('/tmp/asus-landscape-trial')
folder.mkdir(mode=0o700)
HTML='''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ASUS landscape trial</title><style>
body{font:22px sans-serif;margin:24px;background:#f6f3ed;color:#143c36;touch-action:pan-y pinch-zoom}h1{font-size:32px;margin:12px 0}button,input{font:inherit;padding:16px}#targets{height:300px;position:relative;border:2px solid #adc1b9}#targets button{position:absolute;min-width:100px;min-height:64px;background:#e0ece5;border:2px solid #143c36;border-radius:12px}#tl{top:8px;left:8px}#tr{top:8px;right:8px}#bl{bottom:8px;left:8px}#br{bottom:8px;right:8px}#centre{top:50%;left:50%;transform:translate(-50%,-50%)}section{min-height:230px;padding:20px;border:2px solid #adc1b9;margin-top:24px}#live{position:fixed;bottom:0;left:0;background:#143c36;color:white;padding:6px;font:16px monospace;pointer-events:none}
</style><h1>Landscape touch trial</h1>
<p>Hold the tablet so this text is upright. Tap all five targets. Then scroll, pinch, and type <b>ok</b> below Marker 3.</p>
<div id="targets"><button id="tl">Top left</button><button id="tr">Top right</button><button id="bl">Bottom left</button><button id="br">Bottom right</button><button id="centre">Centre</button></div>
<div id="rows"></div><p id="live">Waiting for touch...</p><script>
const rows=document.getElementById('rows');for(let i=1;i<=4;i++){const s=document.createElement('section');s.innerHTML='<h2>Marker '+i+'</h2><p>Scroll and pinch this page.</p>';if(i===3)s.innerHTML+='<label>Keyboard check<br><input id="entry" placeholder="Type ok"></label><br><button id="done">Done / hide keyboard</button>';rows.appendChild(s)}
const entry=document.getElementById('entry'),done=document.getElementById('done'),hits=new Set();let maxTouches=0,pointerType='',scrollEvents=0,lastReport=0;
function report(reason){const d={reason,cornerHits:[...hits],maxTouches,pointerType,scrollY:Math.round(scrollY),scrollEvents,scale:visualViewport.scale,screenWidth:screen.width,screenHeight:screen.height,innerWidth,innerHeight,activeElement:document.activeElement.id,value:entry.value,time:Date.now()};document.getElementById('live').textContent=hits.size+'/5 targets · '+maxTouches+' contacts · scroll '+d.scrollY+' · scale '+d.scale.toFixed(2);fetch('/state',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)}).catch(()=>{})}
for(const id of ['tl','tr','bl','br','centre'])document.getElementById(id).addEventListener('pointerup',e=>{if(e.isTrusted&&e.pointerType==='touch'){hits.add(id);e.currentTarget.style.background='#b5d4c1';report('target-'+id)}});
addEventListener('touchstart',e=>{maxTouches=Math.max(maxTouches,e.touches.length);report('touchstart')},{passive:true});addEventListener('pointerdown',e=>{pointerType=e.pointerType;report('pointerdown')},{passive:true});addEventListener('scroll',()=>{scrollEvents++;if(Date.now()-lastReport>200){lastReport=Date.now();report('scroll')}},{passive:true});visualViewport.addEventListener('resize',()=>report('viewport-resize'));entry.addEventListener('input',()=>report('input'));entry.addEventListener('focus',()=>report('input-focus'));done.addEventListener('click',()=>{done.focus();report('done-click')});report('loaded');
</script>'''.encode()
state={'pid':os.getpid(),'status':'running','events':[],'latest':None}

def save():
    temporary=folder/'state.json.new';temporary.write_text(json.dumps(state)+'\n');temporary.replace(folder/'state.json')

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        if self.path=='/':body,kind=HTML,'text/html; charset=utf-8'
        elif self.path=='/state':body,kind=json.dumps(state).encode(),'application/json'
        else:self.send_error(404);return
        self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def do_POST(self):
        n=int(self.headers.get('Content-Length',0))
        if self.path!='/state' or not 0<n<8192:self.send_error(400);return
        value=json.loads(self.rfile.read(n));state['latest']=value;state['events'].append(value);state['events']=state['events'][-160:];save();self.send_response(204);self.end_headers()

server=HTTPServer(('127.0.0.1',8084),Handler);server.timeout=.5;save();deadline=time.monotonic()+900
try:
    while time.monotonic()<deadline and not (folder/'STOP').exists():server.handle_request()
finally:server.server_close();state['status']='stopped';save()
