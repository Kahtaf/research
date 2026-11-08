from pathlib import Path
import os,json,subprocess as s,resource,re
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');S=R/'inputs/native-snapshot';os.environ['TMPDIR']=str(R/'tmp');os.environ['LD_LIBRARY_PATH']=str(S/'out/host/linux-x86/lib64');os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));resource.setrlimit(resource.RLIMIT_CORE,(0,0));P=json.loads((R/'evidence/native-snapshot-pins.json').read_text());runs={}
for name,exe in [('before-old19',S/P['selected_edges']['host']['testld']['out'][0]),('after-all',R/'work/native/host-tests')]:
 os.chmod(exe,0o755);p=s.run([str(exe),'--gtest_color=no'],cwd=S,capture_output=True,text=True,timeout=30);(R/'evidence'/('tests-'+name+'.log')).write_text(p.stdout+p.stderr);runs[name]={'rc':p.returncode,'passed':re.findall(r'\[  PASSED  \] (\d+) tests?',p.stdout),'stderr':p.stderr[-1000:]};assert p.returncode==0,p.stdout[-3000:]+p.stderr
(R/'evidence/host-tests.json').write_text(json.dumps(runs,indent=2));print(json.dumps(runs,indent=2))
