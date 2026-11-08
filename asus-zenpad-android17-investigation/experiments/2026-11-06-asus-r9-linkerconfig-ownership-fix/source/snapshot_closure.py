from pathlib import Path
import os,json,shlex,subprocess as sp,hashlib,shutil,resource,re
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');A=Path('/srv/android/lineage24');S=R/'inputs/native-snapshot';S.mkdir();os.environ['TMPDIR']=str(R/'tmp');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0));exec((R/'source/ninja_leaf.py').read_text());g,r,_=parse((R/'inputs/leaf/main-prelude.ninja').read_text());G={};ED={}
for n in ['linkerconfig','linkerconfig_contents','linkerconfig_contents_fulltest']:
 mg,_,edges=parse((R/'inputs/leaf'/(n+'.ninja')).read_text());G.update(mg);ED[n]=edges
pin={};commands=[]
def capture(rel):
 p=Path(rel);assert not p.is_absolute() and '..' not in p.parts,rel
 if rel in pin:return
 src=A/p;assert src.is_file(),rel;before=src.stat();b=src.read_bytes();after=src.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns);dest=S/p;dest.parent.mkdir(exist_ok=True,parents=True);dest.write_bytes(b);pin[rel]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'mtime_ns':before.st_mtime_ns,'dev':before.st_dev,'inode':before.st_ino}
def vars(edge):return {**g,**G,**edge['vars'],'in':' '.join(edge['inputs']),'out':' '.join(edge['out'])}
def expedge(edge):
 v=vars(edge);return {**edge,'expanded':{k:expand(x,v) for k,x in edge['vars'].items() if k not in ['description','tags']}}
def run(cmd,cwd=A):
 p=sp.run([str(x) for x in cmd],cwd=cwd,capture_output=True,text=True,timeout=60);commands.append(dict(command=[str(x) for x in cmd],cwd=str(cwd),rc=p.returncode,stdout=p.stdout,stderr=p.stderr));(R/'evidence/snapshot-commands.json').write_text(json.dumps(commands,indent=2));assert p.returncode==0,p.stderr;return p
selected={}
for key,var,host in [('arm64','android_arm64_armv8-a_static_apex10000',False),('host','linux_glibc_x86_64_static',True)]:
 cc=next(x for x in ED['linkerconfig_contents'] if x['variant']==var and x['rule']=='g.cc.cc' and x['inputs']==['system/linkerconfig/contents/namespace/systemdefault.cc']);ar=next(x for x in ED['linkerconfig_contents'] if x['variant']==var and x['rule']=='g.cc.ar')
 ldvar='linux_glibc_x86_64' if host else 'android_arm64_armv8-a_apex10000';ld=next(x for x in ED['linkerconfig'] if x['variant']==ldvar and x['rule']=='g.cc.ld')
 testld=next(x for x in ED['linkerconfig_contents_fulltest'] if x['variant']=='linux_glibc_x86_64' and x['rule']=='g.cc.ld') if host else None
 for ed in [ar,ld]+([testld] if testld else []):
  v=vars(ed);tokens=ed['inputs']+ed['implicit']
  for field in ['libFlags','crtBegin','crtEnd','ldFlags','extraLibFlags']:
   if field in v:tokens+=shlex.split(expand(v[field],v))
  for token in tokens:
   for t in token.split(','):
    if t.startswith(('out/','prebuilts/')) and (A/t).is_file():capture(t)
  if (A/(ed['out'][0]+'.rsp')).is_file():capture(ed['out'][0]+'.rsp')
  capture(ed['out'][0])
 v=vars(cc);flags=shlex.split(expand(v['cFlags'],v));cmd=[str(A/expand(v['ccCmd'],v))]+flags+['-M','-MF',str(R/'tmp'/('headers-'+key+'.d')),'-MT','snapshot',cc['inputs'][0]];run(cmd)
 dep=(R/'tmp'/('headers-'+key+'.d')).read_text().replace('\\\n',' ').split(':',1)[1]
 for p in shlex.split(dep):
  if not Path(p).is_absolute():capture(p)
  else:
   try:capture(str(Path(p).relative_to(A)))
   except ValueError:raise AssertionError('external header dependency: '+p)
 selected[key]={'cc':expedge(cc),'ar':expedge(ar),'ld':expedge(ld),'testld':expedge(testld) if testld else None}
# Full frozen project source/headers for a coherent own tree and exact r6 source equality.
for p in (R/'inputs/linkerconfig-before').rglob('*'):
 if p.is_file():
  rel='system/linkerconfig/'+str(p.relative_to(R/'inputs/linkerconfig-before'));src=A/rel;assert src.read_bytes()==p.read_bytes(),rel;capture(rel)
# Test compilation flags from original p00a test, and its full header closure.
testcc=next(x for x in ED['linkerconfig_contents_fulltest'] if x['variant']=='linux_glibc_x86_64' and x['rule']=='g.cc.cc' and x['inputs']==['system/linkerconfig/contents/tests/configuration/p00a_legacy_graphics_test.cc']);v=vars(testcc);flags=shlex.split(expand(v['cFlags'],v));run([str(A/expand(v['ccCmd'],v))]+flags+['-M','-MF',str(R/'tmp/headers-test.d'),'-MT','snapshot',testcc['inputs'][0]])
for p in shlex.split((R/'tmp/headers-test.d').read_text().replace('\\\n',' ').split(':',1)[1]):capture(str(Path(p).relative_to(A)) if Path(p).is_absolute() else p)
selected['host']['testcc']=expedge(testcc)
# Pinned shared host runtime libraries used by official host linkerconfig/fulltest.
for rel in ['out/host/linux-x86/lib64/libbase.so','out/host/linux-x86/lib64/liblog.so','out/host/linux-x86/lib64/libc++.so']:
 if (A/rel).is_file():capture(rel)
# Exact installed APEX variant must match the actual executed immutable APEX ELF.
armvar='out/soong/.intermediates/system/linkerconfig/linkerconfig/android_arm64_armv8-a_apex10000/linkerconfig';capture(armvar);assert pin[armvar]['sha256']=='f697b2f950e3693449989cfc3e1c94ae9845f48dc9ff1e9af271b01a815bd157'
# Clang and its companion tools are retained read-only in place.
clangdir=A/'prebuilts/clang/host/linux-x86/clang-r584948b/bin';tools={n:{'path':str(clangdir/n),'sha256':hashlib.sha256((clangdir/n).read_bytes()).hexdigest()} for n in ['clang++','ld.lld','llvm-ar','llvm-strip','llvm-readelf']}
(R/'evidence/native-snapshot-pins.json').write_text(json.dumps(dict(files=pin,tools=tools,selected_edges=selected,actual_executed_apex_elf_sha256=pin[armvar]['sha256'],native_snapshot_bytes=sum(x['bytes'] for x in pin.values()),TMPDIR=os.environ['TMPDIR']),indent=2));print(json.dumps({'files':len(pin),'bytes':sum(x['bytes'] for x in pin.values()),'runtime_apex_elf_matches':True,'variants':list(selected)},indent=2))
