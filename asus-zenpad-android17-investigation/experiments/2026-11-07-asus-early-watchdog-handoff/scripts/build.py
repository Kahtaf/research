from pathlib import Path
import subprocess,os,json,hashlib,datetime,resource,traceback
from initcall_evidence import analyze
R=Path('/srv/android/asus-early-watchdog-handoff-20261107');K=R/'kernel';O=R/'out';E=R/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,obj):(E/n).write_text(json.dumps(obj,indent=2)+'\n')
assert not (E/'build-status.json').exists(),'Existing compile attempt refused'
assert json.loads((E/'prepare-status.json').read_text())['status']=='ready'
config=(O/'.config').read_bytes()
assert hashlib.sha256(config).hexdigest()=='708a88175ea777c09410000dfe5cf562ccbf764955eb9deaadda7326d0a966e1'
record=dict(status='preparing',started=now(),rlimit_as=list(resource.getrlimit(resource.RLIMIT_AS)),max_jobs=8,commands=[],compile_attempts=1,supervisor_timeout=None)
save('build-status.json',record)
try:
 assert resource.getrlimit(resource.RLIMIT_AS)==(-1,-1)
 for n in ['MAKEFLAGS','MFLAGS','KBUILD_OUTPUT','KCONFIG_CONFIG','LOCALVERSION','CROSS_COMPILE','KBUILD_BUILD_TIMESTAMP','KBUILD_BUILD_VERSION']:os.environ.pop(n,None)
 os.environ['TMPDIR']=str(R/'tmp');os.environ['KBUILD_BUILD_TIMESTAMP']=datetime.datetime.now(datetime.timezone.utc).strftime('%a %b %d %H:%M:%S UTC %Y');os.environ['KBUILD_BUILD_VERSION']='1'
 cmd=['make','-C',str(K),'O='+str(O),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','LOCALVERSION=-g717bb3c9e13c-dirty','-j8','Image.gz-dtb']
 record.update(status='running',build_timestamp=os.environ['KBUILD_BUILD_TIMESTAMP']);row=dict(command=cmd,started=now());record['commands'].append(row);save('build-status.json',record)
 with (E/'Image.gz-dtb.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 row.update(exit=p.returncode,finished=now());record['compile_exit']=p.returncode;save('build-status.json',record)
 assert p.returncode==0,('Compile failed; no source fix or rebuild',p.returncode)
 assert (O/'.config').read_bytes()==config
 pins=json.loads((E/'baseline-selected-pins.json').read_text());after={n:dict(bytes=Path(n).stat().st_size,sha256=sha(Path(n))) for n in pins};assert after==pins
 copied=json.loads((E/'source-copy.json').read_text());patch=json.loads((E/'patch-receipt.json').read_text());expected={n:v['sha256'] for n,v in copied.items()};expected['drivers/watchdog/mtk_wdt.c']=patch['after_sha256'];assert {n:sha(K/n) for n in expected}==expected
 save('input-preservation.json',dict(baseline_selected_pins_before=pins,baseline_selected_pins_after=after,unchanged=True,selected_copy_expected=expected,only_source_edit='drivers/watchdog/mtk_wdt.c',full_tree_rehash=False,config_byte_identical=True))
 linked=analyze(O/'vmlinux',3);assert not (O/'drivers/tty/serial/8250/8250_early.o').exists();linked['early_8250_object_absent']=True
 save('compiled-initcalls.json',linked)
 artifacts={n:dict(bytes=(O/n).stat().st_size,sha256=sha(O/n)) for n in ['arch/arm64/boot/Image.gz-dtb','arch/arm64/boot/Image','.config','System.map','vmlinux','include/generated/utsrelease.h','include/generated/compile.h']}
 save('build-receipt.json',dict(artifacts=artifacts,release=(O/'include/generated/utsrelease.h').read_text(),version=(O/'include/generated/compile.h').read_text(),config_byte_identical=True,config_delta={},source_edits=['drivers/watchdog/mtk_wdt.c'],physical_tested=False))
 log=E/'Image.gz-dtb.log';save('log-summary.json',dict(path=str(log),bytes=log.stat().st_size,sha256=sha(log),tail=log.read_text(errors='replace').splitlines()[-25:]))
 record.update(status='complete',exit=0)
except BaseException as exc:record.update(status='failed',exit=1,error=repr(exc));traceback.print_exc()
finally:
 record['finished']=now();save('build-status.json',record);print(json.dumps(record),flush=True)
raise SystemExit(record['exit'])
