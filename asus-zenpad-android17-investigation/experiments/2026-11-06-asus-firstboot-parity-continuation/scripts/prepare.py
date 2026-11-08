from pathlib import Path
import json,hashlib,shutil,subprocess,datetime
P=Path('/srv/android/asus-firstboot-runtime'); R=Path('/srv/android/asus-firstboot-parity-continuation')
assert not R.exists(); R.mkdir()
for d in ['source','evidence','tmp']: (R/d).mkdir()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
status=json.loads((P/'evidence/kernel-r7-status.json').read_text()); assert status['returncode']==0
hashes=json.loads((P/'evidence/kernel-r7-hashes.json').read_text())
for n,h in hashes.items(): assert sha(P/n)==h
for f in ['kernel-r7-status.json','kernel-r7-hashes.json','kernel-r7-command.json','kernel-build-r7-compile.log','firstboot-config-equivalence-r3.json','firstboot-source-equivalence.json','physical-apply-validation.json','qualification-r2-equivalence-failure.json']:
 shutil.copy2(P/'evidence'/f,R/'evidence'/f)
for d in ['run-cpuset-r1','run-cpuset-r2','run-boot-r8','run-boot-r10']:
 (R/'evidence'/d).mkdir()
 for f in ['status.json','command.json','serial.log']: shutil.copy2(P/d/f,R/'evidence'/d/f)
for n in ['seed_exec.c','cpuset_probe.c','locks_probe.c','policy_probe.c','observer_r3.c','prepare_boot.py']: shutil.copy2(P/'source'/n,R/'source'/n)
for n in ['run_boot_r10.py','run_cpuset_probe.py','run_locks_probe.py','run_policy.py']:
 t=(P/'source'/n).read_text().replace("R=Path('/srv/android/asus-firstboot-runtime')",f"P=Path('{P}');R=Path('{R}')")
 t=t.replace("I=R/'inputs/boot-r10'","I=P/'inputs/boot-r10'").replace("E=R/'inputs/early-r1'","E=P/'inputs/early-r1'").replace("I=R/'inputs/early-r1'","I=P/'inputs/early-r1'")
 t=t.replace("str(R/'kernel-build-r6/arch/arm64/boot/Image')","str(P/'kernel-build-r7/arch/arm64/boot/Image')").replace("str(R/f'kernel-build-{kernel}/arch/arm64/boot/Image')","str(P/f'kernel-build-{kernel}/arch/arm64/boot/Image')").replace("str(I/'Image')","str(P/'kernel-build-r7/arch/arm64/boot/Image')")
 t=t.replace("'1536'","'1024'").replace("O=R/'run-policy-r2'","O=R/'run-policy-r4'")
 if n=='run_boot_r10.py':
  t=t.replace("['seed_exec.c','run_boot_r10.py','prepare_boot_r10.py','observer_r3.c']","['seed_exec.c','run_boot_r11.py','observer_r3.c']"); n='run_boot_r11.py'
 (R/'source'/n).write_text(t)
(R/'evidence/preflight.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'r7_verified':hashes,'source_scripts':{p.name:sha(p) for p in (R/'source').iterdir()},'prior_r11_absent':not (P/'run-boot-r11').exists(),'prior_qualification_r3_absent':not (P/'evidence/qualification-r3.json').exists(),'processes':subprocess.check_output(['ps','-eo','pid,ppid,etime,args'],text=True)},indent=2))
print('Prepared isolated fixture with verified r7; no compilation of kernel')
