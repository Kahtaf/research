from pathlib import Path
import json,mmap,shlex,shutil,hashlib,subprocess,resource,datetime
R=Path('/srv/android/asus-genuine-service-runtime');T=Path('/srv/android/lineage24');C=R/'inputs/capture-r1';G=R/'inputs/vintf-r9';M=G/'mirror';M.mkdir(parents=True);I=R/'inputs/boot-r9';shutil.copytree(R/'inputs/boot-r7',I,symlinks=True)
# Reuse previously frozen genuine host tool and its dependency closure.
shutil.copytree(R/'inputs/vintf-r7/mirror/out/host',M/'out/host',symlinks=True)
f=Path(next(x['ninja'] for x in json.loads((R/'evidence/vintf-module-rules.json').read_text()) if x['module']=='system_ext_manifest.xml'))
with f.open('rb') as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ) as m:
 needle=b'# Module:  system_manifest.xml\n';start=m.find(needle);assert start>=0;end=m.find(b'# Module:',start+len(needle));block=m[start:end].decode()
cmd=next(x.split('command = ',1)[1] for x in block.splitlines() if '    command =' in x).replace('$$','$');args=shlex.split(cmd);rows=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for rel in args[args.index('-i')+1].split(':'):
 src=C/rel;origin='pre-r6 capture-r1'
 if not src.is_file():src=T/rel;origin='late frozen genuine source input, not generated data'
 a=sha(src);dst=M/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert a==sha(src)==sha(dst);rows.append(dict(source=str(src),copy=str(dst),origin=origin,before=a,after=sha(src)))
output=args[args.index('-o')+1];(M/output).parent.mkdir(parents=True,exist_ok=True)
def limit():resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
p=subprocess.run(['/bin/sh','-c',cmd],cwd=M,capture_output=True,text=True,preexec_fn=limit,timeout=30);rec=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),ninja=str(f),module_block=block,inputs=rows,command=cmd,cwd=str(M),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr);(R/'evidence/system-vintf-r9-generation.json').write_text(json.dumps(rec,indent=2));assert p.returncode==0,p.stderr
dst=I/'root/system/etc/vintf/manifest.xml';shutil.copy2(M/output,dst);rec['output']=dict(path=str(dst),sha256=sha(dst),content=dst.read_text());(R/'evidence/system-vintf-r9-generation.json').write_text(json.dumps(rec,indent=2))
# Read-only init expansions expose owning real service's protected properties.
f=I/'root/system/etc/init/hw/init.rc';s=f.read_text();needle='    exec_start firstboot-observer\n';assert s.count(needle)==1;s=s.replace(needle,needle+'    write /dev/kmsg FIXTURE_HWSM_DISABLED=${hwservicemanager.disabled}\n    write /dev/kmsg FIXTURE_HWSM_READY=${hwservicemanager.ready}\n');f.write_text(s)
print('Genuine base framework manifest generated; mandatory self-tests unchanged')
