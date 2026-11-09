#!/usr/bin/env python3
"""A bounded, local real-browser workload; reports only browser capabilities."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import argparse,base64,json,threading
p=argparse.ArgumentParser();p.add_argument('--nonce',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();completed=threading.Event()
HTML='''<!doctype html><meta charset="utf-8"><title>Browser workload running</title><style>body{font:24px sans-serif;margin:36px;background:#f4f3ed;color:#143c36}h1{font-size:38px}canvas{border:1px solid #98a8a0}pre{white-space:pre-wrap}</style><h1 id="status">Checking browser…</h1><canvas id="paint" width="400" height="100"></canvas><pre id="results"></pre><img src="/wait" width="1" height="1" alt=""><script>
(async()=>{
const result={};
try {
 result.modernJavaScript=({value:{answer:42}})?.value?.answer===42;
 const data=await fetch('/api').then(r=>r.json());result.fetch=data.answer===42;
 const c=document.getElementById('paint').getContext('2d');c.fillStyle='#174d46';c.fillRect(0,0,400,100);c.fillStyle='white';c.font='26px sans-serif';c.fillText('Firefox on stock Linux',30,60);result.canvas=c.getImageData(1,1,1,1).data[0]===23;
 localStorage.setItem('asus-browser-check','42');result.localStorage=localStorage.getItem('asus-browser-check')==='42';
 const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('asus-browser-check',1);r.onupgradeneeded=()=>r.result.createObjectStore('data');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});
 await new Promise((resolve,reject)=>{const t=db.transaction('data','readwrite');t.objectStore('data').put(42,'answer');t.oncomplete=resolve;t.onerror=()=>reject(t.error);});
 result.indexedDB=await new Promise((resolve,reject)=>{const r=db.transaction('data').objectStore('data').get('answer');r.onsuccess=()=>resolve(r.result===42);r.onerror=()=>reject(r.error);});db.close();
 result.passed=Object.values(result).every(v=>v===true);
} catch(e){result.passed=false;result.error=String(e);}
result.userAgent=navigator.userAgent;document.getElementById('status').textContent=result.passed?'Browser workload passed':'Browser workload failed';document.title=result.passed?'ASUS browser workload PASS':'ASUS browser workload FAIL';document.getElementById('results').textContent=JSON.stringify(result,null,2);
await fetch('/proof',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nonce:NONCE,...result})});
})();</script>'''.replace('NONCE',json.dumps(a.nonce))
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path=='/wait':
   completed.wait(15);body=base64.b64decode('R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==');kind='image/gif'
  elif self.path=='/api':body=b'{"answer":42}';kind='application/json' 
  else:body=HTML.encode();kind='text/html; charset=utf-8'
  self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def do_POST(self):
  assert self.path=='/proof'
  n=int(self.headers['Content-Length']);assert 0<n<4096
  result=json.loads(self.rfile.read(n));assert result.pop('nonce')==a.nonce
  a.output.write_text(json.dumps(result,indent=2)+'\n');completed.set();self.send_response(204);self.end_headers()
ThreadingHTTPServer(('127.0.0.1',8081),Handler).serve_forever()
