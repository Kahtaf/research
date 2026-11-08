from pathlib import Path
import subprocess,os,json,hashlib,datetime,shutil,traceback
R=Path('/srv/android/asus-retained-trace-kernel-probe-20261107');B=Path('/srv/android/asus-bmc156-full-kernel-r1');K=R/'kernel';O=R/'out';E=R/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def cfg(p):
 d={}
 for l in p.read_text().splitlines():
  if l.startswith('CONFIG_'):k,v=l.split('=',1);d[k]=v
  elif l.startswith('# CONFIG_') and l.endswith(' is not set'):d[l.split()[1]]='n'
 return d
assert not (E/'build-status.json').exists() and not K.exists() and not O.exists()
assert R.resolve()==R and shutil.disk_usage(R).free>25*1024**3
record=dict(started=now(),pid=os.getpid(),status='preparing',max_jobs=8,affinity=sorted(os.sched_getaffinity(0)),commands=[])
def save():(E/'build-status.json').write_text(json.dumps(record,indent=2)+'\n')
save()
try:
 trace=json.loads((R/'source/trace-pins.json').read_text())
 expected={k:v['before_sha256'] for k,v in trace['files'].items()}
 expected['drivers/clocksource/mtk_timer.c']='2b298b9f5b7951104340b20b5591c2496746be088d3bec935a69157ba30ca197'
 selected=[B/'kernel'/p for p in expected]+[B/'out/.config',B/'out/arch/arm64/boot/Image.gz-dtb',B/'out/include/generated/utsrelease.h',B/'out/include/generated/compile.h',B/'evidence/reconstruction.json']
 originals={str(p):sha(p) for p in selected}
 assert sha(B/'out/.config')=='10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2'
 assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')=='e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1'
 assert not (B/'kernel/.git').exists()
 # Ordinary independent fixture copy; no hardlinks, checkout, worktree or out reuse.
 subprocess.run(['cp','-a',str(B/'kernel'),str(K)],check=True)
 O.mkdir();shutil.copyfile(B/'out/.config',O/'.config');shutil.copyfile(B/'out/.config',E/'original.config')
 for p,h in expected.items():assert sha(K/p)==h,(p,sha(K/p),h)
 patches={'retained-boot-trace.patch':'a0efbb7dee1688b07b0accebb8ef7f22a183fd58752aad9447bf89f1ba78cdbb','timer-clock.patch':'13294c10548d583e7fa86a4010fd3455822e3ba012a001cb40a6ecb1378d0816'}
 for name,h in patches.items():
  assert sha(R/'source'/name)==h
  with (E/(name+'.log')).open('w') as f:subprocess.run(['patch','--batch','--forward','-p1','-i',str(R/'source'/name)],cwd=K,stdout=f,stderr=subprocess.STDOUT,check=True)
 after={k:v['after_sha256'] for k,v in trace['files'].items()};after['drivers/clocksource/mtk_timer.c']='0c9e26f54ecbbdd8d60c9ed35cbfb62820b6a515ef25d0750fd16c3834db2913'
 for p,h in after.items():assert sha(K/p)==h,(p,sha(K/p),h)
 (E/'changed-source-pins.json').write_text(json.dumps(dict(before=expected,after=after,patches=patches,copy_method='cp -a full e9 source; independent new output',prior_port_delta_preserved_by_full_copy=True),indent=2)+'\n')
 assert (R/'source/diagnostic.config').read_text()=='CONFIG_ASUS_P00A_RETAINED_BOOT_TRACE=y\n'
 with (O/'.config').open('a') as f:f.write((R/'source/diagnostic.config').read_text())
 for name in ['MAKEFLAGS','MFLAGS','KBUILD_OUTPUT','KCONFIG_CONFIG','LOCALVERSION','CROSS_COMPILE','KBUILD_BUILD_TIMESTAMP','KBUILD_BUILD_VERSION']:os.environ.pop(name,None)
 os.environ['TMPDIR']=str(R/'tmp')
 os.environ['KBUILD_BUILD_TIMESTAMP']=datetime.datetime.now(datetime.timezone.utc).strftime('%a %b %d %H:%M:%S UTC %Y')
 os.environ['KBUILD_BUILD_VERSION']='1'
 base=['make','-C',str(K),'O='+str(O),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','LOCALVERSION=-g717bb3c9e13c-dirty','-j8']
 record.update(status='running',build_timestamp=os.environ['KBUILD_BUILD_TIMESTAMP']);save()
 for target in ['olddefconfig','Image.gz-dtb']:
  cmd=base+[target];row=dict(command=cmd,started=now());record['commands'].append(row);save()
  with (E/(target+'.log')).open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
  row.update(exit=p.returncode,finished=now());save()
  assert p.returncode==0,(target,p.returncode)
  old,new=cfg(E/'original.config'),cfg(O/'.config')
  delta={k:dict(before=old.get(k,'n'),after=new.get(k,'n')) for k in old.keys()|new.keys() if old.get(k,'n')!=new.get(k,'n')}
  assert delta=={'CONFIG_ASUS_P00A_RETAINED_BOOT_TRACE':{'before':'n','after':'y'}},delta
  (E/'config-delta.json').write_text(json.dumps(delta,indent=2)+'\n')
 for p,h in originals.items():assert sha(Path(p))==h,('original changed',p)
 for p,h in after.items():assert sha(K/p)==h,('new source changed',p)
 (E/'original-selected-inputs.json').write_text(json.dumps(dict(before=originals,after={p:sha(Path(p)) for p in originals},unchanged=True,no_full_tree_rehash=True),indent=2)+'\n')
 artifacts={}
 for p in [O/'arch/arm64/boot/Image.gz-dtb',O/'arch/arm64/boot/Image',O/'vmlinux',O/'.config',O/'include/generated/utsrelease.h',O/'include/generated/compile.h']:
  artifacts[str(p.relative_to(O))]=dict(bytes=p.stat().st_size,sha256=sha(p))
 objects={}
 for rel in ['arch/arm64/kernel/asus_retained_trace.o','arch/arm64/kernel/setup.o','init/main.o','kernel/printk/printk.o','drivers/clocksource/mtk_timer.o']:
  p=O/rel;objects[rel]=dict(bytes=p.stat().st_size,sha256=sha(p))
 (E/'build-receipt.json').write_text(json.dumps(dict(artifacts=artifacts,objects=objects,release=(O/'include/generated/utsrelease.h').read_text(),version=(O/'include/generated/compile.h').read_text(),build_timestamp=record['build_timestamp'],original_inputs_unchanged=True,config_delta=delta,physical_tested=False),indent=2)+'\n')
 record.update(status='complete',exit=0)
except BaseException as exc:
 record.update(status='failed',exit=1,error=repr(exc));traceback.print_exc()
finally:
 record['finished']=now();save();print(json.dumps(record),flush=True)
raise SystemExit(record['exit'])
