import pathlib,json,base64,os,resource
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(30,30))
R=pathlib.Path('/srv/android/asus-userdata-block-labels-20261106')
paths=list((R/'inputs').rglob('*'))+list((R/'current').glob('*'))+[R/n for n in ['candidate.patch','candidate-device-file_contexts','fixture-only-vendor_file_contexts','native-evidence-attempt2.json']]
print(json.dumps({str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode()for p in paths if p.is_file() and p.name!='precompiled_sepolicy'}))
