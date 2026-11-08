import subprocess,json
argv=['find','/srv/android','-maxdepth','7','(','-path','/srv/android/lineage24','-o','-iname','*private*','-o','-iname','*calibration*',')','-prune','-o','(','-name','checkvintf','-o','-name','assemble_vintf',')','-print']
try:r=subprocess.run(argv,capture_output=True,text=True,timeout=20);print(json.dumps({'argv':argv,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}))
except subprocess.TimeoutExpired as e:print(json.dumps({'argv':argv,'timeout_seconds':20,'partial_stdout':(e.stdout or b'').decode()}))
