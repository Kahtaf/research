import os,resource,pathlib,subprocess,json
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
P=pathlib.Path;A=P('/srv/android/lineage24');out={}
for args in [['grep','-RnE','file_contexts|file_context_handle','external/selinux/libselinux/src/android'],['grep','-RnE','SelabelLookupFileContextBestMatch|MakeDevice|0660|0600','system/core/init/devices.cpp'],['grep','-RnE','string_to|load_policy|context_to_sid','external/selinux/libsepol/include/sepol/policydb/services.h'],['ls','-l','out/host/linux-x86/lib64/libsepol.so']]:
 r=subprocess.run(args,cwd=A,capture_output=True,text=True,timeout=10);out[' '.join(args)]={'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
print(json.dumps(out,indent=2))
