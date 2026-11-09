#!/usr/bin/env python3
"""Navigate only the live appliance profile's managed Firefox Navigator window."""
from pathlib import Path
import argparse,json,re,subprocess,time
from urllib.parse import urlsplit

def output(*args):
    result=subprocess.run(args,capture_output=True,text=True)
    return result.stdout if result.returncode==0 else ''

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url');parser.add_argument('--expect-title');parser.add_argument('--timeout',type=int,default=25)
    args=parser.parse_args();url=urlsplit(args.url)
    assert url.scheme in ('http','https') and url.hostname and not url.username and not url.password
    assert len(args.url)<2048 and 1<=args.timeout<=40
    profile=Path('/root/.mozilla/asus-appliance');deadline=time.monotonic()+args.timeout
    while time.monotonic()<deadline:
        try:
            pid=int((profile/'lock').readlink().name.rsplit('+',1)[1])
            command=Path('/proc',str(pid),'cmdline').read_bytes().split(b'\0')
            assert command[0]==b'/usr/lib/firefox-esr/firefox-esr'
            assert command[command.index(b'--profile')+1]==str(profile).encode()
            windows=output('xdotool','search','--pid',str(pid),'--class','firefox').split()
            windows=[w for w in windows if '"Navigator"' in output('xprop','-id',w,'WM_CLASS')]
            wm=output('xprop','-root','_NET_ACTIVE_WINDOW')
            if len(windows)==1 and 'window id #' in wm:break
        except (OSError,ValueError,IndexError,AssertionError):pass
        time.sleep(.1)
    else:raise RuntimeError('The owned Firefox window and window manager are not ready')
    window=windows[0]
    subprocess.run(['xdotool','windowactivate','--sync',window],check=True,timeout=5)
    for _ in range(50):
        active=re.search(r'window id # (0x[0-9a-fA-F]+)',output('xprop','-root','_NET_ACTIVE_WINDOW'))
        if active and int(active[1],16)==int(window):break
        time.sleep(.1)
    else:raise RuntimeError('The actual browser window did not activate')
    time.sleep(.4)
    subprocess.run(['xdotool','key','--clearmodifiers','ctrl+l'],check=True);time.sleep(.8)
    subprocess.run(['xdotool','key','--clearmodifiers','ctrl+a','BackSpace'],check=True);time.sleep(.1)
    subprocess.run(['xdotool','type','--clearmodifiers','--delay','40',args.url],check=True)
    time.sleep(.2);subprocess.run(['xdotool','key','Return'],check=True)
    if args.expect_title:
        while time.monotonic()<deadline:
            if args.expect_title in output('xdotool','getwindowname',window):break
            time.sleep(.1)
        else:raise RuntimeError('Requested page title was not observed')
    print(json.dumps({'pid':pid,'window':int(window),'url':args.url,'expected_title_observed':bool(args.expect_title)}))

if __name__=='__main__':main()
