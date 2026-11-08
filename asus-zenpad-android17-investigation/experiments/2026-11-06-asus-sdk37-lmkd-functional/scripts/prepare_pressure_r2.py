from pathlib import Path
import subprocess as s,shutil,os,json,sys,resource,re,hashlib
R=Path('/srv/android/asus-sdk37-lmkd-functional');name=sys.argv[1];assert re.fullmatch('r[0-9]+',name);mode=sys.argv[2];assert mode in ['startup','compressible','incompressible','invalid-window','old-strategy'];I=R/('inputs/fixture-'+name);I.mkdir();root=I/'root';shutil.copytree(R/'inputs/fixture-r4/root',root,symlinks=True);shutil.copyfile(R/'inputs/fixture-r4/fstab.mt8163',I/'fstab.mt8163')
for x in json.loads((R/'inputs/native-r3/manifest.json').read_text()):
 f=R/'inputs/native-r3'/x['name'];assert hashlib.sha256(f.read_bytes()).hexdigest()==x['sha256'];dest=root/'system'/('lib64' if f.name.endswith('.so') else 'bin')/f.name;shutil.copyfile(f,dest);dest.chmod(0o755)
for n in ['libc.so','libm.so','libdl.so']:shutil.copyfile(root/'system/lib64'/n,root/'system/lib64/bootstrap'/n)
shutil.copyfile(root/'system/bin/linker64',root/'system/bin/bootstrap/linker64');os.symlink('/system/bin/toybox',root/'system/bin/mkswap')
source='pressure_harness_r2.c' if mode in ['compressible','incompressible'] else 'daemon_observer.c'
cmd=['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra','-Werror','-I'+str(R/'inputs/lmkd/include'),str(R/'source'/source),'-o',str(root/'system/bin/firstboot-observer')]
def limits():
 os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(90,90))
p=s.run(cmd,capture_output=True,text=True,preexec_fn=limits);(I/'compile.json').write_text(json.dumps({'argv':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2));assert p.returncode==0,p.stderr
rc=root/'system/etc/init/hw/init.rc';rc.write_text(rc.read_text().replace('service memory-observer /system/bin/firstboot-observer','service memory-observer /system/bin/firstboot-observer '+mode))
props=root/'system/etc/prop.default'
if mode=='invalid-window':props.write_text(props.read_text()+'ro.lmk.psi_window_size_ms=100\n')
if mode=='old-strategy':props.write_text(props.read_text().replace('ro.lmk.use_new_strategy=true','ro.lmk.use_new_strategy=false'))
(I/'boundary.json').write_text(json.dumps({'mode':mode,'production_policy_unchanged':True,'enforcing':True,'observer_domain':'su instrumentation','log_capture':'diagnostic datagram receiver, socket labeled logd, not genuine logd','daemon_uid':1069,'daemon_capabilities':'unchanged from genuine lmkd.rc','framework_GMS_boot':False,'service_graph':'fixture-only, no fake readiness properties','delta':'lmkd oneshot without critical restart; ro.lmk.debug=true; mkswap symlink; genuine init props'},indent=2))
(I/'root-manifest.json').write_text(json.dumps([{'path':str(f.relative_to(root)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in root.rglob('*') if f.is_file() and not f.is_symlink()],indent=2));print('prepared',name,mode)
