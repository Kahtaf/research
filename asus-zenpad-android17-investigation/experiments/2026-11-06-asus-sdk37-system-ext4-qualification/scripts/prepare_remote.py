import os,resource,pathlib,json,hashlib,subprocess,shutil,re,ast,types,uuid,logging
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(120,120))
P=pathlib.Path;R=P('/srv/android/asus-sdk37-system-ext4-qualification-20261106');F=R/'fixture-r1';F.mkdir();(F/'bin').mkdir();(F/'lib64').mkdir();(F/'sources').mkdir();(F/'tmp').mkdir();os.environ['TMPDIR']=str(F/'tmp')
plan=json.loads(P('/srv/android/asus-reviewed-build-kit/r8/inputs/plan.json').read_text());A=P(plan['aosp']);H=A/'out/host/linux-x86';K=P('/srv/android/asus-sdk37-lmkd-functional/kernel-memory-r1');copies=[]
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def copy(p,q):
 before=sha(p);shutil.copyfile(p,q);P(q).chmod(P(p).stat().st_mode & 0o777);copied=sha(q);after=sha(p);assert before==copied==after;copies.append(dict(source=str(p),copy=str(q),before=before,copied=copied,after=after));return q
for n in ['mke2fs','e2fsdroid','e2fsck','simg2img','debugfs']:
 p=H/'bin'/n;copy(p,F/'bin'/n)
 deps=subprocess.check_output(['ldd',str(p)],text=True)
 for x in re.findall(r'=> (\S+)',deps):
  p=P(x)
  if str(H) in str(p) and not (F/'lib64'/p.name).exists():copy(p,F/'lib64'/p.name)
for n in ['qemu-system-aarch64','aarch64-linux-gnu-gcc']:
 p=P(shutil.which(n));copy(p,F/'bin'/n)
# Freeze runtime dynamic dependencies as well; binaries retain system interpreter.
for p in list((F/'bin').iterdir()):
 deps=subprocess.check_output(['ldd',str(p)],text=True,stderr=subprocess.STDOUT)
 for x in re.findall(r'=> (\S+)',deps):
  p=P(x)
  if p.exists() and not (F/'lib64'/p.name).exists():copy(p,F/'lib64'/p.name)
copy(K/'out/arch/arm64/boot/Image',F/'Image');assert sha(F/'Image')=='c59e030cdfc3e752eeddbbf62d091ae9760c94d5fbf780a22824e004ec872080'
for p in [K/'out/.config',A/'system/extras/ext4_utils/mke2fs.conf',A/'system/extras/ext4_utils/mkuserimg_mke2fs.py',A/'build/make/tools/releasetools/build_image.py',A/'system/core/libcutils/fs_config.cpp',A/'external/e2fsprogs/contrib/android/fs_config.c',A/'external/e2fsprogs/contrib/android/perms.c']:
 if p.exists():copy(p,F/'sources'/p.name)
os.environ['LD_LIBRARY_PATH']=str(F/'lib64');os.environ['MKE2FS_CONFIG']=str(F/'sources/mke2fs.conf')
root=F/'input';(root/'system/etc').mkdir(parents=True);(root/'system/bin').mkdir();(F/'target-out').mkdir()
(root/'system/etc/fixture.txt').write_text('SDK37 SYSTEM ext4 fixture\n')
(root/'system/bin/run-as').write_text('nonexecutable fixture content\n');(root/'system/bin/ping').write_text('capability fixture content\n');(root/'system/bin/link').symlink_to('../etc/fixture.txt')
contexts=F/'file_contexts';contexts.write_text('/ u:object_r:rootfs:s0\n/system(/.*)? u:object_r:system_file:s0\n')
# Execute only public argument-construction functions; no build_image IO or captured Ninja commands.
build=P(F/'sources/build_image.py').read_text();tree=ast.parse(build);names={'BuildImageMkfs','SetUUIDIfNotExist'};ns={'os':os,'uuid':uuid,'logger':logging.getLogger('fixture'),'RunE2fsck':lambda x:None}
commands=[];ns['common']=types.SimpleNamespace(RunAndCheckOutput=lambda cmd,**kwargs:commands.append(cmd) or '')
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'captured_build_image.py','exec'),ns)
props=dict(fs_type='ext4',ext_mkuserimg='mkuserimg_mke2fs',extfs_sparse_flag='-s',mount_point='/',image_size=str(64*1024**2),journal_size='0',extfs_rsv_pct='0',skip_fsck='true',selinux_fc=str(contexts))
ns['SetUUIDIfNotExist'](props);ns['BuildImageMkfs'](str(root),props,str(F/'system.sparse'),str(F/'target-out'),None)
import importlib.util
spec=importlib.util.spec_from_file_location('mkuserimg_source',F/'sources/mkuserimg_mke2fs.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
args=mod.ParseArguments(commands[0][1:]);mk,fill=mod.ConstructE2fsCommands(args)
def run(cmd,name,env=None):
 p=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=60);(F/(name+'.log')).write_text(json.dumps(cmd)+'\n'+p.stdout+'\nexit='+str(p.returncode)+'\n');return p
for cmd,name in [(mk,'mke2fs'),(fill,'e2fsdroid')]:
 cmd[0]=str(F/'bin'/cmd[0]);p=run(cmd,name);assert p.returncode==0,p.stdout
p=run([str(F/'bin/simg2img'),str(F/'system.sparse'),str(F/'system.raw')],'simg2img');assert p.returncode==0,p.stdout
# Non-writing large-size resolution; no full image is created.
cmd=mk.copy();cmd.insert(1,'-n');cmd.insert(1,'-v');cmd[-2]=str(F/'size-only-never-created');cmd[-1]=str(3753902080//4096)
p=run(cmd,'full-size-noaction');assert p.returncode==0,p.stdout;assert not (F/'size-only-never-created').exists()
for query,n in [('stats','stats'),('stat /system/bin/run-as','run-as-stat'),('ea_list /system/bin/run-as','run-as-xattrs'),('stat /system/bin/ping','ping-stat'),('ea_list /system/bin/ping','ping-xattrs')]:
 p=run([str(F/'bin/debugfs'),'-R',query,str(F/'system.raw')],n);assert p.returncode==0
p=run([str(F/'bin/e2fsck'),'-f','-n',str(F/'system.raw')],'e2fsck-before');assert p.returncode==0,p.stdout
# One meaningful negative: unknown incompat bit; checksum-free superblock (no metadata_csum).
neg=F/'unsupported.raw';shutil.copyfile(F/'system.raw',neg)
import struct
with neg.open('r+b') as f:
 f.seek(1024+96);old=struct.unpack('<I',f.read(4))[0];f.seek(1024+96);f.write(struct.pack('<I',old|0x80000000))
result={'fixture':str(F),'copies':copies,'properties':props,'wrapper_argv':commands[0],'mke2fs_argv':mk,'e2fsdroid_argv':fill,'specimen_raw_sha256':sha(F/'system.raw'),'specimen_raw_bytes':(F/'system.raw').stat().st_size,'sparse_sha256':sha(F/'system.sparse'),'negative':{'changed_offset':1120,'old':old,'new':old|0x80000000},'public_fs_config':(F/'sources/fs_config.cpp').read_text(),'logs':{p.name:p.read_text() for p in F.glob('*.log')}}
(F/'preparation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
