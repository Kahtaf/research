from pathlib import Path
import base64,hashlib,json,os,subprocess,sys
from vm import R,channel
pins=json.loads((R/'evidence/source-pins.json').read_text())
files={'kernel/'+n:(R/'source'/n).read_bytes() for n in pins}
files['scripts/build_remote.py']=(R/'scripts/build_remote.py').read_bytes();files['evidence/source-pins.json']=(R/'evidence/source-pins.json').read_bytes()
script=r'''from pathlib import Path
import base64,hashlib,json,shutil,subprocess,os
R=Path('/srv/android/asus-linux49-work-dispatch-capture-20261107-b4702f9a');B=Path('/srv/android/asus-linux49-active-work-capture-20261107-8e5c5d4d')
assert not R.exists(),'Owned prefix exists; reconcile, never redispatch'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins=PINS
for n,v in pins.items():assert sha(B/'kernel'/n)==v['before']
assert sha(B/'out/.config')=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')=='a3ce18e1e0d1f38307a2a63e783af3cb2b633c26a706366e6714b24ae36302b4'
assert shutil.disk_usage('/srv/android').free>30*1024**3
R.mkdir();[(R/n).mkdir() for n in ['tmp','source','scripts','evidence']]
# Independent source and output inodes; no hardlinks, no old output mutation.
for n in ['kernel','out']:subprocess.run(['cp','-a','--reflink=auto',str(B/n),str(R/n)],check=True)
assert (R/'out/.config').stat().st_ino!=(B/'out/.config').stat().st_ino
for n in pins:assert (R/'kernel'/n).stat().st_ino!=(B/'kernel'/n).stat().st_ino
for n,v in FILES.items():
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(v))
(R/'evidence/source-copy.json').write_text(json.dumps(dict(base=str(B),owned=str(R),method='cp -a --reflink=auto kernel AND out; independent inodes',scoped_source_pins=pins,full_tree_rehash=False),indent=2)+'\n')
with (R/'evidence/build-supervisor.stdout').open('w') as out,(R/'evidence/build-supervisor.stderr').open('w') as err:
 p=subprocess.Popen(['python3','-B',str(R/'scripts/build_remote.py')],stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
(R/'evidence/dispatch.json').write_text(json.dumps(dict(pid=p.pid,one_candidate=True),indent=2)+'\n')
print(json.dumps(dict(remote_root=str(R),build_pid=p.pid,status='dispatched_once')))
'''.replace('PINS',repr(pins)).replace('FILES',repr({n:base64.b64encode(v).decode() for n,v in files.items()}))
assert not (R/'evidence/dispatch-local.json').exists()
(R/'evidence/dispatch-local.json').write_text(json.dumps(dict(one_candidate=True,remote_root='/srv/android/asus-linux49-work-dispatch-capture-20261107-b4702f9a',uploaded={n:hashlib.sha256(v).hexdigest() for n,v in files.items()}),indent=2)+'\n')
os.chdir(R)
p=subprocess.run(channel()+['python3 -B -'],input=script,text=True,capture_output=True)
(R/'evidence/dispatch.stdout').write_text(p.stdout);(R/'evidence/dispatch.stderr').write_text(p.stderr)
p.check_returncode();print(p.stdout)
