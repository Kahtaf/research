from pathlib import Path
P=Path('2026-11-07-asus-android-runtime-network-parity/scripts');R=Path('2026-11-07-asus-vendor-bpf-load-compat/scripts');old='/srv/android/asus-android-runtime-network-parity-20261107';new='/srv/android/asus-vendor-bpf-load-compat-20261107'
for n in ['admit','corroborate_boot','prepare','execute','verify_cow','extract']:
 t=(P/(n+'.py')).read_text().replace(old,new)
 if n=='prepare':
  t=t.replace("E/'build-result.json'","E/'kernel-selection.json'").replace("assert build['genuine_build_success']","assert build['reused_qualified_image']")
  start=t.index("p=(P/'source/runtime_patcher_r2.c')");end=t.index("run(['aarch64-linux-gnu-gcc'",start)
  t=t[:start]+"p=(R/'source/patcher.c').read_text();"+t[end:]
  t=t.replace("('observer.rc','observer.rc')","('observer.rc','observer.rc'),('candidate-lib','libbpf_android.candidate.so')")
  t=t.replace("system_modified=['system/vendor", "candidate_runtime=True,candidate_overlay={'system/lib64/libbpf_android.so':hashlib.sha256((I/'libbpf_android.candidate.so').read_bytes()).hexdigest()},system_modified=['system/lib64/libbpf_android.so','system/vendor")
 if n in ['execute','verify_cow']:t=t.replace('modified=2 added_observer=2','modified=3 added_observer=2')
 if n=='execute':
  t=t.replace("assert json.loads((E/'cow-verification.json').read_text())['passed']", "assert json.loads((E/'cow-verification.json').read_text())['passed']\n assert not (E/'actual-os-once.json').exists();(E/'actual-os-once.json').write_text(json.dumps({'authorized_actual_os_invocations':1}))")
  t=t.replace("fatal=next((line", "fatal=next((line")
  t=t.replace("if 'Kernel panic - not syncing' in line or", "if '=== CRITICAL FAILURE' in line or 'Kernel panic - not syncing' in line or ('F libc' in line and 'Fatal signal' in line) or 'Fatal error' in line or")
  t=t.replace('timeout=min(1,','timeout=min(0.2,')
 if n=='verify_cow':
  t=t.replace("('system/vendor/etc/fstab.mt8163','vendor.fstab'),", "('system/lib64/libbpf_android.so','libbpf_android.candidate.so'),('system/vendor/etc/fstab.mt8163','vendor.fstab'),")
  t=t.replace("for path in ['system/vendor", "for path in ['system/lib64/libbpf_android.so','system/vendor")
  t=t.replace('Two existing files + two observer files','Three existing files (including exact candidate library) + two observer files')
 if n=='extract':
  start=t.index('files=[p for p in R.rglob');end=t.index('d=dict(',start)
  t=t[:start]+"files=[p for root in [I,R/'run-runtime',R/'run-patch',E] for p in root.rglob('*') if p.is_file() and not p.is_symlink()]\n"+t[end:]
 (R/(n+'.py')).write_text(t)
