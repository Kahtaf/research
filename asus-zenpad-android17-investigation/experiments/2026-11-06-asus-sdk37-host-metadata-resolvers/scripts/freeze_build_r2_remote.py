import os,resource,signal,pathlib,json,hashlib,subprocess,shutil,re,base64
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));signal.alarm(90)
P=pathlib.Path;R=P('/srv/android/asus-sdk37-host-metadata-resolvers-20261106');A=P('/srv/android/lineage24');I=R/'inputs-r2';I.mkdir();(I/'lib64').mkdir();(I/'compiler').mkdir();(R/'bin').mkdir(exist_ok=True);(R/'build-r2').mkdir();(R/'tmp').mkdir(exist_ok=True)
PAYLOAD = {'source/resolve_fs_config.cpp': 'Ly8gRnV0dXJlIGhvc3QgcHJvZHVjZXI6IGxpbmsgYWdhaW5zdCB0aGUgYWRtaXR0ZWQgU0RLMzcgbGliY3V0aWxzIGltcGxlbWVudGF0aW9uLgojaW5jbHVkZSA8cHJpdmF0ZS9mc19jb25maWcuaD4KI2luY2x1ZGUgPHN0ZGludC5oPgojaW5jbHVkZSA8c3RkaW8uaD4Kc3RhdGljIGNvbnN0IGNoYXIgKmNvbnN0IHBhdGhzW109eyJzeXN0ZW0vYnVpbGQucHJvcCIsInN5c3RlbS9iaW4vaW5pdCIsInN5c3RlbS9iaW4vcnVuLWFzIiwic3lzdGVtL3ZlbmRvci9ldGMvc2VsaW51eC92ZW5kb3JfZmlsZV9jb250ZXh0cyJ9OwppbnQgbWFpbihpbnQgYXJnYyxjaGFyICoqYXJndikgewogaWYoYXJnYyE9Mil7ZnByaW50ZihzdGRlcnIsInVzYWdlOiByZXNvbHZlX2ZzX2NvbmZpZyBGUk9aRU5fVEFSR0VUX09VVFxuIik7cmV0dXJuIDI7fQogZm9yKGNvbnN0IGNoYXIgKnBhdGg6cGF0aHMpe3Vuc2lnbmVkIHVpZD0wLGdpZD0wLG1vZGU9MDt1aW50NjRfdCBjYXBzPTA7ZnNfY29uZmlnKHBhdGgsMCxhcmd2WzFdLCZ1aWQsJmdpZCwmbW9kZSwmY2Fwcyk7cHJpbnRmKCIvJXMgJXUgJXUgJTA0byBjYXBhYmlsaXRpZXM9MHglbGx4XG4iLHBhdGgsdWlkLGdpZCxtb2RlJjA3Nzc3LCh1bnNpZ25lZCBsb25nIGxvbmcpY2Fwcyk7fQogcmV0dXJuIGZlcnJvcihzdGRvdXQpPzE6MDsKfQo=', 'source/resolve_contexts.c': 'LyogRnV0dXJlIGhvc3QgcHJvZHVjZXI6IHVzZSB0aGUgYWRtaXR0ZWQgU0RLMzcgbGlic2VsaW51eCBhbmQgY29tcGlsZWQtY29udGV4dCBzdGVtLiAqLwojaW5jbHVkZSA8c2VsaW51eC9sYWJlbC5oPgojaW5jbHVkZSA8c2VsaW51eC9zZWxpbnV4Lmg+CiNpbmNsdWRlIDxzdGRpby5oPgojaW5jbHVkZSA8c3lzL3N0YXQuaD4Kc3RhdGljIGNvbnN0IGNoYXIgKmNvbnN0IHBhdGhzW109eyIvc3lzdGVtL2J1aWxkLnByb3AiLCIvc3lzdGVtL2Jpbi9pbml0IiwiL3N5c3RlbS9iaW4vcnVuLWFzIiwiL3N5c3RlbS92ZW5kb3IvZXRjL3NlbGludXgvdmVuZG9yX2ZpbGVfY29udGV4dHMifTsKaW50IG1haW4oaW50IGFyZ2MsY2hhciAqKmFyZ3YpIHsKIGlmKGFyZ2MhPTIpe2ZwcmludGYoc3RkZXJyLCJ1c2FnZTogcmVzb2x2ZV9jb250ZXh0cyBGUk9aRU5fQ09OVEVYVF9TVEVNXG4iKTtyZXR1cm4gMjt9CiBzdHJ1Y3Qgc2VsaW51eF9vcHQgb3B0aW9uc1tdPXt7U0VMQUJFTF9PUFRfUEFUSCxhcmd2WzFdfSx7U0VMQUJFTF9PUFRfQkFTRU9OTFksIjEifX07CiBzdHJ1Y3Qgc2VsYWJlbF9oYW5kbGUgKmg9c2VsYWJlbF9vcGVuKFNFTEFCRUxfQ1RYX0ZJTEUsb3B0aW9ucywyKTtpZighaCl7cGVycm9yKCJzZWxhYmVsX29wZW4iKTtyZXR1cm4gMTt9CiBmb3IoaW50IGk9MDtpPDQ7aSsrKXtjaGFyICpsYWJlbD1OVUxMO2lmKHNlbGFiZWxfbG9va3VwKGgsJmxhYmVsLHBhdGhzW2ldLFNfSUZSRUcpIT0wKXtwZXJyb3IocGF0aHNbaV0pO3NlbGFiZWxfY2xvc2UoaCk7cmV0dXJuIDE7fXByaW50ZigiJXMgJXNcbiIscGF0aHNbaV0sbGFiZWwpO2ZyZWVjb24obGFiZWwpO30KIHNlbGFiZWxfY2xvc2UoaCk7cmV0dXJuIGZlcnJvcihzdGRvdXQpPzE6MDsKfQo='}
pins=[]
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def cp(p,q):
 p=P(p);q=P(q);before=sha(p);q.parent.mkdir(parents=True,exist_ok=True);old=R/'inputs'/q.relative_to(I)
 if old.is_file() and sha(old)==before:os.link(old,q)
 else:shutil.copyfile(p,q);q.chmod(p.stat().st_mode&0o777);after=sha(p);copied=sha(q);assert before==after==copied;pins.append(dict(source=str(p),copy=str(q),bytes=q.stat().st_size,before=before,copied=copied,after=after))
for name in ['system/core/libcutils/include/private/fs_config.h','system/core/libcutils/include/private/android_filesystem_config.h','system/core/libcutils/fs_config.cpp','system/core/libcutils/fs_config.h','system/core/libcutils/Android.bp','external/selinux/libselinux/Android.bp','external/selinux/libselinux/include/selinux/label.h','external/selinux/libselinux/include/selinux/selinux.h','external/selinux/libselinux/src/label_file.c','external/selinux/libselinux/src/label_file.h','external/selinux/libselinux/src/label.c','external/e2fsprogs/contrib/android/perms.c','external/e2fsprogs/lib/ext2fs/ext2_ext_attr.h','external/selinux/libselinux/utils/sefcontext_compile.c']:
 p=A/name
 if p.exists():cp(p,I/'source'/name)
# The four tiny TUs compile using the actual exported SDK37 public headers.
cp(A/'system/core/libcutils/include/private/fs_config.h',I/'include/private/fs_config.h')
for n in ['selinux.h','label.h']:cp(A/'external/selinux/libselinux/include/selinux'/n,I/'include/selinux'/n)
seeds=[A/'out/host/linux-x86/lib64'/n for n in ['libcutils.so','libselinux.so']]+[A/'out/host/linux-x86/bin/sefcontext_compile']
ldd={}
for p in seeds:
 cp(p,(I/'bin'/p.name) if p.name=='sefcontext_compile' else I/'lib64'/p.name)
 result=subprocess.run(['/usr/bin/ldd',str(p)],capture_output=True,text=True,timeout=15);assert result.returncode==0
 ldd[str(p)]=result.stdout
 deps=re.findall(r'=> (/\S+)',result.stdout)+re.findall(r'^\s*(/\S*ld-linux\S*)\s',result.stdout,re.M)
 for dep in deps:
  q=I/'lib64'/P(dep).name
  if not q.exists():cp(P(dep),q)
compiler=P(shutil.which('gcc'));cp(compiler,I/'compiler/gcc')
for name in ['cc1','cc1plus','collect2','as','ld']:
 p=subprocess.check_output([str(compiler),'-print-prog-name='+name],text=True).strip();p=P(shutil.which(p)or p);cp(p,I/'compiler'/name)
# Pin the compiler executable dynamic closure (also used through an owned loader).
for p in list((I/'compiler').iterdir()):
 r=subprocess.run(['/usr/bin/ldd',str(p)],text=True,capture_output=True,timeout=15)
 for dep in re.findall(r'=> (/\S+)',r.stdout):
  q=I/'lib64'/P(dep).name
  if not q.exists():cp(P(dep),q)
for name,data in PAYLOAD.items():
 p=R/name;p.parent.mkdir(parents=True,exist_ok=True);data=base64.b64decode(data)
 if p.exists():assert p.read_bytes()==data
 else:p.write_bytes(data)
env=os.environ.copy();env['TMPDIR']=str(R/'tmp');env['LC_ALL']='C';env['LD_LIBRARY_PATH']=str(I/'lib64')
for k in ['LD_PRELOAD','LD_AUDIT']:env.pop(k,None)
results={}
for name,language,lib in [('resolve_fs_config','c++','libcutils.so'),('resolve_contexts','c','libselinux.so')]:
 src=R/'source'/(name+('.cpp'if language=='c++'else'.c'));out=R/'bin'/name
 cmd=[str(I/'compiler/gcc'),'-B'+str(I/'compiler')+'/', '-B'+str(P(subprocess.check_output([str(compiler),'-print-file-name=libgcc.a'],text=True).strip()).parent)+'/', '-isystem',subprocess.check_output([str(compiler),'-print-file-name=include'],text=True).strip(), '-x',language,'-O2','-Wall','-Wextra','-Werror','-I'+str(I/'include'),'-MD','-MF',str(R/'build-r2'/(name+'.d')),str(src),'-x','none','-L'+str(I/'lib64'),'-Wl,-rpath,$ORIGIN/../inputs-r2/lib64','-Wl,--disable-new-dtags','-Wl,--dynamic-linker='+str(I/'lib64/ld-linux-x86-64.so.2'),'-l:'+lib,'-o',str(out)]
 p=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=90)
 (R/'build-r2'/(name+'.log')).write_text(json.dumps(cmd)+'\n'+p.stdout+'\nexit='+str(p.returncode)+'\n');results[name]={'exit':p.returncode,'argv':cmd,'log':p.stdout};assert p.returncode==0,p.stdout
 results[name]['sha256']=sha(out)
 # Snapshot precisely the compiler-read header closure from its depfile, not /usr/include broadly.
 dep=(R/'build-r2'/(name+'.d')).read_text().replace('\\\n',' ').split(':',1)[1].split()
 for item in dep:
  p=P(item)
  if str(p).startswith('/usr/'):
   q=I/'compiler-headers'/str(p).lstrip('/')
   if not q.exists():cp(p,q)
 # Pin source/compiler library provenance and dynamic metadata, without executing product code.
 results[name]['elf_dynamic']=subprocess.check_output(['/usr/bin/readelf','-d',str(out)],text=True)
 results[name]['closure']=subprocess.check_output([str(I/'lib64/ld-linux-x86-64.so.2'),'--inhibit-cache','--library-path',str(I/'lib64'),'--list',str(out)],env=env,text=True)
 assert all(str(I/'lib64') in x for x in re.findall(r'=> (/\S+)',results[name]['closure']))
# Compiler support objects actually used by driver search are fixed and pinned too.
for name in ['crt1.o','Scrt1.o','crti.o','crtn.o','crtbeginS.o','crtendS.o','libgcc.a','libgcc_s.so']:
 p=P(subprocess.check_output([str(compiler),'-print-file-name='+name],text=True).strip())
 if p.exists():cp(p,I/'compiler-support'/name)
assert sum(v for v in {(p.stat().st_dev,p.stat().st_ino):p.stat().st_size for p in R.rglob('*')if p.is_file()}.values())<256*1024**2,'Storage cap'
result=dict(host_resolvers_built=True,remote_root=str(R),resources=dict(cpus=1,address_space_bytes=1024**3,cpu_seconds=60,wall_seconds=90,storage_cap_bytes=256*1024**2),results=results,seed_ldd=ldd,copies=pins,actual_product_inputs_used=False)
(R/'copy-receipts.json').write_text(json.dumps(pins,indent=2));(R/'build.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
