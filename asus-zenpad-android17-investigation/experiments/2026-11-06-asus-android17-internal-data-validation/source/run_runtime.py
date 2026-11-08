from pathlib import Path
import subprocess as s,json,hashlib,os,stat,gzip,re,sys,shutil
from image import R,SIZE,safe,new,inspect,need,hashes
sys.path.insert(0,str(R/'inputs'));from analyze_materials import analyze_materials
name=sys.argv[1];need(bool(re.fullmatch(r'r[0-9]+',name)),'run name');O=R/name;O.mkdir();os.environ['TMPDIR']=str(O)
for p in (R/'source').glob('*'):
 if p.is_file():shutil.copyfile(p,O/p.name)
payloads=json.loads((R/'inputs/payload-manifest.json').read_text());header='struct payload {const char*name; unsigned long long offset,size,data_size,tree_offset;const char*digest,*salt;int count;const char**files;};\n'
for p in payloads:header+='static const char* '+p['name']+'_files[]={'+','.join(json.dumps(f['path']) for f in p['files'])+'};\n'
header+='static struct payload payloads[]={\n'
for p in payloads:
 v=p['verity'];header+='{'+','.join([json.dumps(p['name']),str(p['offset']),str(p['size']),v['Image Size'],v['Tree Offset'],json.dumps(v['Root Digest']),json.dumps(v['Salt']),str(len(p['files'])),p['name']+'_files'])+'},\n'
header+='};\n';(O/'payloads.h').write_text(header)
cmd=['aarch64-linux-gnu-gcc','-static','-O2','-Wall','-Wextra','-Werror','-I'+str(O),str(O/'guest_init.c'),'-o',str(O/'init')]
p=s.run(cmd,stdout=s.PIPE,stderr=s.STDOUT,text=True);(O/'compile.txt').write_text(json.dumps(cmd)+'\n'+p.stdout+f'\nexit={p.returncode}\n');print(p.stdout,flush=True);need(p.returncode==0,'compile')
files={str(f.relative_to(R/'inputs/root')):f for f in (R/'inputs/root').rglob('*') if f.is_file()};files['init']=O/'init'
for n in ['adbd','google']:files['payload/'+n+'.apex']=R/'inputs'/(n+'.apex')
# Stream cpio directly into gzip so APEX contents do not require a second RAM copy.
with gzip.GzipFile(filename=str(O/'initramfs.cpio.gz'),mode='wb',compresslevel=1,mtime=0) as out:
 offset=0
 def entry(name,mode,path=None,major=0,minor=0):
  global offset
  size=path.stat().st_size if path else 0;n=name.encode()+b'\0';fields=[1,mode,0,0,1,0,size,0,0,major,minor,len(n),0];h=b'070701'+''.join(f'{v:08x}' for v in fields).encode()+n;out.write(h);offset+=len(h);pad=-offset%4;out.write(bytes(pad));offset+=pad
  if path:
   with path.open('rb') as f:shutil.copyfileobj(f,out,1024*1024)
   offset+=size
  pad=-offset%4;out.write(bytes(pad));offset+=pad
 dirs={'dev','proc','sys','tmp','linkerconfig','data','mnt','payload'}
 for n in files:dirs.update(str(p) for p in Path(n).parents if str(p)!='.')
 for d in sorted(dirs,key=lambda n:(n.count('/'),n)):entry(d,stat.S_IFDIR|0o755)
 entry('dev/console',stat.S_IFCHR|0o600,major=5,minor=1)
 for n,p in sorted(files.items()):entry(n,stat.S_IFREG|(0o755 if n=='init' or '/bin/' in n else 0o444),p)
 entry('TRAILER!!!',0)
(O/'initramfs-inputs.json').write_text(json.dumps([dict(path=n,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for n,p in files.items()],indent=2)+'\n')
pristine=R/'artifacts/A17DATA-pristine.raw';inspect(pristine);clone=O/'data-qa.raw';fd=new(clone);os.close(fd)
s.run(['cp','--reflink=auto','--sparse=always',str(pristine),str(clone)],check=True);clone.chmod(0o600);need(clone.stat().st_size==SIZE,'clone size')
manifest=json.loads((R/'evidence/image-manifest.json').read_text());h=s.check_output(['sha256sum',str(clone)],text=True).split()[0];need(h==manifest['sha256'],'clone full hash');(O/'clone-initial-sha256.txt').write_text(h+'\n')
k=R/'inputs/kernel';need(hashlib.sha256(k.read_bytes()).hexdigest()=='113c4f19c736b949626c62bbf68cf23c9e3c5a821ec6ab031a5684cdcba14431','kernel pin')
results=[]
for phase in [1,2]:
 cmd=['qemu-system-aarch64','-machine','virt,gic-version=3','-cpu','cortex-a53','-smp','2','-m','1536','-nographic','-monitor','none','-no-reboot','-nic','none','-kernel',str(k),'-initrd',str(O/'initramfs.cpio.gz'),'-drive',f'file={clone},format=raw,if=none,id=data,cache=none','-device','virtio-blk-device,drive=data','-append',f'console=ttyAMA0 rdinit=/init panic=-1 loglevel=7 data_phase={phase}']
 (O/f'qemu-{phase}.json').write_text(json.dumps(cmd,indent=2)+'\n');code=None;timed=False
 with (O/f'serial-{phase}.log').open('w') as f:
  try:code=s.run(cmd,stdin=s.DEVNULL,stdout=f,stderr=s.STDOUT,timeout=420).returncode
  except s.TimeoutExpired:timed=True
 text=(O/f'serial-{phase}.log').read_text(errors='replace');materials=analyze_materials(text,payloads);m=re.search(r'INTERNAL_DATA_RESULT (\{[^\r\n]+\})',text);guest=json.loads(m[1]) if m else None
 expected=hashlib.sha256(bytes((i*17+(i>>12)*3+91)&255 for i in range(8*1024*1024))).hexdigest()
 fsck=s.run(['e2fsck','-fn',str(clone)],text=True,stdout=s.PIPE,stderr=s.STDOUT);(O/f'e2fsck-{phase}.txt').write_text(fsck.stdout+f'\nexit={fsck.returncode}\n')
 info=inspect(clone,False);(O/f'inspection-{phase}.json').write_text(json.dumps(info,indent=2)+'\n')
 result=dict(phase=phase,qemu_returncode=code,timed_out=timed,guest=guest,material_hashes=materials,material_hash_count=len(materials),sentinel_expected_sha256=expected,sentinel_hash_pass=expected+'  /data/system/fullsize-sentinel.bin' in text,e2fsck_returncode=fsck.returncode,clean_unmount='CHECK clean_data_umount rc=0' in text,complete='INTERNAL_DATA_DONE' in text)
 result['passed']=bool(code==0 and not timed and guest and guest['failures']==0 and len(materials)==68 and all(h['passed'] for h in materials) and result['sentinel_hash_pass'] and result['clean_unmount'] and result['complete'] and fsck.returncode==0)
 (O/f'result-{phase}.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='material_hashes'},indent=2),flush=True);results.append(result);need(result['passed'],'runtime phase failed')
final=hashes(pristine);need(final['sha256']==manifest['sha256'] and final['chunks']==manifest['chunks'],'pristine changed')
(O/'result.json').write_text(json.dumps(dict(passed=True,kernel_sha256=hashlib.sha256(k.read_bytes()).hexdigest(),pristine_after_sha256=final['sha256'],phases=[r['passed'] for r in results],physical_validated=False,android_init_executed=False,apexd_executed=False,selinux_policy_validated=False),indent=2)+'\n')
