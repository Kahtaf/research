#!/usr/bin/env python3
"""Run a bounded command only on the identity-matched capsule USB console."""
from pathlib import Path
import argparse,base64,fcntl,glob,json,os,plistlib,re,secrets,select,struct,subprocess,termios,time
HERE=Path(__file__).resolve().parents[1]
def matches(n):
 if isinstance(n,list):return any(matches(x) for x in n)
 if not isinstance(n,dict):return False
 if n.get('idVendor')==0xe8d and n.get('idProduct')==0x2007 and n.get('USB Product Name') in ('ASUS-Alpine-RAM','ASUS_Alpine_RAM') and str(n.get('USB Serial Number','')).strip()=='asus-alpine-ram':return True
 return matches(n.get('IORegistryEntryChildren',[]))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('script',type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--timeout',type=int,default=30);p.add_argument('--reset-input',action='store_true');a=p.parse_args()
 assert 1<=a.timeout<=55
 raw=subprocess.check_output(['ioreg','-p','IOUSB','-l','-a'],timeout=8)
 assert matches(plistlib.loads(raw)),'Capsule USB identity not present'
 state=json.loads((HERE/'private/live/capsule-serial-state.json').read_text());port=state['port'];assert port in glob.glob('/dev/cu.usbmodem*')
 script=a.script.read_text();assert len(script.encode())<2200,'Use smaller serial command unit'
 fd=os.open(port,os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
 t=termios.tcgetattr(fd);t[0]=0;t[1]=0;t[2]=termios.CS8|termios.CREAD|termios.CLOCAL;t[3]=0;t[4]=t[5]=termios.B115200;t[6][termios.VMIN]=0;t[6][termios.VTIME]=0;termios.tcsetattr(fd,termios.TCSANOW,t)
 fcntl.ioctl(fd,termios.TIOCMBIS,struct.pack('I',termios.TIOCM_DTR|termios.TIOCM_RTS))
 def send_all(payload):
  offset=0;limit=time.monotonic()+8
  while offset<len(payload):
   assert time.monotonic()<limit,'Serial write incomplete; inspect before retry'
   _,w,_=select.select([],[fd],[],.2)
   if not w:continue
   try:count=os.write(fd,payload[offset:offset+256])
   except BlockingIOError:continue
   assert count>0
   offset+=count
 if a.reset_input:send_all(b'\003')
 send_all(b'\n')
 initial=bytearray();handshake=time.monotonic()+4
 while time.monotonic()<handshake:
  ready,_,_=select.select([fd],[],[],.2)
  if not ready:continue
  try:part=os.read(fd,4096)
  except BlockingIOError:continue
  initial.extend(part)
  if b'/ #' in initial or b'alpine#' in initial or b'ASUS#' in initial:break
 else:raise AssertionError('No shell prompt before command dispatch')
 token=secrets.token_hex(12);end=('ASUS_RPC_END_'+token+':').encode()
 encoded=base64.b64encode(script.encode()).decode()
 remote='/run/asus-alpine/rpc-'+token+'.sh'
 command="stty -echo; export TERM=dumb; printf '\\nASUS_RPC_BEGIN_"+token+"\\n'; printf '%s' '"+encoded+"' | base64 -d > "+remote+"; /bin/sh "+remote+"; rpc_rc=$?; printf '\\nASUS_RPC_END_"+token+":%s\\n' \"$rpc_rc\"\n"
 assert len(command.encode())<4000
 send_all(command.encode());data=bytearray(initial);result=None;deadline=time.monotonic()+a.timeout
 with a.output.open('wb') as log:
  log.write(initial)
  while time.monotonic()<deadline:
   ready,_,_=select.select([fd],[],[],1)
   if not ready:continue
   try:b=os.read(fd,4096)
   except BlockingIOError:continue
   if not b:continue
   data.extend(b);log.write(b);log.flush()
   m=re.search(rb'\n'+end+rb'(\d+)\n',bytes(data).replace(b'\r',b''))
   if m:result=int(m[1]);break
 os.close(fd)
 assert result is not None,'Serial command completion unverified; inspect private capture'
 print('CAPSULE_SERIAL_RPC_EXIT',result,'BYTES',len(data))
 raise SystemExit(result)
if __name__=='__main__':main()
