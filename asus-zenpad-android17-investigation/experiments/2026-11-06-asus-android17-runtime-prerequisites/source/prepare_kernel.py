from pathlib import Path
import subprocess as s, json,hashlib,shutil
R=Path('/srv/android/asus-android17-runtime-prereqs')
R.mkdir(exist_ok=True)
for p in ['source','inputs','evidence','artifacts','tests']: (R/p).mkdir(exist_ok=True)
virtual='/srv/android/asus-virtual-validation/kernel-fd'; vr='fcb1b6c2de6348e2724981dcd520dec631ed5255'
physical='/srv/android/asus-android17/kernel-bpf-fd'; pr='717bb3c9e13ce573cfdd2dda856debd27a0fa17f'
paths=['fs/erofs','drivers/android','drivers/block/loop.c','drivers/block/loop.h','drivers/md/dm-verity-target.c','drivers/md/dm-verity.h','drivers/md/dm-verity-fec.c','drivers/md/dm-verity-fec.h','drivers/md/dm.c','drivers/md/dm-table.c','include/uapi/linux/android','include/uapi/linux/loop.h','include/linux/device-mapper.h']
def inventory(repo,rev):
    lines=s.check_output(['git','-C',repo,'ls-tree','-r',rev,'--']+paths,text=True).splitlines()
    return {line.split('\t')[1]:line.split()[2] for line in lines}
v=inventory(virtual,vr); p=inventory(physical,pr)
assert v==p, 'Driver code differs; inspect before build'
manifest={'virtual_commit':vr,'physical_commit':pr,'equal_git_objects':v,'all_equal':v==p,'files':{}}
for path in v:
    blob=s.check_output(['git','-C',physical,'show',pr+':'+path])
    manifest['files'][path]={'sha256':hashlib.sha256(blob).hexdigest(),'bytes':len(blob)}
(R/'evidence/source-equivalence.json').write_text(json.dumps(manifest,indent=2)+'\n')
assert not (R/'kernel').exists()
(R/'kernel').mkdir()
a=s.Popen(['git','-C',virtual,'archive',vr],stdout=s.PIPE)
s.run(['tar','xf','-','-C',str(R/'kernel')],stdin=a.stdout,check=True); assert a.wait()==0
shutil.copyfile('/srv/android/asus-userspace-startup/checkpoint/kernel.config',R/'inputs/startup.config')
shutil.copyfile('/srv/android/asus-android17/bpf-fd-result/kernel.config',R/'inputs/physical.config')
(R/'build-r1').mkdir()
shutil.copyfile(R/'inputs/startup.config',R/'build-r1/.config')
print(json.dumps({'equivalent_files':len(v),'prepared':str(R)},indent=2))
