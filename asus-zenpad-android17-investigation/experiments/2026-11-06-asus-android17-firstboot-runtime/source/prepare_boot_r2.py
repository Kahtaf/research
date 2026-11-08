from pathlib import Path
import subprocess as s,hashlib,json,shlex,shutil,os
R=Path('/srv/android/asus-firstboot-runtime');T=Path('/srv/android/lineage24');I=R/'inputs/boot-r2';I.mkdir();W=I/'work';W.mkdir();root=I/'root';shutil.copytree(R/'inputs/early-r1/root',root);(root/'policy').unlink();manifest=[];commands=[]
def freeze(src,dst):
 src=Path(src);d=src.read_bytes();assert hashlib.sha256(d).digest()==hashlib.sha256(src.read_bytes()).digest();dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();dst.write_bytes(d);dst.chmod(src.stat().st_mode&0o777);manifest.append(dict(source=str(src),destination=str(dst.relative_to(I)),sha256=hashlib.sha256(d).hexdigest(),bytes=len(d)));return dst
wanted={p+'_file_contexts' for p in ['plat','vendor','system_ext','product']}|{p+'_property_contexts' for p in ['plat','vendor','system_ext','product']}
for idx in [8,9]:
 name=''
 for line in (T/f'out/soong/build.lineage_p00a.{idx}.ninja').open():
  if line.startswith('# Module:'):name=line.split(':',1)[1].strip()
  if name not in wanted or not line.startswith('    command = echo >'):continue
  command=line.strip()[len('command = '):];(I/(name+'.ninja-command')).write_text(command+'\n')
  parts=shlex.split(command.split(' && ')[1].split(' > ')[0]);argv=[]
  for x in parts:
   if x.startswith(('system/','device/','prebuilts/')):
    f=I/'source'/x
    if not f.exists():freeze(T/x,f)
    argv.append(str(f))
   elif x.endswith('/newline'):
    f=W/'newline';f.write_text('\n');argv.append(str(f))
   else:argv.append(x)
  p=s.run(argv,capture_output=True,text=True);commands.append(dict(command=argv,returncode=p.returncode,stderr=p.stderr));assert p.returncode==0,p.stderr
  # Same comment/empty-line removal as the file-context rule. Property contexts retain comments.
  data='\n'.join(l.split('#')[0] for l in p.stdout.splitlines() if l.split('#')[0])+'\n' if name.endswith('file_contexts') else p.stdout
  dest=W/name;dest.write_text(data)
  if name=='vendor_file_contexts':
   tool=freeze(T/'system/sepolicy/tests/fc_sort.py',I/'tools/fc_sort.py');cmd=['python3',str(tool),'-i',str(dest),'-o',str(W/(name+'.sorted'))];p=s.run(cmd,capture_output=True,text=True);commands.append(dict(command=cmd,returncode=p.returncode,stderr=p.stderr));assert p.returncode==0,p.stderr;shutil.copyfile(W/(name+'.sorted'),dest)
  prefix=name.split('_')[0] if not name.startswith('system_ext') else 'system_ext'
  part={'plat':'system','vendor':'system/vendor','product':'system/product','system_ext':'system/system_ext'}[prefix]
  target=root/part/'etc/selinux'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(dest,target)
# Genuine compiler-produced split policy. Identity files follow the product's sha256(cat(cil,mapping)) rule.
P=R/'inputs/early-r1/compiled-policy'
for prefix,part in [('plat','system'),('vendor','system/vendor'),('system_ext','system/system_ext'),('product','system/product')]:
 f=next((P/(prefix+'_sepolicy.cil')).rglob(prefix+'_sepolicy.cil'));dest=root/part/'etc/selinux';dest.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest/f.name)
 if prefix!='vendor':
  mapping=next((P/(prefix+'_mapping_file')).rglob('202704.cil'));(dest/'mapping').mkdir();shutil.copyfile(mapping,dest/'mapping/202704.cil');digest=hashlib.sha256(f.read_bytes()+mapping.read_bytes()).hexdigest()+'\n'
  (dest/(prefix+'_sepolicy_and_mapping.sha256')).write_text(digest)
  vd=root/'system/vendor/etc/selinux';vd.mkdir(parents=True,exist_ok=True);(vd/('precompiled_sepolicy.'+prefix+'_sepolicy_and_mapping.sha256')).write_text(digest)
vd=root/'system/vendor/etc/selinux';shutil.copyfile(R/'inputs/early-r1/root/policy',vd/'precompiled_sepolicy');(vd/'plat_sepolicy_vers.txt').write_text('202704\n')
for f in (P/'plat_pub_versioned.cil').rglob('plat_pub_versioned.cil'):shutil.copyfile(f,vd/f.name)
# Required top-level mountpoints and nested partition layout.
for d in ['dev','proc','sys','mnt','data','metadata','apex','bootstrap-apex','linkerconfig','debug_ramdisk','second_stage_resources','tmp','system/etc/init/hw','system/vendor/etc/init/hw']:(root/d).mkdir(parents=True,exist_ok=True)
for n,target in [('vendor','/system/vendor'),('product','/system/product'),('system_ext','/system/system_ext'),('init','/system/bin/init'),('etc','/system/etc')]:os.symlink(target,root/n)
# Actual ELF init uses the bootstrap interpreter and core bootstrap libraries.
(root/'system/bin/bootstrap').mkdir(exist_ok=True);shutil.copyfile(root/'system/bin/linker64',root/'system/bin/bootstrap/linker64')
(root/'system/lib64/bootstrap').mkdir(exist_ok=True)
for n in ['libc.so','libm.so','libdl.so']:shutil.copyfile(root/'system/lib64'/n,root/'system/lib64/bootstrap'/n)
for f in (root/'system/bin').rglob('*'):
 if f.is_file():f.chmod(0o755)
for f in (R/'inputs/early-r1/source/system/core/rootdir').glob('*.rc'):shutil.copyfile(f,root/'system/etc/init/hw'/f.name)
for f in (R/'inputs/early-r1/source/device/asus/p00a/rootdir').glob('*.rc'):shutil.copyfile(f,root/'system/vendor/etc/init/hw'/f.name)
orig=(R/'inputs/early-r1/source/device/asus/p00a/rootdir/fstab.mt8163').read_text();data=orig.replace('/dev/block/platform/soc/11230000.mmc/by-name/system','/dev/block/vda').replace('/dev/block/platform/soc/11230000.mmc/by-name/userdata','/dev/block/vdb');(I/'fstab.mt8163').write_text(data);(root/'system/vendor/etc/fstab.mt8163').write_text(data)
# Capture generated build properties where available; do not invent readiness properties.
for module,part in [('system','system'),('vendor','system/vendor'),('system_ext','system/system_ext'),('product','system/product')]:
 src=T/f'out/soong/.intermediates/build/soong/{module}-build.prop/android_common/build.prop'
 if src.exists():freeze(src,root/part/'build.prop')
# Host labels/image construction tools are copied completed outputs, run only on this fixture.
for n in ['e2fsdroid','sefcontext_compile']:
 freeze(T/'out/host/linux-x86/bin'/n,I/'tools'/n)
ctx='\n'.join((W/(p+'_file_contexts')).read_text() for p in ['plat','system_ext','product','vendor']);(W/'file_contexts').write_text(ctx)
cmd=[str(I/'tools/sefcontext_compile'),'-o',str(W/'file_contexts.bin'),str(W/'file_contexts')];p=s.run(cmd,capture_output=True,text=True);commands.append(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,p.stderr
(I/'manifest.json').write_text(json.dumps(manifest,indent=2));(I/'commands.json').write_text(json.dumps(commands,indent=2));print('boot inputs prepared',len(manifest))
