from pathlib import Path
import subprocess,os,json,hashlib,datetime,resource,traceback
R=Path('/srv/android/asus-early-uart-disabled-kernel-20261107');B=Path('/srv/android/asus-usb-retained-log-kernel-build-20261107');K=R/'kernel';O=R/'out';E=R/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,obj):(E/n).write_text(json.dumps(obj,indent=2)+'\n')
assert not (E/'build-status.json').exists(),'Existing compile attempt refused'
prep=json.loads((E/'prepare-status.json').read_text());assert prep['status']=='configured_awaiting_dependency_gate'
expected={'CONFIG_SERIAL_8250_CONSOLE','CONFIG_SERIAL_EARLYCON','CONFIG_SERIAL_CORE_CONSOLE','CONFIG_SERIAL_8250_FSL'}
assert set(prep['config_delta'])==expected and all(x['before']=='y' and x['after']=='n' for x in prep['config_delta'].values()),'Non-console config delta; stop'
config=(O/'.config').read_bytes();assert sha(O/'.config')==prep['config_sha256']
for line in [b'CONFIG_SERIAL_8250=y\n',b'CONFIG_SERIAL_8250_MT6577=y\n',b'CONFIG_SERIAL_CORE=y\n',b'CONFIG_FIX_EARLYCON_MEM=y\n']:assert line in config
save('dependency-gate.json',dict(accepted=True,intentional=['CONFIG_SERIAL_8250_CONSOLE'],derived={'CONFIG_SERIAL_EARLYCON':'selected by SERIAL_8250_CONSOLE; no remaining selector enabled','CONFIG_SERIAL_CORE_CONSOLE':'selected by SERIAL_8250_CONSOLE; no remaining selector enabled','CONFIG_SERIAL_8250_FSL':'depends on SERIAL_8250_CONSOLE; default ARM64'},actual_delta=prep['config_delta'],mapping_support='CONFIG_FIX_EARLYCON_MEM=y preserved; unconditional arm64 def_bool y; logger early_memremap unchanged',non_console_config_changes=[],source_edits=[]))
record=dict(status='preparing',started=now(),rlimit_as=list(resource.getrlimit(resource.RLIMIT_AS)),max_jobs=8,commands=[],compile_attempts=1,source_edits=[],supervisor_timeout=None)
save('build-status.json',record)
try:
 assert resource.getrlimit(resource.RLIMIT_AS)==(-1,-1)
 for n in ['MAKEFLAGS','MFLAGS','KBUILD_OUTPUT','KCONFIG_CONFIG','LOCALVERSION','CROSS_COMPILE','KBUILD_BUILD_TIMESTAMP','KBUILD_BUILD_VERSION']:os.environ.pop(n,None)
 os.environ['TMPDIR']=str(R/'tmp');os.environ['KBUILD_BUILD_TIMESTAMP']=datetime.datetime.now(datetime.timezone.utc).strftime('%a %b %d %H:%M:%S UTC %Y');os.environ['KBUILD_BUILD_VERSION']='1'
 cmd=['make','-C',str(K),'O='+str(O),'ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-','HOSTCC=gcc','HOSTCXX=g++','LOCALVERSION=-g717bb3c9e13c-dirty','-j8','Image.gz-dtb']
 record.update(status='running',build_timestamp=os.environ['KBUILD_BUILD_TIMESTAMP']);row=dict(command=cmd,started=now());record['commands'].append(row);save('build-status.json',record)
 with (E/'Image.gz-dtb.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 row.update(exit=p.returncode,finished=now());record['compile_exit']=p.returncode;save('build-status.json',record)
 assert p.returncode==0,('compile failed; no retry',p.returncode)
 assert (O/'.config').read_bytes()==config
 pins=json.loads((E/'baseline-selected-pins.json').read_text());after={n:dict(bytes=Path(n).stat().st_size,sha256=sha(Path(n))) for n in pins};assert after==pins
 copied=json.loads((E/'source-copy.json').read_text());source_after={n:sha(K/n) for n in copied};assert source_after=={n:v['sha256'] for n,v in copied.items()}
 save('original-selected-inputs.json',dict(before=pins,after=after,unchanged=True,copied_source_after=source_after,source_edits=[],full_tree_rehash=False))
 cmd=['aarch64-linux-gnu-nm','-a',str(O/'vmlinux')];p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0
 names={l.split()[-1] for l in p.stdout.splitlines() if l.split()}
 early=['serial8250_early_in','serial8250_early_out','early_serial8250_setup','early_serial8250_write','__earlycon_uart8250','__earlycon_uart']
 assert not any(any(n==s or n.startswith(s+'.') for n in names) for s in early)
 selected=sorted(n for n in names if any(t in n for t in ['serial8250','mtk8250','retained','early_memremap','early_ioremap']))
 assert any('mtk8250' in n for n in selected) and 'serial8250_register_8250_port' in names and 'early_memremap' in names
 maptext=(O/'System.map').read_text();assert all(s not in maptext for s in early)
 assert not (O/'drivers/tty/serial/8250/8250_early.o').exists()
 save('linked-image-assertions.json',dict(linked_image=str(O/'vmlinux'),nm_command=cmd,nm_exit=p.returncode,absent_symbols=early,absent_in_nm_and_System_map=True,early_8250_object_absent=True,preserved_selected_symbols=selected,assertion_scope='actual linked compile/config assertion; no driver simulation or physical test'))
 artifacts={n:dict(bytes=(O/n).stat().st_size,sha256=sha(O/n)) for n in ['arch/arm64/boot/Image.gz-dtb','arch/arm64/boot/Image','.config','System.map','vmlinux','include/generated/utsrelease.h','include/generated/compile.h']}
 save('build-receipt.json',dict(artifacts=artifacts,release=(O/'include/generated/utsrelease.h').read_text(),version=(O/'include/generated/compile.h').read_text(),build_timestamp=record['build_timestamp'],original_inputs_unchanged=True,config_delta=prep['config_delta'],source_edits=[],physical_tested=False))
 record.update(status='complete',exit=0)
except BaseException as exc:record.update(status='failed',exit=1,error=repr(exc));traceback.print_exc()
finally:
 record['finished']=now();save('build-status.json',record);print(json.dumps(record),flush=True)
raise SystemExit(record['exit'])
