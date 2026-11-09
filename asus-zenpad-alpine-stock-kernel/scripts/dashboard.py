#!/usr/bin/env python3
"""Local dashboard workload for the bounded Alpine browser trial."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import html, json, sqlite3, time
from pathlib import Path
DB=Path('/var/lib/asus-dashboard/status.sqlite'); DB.parent.mkdir(parents=True,exist_ok=True)
def power_status():
 def read(name):
  try: return (Path('/sys/class/power_supply')/name).read_text().strip()
  except OSError: return None
 raw=read('battery/capacity')
 percent=int(raw) if raw is not None and raw.isdecimal() and 0<=int(raw)<=100 else None
 status=read('battery/status')
 if status not in ('Charging','Discharging','Not charging','Full','Unknown'): status='Unknown'
 usb=read('usb/online')
 return {'battery_percent':percent,'battery_status':status,'usb_power_connected':{'0':False,'1':True}.get(usb)}

def power_label(power):
 battery='Battery '+str(power['battery_percent'])+'%' if power['battery_percent'] is not None else 'Battery unavailable'
 usb={True:'connected',False:'disconnected',None:'unavailable'}[power['usb_power_connected']]
 return battery+' · '+power['battery_status']+' · USB power '+usb

class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  with sqlite3.connect(DB) as c:
   c.execute('CREATE TABLE IF NOT EXISTS visits(stamp REAL)')
   c.execute('INSERT INTO visits VALUES (?)',(time.time(),))
   count=c.execute('SELECT count(*) FROM visits').fetchone()[0]
  mem=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
  data={'alpine':Path('/etc/alpine-release').read_text().strip(),'kernel':Path('/proc/sys/kernel/osrelease').read_text().strip(),'uptime_seconds':int(float(Path('/proc/uptime').read_text().split()[0])),'available_memory':mem['MemAvailable'].strip(),'requests_saved':count}
  data['power']=power_status()
  if self.path=='/health': body=json.dumps(data).encode(); kind='application/json'
  else:
   mode=Path('/run/asus-alpine/root-mode')
   storage='microSD system' if mode.exists() and mode.read_text().strip()=='SD-loop' else 'RAM demonstration'
   rows=''.join('<tr><th>'+html.escape(k.replace('_',' ').title())+'</th><td>'+html.escape(str(v))+'</td></tr>' for k,v in data.items() if k!='power')
   body=('''<!doctype html><html><head><meta charset="utf-8"><title>ASUS Alpine dashboard</title><style>body{font:24px sans-serif;background:#f6f3ed;color:#172c30;margin:36px}h1{font-size:40px}p{line-height:1.5}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:18px 8px;border-bottom:1px solid #acb7b2}th{font-size:20px;width:52%}a{display:block;padding:24px;margin-top:30px;background:#174d46;color:white;text-align:center;text-decoration:none}small{font-size:18px}</style></head><body><h1>Alpine on ASUS</h1><p>Live Linux dashboard<br><small>Stock kernel · '''+storage+'''</small></p><table>'''+rows+'''</table><a href="/">Refresh status</a><p><small>Python HTTP + SQLite on this tablet.<br>Changes are saved on microSD.</small></p></body></html>''').encode();kind='text/html; charset=utf-8'
   body=body.replace(b'</small></p><table>',('</small><br><small id="power">'+html.escape(power_label(data['power']))+'</small></p><table>').encode(),1)
  self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
HTTPServer(('127.0.0.1',8080),Handler).serve_forever()
