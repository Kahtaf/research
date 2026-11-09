#!/usr/bin/env python3
"""Probe XI2 touch classes on a private dummy X screen; never replace :0."""
from pathlib import Path
import os,secrets,stat,subprocess,time
assert os.uname().release=='3.18.35'
assert Path('/etc/asus-alpine-ram-release').read_text().strip()=='asus-alpine-stock-kernel-v1'
assert Path('/tmp/.X11-unix/X0').is_socket()
assert not Path('/tmp/.X11-unix/X1').exists()
panel=subprocess.check_output(['python3','/usr/local/bin/goodix-preflight.py'],text=True).strip()
assert panel.startswith('/dev/input/event') and Path(panel).is_char_device()
run=Path('/run/asus-goodix/libinput-probe');run.mkdir(mode=0o700)
entry=Path('/sys/class/input',Path(panel).name)
major,minor=map(int,(entry/'dev').read_text().split(':'))
assert Path(panel).stat().st_rdev==os.makedev(major,minor)
for proc in Path('/proc').iterdir():
 if not proc.name.isdecimal():continue
 try:args=(proc/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError):continue
 assert not (args and b'udevd' in args[0]),'Unexpected running udev daemon; inspect before metadata writes'
props=subprocess.run(['udevadm','test-builtin','input_id',str(entry)],capture_output=True,text=True,check=True)
(run/'input-id.txt').write_text(props.stdout+props.stderr)
assert 'ID_INPUT_TOUCHSCREEN=1' in props.stdout,props.stdout
metadata=Path('/run/udev/data',f'c{major}:{minor}')
metadata.parent.mkdir(parents=True,exist_ok=True)
assert not metadata.is_symlink()
previous=metadata.read_bytes() if metadata.exists() else None
previous_mode=stat.S_IMODE(metadata.stat().st_mode) if metadata.exists() else None
if previous is not None:(run/'udev-metadata-before.bin').write_bytes(previous)
try:
 metadata.write_bytes(b'E:ID_INPUT=1\nE:ID_INPUT_TOUCHSCREEN=1\n')
 metadata.chmod(0o644)
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
  Identifier "goodix-native"
  Driver "libinput"
  Option "Device" "PANEL"
  Option "GrabDevice" "false"
 EndSection
 Section "ServerLayout"
  Identifier "probe-layout"
  Screen "probe-screen"
  InputDevice "goodix-native" "CorePointer"
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
   print('NATIVE_LIBINPUT_XI_TOUCH_CLASS='+str('XITouchClass' in output))
   assert 'XITouchClass' in output,'Native libinput did not expose touch class'
  finally:
   if process.poll() is None:
    process.terminate()
    try:process.wait(timeout=3)
    except subprocess.TimeoutExpired:process.kill();process.wait(timeout=2)
 assert Path('/tmp/.X11-unix/X0').is_socket(),'Original X display lost'
 print('HEADLESS_PROBE_FINISHED; original desktop left running')
finally:
 if previous is None:metadata.unlink(missing_ok=True)
 else:metadata.write_bytes(previous);metadata.chmod(previous_mode)
print('TEMPORARY_INPUT_METADATA_RESTORED')
