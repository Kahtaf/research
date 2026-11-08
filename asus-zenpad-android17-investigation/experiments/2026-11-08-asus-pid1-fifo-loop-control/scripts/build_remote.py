from pathlib import Path
import datetime,gzip,hashlib,json,os,resource,shutil,subprocess,sys,traceback,zlib
R=Path('/srv/android/asus-pid1-fifo-loop-control-20261108-f53fadc2');B=Path('/srv/android/asus-sparse-watchdog-observation-20261108-e0b1a1ba');K=R/'kernel';O=R/'out';E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(E/n).write_text(json.dumps(d,indent=2)+'\n')
def run(cmd,log):
 with (E/log).open('w') as f:q=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 assert q.returncode==0,(cmd,q.returncode,log)
 return cmd
assert not (E/'build-status.json').exists()
s=dict(status='running',helper_compiles=0,kernel_builds=0,rlimit_as=list(resource.getrlimit(resource.RLIMIT_AS)),walltime_cap=None)
save('build-status.json',s)
try:
 assert resource.getrlimit(resource.RLIMIT_AS)==(-1,-1)
 cmd=['/usr/bin/aarch64-linux-gnu-gcc','-static','-Os','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-Wall','-Wextra','-o',str(R/'artifacts/init.unstripped'),str(R/'source/init.c')]
 s['helper_compiles']=1;save('build-status.json',s);run(cmd,'helper-compile.log')
 run(['aarch64-linux-gnu-strip','-o',str(R/'artifacts/init'),str(R/'artifacts/init.unstripped')],'helper-strip.log')
 sys.path.insert(0,str(R/'source'));import bootformat as b
 entries={n:(0o040755,0,0,b'') for n in ['dev','proc','sys']};entries['init']=(0o100755,0,0,(R/'artifacts/init').read_bytes())
 payload=gzip.compress(b.make_cpio(entries),compresslevel=9,mtime=0)
 save('compiler-receipt.json',dict(command=cmd,strip='aarch64-linux-gnu-strip -o artifacts/init artifacts/init.unstripped',compiler_sha256=sha(Path(cmd[0])),source_sha256=sha(R/'source/init.c'),binary_sha256=sha(R/'artifacts/init'),binary_bytes=(R/'artifacts/init').stat().st_size,payload_bytes=len(payload),guard_end='0x4403f007',fits=0x44000000+len(payload)<=0x4403f007))
 assert 0x44000000+len(payload)<=0x4403f007,'STOP: actual gzip exceeds unchanged entry guard; no kernel build'
 (R/'artifacts/initramfs.cpio.gz').write_bytes(payload)
 # Isolate only after helper fits; reflink must succeed, no hardlinks or fallback copy.
 frozen={};preserved=['arch/arm64/boot/dts/mediatek/mt8163.dtsi','drivers/watchdog/mtk_wdt.c','kernel/sched/core.c','kernel/sched/rt.c','kernel/time/timekeeping.c','drivers/clocksource/arm_arch_timer.c','arch/arm64/lib/delay.c','drivers/misc/mediatek/Makefile']
 pins=json.loads((E/'prepost.json').read_text())
 for n,v in pins.items():
  if n!='init.c':assert sha(B/'kernel'/n)==v['before']
 selected=['out/.config','out/arch/arm64/boot/Image.gz-dtb','out/System.map','out/vmlinux']+['kernel/'+n for n in preserved if (B/'kernel'/n).is_file()]+['kernel/'+n for n in pins if n!='init.c']
 for tree in ['kernel','out']:
  for rel in ['.git/HEAD','.git/config','.git/index','.gitmodules','kernel/.git/HEAD','kernel/.git/config','kernel/.git/index']:
   if (B/tree/rel).is_file():selected.append(tree+'/'+rel)
 for n in selected:
  p=B/n;frozen[n]=dict(sha256=sha(p),inode=p.stat().st_ino,mtime_ns=p.stat().st_mtime_ns)
 assert frozen['out/.config']['sha256']=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
 assert frozen['out/arch/arm64/boot/Image.gz-dtb']['sha256']=='e6dd31eafb4ede2f202fea6dbc1a7996f494fdf6b421d3d33f2d07092863e7a6'
 for n in ['kernel','out']:run(['cp','-a','--reflink=always',str(B/n),str(R/n)],'copy-'+n+'.log')
 for n,v in frozen.items():assert sha(R/n)==v['sha256'] and (R/n).stat().st_ino!=v['inode']
 save('base-freeze.json',frozen)
 # Relocate copied dependency receipts, so unchanged objects remain incremental.
 relocated=[]
 for p in O.rglob('*'):
  if p.is_file() and not p.is_symlink() and (p.name.endswith('.cmd') or p==O/'Makefile'):
   data=p.read_bytes();new=data.replace(str(B).encode(),str(R).encode())
   if new!=data:p.write_bytes(new);relocated.append(str(p.relative_to(O)))
 if (O/'source').is_symlink():(O/'source').unlink()
 (O/'source').symlink_to(K)
 save('copy-receipt.json',dict(method='cp -a --reflink=always; independent inodes; nested repositories preserved',dependency_paths_relocated=relocated,config_changed=False))
 for n,v in pins.items():
  if n!='init.c':shutil.copyfile(R/'source'/n,K/n);assert sha(K/n)==v['after']
 config=(O/'.config').read_bytes()
 before_objects={str(p.relative_to(O)):(p.stat().st_mtime_ns,p.stat().st_size) for p in O.rglob('*.o')}
 for n in ['MAKEFLAGS','MFLAGS','KBUILD_OUTPUT','KCONFIG_CONFIG','LOCALVERSION','CROSS_COMPILE','KBUILD_BUILD_TIMESTAMP','KBUILD_BUILD_VERSION']:os.environ.pop(n,None)
 os.environ.update(TMPDIR=str(R/'tmp'),KBUILD_BUILD_TIMESTAMP=datetime.datetime.now(datetime.timezone.utc).strftime('%a %b %d %H:%M:%S UTC %Y'),KBUILD_BUILD_VERSION='1')
 cmd=['make','-C',str(K),'O='+str(O),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','LOCALVERSION=-g717bb3c9e13c-dirty','-j8','Image.gz-dtb']
 s.update(kernel_builds=1,kernel_command=cmd);save('build-status.json',s);run(cmd,'compile-1.log')
 assert (O/'.config').read_bytes()==config==(B/'out/.config').read_bytes() and (O/'source').resolve()==K
 for n,v in frozen.items():
  p=B/n;assert sha(p)==v['sha256'] and p.stat().st_ino==v['inode'] and p.stat().st_mtime_ns==v['mtime_ns']
 for n in preserved:
  if (B/'kernel'/n).is_file():assert (B/'kernel'/n).read_bytes()==(K/n).read_bytes()
 changed_objects=[str(p.relative_to(O)) for p in O.rglob('*.o') if before_objects.get(str(p.relative_to(O)))!=(p.stat().st_mtime_ns,p.stat().st_size)]
 def unzip(p):
  d=zlib.decompressobj(31);raw=d.decompress(p.read_bytes());assert d.eof;return raw,d.unused_data
 raw,dt=unzip(O/'arch/arm64/boot/Image.gz-dtb');_,bdt=unzip(B/'out/arch/arm64/boot/Image.gz-dtb');assert dt==bdt
 i=json.loads((E/'identity.json').read_text());assert i['mode'].encode() in raw and ('ASUS49-ENTRY run='+i['kernel_uuid']).encode() in raw
 assert not any((x+' uuid=').encode() in raw for x in ['A49CAP1','A49SW2','A49WD1','A49PS1','A49PM1','A49DL1'])
 names=['arch/arm64/boot/Image.gz-dtb','.config','System.map','vmlinux']
 save('build-receipt.json',dict(artifacts={n:dict(bytes=(O/n).stat().st_size,sha256=sha(O/n)) for n in names},config_byte_identical=True,compiled_DT_byte_identical=True,base_scoped_freeze_unchanged=True,preserved_sources=preserved,changed_objects=changed_objects,helper_compiles=1,kernel_builds=1,hot_header_tags_absent=True))
 # Focused disassembly of actual helper and linked sparse writer; no emulator/harness.
 nm=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(R/'artifacts/init.unstripped')],text=True)
 (E/'helper-symbols.txt').write_text('\n'.join(l for l in nm.splitlines() if any(x in l.split()[-1] for x in ['main','observe','monotonic_clock','finish','event'])))
 for target,binary,symbols in [('helper',R/'artifacts/init.unstripped',['main','observe','monotonic_clock','finish']),('kernel',O/'vmlinux',['asus_retained_trace_write','sparse_admit','trace_init'])]:
  dis=''
  for sym in symbols:dis+=subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--disassemble='+sym,str(binary)],text=True)
  (E/(target+'-scoped.disasm')).write_text(dis)
 obj=O/'arch/arm64/kernel/asus_retained_trace.o'
 (E/'retained-object.disasm').write_text(subprocess.check_output(['aarch64-linux-gnu-objdump','-dr',str(obj)],text=True))
 (E/'retained-object.nm').write_text(subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(obj)],text=True))
 # Preserve RT source defaults without changing them.
 rt='\n'.join(l for l in (K/'kernel/sched/core.c').read_text().splitlines() if 'sysctl_sched_rt_' in l or '950000' in l or '1000000' in l)
 (E/'rt-default-source.txt').write_text(rt+'\n')
 s.update(status='complete')
except BaseException as exc:
 s.update(status='failed',error=repr(exc));traceback.print_exc()
finally:save('build-status.json',s)
print(json.dumps(s));sys.exit(0 if s['status']=='complete' else 1)
