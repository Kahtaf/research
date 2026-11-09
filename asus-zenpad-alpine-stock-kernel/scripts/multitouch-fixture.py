#!/usr/bin/env python3
"""Bounded browser page recording real touch, scrolling, zoom and typing."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
import json,os,time
folder=Path('/tmp/asus-multitouch-trial');folder.mkdir(mode=0o700)
HTML='''<!doctype html><html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ASUS native touch trial</title>
<style>body{font:24px sans-serif;margin:28px;background:#f6f3ed;color:#143c36;touch-action:pan-y pinch-zoom}h1{font-size:38px}section{padding:24px;margin:24px 0;border:2px solid #adc1b9;min-height:220px}input,button{font:inherit;padding:18px}input{max-width:90%}#live{position:fixed;bottom:0;left:0;background:#143c36;color:white;font:16px monospace;padding:8px;pointer-events:none}</style>
<h1>Native touch trial</h1><p>Swipe upward with one finger. Pinch with two fingers to zoom. The typing box is below marker 3.</p>
<div id="rows"></div><p id="live">Waiting for touch...</p><script>
const rows=document.getElementById('rows');for(let i=1;i<=6;i++){const s=document.createElement('section');s.innerHTML='<h2>Marker '+i+'</h2><p>Use a finger to move through the page.</p>';if(i===3)s.innerHTML+='<label>Keyboard check<br><input id="entry" placeholder="Type ok"></label><br><button id="done">Done / hide keyboard</button>';rows.appendChild(s)}
const entry=document.getElementById('entry'),done=document.getElementById('done');let maxTouches=0,pointerType='',scrollEvents=0,zoomEvents=0,lastReport=0;
function report(reason){const data={reason,maxTouchPoints:navigator.maxTouchPoints,maxTouches,pointerType,scrollY:Math.round(scrollY),scrollEvents,zoomEvents,scale:visualViewport?visualViewport.scale:1,devicePixelRatio,innerWidth,activeElement:document.activeElement.id,value:entry.value,time:Date.now()};document.getElementById('live').textContent='touches '+maxTouches+' · scroll '+data.scrollY+' · scale '+data.scale.toFixed(2);fetch('/state',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).catch(()=>{})}
addEventListener('touchstart',e=>{maxTouches=Math.max(maxTouches,e.touches.length);report('touchstart')},{passive:true});addEventListener('pointerdown',e=>{pointerType=e.pointerType;report('pointerdown')},{passive:true});addEventListener('scroll',()=>{scrollEvents++;if(Date.now()-lastReport>200){lastReport=Date.now();report('scroll')}},{passive:true});if(visualViewport)visualViewport.addEventListener('resize',()=>{zoomEvents++;report('viewport-resize')});entry.addEventListener('input',()=>report('input'));entry.addEventListener('focus',()=>report('input-focus'));done.addEventListener('click',()=>{done.focus();report('done-click')});report('loaded');
</script></html>'''.encode()
state={'pid':os.getpid(),'status':'running','events':[],'latest':None}
def save():
 p=folder/'state.json.new';p.write_text(json.dumps(state)+'\n');p.replace(folder/'state.json')
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path=='/':body=HTML;kind='text/html; charset=utf-8'
  elif self.path=='/state':body=json.dumps(state).encode();kind='application/json'
  else:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def do_POST(self):
  n=int(self.headers.get('Content-Length','0'))
  if self.path!='/state' or not 0<n<8192:self.send_error(400);return
  value=json.loads(self.rfile.read(n));state['latest']=value;state['events'].append(value);state['events']=state['events'][-80:];save();self.send_response(204);self.end_headers()
server=HTTPServer(('127.0.0.1',8082),Handler);server.timeout=.5;save();deadline=time.monotonic()+900
try:
 while time.monotonic()<deadline and not (folder/'STOP').exists():server.handle_request()
finally:server.server_close();state['status']='stopped';save()
