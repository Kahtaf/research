from pathlib import Path
import subprocess,os,json,hashlib,datetime,shutil,resource,traceback,re,difflib
R=Path('/srv/android/asus-early-uart-disabled-kernel-20261107');B=Path('/srv/android/asus-usb-retained-log-kernel-build-20261107');K=R/'kernel';O=R/'out';E=R/'evidence'
LOGGER='arch/arm64/kernel/asus_retained_trace.c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,obj):(E/n).write_text(json.dumps(obj,indent=2)+'\n')
def cfg(p):
 d={}
 for l in p.read_text().splitlines():
  if l.startswith('CONFIG_'):k,v=l.split('=',1);d[k]=v
  elif l.startswith('# CONFIG_') and l.endswith(' is not set'):d[l[2:-11]]='n'
 return d
assert not K.exists() and not O.exists() and not (E/'prepare-status.json').exists(),'Existing owned attempt refused'
record=dict(status='preparing',rlimit_as=list(resource.getrlimit(resource.RLIMIT_AS)),source_edits=[],copy_method='ordinary cp -a, independent inodes; no hardlinks',full_tree_rehash=False)
save('prepare-status.json',record)
try:
 assert resource.getrlimit(resource.RLIMIT_AS)==(-1,-1)
 assert shutil.disk_usage(R).free>25*1024**3
 selected=[B/'out/.config',B/'out/arch/arm64/boot/Image.gz-dtb',B/'out/System.map']+[B/'kernel'/n for n in [LOGGER,'arch/arm64/kernel/setup.c','arch/arm64/Kconfig','drivers/tty/serial/8250/Kconfig','drivers/tty/serial/8250/Makefile','drivers/tty/serial/8250/8250_early.c','drivers/tty/serial/Kconfig']]
 pins={str(p):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in selected}
 assert pins[str(B/'out/.config')]==dict(bytes=126511,sha256='0fddb41316305c672b0afd0a64b2615c6dae3c5727f5ff4ead791272ff71b696')
 assert pins[str(B/'out/arch/arm64/boot/Image.gz-dtb')]==dict(bytes=7716878,sha256='ec6e0839d9a6bcdd4be376edc9cb879b4b27cb76097948d244d99d2102dcc438')
 assert sha(B/'kernel'/LOGGER)=='8373baa301650d2bf3befe547df11a3079e22c51aec8a207de64eae0f1bb3348'
 save('baseline-selected-pins.json',pins)
 subprocess.run(['cp','-a',str(B/'kernel'),str(K)],check=True)
 independence={str(p.relative_to(B/'kernel')):dict(sha256=sha(K/p.relative_to(B/'kernel')),independent_inode=(p.stat().st_dev,p.stat().st_ino)!=((K/p.relative_to(B/'kernel')).stat().st_dev,(K/p.relative_to(B/'kernel')).stat().st_ino)) for p in selected if p.is_relative_to(B/'kernel')}
 assert all(v['independent_inode'] and v['sha256']==pins[str(B/'kernel'/n)]['sha256'] for n,v in independence.items())
 save('source-copy.json',independence)
 O.mkdir();shutil.copyfile(B/'out/.config',O/'.config')
 old=(O/'.config').read_text();assert old.count('CONFIG_SERIAL_8250_CONSOLE=y\n')==1
 (O/'.config').write_text(old.replace('CONFIG_SERIAL_8250_CONSOLE=y\n','# CONFIG_SERIAL_8250_CONSOLE is not set\n'))
 for n in ['MAKEFLAGS','MFLAGS','KBUILD_OUTPUT','KCONFIG_CONFIG','LOCALVERSION','CROSS_COMPILE','KBUILD_BUILD_TIMESTAMP','KBUILD_BUILD_VERSION']:os.environ.pop(n,None)
 os.environ['TMPDIR']=str(R/'tmp')
 cmd=['make','-C',str(K),'O='+str(O),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','LOCALVERSION=-g717bb3c9e13c-dirty','olddefconfig']
 with (E/'olddefconfig.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 record.update(olddefconfig_command=cmd,olddefconfig_exit=p.returncode)
 assert p.returncode==0
 before,after=cfg(B/'out/.config'),cfg(O/'.config')
 delta={n:dict(before=before.get(n,'n'),after=after.get(n,'n'),before_present=n in before,after_present=n in after) for n in before.keys()|after.keys() if before.get(n,'n')!=after.get(n,'n')}
 save('config-delta.json',delta)
 (E/'config.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),(O/'.config').read_text().splitlines(True),fromfile='baseline/.config',tofile='out/.config')))
 record.update(status='configured_awaiting_dependency_gate',config_sha256=sha(O/'.config'),config_delta=delta)
except BaseException as exc:record.update(status='failed',error=repr(exc));traceback.print_exc()
finally:save('prepare-status.json',record);print(json.dumps(record))
raise SystemExit(0 if record['status']=='configured_awaiting_dependency_gate' else 1)
