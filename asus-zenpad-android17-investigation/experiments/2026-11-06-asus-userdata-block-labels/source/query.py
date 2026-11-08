import os,resource,pathlib,subprocess,json,hashlib,base64,difflib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60));resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2))
P=pathlib.Path;A=P('/srv/android/lineage24');R=P('/srv/android/asus-userdata-block-labels-20261106');Q=P('/srv/android/asus-sdk37-host-metadata-resolvers-20261106/inputs-r4');out={'scope':'native metadata diagnosis; not production capture admission','commands':[]};pins=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def capture(p,q):
 b=p.read_bytes();assert len(b)<16*1024**2;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b);assert sha(p)==sha(q);pins.append({'path':str(p),'copy':str(q),'sha256':sha(p),'bytes':len(b)});return q

def run(args,ok=(0,),env=None):
 p=subprocess.run([str(x)for x in args],cwd=R,env=env,capture_output=True,text=True,timeout=30);row={'argv':[str(x)for x in args],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr};out['commands'].append(row);assert p.returncode in ok,row;return p.stdout
PAYLOAD = {'block_lookup.c': 'I2luY2x1ZGUgPHNlbGludXgvbGFiZWwuaD4KI2luY2x1ZGUgPHNlbGludXgvc2VsaW51eC5oPgojaW5jbHVkZSA8c3lzL3N0YXQuaD4KI2luY2x1ZGUgPHN0ZGlvLmg+CiNpbmNsdWRlIDxzdGRsaWIuaD4Kc3RhdGljIGNvbnN0IGNoYXIgKnBhdGhzW109eyIvZGV2L2Jsb2NrL21tY2JsazBwMjYiLCIvZGV2L2Jsb2NrL3BsYXRmb3JtL3NvYy8xMTIzMDAwMC5tbWMvYnktbmFtZS91c2VyZGF0YSIsIi9kZXYvYmxvY2svYnktbmFtZS91c2VyZGF0YSIsIi9kZXYvYmxvY2svcGxhdGZvcm0vc29jLzExMjMwMDAwLm1tYy9tbWNibGswcDI2IiwiL2Rldi9ibG9jay92ZGEiLCIvZGV2L2Jsb2NrL21tY2JsazBwMjUiLCIvZGV2L2Jsb2NrL2J5LW5hbWUvYm9vdCIsIi9kZXYvYmxvY2svYnktbmFtZS9wcmVsb2FkZXIiLCIvZGV2L2Jsb2NrL2J5LW5hbWUvbnZyYW0iLCIvZGV2L2Jsb2NrL2J5LW5hbWUvcGVyc2lzdCJ9OwppbnQgbWFpbihpbnQgYXJnYyxjaGFyICoqYXJndil7CiBpZihhcmdjPDIpcmV0dXJuIDI7CiBzdHJ1Y3Qgc2VsaW51eF9vcHQgKm9wdHM9Y2FsbG9jKChzaXplX3QpYXJnYyxzaXplb2YoKm9wdHMpKTsKIGZvcihpbnQgaT0xO2k8YXJnYztpKyspb3B0c1tpLTFdPShzdHJ1Y3Qgc2VsaW51eF9vcHQpe1NFTEFCRUxfT1BUX1BBVEgsYXJndltpXX07CiBvcHRzW2FyZ2MtMV09KHN0cnVjdCBzZWxpbnV4X29wdCl7U0VMQUJFTF9PUFRfQkFTRU9OTFksIjEifTsKIHN0cnVjdCBzZWxhYmVsX2hhbmRsZSAqaD1zZWxhYmVsX29wZW4oU0VMQUJFTF9DVFhfRklMRSxvcHRzLCh1bnNpZ25lZClhcmdjKTtpZighaCl7cGVycm9yKCJzZWxhYmVsX29wZW4iKTtyZXR1cm4gMTt9CiBmb3IodW5zaWduZWQgaT0wO2k8c2l6ZW9mKHBhdGhzKS9zaXplb2YocGF0aHNbMF0pO2krKyl7Y2hhciAqY3R4PU5VTEw7aWYoc2VsYWJlbF9sb29rdXAoaCwmY3R4LHBhdGhzW2ldLFNfSUZCTEspKXtwZXJyb3IocGF0aHNbaV0pO3JldHVybiAxO31wcmludGYoImRpcmVjdFx0JXNcdCVzXG4iLHBhdGhzW2ldLGN0eCk7ZnJlZWNvbihjdHgpO30KIGNvbnN0IGNoYXIgKmFsaWFzZXNbXT17cGF0aHNbMV0scGF0aHNbMl0scGF0aHNbM10sTlVMTH07CiBmb3IoaW50IG49MDtuPDM7bisrKXtjaGFyICpjdHg9TlVMTDtjb25zdCBjaGFyICoqYT1uPT0wP2FsaWFzZXM6bj09MT9hbGlhc2VzKzE6TlVMTDtpZihzZWxhYmVsX2xvb2t1cF9iZXN0X21hdGNoKGgsJmN0eCxuPT0yP3BhdGhzWzRdOnBhdGhzWzBdLGEsU19JRkJMSykpe3BlcnJvcigiYmVzdF9tYXRjaCIpO3JldHVybiAxO31wcmludGYoImJlc3RfbWF0Y2hcdCVzXHQlc1xuIixuPT0wPyJwaHlzaWNhbF9wbGF0Zm9ybV9nbG9iYWwiOm49PTE/InBoeXNpY2FsX2dsb2JhbF9vbmx5IjoidmlydHVhbF9ub19hbGlhcyIsY3R4KTtmcmVlY29uKGN0eCk7fQogc2VsYWJlbF9jbG9zZShoKTtmcmVlKG9wdHMpO3JldHVybiBmZXJyb3Ioc3Rkb3V0KT8xOjA7Cn0K', 'policy_query.c': 'I2luY2x1ZGUgPHNlcG9sL3BvbGljeWRiL3NlcnZpY2VzLmg+CiNpbmNsdWRlIDxzdGRpby5oPgojaW5jbHVkZSA8c3RkbGliLmg+CiNpbmNsdWRlIDxzdHJpbmcuaD4KaW50IG1haW4oaW50IGFyZ2MsY2hhciAqKmFyZ3YpewogaWYoYXJnYyE9MilyZXR1cm4gMjtGSUxFICpmPWZvcGVuKGFyZ3ZbMV0sInJiIik7aWYoIWYpcmV0dXJuIDE7ZnNlZWsoZiwwLFNFRUtfRU5EKTtsb25nIGxlbj1mdGVsbChmKTtyZXdpbmQoZik7aWYobGVuPD0wfHxsZW4+MTYqMTAyNCoxMDI0KXJldHVybiAxO3ZvaWQgKmRhdGE9bWFsbG9jKChzaXplX3QpbGVuKTtpZihmcmVhZChkYXRhLDEsKHNpemVfdClsZW4sZikhPShzaXplX3QpbGVuKXJldHVybiAxO2ZjbG9zZShmKTtpZihzZXBvbF9sb2FkX3BvbGljeShkYXRhLChzaXplX3QpbGVuKSlyZXR1cm4gMTsKIHNlcG9sX3NlY3VyaXR5X2lkX3Qgc3JjLHRndDtzZXBvbF9zZWN1cml0eV9jbGFzc190IGNsczsKIGNvbnN0IGNoYXIgKnNvdXJjZT0idTpyOmZzY2s6czAiO2lmKHNlcG9sX2NvbnRleHRfdG9fc2lkKHNvdXJjZSxzdHJsZW4oc291cmNlKSsxLCZzcmMpKXJldHVybiAxO2lmKHNlcG9sX3N0cmluZ190b19zZWN1cml0eV9jbGFzcygiYmxrX2ZpbGUiLCZjbHMpKXJldHVybiAxOwogY29uc3QgY2hhciAqdHlwZXNbXT17InVzZXJkYXRhX2Jsb2NrX2RldmljZSIsImJsb2NrX2RldmljZSIsImJvb3RfYmxvY2tfZGV2aWNlIn07Y29uc3QgY2hhciAqcGVybXNbXT17Im9wZW4iLCJyZWFkIiwid3JpdGUiLCJnZXRhdHRyIiwiaW9jdGwifTsKIGZvcihpbnQgaT0wO2k8MztpKyspe2NoYXIgY3R4WzEyOF07c25wcmludGYoY3R4LHNpemVvZihjdHgpLCJ1Om9iamVjdF9yOiVzOnMwIix0eXBlc1tpXSk7aWYoc2Vwb2xfY29udGV4dF90b19zaWQoY3R4LHN0cmxlbihjdHgpKzEsJnRndCkpcmV0dXJuIDE7Zm9yKGludCBqPTA7ajw1O2orKyl7c2Vwb2xfYWNjZXNzX3ZlY3Rvcl90IHJlcXVlc3RlZDtzdHJ1Y3Qgc2Vwb2xfYXZfZGVjaXNpb24gYXZkO2lmKHNlcG9sX3N0cmluZ190b19hdl9wZXJtKGNscyxwZXJtc1tqXSwmcmVxdWVzdGVkKSlyZXR1cm4gMTtpZihzZXBvbF9jb21wdXRlX2F2KHNyYyx0Z3QsY2xzLHJlcXVlc3RlZCwmYXZkKSlyZXR1cm4gMTtwcmludGYoImZzY2tcdCVzXHRibGtfZmlsZVx0JXNcdCVzXG4iLHR5cGVzW2ldLHBlcm1zW2pdLChhdmQuYWxsb3dlZCZyZXF1ZXN0ZWQpPT1yZXF1ZXN0ZWQ/ImFsbG93IjoiZGVueSIpO319CiBmcmVlKGRhdGEpO3JldHVybiBmZXJyb3Ioc3Rkb3V0KT8xOjA7Cn0K'}
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
