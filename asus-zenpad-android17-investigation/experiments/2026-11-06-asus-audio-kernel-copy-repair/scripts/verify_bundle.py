"""Local software-only bundle verification. Never modifies the supplied kernel."""
import hashlib,json,pathlib,shutil,subprocess,tempfile,sys
p=pathlib.Path(__file__).resolve().parents[1]
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
delta=json.loads((p/'patches/pre-post.json').read_text())
for rel,rec in delta.items():
 assert sha(p/'source/current'/rel)==rec['after']
 if rec['before']:assert sha(p/'source/original'/rel)==rec['before']
inputs=json.loads((p/'evidence/remote/evidence/compiler-inputs.json').read_text())
for rel,rec in delta.items():assert inputs['/srv/android/asus-audio-kernel-copy-repair-20261106-r1/source/'+rel]['sha256']==rec['after']
for rec in json.loads((p/'evidence/remote/evidence/compile.json').read_text()):
 assert rec['exit']==0
 obj=p/'evidence/remote/out'/pathlib.Path(rec['command'][rec['command'].index('-o')+1]).name
 assert sha(obj)==rec['object_sha256']
assert json.loads((p/'evidence/remote/evidence/fixture-pre.json').read_text())==json.loads((p/'evidence/remote/evidence/fixture-post.json').read_text())
with tempfile.TemporaryDirectory(dir=p/'tests',prefix='patch-check-') as tmp:
 root=pathlib.Path(tmp)
 for rel,rec in delta.items():
  if rec['before']:
   f=root/rel;f.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p/'source/original'/rel,f)
 r=subprocess.run(['patch','-p1','--batch','-d',str(root),'-i',str(p/'patches/audio-copy.patch')],capture_output=True,text=True)
 assert r.returncode==0,r.stdout+r.stderr
 for rel,rec in delta.items():assert sha(root/rel)==rec['after']
if len(sys.argv)>1:
 target=pathlib.Path(sys.argv[1])
 for rel,rec in delta.items():
  f=target/rel
  assert (sha(f) if f.exists() else None)==rec['before'],str(f)
 print('Target preimages verified read-only; patch was NOT applied to target.')
print('PASS: exact three-file patch application on disposable copies; compiled source/object hashes; original fixture pre/post pins.')
