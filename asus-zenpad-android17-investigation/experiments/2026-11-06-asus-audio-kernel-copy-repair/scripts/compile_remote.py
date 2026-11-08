import hashlib,json,os,pathlib,resource,shlex,subprocess,time
base=pathlib.Path('/srv/android/asus-bmc156-full-kernel-r1')
own=pathlib.Path('/srv/android/asus-audio-kernel-copy-repair-20261106-r1')
a=pathlib.Path('sound/soc/mediatek/mt_soc_audio_8163')
(own/'evidence').mkdir(exist_ok=True);(own/'out').mkdir(exist_ok=True)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
pins=[base/'out/.config',base/'out/arch/arm64/boot/Image.gz-dtb']
pins += list((base/'kernel'/a).glob('*'))
pins=[x for x in pins if x.is_file()]
before={str(x):digest(x) for x in pins}
(own/'evidence/fixture-pre.json').write_text(json.dumps(before,indent=2))
records=[];headers={}
for name in ['mt_soc_pcm_dl1','mt_soc_pcm_capture']:
 saved=base/'out'/a/('.'+name+'.o.cmd');content=saved.read_text();(own/'evidence'/saved.name).write_text(content)
 cmd=shlex.split(content.splitlines()[0].split(' := ',1)[1])
 cmd=[str(own/'source'/a/(name+'.c')) if x==str(base/'kernel'/a/(name+'.c')) else x for x in cmd]
 cmd[cmd.index('-o')+1]=str(own/'out'/(name+'.o'))
 cmd=[('-Wp,-MD,'+str(own/'out'/(name+'.d'))) if x.startswith('-Wp,-MD,') else x for x in cmd]
 start=time.time()
 proc=subprocess.run(cmd,cwd=base/'out',stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (own/'evidence'/(name+'.compile.log')).write_bytes(proc.stdout)
 rec={'command':cmd,'cwd':str(base/'out'),'saved_command_sha256':digest(saved),'exit':proc.returncode,'seconds':time.time()-start,'affinity':list(os.sched_getaffinity(0)),'address_space_limit_bytes':1024**3}
 if proc.returncode==0:
  obj=own/'out'/(name+'.o');rec.update(object_sha256=digest(obj),object_bytes=obj.stat().st_size)
  out=subprocess.check_output(['aarch64-linux-gnu-readelf','-h',str(obj)]);(own/'evidence'/(name+'.elf.txt')).write_bytes(out)
  dep=(own/'out'/(name+'.d')).read_text().replace('\\\n',' ')
  for raw in dep.split(':',1)[1].split():
   path=pathlib.Path(raw);path=path if path.is_absolute() else base/'out'/path
   if path.is_file():headers[str(path)]={'sha256':digest(path),'bytes':path.stat().st_size}
 records.append(rec)
 if proc.returncode:break
(own/'evidence/compile.json').write_text(json.dumps(records,indent=2))
(own/'evidence/compiler-inputs.json').write_text(json.dumps(headers,indent=2,sort_keys=True))
after={str(x):digest(x) for x in pins}
assert before==after
(own/'evidence/fixture-post.json').write_text(json.dumps(after,indent=2))
tool=pathlib.Path(subprocess.check_output(['which','aarch64-linux-gnu-gcc'],text=True).strip()).resolve()
(own/'evidence/compiler.json').write_text(json.dumps({'path':str(tool),'sha256':digest(tool),'version':subprocess.check_output([str(tool),'--version'],text=True)},indent=2))
print(json.dumps(records,indent=2))
assert all(x['exit']==0 for x in records)
