from pathlib import Path
import subprocess as s,re,json,hashlib,os
R=Path('/srv/android/asus-firstboot-runtime');T=Path('/srv/android/lineage24');I=R/'inputs/api-generators-r1';I.mkdir();M=I/'mirror';M.mkdir();manifest=[];modules=[]
def copy(src,dst):
 if dst.exists():return
 b=src.read_bytes();assert hashlib.sha256(b).digest()==hashlib.sha256(src.read_bytes()).digest();dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b);dst.chmod(src.stat().st_mode&0o777);manifest.append(dict(source=str(src),path=str(dst.relative_to(I)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)));(I/'input-manifest.json').write_text(json.dumps(manifest,indent=2))
copy(T/'out/host/linux-x86/bin/sbox',I/'tools/sbox')
for n in ['current','module-lib-current','system-current','system-server-current']:
 name='frameworks-base-api-'+n+'.txt';raw=(R/'evidence'/('sbox-ninja-'+name+'.txt')).read_text();original=I/'manifests'/name/'original.textproto';original.parent.mkdir(parents=True);original.write_text(raw);missing=[]
 def before(m):
  block=m[0];path=json.loads(re.search(r'from: ("[^"\n]+")',block)[1]);src=T/path
  if src.exists():copy(src,M/path)
  else:missing.append(path)
  return block.replace('from: '+json.dumps(path),'from: '+json.dumps(str(M/path)),1)
 txt=re.sub(r'copy_before: \{.*?\}',before,raw,flags=re.S)
 def after(m):
  block=m[0];path=json.loads(re.search(r'to: ("[^"\n]+")',block)[1]);dst=I/'outputs'/name/Path(path).name
  return block.replace('to: '+json.dumps(path),'to: '+json.dumps(str(dst)),1)
 txt=re.sub(r'copy_after: \{.*?\}',after,txt,flags=re.S)
 options='-XX:ActiveProcessorCount=1 -Xmx1024m -XX:-UsePerfData -Djava.io.tmpdir='+str(R/'tmp')
 pos=txt.rfind('}');txt=txt[:pos]+' env: { name: "JAVA_TOOL_OPTIONS" value: '+json.dumps(options)+' }\n'+txt[pos:]
 out=original.with_name('fixture.textproto');out.write_text(txt);modules.append(dict(name=name,manifest=str(out),missing=missing))
(I/'modules.json').write_text(json.dumps(modules,indent=2));print(json.dumps([dict(name=m['name'],missing=m['missing']) for m in modules],indent=2))
