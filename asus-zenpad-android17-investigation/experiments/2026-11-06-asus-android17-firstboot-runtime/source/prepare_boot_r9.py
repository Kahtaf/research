from pathlib import Path
import subprocess as s, shutil,json,hashlib
R=Path('/srv/android/asus-firstboot-runtime');I=R/'inputs/boot-r9';assert not I.exists();shutil.copytree(R/'inputs/boot-r8',I,symlinks=True)
cmd=json.loads((R/'evidence/observer-compile.json').read_text())['command'];cmd=[x.replace(str(R/'source/observer.c'),str(R/'source/observer_r2.c')).replace(str(R/'artifacts/observer'),str(R/'artifacts/observer-r2')).replace(str(R/'inputs/observer-r1/observer.d'),str(R/'evidence/observer-r2.d')) for x in cmd]
p=s.run(cmd,capture_output=True,text=True);(R/'evidence/observer-r2-compile.json').write_text(json.dumps(dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0,p.stderr
shutil.copyfile(R/'artifacts/observer-r2',I/'root/system/bin/firstboot-observer');(I/'root/system/bin/firstboot-observer').chmod(0o755)
(I/'observer-r2-manifest.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256((R/'source/observer_r2.c').read_bytes()).hexdigest(),elf_sha256=hashlib.sha256((R/'artifacts/observer-r2').read_bytes()).hexdigest(),cgroups_sha256=hashlib.sha256((I/'root/system/etc/cgroups.json').read_bytes()).hexdigest(),fixture_changes='Only read-only observations and the same allowed/denied non-readiness property tests; unchanged platform init commands'),indent=2))
script=(R/'source/run_boot.py').read_text().replace("I=R/'inputs/boot-r8'","I=R/'inputs/boot-r9'").replace('kernel-build-r5/arch/arm64/boot/Image','kernel-build-r6/arch/arm64/boot/Image');(R/'source/run_boot_r9.py').write_text(script)
# Dedicated copy of the policy loader using the same already-built cpuset kernel.
script=(R/'source/run_policy.py').read_text().replace("O=R/'run-policy-r2'","O=R/'run-policy-r3'").replace("str(I/'Image')","str(R/'kernel-build-r6/arch/arm64/boot/Image')");(R/'source/run_policy_r3.py').write_text(script)
print('boot r9 prepared')
