import subprocess
for a in [['patchelf','--version'],['patchelf','--help']]:
 p=subprocess.run(a,capture_output=True,text=True,timeout=10);print(p.stdout,p.stderr)
