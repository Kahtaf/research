import os,resource,pathlib,json
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
F=pathlib.Path('/srv/android/asus-sdk37-system-ext4-qualification-20261106/fixture-r2')
print(json.dumps({'files':{p.name:p.stat().st_size for p in F.iterdir() if p.is_file()},'logs':{p.name:p.read_text() for p in F.glob('*.log')}}))
