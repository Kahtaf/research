from pathlib import Path
import subprocess,os,json,hashlib,datetime,shutil,traceback,resource
R=Path('/srv/android/asus-early-retained-kernel-probe-20261107');B=Path('/srv/android/asus-retained-trace-kernel-probe-20261107');K=R/'kernel';O=R/'out';E=R/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save():(E/'build-status.json').write_text(json.dumps(record,indent=2)+'\n')
assert not K.exists() and not O.exists() and not (E/'build-status.json').exists()
record=dict(started=now(),pid=os.getpid(),status='preparing',max_jobs=8,affinity=sorted(os.sched_getaffinity(0)),rlimit_as=list(resource.getrlimit(resource.RLIMIT_AS)),commands=[])
save()
try:
 assert resource.getrlimit(resource.RLIMIT_AS)==(resource.RLIM_INFINITY,resource.RLIM_INFINITY)
 assert shutil.disk_usage(R).free>25*1024**3
 pins=json.loads((E/'next-trace-patch.json').read_text())
 assert sha(R/'source/early-retained-checkpoint.patch')==pins['patch_sha256']=='2991e2f9fdab79af5d87783fec3f3e7f0721cb8911df9f172c355d272489643d'
 expected={n:v['before_sha256'] for n,v in pins['files'].items()}
 selected=[B/'kernel'/n for n in expected]+[B/'kernel/drivers/clocksource/mtk_timer.c',B/'out/.config',B/'out/arch/arm64/boot/Image.gz-dtb']
 original={str(p):sha(p) for p in selected}
 assert sha(B/'out/.config')=='0fddb41316305c672b0afd0a64b2615c6dae3c5727f5ff4ead791272ff71b696'
 assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')=='81792d8df329f20d927325e3b46b6bd1c991742db25c6d0695f2e837c7755bc3'
 assert sha(B/'kernel/drivers/clocksource/mtk_timer.c')=='0c9e26f54ecbbdd8d60c9ed35cbfb62820b6a515ef25d0750fd16c3834db2913'
 assert not (B/'kernel/.git').exists()
 subprocess.run(['cp','-a',str(B/'kernel'),str(K)],check=True)
 O.mkdir();shutil.copyfile(B/'out/.config',O/'.config')
 for name,h in expected.items():assert sha(K/name)==h,(name,sha(K/name),h)
 cmd=['patch','--batch','--forward','--fuzz=0','-p1','-d',str(K),'-i',str(R/'source/early-retained-checkpoint.patch')]
 with (E/'patch.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 assert p.returncode==0
 assert 'fuzz' not in (E/'patch.log').read_text().lower() and 'offset' not in (E/'patch.log').read_text().lower()
 after={n:v['after_sha256'] for n,v in pins['files'].items()}
 for name,h in after.items():assert sha(K/name)==h,(name,sha(K/name),h)
 (E/'changed-source-pins.json').write_text(json.dumps(dict(before=expected,after=after,patch_sha256=pins['patch_sha256'],patch_command=cmd,patch_exit=p.returncode,copy_method='cp -a preserved retained-trace kernel; fresh out; no hardlinks',compile_corrections=[],only_three_documented_files_changed=True,no_full_tree_rehash=True),indent=2)+'\n')
 # Preserve exact relevant local API source, not a source-tree inventory.
 refs=['arch/arm64/include/asm/Kbuild','arch/arm64/include/asm/fixmap.h','mm/early_ioremap.c','arch/arm64/mm/init.c','drivers/of/fdt.c','include/asm-generic/early_ioremap.h','include/asm-generic/fixmap.h']
 snippets={}
 ranges={'mm/early_ioremap.c':[(90,225),(275,281)],'arch/arm64/mm/init.c':[(195,309)],'drivers/of/fdt.c':[(686,811)]}
 for n in refs:
  lines=(K/n).read_text().splitlines()
  if n in ranges: snippets[n]='\n'.join(f'{i+1}: {lines[i]}' for a,b in ranges[n] for i in range(a-1,min(b,len(lines))))
  else:snippets[n]='\n'.join(f'{i+1}: {l}' for i,l in enumerate(lines))
 assert 'early_ioremap.h' in snippets['arch/arm64/include/asm/Kbuild']
 assert 'FIXMAP_PAGE_NORMAL' in snippets['mm/early_ioremap.c']
 assert 'early_init_fdt_scan_reserved_mem();' in snippets['arch/arm64/mm/init.c']
 (E/'early-api-source.json').write_text(json.dumps(snippets,indent=2)+'\n')
 for name in ['MAKEFLAGS','MFLAGS','KBUILD_OUTPUT','KCONFIG_CONFIG','LOCALVERSION','CROSS_COMPILE','KBUILD_BUILD_TIMESTAMP','KBUILD_BUILD_VERSION']:os.environ.pop(name,None)
 os.environ['TMPDIR']=str(R/'tmp')
 os.environ['KBUILD_BUILD_TIMESTAMP']=datetime.datetime.now(datetime.timezone.utc).strftime('%a %b %d %H:%M:%S UTC %Y')
 os.environ['KBUILD_BUILD_VERSION']='1'
 cmd=['make','-C',str(K),'O='+str(O),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','LOCALVERSION=-g717bb3c9e13c-dirty','-j8','Image.gz-dtb']
 record.update(status='running',build_timestamp=os.environ['KBUILD_BUILD_TIMESTAMP']);row=dict(command=cmd,started=now());record['commands'].append(row);save()
 with (E/'Image.gz-dtb.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 row.update(exit=p.returncode,finished=now());record['compile_exit']=p.returncode;save()
 assert p.returncode==0,('Image.gz-dtb',p.returncode)
 assert sha(O/'.config')==sha(B/'out/.config')=='0fddb41316305c672b0afd0a64b2615c6dae3c5727f5ff4ead791272ff71b696'
 for n,h in original.items():assert sha(Path(n))==h,('original changed',n)
 for n,h in after.items():assert sha(K/n)==h,('owned source changed',n)
 assert sha(K/'drivers/clocksource/mtk_timer.c')==sha(B/'kernel/drivers/clocksource/mtk_timer.c')
 (E/'original-selected-inputs.json').write_text(json.dumps(dict(before=original,after={n:sha(Path(n)) for n in original},unchanged=True,no_full_tree_rehash=True),indent=2)+'\n')
 artifacts={}
 for n in ['arch/arm64/boot/Image.gz-dtb','arch/arm64/boot/Image','vmlinux','.config','include/generated/utsrelease.h','include/generated/compile.h']:
  p=O/n;artifacts[n]=dict(bytes=p.stat().st_size,sha256=sha(p))
 objects={}
 for n in ['arch/arm64/kernel/asus_retained_trace.o','arch/arm64/kernel/setup.o','drivers/clocksource/mtk_timer.o']:
  p=O/n;objects[n]=dict(bytes=p.stat().st_size,sha256=sha(p))
 (E/'build-receipt.json').write_text(json.dumps(dict(artifacts=artifacts,objects=objects,release=(O/'include/generated/utsrelease.h').read_text(),version=(O/'include/generated/compile.h').read_text(),build_timestamp=record['build_timestamp'],original_inputs_unchanged=True,resolved_config_byte_identical=True,config_delta={},physical_tested=False),indent=2)+'\n')
 record.update(status='complete',exit=0)
except BaseException as exc:
 record.update(status='failed',exit=1,error=repr(exc));traceback.print_exc()
finally:
 record['finished']=now();save();print(json.dumps(record),flush=True)
raise SystemExit(record['exit'])
