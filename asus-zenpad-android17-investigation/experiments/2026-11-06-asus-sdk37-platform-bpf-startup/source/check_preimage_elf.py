from pathlib import Path
import hashlib,json,subprocess as s
O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106');T=Path('/srv/android/lineage24')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
refs=['out/target/product/p00a/system/bin/bpfloader','out/soong/.intermediates/system/bpf/loader/bpfloader/android_arm64_armv8-a/bpfloader','out/soong/.intermediates/system/bpf/loader/bpfloader/android_arm64_armv8-a/unstripped/bpfloader']
prior=sha(O/'inputs/prior/inputs/platform-bpfloader');rows={p:{'sha256':sha(T/p),'bytes':(T/p).stat().st_size,'equals_captured_preimage':sha(T/p)==prior} for p in refs if (T/p).is_file()}
result={'captured_preimage_sha256':prior,'actual_outputs':rows,'active_source_sha256':sha(T/'system/bpf/loader/bpfloader.rs')};assert any(x['equals_captured_preimage'] for x in rows.values()),result
(O/'evidence/actual-preimage-elf-binding.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
