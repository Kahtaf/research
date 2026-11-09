#!/usr/bin/env python3
"""Exercise actual Firefox focus, Onboard keys and JWM workarea geometry."""
from pathlib import Path
import ctypes,json,os,re,subprocess,time,urllib.request
os.environ.update(DISPLAY=':0',XAUTHORITY='/run/asus-goodix/Xauthority')
run=Path('/run/asus-goodix')
pid=int((run/'onboard.pid').read_text())
env=dict(item.split(b'=',1) for item in Path('/proc',str(pid),'environ').read_bytes().split(b'\0') if b'=' in item)
os.environ['DBUS_SESSION_BUS_ADDRESS']=env[b'DBUS_SESSION_BUS_ADDRESS'].decode()
import dbus
bus=dbus.SessionBus();keyboard=bus.get_object('org.onboard.Onboard','/org/onboard/Onboard/Keyboard')
props=dbus.Interface(keyboard,'org.freedesktop.DBus.Properties')
def visible():return bool(props.Get('org.onboard.Onboard.Keyboard','Visible'))
def call(*args):return subprocess.check_output(list(args),text=True).strip()
def geometry(win):
 d=dict(line.split('=',1) for line in call('xdotool','getwindowgeometry','--shell',str(win)).splitlines())
 return {k:int(d[k]) for k in ('X','Y','WIDTH','HEIGHT')}
owner=int(Path('/root/.mozilla/asus-appliance/lock').readlink().name.rsplit('+',1)[1])
windows=call('xdotool','search','--pid',str(owner),'--class','firefox').split()
windows=[w for w in windows if 'ASUS automatic keyboard trial' in call('xdotool','getwindowname',w)]
assert len(windows)==1,windows
window=windows[0]
def state():return json.load(urllib.request.urlopen('http://127.0.0.1:8081/state',timeout=3))
def command(action):
 data=json.dumps({'action':action}).encode()
 urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8081/command',data=data,headers={'Content-Type':'application/json'}),timeout=3).read()
 time.sleep(1)
def assert_layout(shown):
 for attempt in range(30):
  keywin=subprocess.run(['xdotool','search','--onlyvisible','--name','^Onboard$'],capture_output=True,text=True).stdout.split()
  keywin=[w for w in keywin if '_NET_WM_WINDOW_TYPE_DOCK' in call('xprop','-id',w,'_NET_WM_WINDOW_TYPE')]
  if visible()==shown and (len(keywin)==1 if shown else not keywin):break
  time.sleep(.1)
 assert visible()==shown
 area=list(map(int,re.findall(r'\d+',call('xprop','-root','-notype','_NET_WORKAREA').split('=',1)[1])))[:4]
 g=geometry(window)
 ext=list(map(int,re.findall(r'\d+',call('xprop','-id',window,'-notype','_NET_FRAME_EXTENTS').split('=',1)[1])))
 bottom=g['Y']+g['HEIGHT']+ext[3]
 assert bottom==area[1]+area[3],(g,ext,area)
 if shown:
  assert len(keywin)==1,keywin
  kg=geometry(keywin[0]);assert kg['X']==0 and kg['WIDTH']==800 and kg['HEIGHT']==280,kg
  assert bottom==kg['Y'],(bottom,kg)
  return g,kg
 return g,None
def maximize(action):
 class Data(ctypes.Union):_fields_=[('l',ctypes.c_long*5)]
 class Message(ctypes.Structure):
  _fields_=[('type',ctypes.c_int),('serial',ctypes.c_ulong),('send_event',ctypes.c_int),('display',ctypes.c_void_p),('window',ctypes.c_ulong),('message_type',ctypes.c_ulong),('format',ctypes.c_int),('data',Data)]
 class Event(ctypes.Union):_fields_=[('client',Message),('pad',ctypes.c_long*24)]
 lib=ctypes.CDLL('libX11.so.6');lib.XOpenDisplay.restype=ctypes.c_void_p
 lib.XInternAtom.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_int];lib.XInternAtom.restype=ctypes.c_ulong
 lib.XDefaultRootWindow.argtypes=[ctypes.c_void_p];lib.XDefaultRootWindow.restype=ctypes.c_ulong
 lib.XSendEvent.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_long,ctypes.POINTER(Event)]
 lib.XFlush.argtypes=[ctypes.c_void_p];lib.XCloseDisplay.argtypes=[ctypes.c_void_p]
 display=lib.XOpenDisplay(None);assert display
 def atom(name):return lib.XInternAtom(display,name.encode(),0)
 event=Event();event.client.type=33;event.client.display=display;event.client.window=int(window)
 event.client.message_type=atom('_NET_WM_STATE');event.client.format=32
 event.client.data.l[:]=[action,atom('_NET_WM_STATE_MAXIMIZED_VERT'),atom('_NET_WM_STATE_MAXIMIZED_HORZ'),2,0]
 assert lib.XSendEvent(display,lib.XDefaultRootWindow(display),0,(1<<20)|(1<<19),ctypes.byref(event))
 lib.XFlush(display);lib.XCloseDisplay(display);time.sleep(.6)
command('focus');shown,kg=assert_layout(True)
subprocess.run(['xdotool','key','ctrl+a','BackSpace'],check=True);time.sleep(.3)
assert state()['fixture']['value']==''
print('SHOWN_BROWSER_AND_KEYBOARD',shown,kg,flush=True)
maximize(0);restore_a=geometry(window);maximize(1);assert_layout(True)
command('done');hidden,_=assert_layout(False)
print('HIDDEN_BROWSER',hidden,flush=True)
maximize(0);restore_b=geometry(window);assert restore_a==restore_b,(restore_a,restore_b)
print('RESTORE_GEOMETRY_PRESERVED',restore_a,flush=True)
maximize(1);assert_layout(False)
command('focus');assert_layout(True)
assert state()['fixture']['activeElement']=='entry' and state()['fixture']['hasFocus']
subprocess.run(['xdotool','mousemove',str(kg['X']+110),str(kg['Y']+140),'click','1'],check=True)
time.sleep(.5);assert state()['fixture']['value']=='a',state()['fixture']
subprocess.run(['xdotool','mousemove',str(kg['X']+763),str(kg['Y']+28),'click','1'],check=True)
time.sleep(.8);assert not visible(),'Keyboard own hide key failed'
command('done');command('focus');assert_layout(True)
subprocess.run(['xdotool','key','ctrl+a','BackSpace'],check=True);time.sleep(.4)
assert state()['fixture']['value']==''
command('done');assert_layout(False)
proof={'status':'SOFTWARE_WORKLOAD_PASS','automatic_focus_show_hide':True,'bottom_docking':kg,'shown_browser':shown,'hidden_browser':hidden,'restore_geometry_preserved':restore_a==restore_b,'onboard_a_key_delivered':True,'keyboard_own_hide_key':True,'physical_touch_typing':'pending owner check'}
Path('/tmp/asus-osk-integration/proof.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof))
