"""Reproduce the terminal failed compile in a new isolated builder fixture."""
from pathlib import Path
import base64
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / '2026-11-06-asus-product-input-build-kit/scripts'))
from remote import run

script = r'''
from pathlib import Path
import base64,datetime,difflib,hashlib,json,os,resource,shlex,subprocess
a=Path('/srv/android/lineage24');r=Path('/srv/android/asus-vold-build-include-fix')
assert not r.exists()
r.mkdir()
for folder in ('before','after','evidence','out'):(r/folder).mkdir()
source=a/'system/vold/model/PublicVolume.cpp';before=source.read_bytes()
assert hashlib.sha256(before).hexdigest()=='0e17fccedefabb20e2d8650252af8c765af68378a1d853e0fbaa6a8bd1ea67fd'
assert b'#include <algorithm>' not in before and before.count(b'#include <fcntl.h>')==1
after=before.replace(b'#include <fcntl.h>',b'#include <algorithm>\n#include <fcntl.h>')
(r/'before/PublicVolume.cpp').write_bytes(before);(r/'after/PublicVolume.cpp').write_bytes(after)
patch=''.join(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),
 fromfile='a/model/PublicVolume.cpp',tofile='b/model/PublicVolume.cpp'))
(r/'include-algorithm.patch').write_text(patch)
failed=(a/'out/siso_failed_commands.sh').read_text()
(r/'evidence/original-failed-command.sh').write_text(failed)
lines=[x for x in failed.splitlines() if 'bin/clang++ ' in x and 'model/PublicVolume.cpp' in x]
assert len(lines)==1
tokens=shlex.split(lines[0]);idx=next(i for i,t in enumerate(tokens) if t.endswith('/bin/clang++'))
argv=tokens[idx:];assert argv[-1]=='system/vold/model/PublicVolume.cpp'
assert not any(t in ('&&',';','|') for t in argv)
def restrict():
 os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
 resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));os.nice(10)
rows=[]
for name in ('before','after'):
 cmd=list(argv)
 cmd[cmd.index('-o')+1]=str(r/'out'/(name+'.o'))
 cmd[cmd.index('-MF')+1]=str(r/'out'/(name+'.d'))
 cmd[-1]=str(r/name/'PublicVolume.cpp')
 cmd[1:1]=['-I'+str(a/'system/vold/model')]
 (r/'evidence'/(name+'-argv.json')).write_text(json.dumps(cmd,indent=2)+'\n')
 p=subprocess.run(cmd,cwd=a,capture_output=True,text=True,timeout=180,preexec_fn=restrict)
 (r/'evidence'/(name+'.log')).write_text(p.stdout+p.stderr)
 rows.append({'case':name,'exit_code':p.returncode,'diagnostic':(p.stdout+p.stderr)[-2000:],
 'object_bytes':(r/'out'/(name+'.o')).stat().st_size if (r/'out'/(name+'.o')).exists() else None})
assert rows[0]['exit_code']!=0 and "no member named 'replace'" in rows[0]['diagnostic']
assert rows[1]['exit_code']==0
assert source.read_bytes()==before
v={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'fixture':str(r),
 'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest(),
 'patch_sha256':hashlib.sha256(patch.encode()).hexdigest(),'rows':rows,'active_source_unchanged':True,
 'object_sha256':hashlib.sha256((r/'out/after.o').read_bytes()).hexdigest(),
 'object_is_thin_lto_bitcode':(r/'out/after.o').read_bytes()[:4]==b'BC\xc0\xde',
 'compiled_not_linked':True,'full_build_started':False}
(r/'evidence/receipt.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps({'receipt':v,'before_b64':base64.b64encode(before).decode(),
 'after_b64':base64.b64encode(after).decode(),'patch_b64':base64.b64encode(patch.encode()).decode()}))
'''
result = json.loads(run(script))
for key, destination in [('before_b64','inputs/PublicVolume.cpp'),
                         ('after_b64','artifacts/PublicVolume.cpp'),
                         ('patch_b64','artifacts/include-algorithm.patch')]:
    (ROOT / destination).write_bytes(base64.b64decode(result[key]))
(ROOT / 'evidence/receipt.json').write_text(json.dumps(result['receipt'], indent=2) + '\n')
print(json.dumps(result['receipt'], indent=2))
