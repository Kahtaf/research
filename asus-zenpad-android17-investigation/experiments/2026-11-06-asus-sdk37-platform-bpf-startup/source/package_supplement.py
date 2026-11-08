from pathlib import Path
import os,hashlib,json,shutil,time,subprocess as s
O=Path('/srv/android/asus-sdk37-platform-bpf-startup-20261106');T=Path('/srv/android/lineage24');H=O/'supplement-r1';H.mkdir(exist_ok=False);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
files={}
def cp(src,rel):
 src=O/src;dst=H/rel;dst.parent.mkdir(parents=True,exist_ok=True);before=sha(src);shutil.copyfile(src,dst);assert before==sha(src)==sha(dst);files[str(rel)]={'sha256':before,'bytes':dst.stat().st_size,'source':str(src)}
cp('artifacts/12-platform-ringbuf-selftest-minimum.patch','patches/12-platform-ringbuf-selftest-minimum.patch')
for x in ['preimage','postimage']:cp('artifacts/'+x+'/system/bpf/loader/bpfloader.rs',x+'/system/bpf/loader/bpfloader.rs')
cp('artifacts/bpfloader-postimage','elf/bpfloader-postimage');cp('inputs/prior/inputs/platform-bpfloader','elf/bpfloader-preimage');cp('inputs/prior/artifacts/bpfloader-legacy','elf/bpfloader-prior-r16')
cp('artifacts/fixture-init-r2','runtime/fixture-init-r2');cp('source/fixture_init_r2.c','runtime/fixture_init_r2.c');cp('source/run_owned_r2.py','runtime/run_owned_r2.py')
for n in ['network.config','physical-baseline.config','manifest.json']:cp('inputs/prior/handoff-r1/'+n,'core-reference/'+n)
for n in ['command.json','bpfloader.clang.rsp','build.log','build.exit','strip.log','file-access.strace']:cp('build/postimage/'+n,'build/'+n)
for n in ['command.json','build.log','bpfloader.clang.rsp']:cp('inputs/prior/platform-build-legacy/'+n,'prior-build/'+n)
cp('inputs/prior/evidence/platform-rust-command.txt','prior-build/platform-rust-command.txt')
for n in ['run-r15','run-r16']:
 for f in ['serial.log','inputs.json','result.json']:cp('inputs/prior/'+n+'/'+f,'prior-runs/'+n+'/'+f)
for n in ['run-preimage','run-preimage-r2','run-postimage-r2','run-mandatory-negative-r2']:
 for f in ['serial.log','result.json','inputs.json','command.json','host-resources.txt']:cp(n+'/'+f,'runtime/'+n+'/'+f)
for p in (O/'evidence').rglob('*'):
 if p.is_file() and not p.name.endswith(('.pid','.supervisor.log')):cp(p.relative_to(O),Path('evidence')/p.relative_to(O/'evidence'))
for base in ['inputs/selected-root','inputs/object-source']:
 for p in (O/base).rglob('*'):
  if p.is_file():cp(p.relative_to(O),Path('objects' if base.endswith('selected-root') else 'object-source')/p.relative_to(O/base))
for name in ['system/bin/network_loader','system/bin/seed_properties','apex/com.android.uprobestats/bin/uprobestatsbpfload','apex/com.android.tethering/etc/bpf/mainline/netd.o']:
 cp('inputs/runtime-root-r2/'+name,'runtime-executables/'+name)
for rel in ['system/bpf/loader/Android.bp','system/bpf/loader/Loader.cpp','system/bpfprogs/Android.bp','system/bpfprogs/progs.aconfig']:
 cp('inputs/actual/'+rel,'actual-source/'+rel)
cp('inputs/prior/source/seed_properties.cpp','actual-source/seed_properties.cpp')
selection=json.loads((O/'evidence/selection.json').read_text());pre=sha(O/'artifacts/preimage/system/bpf/loader/bpfloader.rs');post=sha(O/'artifacts/postimage/system/bpf/loader/bpfloader.rs')
state=s.check_output(['ps','-p','78673,132874','-o','pid,ppid,etime,stat,comm'],text=True);(H/'evidence/parent-job-state-final.txt').write_text(state);files['evidence/parent-job-state-final.txt']={'sha256':sha(H/'evidence/parent-job-state-final.txt'),'bytes':(H/'evidence/parent-job-state-final.txt').stat().st_size,'source':'native ps at packaging'}
manifest={'schema':1,'kind':'offline SDK37 platform BPF startup supplement; parent integration input only','created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'owned_remote':str(O),'core_handoff_manifest_sha256':sha(O/'inputs/prior/handoff-r1/manifest.json'),'patch':{'path':'patches/12-platform-ringbuf-selftest-minimum.patch','sha256':sha(O/'artifacts/12-platform-ringbuf-selftest-minimum.patch'),'bytes':1353,'apply_root':'system/bpf','strip':1,'fuzz':0},'changes':{'system/bpf/loader/bpfloader.rs':{'before':pre,'after':post}},'test_elf_sha256':sha(O/'artifacts/bpfloader-postimage'),'test_kernel_sha256':sha(O/'inputs/network-qualified.Image'),'test_config_sha256':sha(O/'inputs/prior/handoff-r1/network.config'),'new_kernel_config_requirements':[],'build':json.loads((O/'evidence/build-result.json').read_text()),'qualification':json.loads((O/'evidence/qualification.json').read_text()),'reproduce':{'dependency_snapshot':str(O/'snapshot'),'dependency_pins':'evidence/frozen-inputs.json','compiler_pins':'evidence/toolchain-pins.json','command':'build/command.json','logs':'runtime/','runtime_full_closure':str(O/'inputs/runtime-root-r2'),'large_inputs_remote_only':['frozen Rust dependency closure','qualified virtual Image','runtime shared libraries','initramfs archives'],'not_a_product_binary_dropin':True},'gates':{'missing_selected_vendor_object':'system/vendor/etc/bpf/filterPowerSupplyEvents.o','actual_property_service_exit':125,'all_optional_platform_features':False,'supported_kernel_5_8_plus_runtime_tested':False,'cross_profile_policy':'inherited unqualified; not expanded in this startup supplement','physical_go':False,'full_os_ready':False,'ram_probe_blocker':False},'files':files}
(H/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'handoff':str(H),'manifest_sha256':sha(H/'manifest.json'),'files':len(files),'bytes':sum(v['bytes'] for v in files.values()),'parent_jobs':state}))
