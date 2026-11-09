#!/usr/bin/env python3
"""Observe one real DHCP renewal without replacing the resident client."""
from pathlib import Path
import json,os,re,signal,subprocess,time
run=Path('/run/asus-alpine');pid=int((run/'udhcpc.pid').read_text())
args=Path('/proc',str(pid),'cmdline').read_bytes().split(b'\0')
assert args[0]==b'udhcpc' and b'wlan0' in args
original=subprocess.check_output(['ip','-o','-4','addr','show','wlan0'],text=True)
trace=run/'dhcp-renewal.full.trace'
before_resolver=Path('/etc/resolv.conf').stat().st_mtime_ns
tracer=subprocess.Popen(['strace','-xx','-s','700','-e','trace=read,write,sendto,recvfrom,sendmsg,recvmsg','-o',str(trace),'-p',str(pid)],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
try:
 for i in range(30):
  assert tracer.poll() is None,'Tracer exited before attach'
  status=Path('/proc',str(pid),'status').read_text()
  if re.search(r'^TracerPid:\s*'+str(tracer.pid)+r'$',status,re.M):break
  time.sleep(.1)
 else:raise AssertionError('Resident client not traced')
 os.kill(pid,signal.SIGUSR1);time.sleep(4)
finally:
 if tracer.poll() is None:tracer.send_signal(signal.SIGINT)
 tracer.communicate(timeout=5)
assert Path('/proc',str(pid),'cmdline').read_bytes().split(b'\0')==args
assert subprocess.check_output(['ip','-o','-4','addr','show','wlan0'],text=True)==original
acks=0
for line in trace.read_text().splitlines():
 if not any(name+'(' in line for name in ('read','recvfrom','recvmsg')):continue
 for encoded in re.findall(r'"((?:\\x[0-9a-f]{2})+)"',line):
  data=bytes.fromhex(encoded.replace('\\x',''));magic=data.find(b'\x63\x82\x53\x63')
  if magic<236 or data[magic-236]!=2:continue
  offset=magic+4
  while offset<len(data):
   code=data[offset];offset+=1
   if code==0:continue
   if code==255:break
   if offset>=len(data):break
   length=data[offset];offset+=1
   value=data[offset:offset+length];offset+=length
   if code==53 and value==b'\x05':acks+=1
assert acks>=1,'No actual DHCPACK observed; inspect the private trace'
assert Path('/etc/resolv.conf').stat().st_mtime_ns>before_resolver,'Renew hook did not update resolver'
proof={'status':'REAL_DHCP_RENEWAL_PASS','dhcpacks_observed':acks,'renew_hook_executed':True,'same_resident_client':True,'ipv4_lease_retained':True,'daemon_stdout_stderr':'/dev/null; initial logs cannot prove renewal'}
(run/'dhcp-renewal-proof.json').write_text(json.dumps(proof)+'\n')
print(json.dumps(proof))
