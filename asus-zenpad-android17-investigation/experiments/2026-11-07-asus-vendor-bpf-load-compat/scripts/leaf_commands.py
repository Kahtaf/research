from pathlib import Path
import subprocess as s,json
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');A=Path('/srv/android/lineage24');target='out/soong/.intermediates/system/bpf/loader/libbpf_android/android_arm64_armv8-a_shared/libbpf_android.so'
x=s.run([str(A/'prebuilts/build-tools/linux-x86/bin/ninja'),'-f','out/combined-lineage_p00a.ninja','-t','commands',target],cwd=A,capture_output=True,text=True);print('RC',x.returncode,x.stderr);lines=x.stdout.splitlines();selected=[l for l in lines if 'Loader.cpp' in l or ('libbpf_android.so' in l and ('clang++' in l or 'llvm-strip' in l))];(R/'evidence/native-commands.json').write_text(json.dumps(selected,indent=2));print('\n'.join(selected)[-19000:])
for p in [Path('/srv/android/asus-network-runtime/source/loader_probe.cpp'),A/'system/bpf/loader/include/libbpf_android.h']:
 if p.exists():print(p,p.read_text()[:6500])
