from pathlib import Path
import subprocess as s, shutil, json, hashlib, os
R=Path('/srv/android/asus-firstboot-runtime');T=Path('/srv/android/lineage24');old=R/'inputs/api-generators-r1';I=R/'inputs/api-generators-r2';assert not I.exists();shutil.copytree(old,I,symlinks=True)
manifest=json.loads((I/'input-manifest.json').read_text());mods=json.loads((I/'modules.json').read_text())
for m in mods:
 m['manifest']=m['manifest'].replace(str(old),str(I));p=Path(m['manifest']);p.write_text(p.read_text().replace(str(old),str(I)))
 still=[]
 for rel in m['missing']:
  src=T/rel
  if not src.exists():still.append(rel);continue
  b=src.read_bytes();assert b==src.read_bytes();dst=I/'mirror'/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b);manifest.append(dict(source=str(src),path=str(dst.relative_to(I)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)))
 m['missing']=still
# Match the running product build's pinned JDK, not host Java.
jdk=T/'prebuilts/jdk/jdk21/linux-x86';dst=I/'jdk21';shutil.copytree(jdk,dst,symlinks=True)
for f in sorted(dst.rglob('*')):
 if f.is_file() and not f.is_symlink():manifest.append(dict(source=str(jdk/f.relative_to(dst)),path=str(f.relative_to(I)),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),bytes=f.stat().st_size))
(I/'input-manifest.json').write_text(json.dumps(manifest,indent=2));(I/'modules.json').write_text(json.dumps(mods,indent=2));env=os.environ.copy();env['JAVA_HOME']=str(dst);env['PATH']=str(dst/'bin')+':/usr/bin:/bin';env['TMPDIR']=str(R/'tmp');records=[]
for m in mods:
 if m['missing']:records.append(dict(module=m['name'],state='missing_genuine_inputs',missing=m['missing']));continue
 output=I/'outputs'/m['name'];output.parent.mkdir(exist_ok=True);cmd=[str(I/'tools/sbox'),'--sandbox-path',str(I/'sandbox'),'--output-dir',str(output),'--manifest',m['manifest']]
 p=s.run(cmd,capture_output=True,text=True,env=env,cwd=I,timeout=120);records.append(dict(module=m['name'],command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));(I/'commands.json').write_text(json.dumps(records,indent=2))
(I/'commands.json').write_text(json.dumps(records,indent=2));outputs=[dict(path=str(p.relative_to(I)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in (I/'outputs').rglob('*') if p.is_file()];(I/'output-manifest.json').write_text(json.dumps(outputs,indent=2));print(json.dumps(records,indent=2))
