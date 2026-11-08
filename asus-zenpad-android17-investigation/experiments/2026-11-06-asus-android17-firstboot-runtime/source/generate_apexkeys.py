from pathlib import Path
import re,json,hashlib,subprocess as s,shutil
R=Path('/srv/android/asus-firstboot-runtime');T=Path('/srv/android/lineage24');I=R/'inputs/apexkeys-generator-r1';I.mkdir();M=I/'mirror';M.mkdir();captured=(R/'evidence/ninja-make-props-apexkeys.txt').read_text();line=next(l for l in captured.splitlines() if l.startswith(' command = ') and 'apexkeys_intermediates' in l);command=line[len(' command = '):].replace('$$','$');paths=list(dict.fromkeys(re.findall(r'cat ([^ ]+apexkeys.txt)',command)));assert len(paths)==39;wanted=set(paths);edges={};manifest=[]
def freeze(src,dst):
 b=src.read_bytes();assert b==src.read_bytes();dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b);manifest.append(dict(source=str(src),path=str(dst.relative_to(I)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)));return b
for f in (T/'out/soong').glob('build.lineage_p00a.*.ninja'):
 acc=''
 for l in f.open():
  if acc:acc+=l
  elif l.startswith('build '):acc=l
  else:continue
  if l.rstrip().endswith('$'):continue
  logical=acc.replace('$\n','');acc='';toks=logical.split()
  for p in wanted:
   if toks[1:2]==[p+':']:edges[p]=dict(ninja=str(f),edge=logical)
(I/'edges.json').write_text(json.dumps(edges,indent=2));assert len(edges)==len(paths),(len(edges),len(paths));runs=[]
for rel in paths:
 e=edges[rel];toks=e['edge'].split();rule=toks[2];assert rule=='g.android.rawFileCopy',(rel,rule);raw=toks[3];assert raw.startswith('out/soong/raw-lineage_p00a/');freeze(T/raw,M/raw);dst=M/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 # rawFileCopy copies Soong's exact serialized metadata. It does not invoke a signer or read private key files.
 cmd=['cp',str(M/raw),str(dst)];p=s.run(cmd,capture_output=True,text=True);runs.append(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0
(I/'aggregate.ninja-command').write_text(command+'\n');dest=M/'out/target/product/p00a/obj/PACKAGING/apexkeys_intermediates';dest.mkdir(parents=True,exist_ok=True);p=s.run(['/bin/sh','-c',command],cwd=M,capture_output=True,text=True);runs.append(dict(command=command,cwd=str(M),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,p.stderr
(I/'input-manifest.json').write_text(json.dumps(manifest,indent=2));(I/'commands.json').write_text(json.dumps(runs,indent=2));out=dest/'apexkeys.txt';(I/'output-manifest.json').write_text(json.dumps(dict(path=str(out),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),bytes=out.stat().st_size,entries=len(out.read_text().splitlines()),private_key_contents_accessed=False),indent=2));print('generated exact apexkeys metadata',len(out.read_text().splitlines()))
