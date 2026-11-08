from pathlib import Path
import hashlib,json,shutil,subprocess,shlex,re,resource,os,datetime
R=Path('/srv/android/asus-genuine-service-runtime');T=Path('/srv/android/lineage24');C=R/'inputs/capture-r1';G=R/'inputs/vintf-r7';M=G/'mirror';M.mkdir(parents=True);I=R/'inputs/boot-r7';shutil.copytree(R/'inputs/boot-r6',I,symlinks=True);rows=[];inputs=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def freeze(src,dst,origin):
 a=sha(src);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert a==sha(src)==sha(dst);inputs.append(dict(source=str(src),destination=str(dst),origin=origin,before=a,after=sha(src)));return dst
host=T/'out/host/linux-x86';tool=host/'bin/assemble_vintf'
if not tool.is_file():tool=T/'out/soong/.intermediates/system/libvintf/assemble_vintf/linux_glibc_x86_64/assemble_vintf'
freeze(tool,M/'out/host/linux-x86/bin/assemble_vintf','completed genuine host tool; copied read-only')
queue=[tool];seen=set()
while queue:
 f=queue.pop()
 for n in re.findall(r'\(NEEDED\).*\[(.*?)\]',subprocess.check_output(['readelf','-d',str(f)],text=True)):
  if n in seen:continue
  seen.add(n);src=host/'lib64'/n
  if src.is_file():freeze(src,M/'out/host/linux-x86/lib64'/n,'completed genuine host tool dependency');queue.append(src)
def limit():resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
for row in json.loads((R/'evidence/vintf-module-rules.json').read_text()):
 cmd=next(x.split('command = ',1)[1] for x in row['block'].splitlines() if '    command =' in x).replace('$$','$')
 args=shlex.split(cmd);inputsarg=args[args.index('-i')+1].split(':');output=args[args.index('-o')+1]
 for rel in inputsarg:
  src=C/rel;origin='pre-r6 coherent capture-r1'
  if not src.is_file():
   assert rel=='system/libhidl/vintfdata/system_ext_manifest.default.xml',rel
   src=T/rel;origin='late copy of genuine generic source; not a product-generated value'
  freeze(src,M/rel,origin)
 (M/output).parent.mkdir(parents=True,exist_ok=True);p=subprocess.run(['/bin/sh','-c',cmd],cwd=M,capture_output=True,text=True,preexec_fn=limit,timeout=30);rec=dict(module=row['module'],command=cmd,cwd=str(M),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr);rows.append(rec);(R/'evidence/vintf-generation.json').write_text(json.dumps(dict(inputs=inputs,commands=rows),indent=2));assert p.returncode==0,p.stderr
 part='system/system_ext' if row['module']=='system_ext_manifest.xml' else 'system/vendor';dst=I/'root'/part/'etc/vintf/manifest.xml';dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(M/output,dst);rec['output']=dict(path=str(dst),sha256=sha(dst),bytes=dst.stat().st_size,content=dst.read_text())
(R/'evidence/vintf-generation.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),inputs=inputs,commands=rows,note='Exact genuine selected commands, no additions to XML or readiness properties'),indent=2));print('Generated exact system_ext/vendor manifests')
