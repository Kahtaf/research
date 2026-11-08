from pathlib import Path
import subprocess,json,hashlib,shutil,os
P=Path('/srv/android/asus-linux49-historical-vintf-20261106');H=Path('/srv/android/lineage24/out/host/linux-x86');T=P/'tools'
assert not T.exists();(T/'bin').mkdir(parents=True);(T/'lib64').mkdir()
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();pins={};logs={};copies={}
for name in ['checkvintf','assemble_vintf']:
 src=H/'bin'/name
 if name=='checkvintf':assert h(src)=='f67a37ca56cc1fbb8cf5c919a69990e8493ab0a17248a9cd053ff97d7d1ba4c0','host tool changed from earlier pin'
 assert src.stat().st_size<50*1024*1024
 before=h(src);shutil.copy2(src,T/'bin'/name);assert h(src)==before==h(T/'bin'/name);pins[str(src)]=before;copies[str(T/'bin'/name)]=before
 q=subprocess.run(['ldd',str(src)],capture_output=True,text=True,timeout=10);assert q.returncode==0;logs[name]=q.stdout
 for line in q.stdout.splitlines():
  if '=>' not in line:continue
  path=line.split('=>',1)[1].strip().split()[0]
  if path.startswith(str(H)):
   lib=Path(path);dest=T/'lib64'/lib.name;before=h(lib);shutil.copy2(lib,dest);assert h(lib)==before==h(dest);pins[str(lib)]=before;copies[str(dest)]=before
assert sum(p.stat().st_size for p in P.rglob('*') if p.is_file())<256*1024*1024
result={'original_tool_only_read_pins':pins,'copied_tool_pins':copies,'ldd':logs,'active_metadata_read':False,'copied_bytes':sum(p.stat().st_size for p in T.rglob('*') if p.is_file()),'all_original_tools_unchanged_during_copy':True}
(P/'evidence/tools.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
