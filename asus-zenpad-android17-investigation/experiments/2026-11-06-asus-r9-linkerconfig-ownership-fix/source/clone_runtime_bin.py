from pathlib import Path
import os,subprocess as s,zipfile,io,shutil,json,re,hashlib
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');src=(R/'source/actual_metadata.py').read_text();exec(compile(src.split("D={'raw_identity_before'")[0],'public-readonly-reader','exec'));b=get('system/apex/com.android.runtime.apex');assert hashlib.sha256(b).hexdigest()=='638361e8de6863d070e491914a75e5e5b3a07ee2929bb6b048fe5f3bbdab403d';out=R/'inputs/runtime-bin-original';out.mkdir();payload=R/'tmp/runtime-payload.img';z=zipfile.ZipFile(io.BytesIO(b));payload.write_bytes(z.read('apex_payload.img'));tools=R/'inputs/host-deps/root/usr/bin';extract=R/'tmp/runtime-extract';p=s.run([str(tools/'fsck.erofs'),'--extract='+str(extract),'--no-preserve',str(payload)],capture_output=True,text=True,timeout=20);assert p.returncode==0,p.stderr;d={}
for path in ['bin']+['bin/'+p.name for p in sorted((extract/'bin').iterdir())]:
 p=s.run([str(tools/'dump.erofs'),'--path=/'+path,str(payload)],capture_output=True,text=True,timeout=10);assert p.returncode==0,p.stderr;d[path]={'metadata_stdout':p.stdout,'metadata_stderr':p.stderr}
 if path!='bin':
  f=extract/path;shutil.copyfile(f,out/f.name);d[path].update(bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest())
(R/'evidence/runtime-bin-original.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2));shutil.rmtree(extract);payload.unlink()
