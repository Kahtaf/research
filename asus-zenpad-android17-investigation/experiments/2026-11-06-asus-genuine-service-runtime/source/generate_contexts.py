from pathlib import Path
import json,shlex,subprocess,hashlib,shutil,os,resource
R=Path('/srv/android/asus-genuine-service-runtime');T=Path('/srv/android/lineage24');G=R/'inputs/service-contexts-r1';M=G/'mirror';M.mkdir(parents=True);I=R/'inputs/boot-r3';shutil.copytree(R/'inputs/boot-r2',I,symlinks=True)
rows=json.loads((R/'evidence/context-rules.json').read_text());receipt=[];inputs=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def freeze(src,dst):
 a=sha(src);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(src)==sha(dst)==a;inputs.append(dict(source=str(src),destination=str(dst),before=a,after=sha(src)))
check=G/'checkfc';freeze(T/'out/soong/.intermediates/system/sepolicy/tools/checkfc/linux_glibc_x86_64/checkfc',check)
def limits():resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
for row in rows:
 if 'command =' not in row['line']:continue
 mod=row['module'];cmd=row['line'].split('command = ',1)[1].replace('$$','$')
 toks=shlex.split(cmd)
 for token in toks:
  if token.startswith(('system/','device/','prebuilts/')) and (T/token).is_file() and not (M/token).exists():freeze(T/token,M/token)
  if token.startswith('out/'):(M/token).parent.mkdir(parents=True,exist_ok=True)
 p=subprocess.run(['/bin/sh','-c',cmd],cwd=M,capture_output=True,text=True,timeout=20,preexec_fn=limits);rec=dict(module=mod,command=cmd,cwd=str(M),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr);receipt.append(rec);(R/'evidence/context-generation.json').write_text(json.dumps(dict(inputs=inputs,commands=receipt),indent=2));assert p.returncode==0,p.stderr
 outputs=list(M.glob('out/soong/.intermediates/system/sepolicy/contexts/'+mod+'/**/'+mod+'_remove_comment')) if mod!='vndservice_contexts' else list(M.glob('out/soong/.intermediates/system/sepolicy/contexts/'+mod+'/**/'+mod+'_m4out'))
 assert len(outputs)==1,(mod,outputs)
 src=outputs[0];part='system/system_ext' if mod.startswith('system_ext') else 'system/product' if mod.startswith('product') else 'system/vendor' if mod.startswith(('vendor','vnd')) else 'system'
 dst=I/'root'/part/'etc/selinux'/mod;shutil.copy2(src,dst)
 mode='-l' if 'hwservice' in mod else '-s' if mod!='vndservice_contexts' else '-v'
 argv=[str(check),mode,str(I/'root/system/vendor/etc/selinux/precompiled_sepolicy'),str(dst)];v=subprocess.run(argv,capture_output=True,text=True,preexec_fn=limits,timeout=20);rec['validation']=dict(command=argv,returncode=v.returncode,stdout=v.stdout,stderr=v.stderr);rec['output']=dict(path=str(dst),bytes=dst.stat().st_size,sha256=sha(dst));(R/'evidence/context-generation.json').write_text(json.dumps(dict(inputs=inputs,commands=receipt),indent=2));assert v.returncode==0,(mod,v.stderr,v.stdout)
print('Generated and validated',len(receipt),'genuine selected service/hwservice contexts')
