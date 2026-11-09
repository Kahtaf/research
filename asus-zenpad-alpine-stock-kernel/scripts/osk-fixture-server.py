#!/usr/bin/env python3
"""Ten-minute input fixture for the actual desktop's browser and keyboard."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
import importlib.util,json,os,time
folder=Path('/tmp/asus-osk-integration');folder.mkdir(mode=0o700)
spec=importlib.util.spec_from_file_location('fixture',Path(__file__).with_name('osk-focus-trial.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
state={'pid':os.getpid(),'fixture':None,'events':[],'command':{'sequence':0,'action':None}}
def save():
 path=folder/'state.json.new';path.write_text(json.dumps(state)+'\n');path.replace(folder/'state.json')
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def reply(self,body,kind='application/json'):
  self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def do_GET(self):
  if self.path=='/':self.reply(module.HTML,'text/html; charset=utf-8')
  elif self.path in ('/state','/command'):self.reply(json.dumps(state if self.path=='/state' else state['command']).encode())
  else:self.send_error(404)
 def do_POST(self):
  size=int(self.headers.get('Content-Length','0'))
  if not 0<size<8192:self.send_error(400);return
  data=json.loads(self.rfile.read(size))
  if self.path=='/state':
   state['fixture']=data;state['events'].append(data);state['events']=state['events'][-40:]
  elif self.path=='/command' and data.get('action') in ('focus','done'):
   state['command']={'sequence':state['command']['sequence']+1,'action':data['action']}
  else:self.send_error(400);return
  save();self.reply(b'{"ok":true}')
server=HTTPServer(('127.0.0.1',8081),Handler);server.timeout=.5
deadline=time.monotonic()+600;state['status']='running';save()
try:
 while time.monotonic()<deadline and not (folder/'STOP').exists():server.handle_request()
finally:
 server.server_close();state['status']='stopped';save()
