import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import os,resource,subprocess,shlex,json,hashlib,zipfile,struct
A=Path('/srv/android/lineage24');R=Path('/srv/android/asus-reviewed-build-kit/r9');F=Path('/srv/android/asus-reviewed-build-kit/r9-fixtures');P=Path('/srv/android/asus-product-integration-staging/r9/webview.apk');old=Path('/srv/android/asus-reviewed-build-kit/r8/attempt/native-evidence/bootimage/siso_failed_commands.sh')
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
assert P.stat().st_size==260835655 and sha(P)=='1d2f61832b2596b0046cb82cf3634609ea866098d097a83fac27c35272ac726a'
r=dict(bytes=P.stat().st_size,sha256=sha(P),one_cpu=True,address_space_bytes=1024**3,tool_pins={n:sha(A/'out/host/linux-x86/bin'/n) for n in ['manifest_check','aapt2']})
with zipfile.ZipFile(P) as z:
 assert z.testzip() is None
 assert len(z.namelist())==len(set(z.namelist()))
 r['zip']=dict(crc_all_passed=True,entries=len(z.infolist()),manifest_bytes=len(z.read('AndroidManifest.xml')),manifest_sha256=hashlib.sha256(z.read('AndroidManifest.xml')).hexdigest())
 r['native_elfs']=[]
 for i in z.infolist():
  if i.filename.startswith('lib/') and i.filename.endswith('.so'):
   with z.open(i) as f:b=f.read(64)
   assert b[:4]==b'\x7fELF';r['native_elfs'].append(dict(path=i.filename,elf_class=b[4],endian=b[5],machine=struct.unpack_from('<H',b,18)[0],bytes=i.file_size))
 assert any(x['machine']==183 for x in r['native_elfs'])
for name,args in [('badging',['dump','badging',str(P)]),('manifest',['dump','xmltree',str(P),'--file','AndroidManifest.xml'])]:
 p=subprocess.run([str(A/'out/host/linux-x86/bin/aapt2')]+args,cwd=F,capture_output=True,text=True,timeout=60)
 (F/(name+'.stdout')).write_text(p.stdout);(F/(name+'.stderr')).write_text(p.stderr);assert p.returncode==0
 r[name]=dict(exit_code=p.returncode,stdout_path=str(F/(name+'.stdout')),stdout_sha256=sha(F/(name+'.stdout')))
line=next(l for l in old.read_text().splitlines() if l.startswith('out/host/linux-x86/bin/manifest_check '));argv=shlex.split(line,comments=True)
assert argv[2]=='external/chromium-webview/prebuilt/arm64/webview.apk'
original_status=argv[argv.index('--enforce-uses-libraries-status')+1]
r['checks']=[]
for case,inputp in [('original-pointer',A/argv[2]),('exact-object',P)]:
 d=F/case;d.mkdir();cmd=list(argv);cmd[2]=str(inputp);cmd[cmd.index('--enforce-uses-libraries-status')+1]=str(d/'status')
 p=subprocess.run(cmd,cwd=A,capture_output=True,text=True,timeout=60,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
 (d/'stdout').write_text(p.stdout);(d/'stderr').write_text(p.stderr)
 r['checks'].append(dict(case=case,argv=cmd,exit_code=p.returncode,stdout_sha256=sha(d/'stdout'),stderr_sha256=sha(d/'stderr'),stderr=p.stderr,status_exists=(d/'status').exists(),status_text=(d/'status').read_text() if (d/'status').exists() else None))
assert r['checks'][0]['exit_code']!=0 and 'Invalid file' in r['checks'][0]['stderr']
assert r['checks'][1]['exit_code']==0 and r['checks'][1]['status_text']==''
r['original_active_pointer_preserved']=sha(A/'external/chromium-webview/prebuilt/arm64/webview.apk')=='a7b12c1895a3b354a91997fffe0e383a88e5b0e0d4371f8fdc090c71f62aade7'
with (R/'evidence/artifact-check.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/artifact-check.json').write_text(r);print(r)
