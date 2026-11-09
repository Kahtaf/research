#!/usr/bin/env python3
"""Probe XI2 touch classes on a private dummy X screen; never replace :0."""
from pathlib import Path
import os,secrets,subprocess,time
assert os.uname().release=='3.18.35'
assert Path('/etc/asus-alpine-ram-release').read_text().strip()=='asus-alpine-stock-kernel-v1'
assert Path('/tmp/.X11-unix/X0').is_socket()
assert not Path('/tmp/.X11-unix/X1').exists()
panel=subprocess.check_output(['python3','/usr/local/bin/goodix-preflight.py'],text=True).strip()
assert panel.startswith('/dev/input/event') and Path(panel).is_char_device()
run=Path('/run/asus-goodix/direct-input');run.mkdir(mode=0o700)
config='''Section "ServerFlags"
 Option "AutoAddDevices" "false"
 Option "AllowEmptyInput" "true"
EndSection
Section "Module"
 Disable "glx"
EndSection
Section "Device"
 Identifier "probe-dummy"
 Driver "dummy"
 VideoRam 8192
EndSection
Section "Monitor"
 Identifier "probe-monitor"
EndSection
Section "Screen"
 Identifier "probe-screen"
 Device "probe-dummy"
 Monitor "probe-monitor"
 DefaultDepth 24
EndSection
Section "InputDevice"
 Identifier "goodix-direct"
 Driver "evdev"
 Option "Device" "PANEL"
 Option "GrabDevice" "false"
EndSection
Section "ServerLayout"
 Identifier "probe-layout"
 Screen "probe-screen"
 InputDevice "goodix-direct" "CorePointer"
EndSection
'''.replace('PANEL',panel)
(run/'xorg.conf').write_text(config)
auth=run/'Xauthority'
subprocess.run(['xauth','-f',str(auth),'add',':1','.',secrets.token_hex(16)],check=True)
env={**os.environ,'DISPLAY':':1','XAUTHORITY':str(auth)}
with (run/'Xorg.stderr').open('wb') as log:
 process=subprocess.Popen(['Xorg',':1','-sharevts','-novtswitch','vt1','-nolisten','tcp','-noreset','-auth',str(auth),'-config',str(run/'xorg.conf'),'-logfile',str(run/'Xorg.log')],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
 try:
  for i in range(100):
   assert process.poll() is None,'Probe Xorg exited; inspect its log'
   if Path('/tmp/.X11-unix/X1').is_socket():break
   time.sleep(.1)
  else:raise AssertionError('Private X display did not start')
  output=subprocess.check_output(['xinput','list','--long'],env=env,text=True,timeout=5)
  (run/'xinput.txt').write_text(output)
  print(output)
  print('RAW_GOODIX_XI_TOUCH_CLASS='+str('XITouchClass' in output))
 finally:
  if process.poll() is None:
   process.terminate()
   try:process.wait(timeout=3)
   except subprocess.TimeoutExpired:process.kill();process.wait(timeout=2)
assert Path('/tmp/.X11-unix/X0').is_socket(),'Original X display lost'
print('HEADLESS_PROBE_FINISHED; original desktop left running')
