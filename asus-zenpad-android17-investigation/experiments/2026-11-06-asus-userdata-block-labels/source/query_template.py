import os,resource,pathlib,subprocess,json,hashlib,base64,difflib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2))
P=pathlib.Path;A=P('/srv/android/lineage24');R=P('/srv/android/asus-userdata-block-labels-20261106');Q=P('/srv/android/asus-sdk37-host-metadata-resolvers-20261106/inputs-r4');out={'scope':'native metadata diagnosis; not production capture admission','commands':[]};pins=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def capture(p,q):
 b=p.read_bytes();assert len(b)<16*1024**2;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b);assert sha(p)==sha(q);pins.append({'path':str(p),'copy':str(q),'sha256':sha(p),'bytes':len(b)});return q

def run(args,ok=(0,),env=None):
 p=subprocess.run([str(x)for x in args],cwd=R,env=env,capture_output=True,text=True,timeout=30);row={'argv':[str(x)for x in args],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr};out['commands'].append(row);assert p.returncode in ok,row;return p.stdout
for name,b in PAYLOAD.items():(R/name).write_bytes(base64.b64decode(b))
context_names=['system/etc/selinux/plat_file_contexts','system/system_ext/etc/selinux/system_ext_file_contexts','system/product/etc/selinux/product_file_contexts','system/vendor/etc/selinux/vendor_file_contexts','system/vendor/odm/etc/selinux/odm_file_contexts']
contexts=[capture(A/'out/target/product/p00a'/n,R/'current'/P(n).name)for n in context_names]
policy=capture(A/'out/target/product/p00a/system/vendor/etc/selinux/precompiled_sepolicy',R/'current/precompiled_sepolicy')
for n in ['external/selinux/libselinux/src/android/android_seapp.c','external/selinux/libselinux/src/android/android_internal.c','system/core/init/devices.cpp','system/core/init/selabel.cpp','system/sepolicy/public/device.te']:
 p=A/n
 if p.exists():capture(p,R/'inputs'/n)
static=list((A/'out/soong/.intermediates/external/selinux/libsepol').glob('**/linux_glibc_x86_64_static*/**/libsepol.a'))
out['static_candidates']=[str(p)for p in static]
assert static,'No SDK37 libsepol static archive found'
lib=static[0];out['libsepol']={'path':str(lib),'sha256':sha(lib)}
env=os.environ.copy();env['TMPDIR']=str(R);env['LD_LIBRARY_PATH']=str(Q/'lib64')
run(['gcc','-O2','-Wall','-Wextra','-I'+str(Q/'include'),R/'block_lookup.c','-L'+str(Q/'lib64'),'-Wl,-rpath,'+str(Q/'lib64'),'-l:libselinux.so','-o',R/'block_lookup'],env=env)
run(['gcc','-O2','-Wall','-Wextra','-I'+str(A/'external/selinux/libsepol/include'),R/'policy_query.c',lib,'-o',R/'policy_query'],env=env)
pre=R/'inputs/device/asus/p00a/sepolicy/vendor/file_contexts';assert sha(pre)=='f7d5656f54655442056e607a620b3bcd37d8818f1f3b9116bbbb190212241f42'
delta='\n# Physical userdata only; retain the platform fsck domain permissions.\n/dev/block/mmcblk0p26    u:object_r:userdata_block_device:s0\n/dev/block/platform/soc/11230000\\.mmc/by-name/userdata    u:object_r:userdata_block_device:s0\n/dev/block/by-name/userdata    u:object_r:userdata_block_device:s0\n'
(R/'candidate-device-file_contexts').write_text(pre.read_text()+delta)
(R/'candidate.patch').write_text(''.join(difflib.unified_diff(pre.read_text().splitlines(True),(pre.read_text()+delta).splitlines(True),fromfile='a/device/asus/p00a/sepolicy/vendor/file_contexts',tofile='b/device/asus/p00a/sepolicy/vendor/file_contexts')))
proposed=R/'proposed/vendor_file_contexts';proposed.parent.mkdir();proposed.write_text(contexts[3].read_text()+delta)
checkfc=A/'out/host/linux-x86/bin/checkfc'
for p in contexts+[proposed,R/'candidate-device-file_contexts']:run([checkfc,'-e',policy,p])
run([R/'policy_query',policy])
run([R/'block_lookup']+contexts,env=env)
after=contexts[:];after[3]=proposed
run([R/'block_lookup']+after,env=env)
# Compile each current and proposed context input with qualified SDK37 compiler,
# then repeat the same multi-input best-match query against binary-only stems.
for tag,inputs in [('current',contexts),('proposed',after)]:
 binaries=[]
 for i,p in enumerate(inputs):
  stem=R/(tag+'-compiled')/str(i);stem.parent.mkdir(exist_ok=True)
  run([Q/'lib64/ld-linux-x86-64.so.2','--inhibit-cache','--library-path',Q/'lib64',Q/'bin/sefcontext_compile','-o',str(stem)+'.bin',p],env=env);binaries.append(stem)
 run([R/'block_lookup']+binaries,env=env)
for p in pins:p['after_sha256']=sha(P(p['path']));assert p['after_sha256']==p['sha256']
out['pins']=pins;out['candidate_patch']=(R/'candidate.patch').read_text();out['candidate_sha256']=sha(R/'candidate-device-file_contexts');out['owned_bytes']=sum(p.stat().st_size for p in R.rglob('*')if p.is_file());assert out['owned_bytes']<=64*1024**2
out['tool_pins']=[{'path':str(p),'sha256':sha(p)}for p in [R/'block_lookup',R/'policy_query',Q/'lib64/libselinux.so',checkfc,Q/'bin/sefcontext_compile']]
(R/'native-evidence.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
