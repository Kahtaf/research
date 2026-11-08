from pathlib import Path
import subprocess as s,json,hashlib,re
R=Path('/srv/android/asus-android17-runtime-prereqs');V=Path('/srv/android/asus-virtual-validation/kernel-fd');vr='fcb1b6c2de6348e2724981dcd520dec631ed5255';pr='717bb3c9e13ce573cfdd2dda856debd27a0fa17f'
paths=['fs/erofs','fs/ext4','fs/jbd2','drivers/android','drivers/md','drivers/block/loop.c','drivers/block/loop.h','security/selinux','security/security.c','security/lsm_audit.c','include/uapi/linux/android','include/uapi/linux/loop.h','include/linux/device-mapper.h','include/linux/lsm_hooks.h','include/linux/security.h']
def objects(rev):return {x.split('\t')[1]:x.split()[2] for x in s.check_output(['git','-C',str(V),'ls-tree','-r',rev,'--']+paths,text=True).splitlines()}
a=objects(vr);b=objects(pr);assert a==b
full=s.check_output(['git','-C',str(V),'diff',vr,pr],text=True);(R/'evidence/full-committed-kernel-difference.patch').write_text(full)
changed=s.check_output(['git','-C',str(V),'diff','--name-only',vr,pr],text=True).splitlines();assert changed==['drivers/irqchip/irq-gic-v3.c']
manifest={'virtual_commit':vr,'physical_commit':pr,'all_other_kernel_files_equal':True,'only_difference':changed,'selected_files':{p:{'git_blob':a[p],'sha256':hashlib.sha256((R/'kernel'/p).read_bytes()).hexdigest(),'bytes':(R/'kernel'/p).stat().st_size} for p in a}}
(R/'evidence/full-source-equivalence.json').write_text(json.dumps(manifest,indent=2)+'\n')
for n in ['r1','r2']:
 conf=R/f'build-{n}/.config'
 if conf.exists():(R/'evidence'/f'kernel-{n}.config').write_bytes(conf.read_bytes())
# Capture dependency/build IDs without transporting the ELF closure to the Mac.
elf=[]
for f in sorted((R/'inputs/root').rglob('*')):
 if not f.is_file() or f.read_bytes()[:4]!=b'\x7fELF':continue
 dyn=s.run(['readelf','-d',str(f)],stdout=s.PIPE,stderr=s.STDOUT,text=True).stdout
 notes=s.run(['readelf','-n',str(f)],stdout=s.PIPE,stderr=s.STDOUT,text=True).stdout
 elf.append({'path':str(f.relative_to(R/'inputs/root')),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size,'needed':re.findall(r'Shared library: \[(.*?)\]',dyn),'build_ids':re.findall(r'Build ID: (\w+)',notes)})
(R/'evidence/elf-manifest.json').write_text(json.dumps(elf,indent=2)+'\n')
T=Path('/srv/android/lineage24');repo=T/'frameworks/native'
commit=s.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
diff=s.check_output(['git','-C',str(repo),'diff',commit,'--','libs/binder'],text=True)
(R/'evidence/libbinder-source-diff.txt').write_text(diff)
(R/'evidence/libbinder-source-revision.json').write_text(json.dumps({'commit':commit,'binder_worktree_diff_empty_at_capture':not bool(diff),'note':'Probe headers are git-archived committed inputs; ELF double-read hash freeze from core Soong intermediate; no AOSP build invoked.'},indent=2)+'\n')
header_files={str(p.relative_to(R/'inputs/headers')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'inputs/headers').rglob('*') if p.is_file()}
(R/'evidence/header-hashes.json').write_text(json.dumps(header_files,indent=2)+'\n')
print('equivalent source files',len(a),'ELFs',len(elf),'header files',len(header_files))
