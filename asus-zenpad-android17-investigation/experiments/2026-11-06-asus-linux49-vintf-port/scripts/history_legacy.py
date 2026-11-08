import subprocess,json
r={}
for root in ['/srv/android/reference-kernel','/srv/android/lineage24/kernel/asus/p00a-fd']:
 r[root]={}
 for args in [['rev-parse','--is-shallow-repository'],['log','-1','--format=%H %s','--all','--','android/configs/android-base.config','android/configs/android-base.cfg','arch/arm64/configs/android-base.config']]:
  try:z=subprocess.run(['git','-C',root]+args,capture_output=True,text=True,timeout=20);r[root][' '.join(args)]=z.stdout+z.stderr
  except subprocess.TimeoutExpired:r[root][' '.join(args)]='bounded 20-second timeout'
print(json.dumps(r,indent=2))
