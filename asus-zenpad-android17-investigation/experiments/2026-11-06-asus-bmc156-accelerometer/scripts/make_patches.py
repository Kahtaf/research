from pathlib import Path
import hashlib,difflib,json,subprocess,shutil
S=Path(__file__).resolve().parents[1];P=S/'source/kernel-preimages';K=S/'source/kernel';rows={};patch=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for p in sorted(K.rglob('*')):
 if not p.is_file():continue
 rel=str(p.relative_to(K));old=P/rel
 before=old.read_bytes() if old.exists() else b'';after=p.read_bytes()
 assert before!=after,rel
 rows[rel]={'before':sha(old) if old.exists() else None,'after':sha(p)}
 patch.append(f'diff --git a/{rel} b/{rel}\n')
 if not old.exists():patch.append('new file mode 100644\n')
 for line in difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),fromfile='a/'+rel if old.exists() else '/dev/null',tofile='b/'+rel):
  patch.append(line if line.endswith('\n') else line+'\n\\ No newline at end of file\n')
file=S/'patches/kernel-from-physical-r5.patch';file.write_bytes(''.join(patch).encode())
(S/'patches/pre-post-hashes.json').write_text(json.dumps(rows,sort_keys=True,indent=2)+'\n')
T=S/'evidence/patch-roundtrip'
if T.exists():shutil.rmtree(T)
shutil.copytree(P,T)
p=subprocess.run(['git','apply','--whitespace=nowarn',str(file.resolve())],cwd=T,capture_output=True,text=True)
assert p.returncode==0 and 'offset' not in p.stdout and 'fuzz' not in p.stdout,(p.stdout,p.stderr)
for rel,row in rows.items():assert sha(T/rel)==row['after'],rel
(S/'evidence/patch-roundtrip.json').write_text(json.dumps(dict(exit=p.returncode,files=len(rows),patch_sha256=sha(file),all_postimages_match=True,stdout=p.stdout,stderr=p.stderr),indent=2)+'\n')
print('Exact git-apply roundtrip:',len(rows),'files; patch',sha(file))
