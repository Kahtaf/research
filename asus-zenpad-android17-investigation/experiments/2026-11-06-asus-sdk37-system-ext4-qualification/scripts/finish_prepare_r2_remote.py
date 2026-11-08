import os,resource,pathlib,json,hashlib,subprocess,shutil,struct
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(120,120))
P=pathlib.Path;R=P('/srv/android/asus-sdk37-system-ext4-qualification-20261106');F=R/'fixture-r2';os.environ.update(LD_LIBRARY_PATH=str(F/'lib64'),MKE2FS_CONFIG=str(F/'sources/mke2fs.conf'),TMPDIR=str(F/'tmp'))
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def run(cmd,name):
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=60);(F/(name+'.log')).write_text(json.dumps(cmd)+'\n'+p.stdout+'\nexit='+str(p.returncode)+'\n');return p
mk=json.loads((F/'mke2fs.log').read_text().splitlines()[0]);fill=json.loads((F/'e2fsdroid.log').read_text().splitlines()[0])
assert not (F/'system-restored.raw').exists()
p=run([str(F/'bin/simg2img'),str(F/'system.sparse'),str(F/'system-restored.raw')],'simg2img-restored');assert p.returncode==0,p.stdout
for query,n in [('stats','stats'),('stat /system/bin/run-as','run-as-stat'),('ea_list /system/bin/run-as','run-as-xattrs'),('stat /system/bin/ping','ping-stat'),('ea_list /system/bin/ping','ping-xattrs')]:
 p=run([str(F/'bin/debugfs'),'-R',query,str(F/'system-restored.raw')],n);assert p.returncode==0
p=run([str(F/'bin/e2fsck'),'-f','-n',str(F/'system-restored.raw')],'e2fsck-before');assert p.returncode==0,p.stdout
neg=F/'unsupported.raw';assert not neg.exists();shutil.copyfile(F/'system-restored.raw',neg)
with neg.open('r+b') as f:
 f.seek(1120);old=struct.unpack('<I',f.read(4))[0];f.seek(1120);f.write(struct.pack('<I',old|0x80000000))
result={'fixture':str(F),'copies':json.loads((F/'copy-receipt.json').read_text()),'mke2fs_argv':mk,'e2fsdroid_argv':fill,'specimen_raw_sha256':sha(F/'system-restored.raw'),'specimen_raw_bytes':(F/'system-restored.raw').stat().st_size,'sparse_sha256':sha(F/'system.sparse'),'negative':{'changed_offset':1120,'old':old,'new':old|0x80000000},'public_fs_config':(F/'sources/fs_config.cpp').read_text(),'logs':{p.name:p.read_text() for p in F.glob('*.log')},'previous_failures':{'r1':{p.name:p.read_text() for p in (R/'fixture-r1').glob('*.log')}}}
(F/'preparation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
