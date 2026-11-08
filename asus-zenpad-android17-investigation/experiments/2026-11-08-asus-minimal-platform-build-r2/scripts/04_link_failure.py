from pathlib import Path
import base64,hashlib,json,os,re,subprocess
R=Path('/srv/android/asus-minimal-platform-build-r2-20261108');F=Path('/srv/android/asus-minimal-platform-build-20261108');P=Path('/srv/android/asus-minimal-platform-preparation-20261108');K=R/'kernel';O=R/'out';E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
status=json.loads((E/'kernel-status.json').read_text());assert status['exit']==2
identity=json.loads((E/'identity.json').read_text());assert sha(O/'.config')==identity['config_sha256']
log=E/'kernel-compile.log';lines=log.read_text().splitlines();hits=[i for i,l in enumerate(lines) if re.search('undefined reference|error:|fatal error:',l)]
contexts=[dict(line=i+1,text='\n'.join(lines[max(0,i-2):min(len(lines),i+3)])) for i in hits]
dev=O/'drivers/misc/mediatek/devapc/mt8163/devapc.o';assert dev.is_file();data=dev.read_bytes();assert b'Enable TEE...Request IRQ in TEE.' in data and b'Disable TEE...Request IRQ in REE.' not in data
objdis=subprocess.check_output(['aarch64-linux-gnu-objdump','-dr','--disassemble=devapc_probe',str(dev)],text=True)
assert 'request_threaded_irq' not in objdis and 'start_devapc' not in objdis and 'devm_clk_get' in objdis
(E/'devapc-TEE-branch.disasm').write_text(objdis)
# Preserve actual failing relocation/call evidence from the linked intermediate, no ELF build/relink.
for name in ['met_tracing_record_cmdline','virtual_sensor_set_cur_state','battery_meter_dts_probe','battery_meter_dts_remove']:
 d=subprocess.check_output(['aarch64-linux-gnu-objdump','-dr','--disassemble='+name,str(O/'drivers/built-in.o')],text=True)
 (E/('failure-call-'+name+'.disasm')).write_text(d)
# Verify the copied sources changed only in the expressly authorized config-hash metadata.
changed=[]
for parent,ds,ns in os.walk(K):
 for name in ns:
  p=Path(parent)/name;rel=p.relative_to(K);old=F/'kernel'/rel
  if p.is_symlink():assert old.is_symlink() and os.readlink(p)==os.readlink(old)
  elif not old.is_file() or sha(p)!=sha(old):changed.append(str(rel))
assert changed==['arch/arm64/kernel/asus_entry_tag.h'],changed
assert sha(F/'out/.config')=='add8f8e85e0fe007364da835f2d45d91663551876387ba4a695e410d4c1cc7bb'
assert json.loads((F/'evidence/kernel-status.json').read_text())['exit']==2
prepared=json.loads((P/'evidence/preparation-receipt.json').read_text())
for n,h in prepared['uploaded'].items():assert sha(P/n)==h,n
assert sha(R/'helper/init')==sha(F/'helper/init')=='37e9e2a2d73447947fb33e57e9513fa6079517b571f5a41bc58fbb91f84633fc'
assert (R/'artifacts/ramdisk.wrapped').read_bytes()==(F/'artifacts/ramdisk.wrapped').read_bytes()
# The retained config distinguishes these failures; it is not changed to repair them.
config=(O/'.config').read_text();selected={}
for n in ['MTK_IN_HOUSE_TEE_SUPPORT','MTEE_CMA_SECURE_MEMORY','OF','CMA','NET','FTRACE','VS_BACKLIGHT_COOLER','MTK_LEDS','ASUS_P00A_LP8557','MTK_FB','FB','MTK_SMART_BATTERY','ASUS_P00A_MAIN_BATTERY_SOC','ASUS_P00A_BATTERY_DIAGNOSTIC','THERMAL','CPU_FREQ']:
 m=re.search(r'^(?:# )?CONFIG_'+n+r'(?:=(.*)| is not set)$',config,re.M);selected[n]=(m[1] or 'n') if m else 'absent'
record=dict(status='STOP_ON_AUTHORIZED_CONTINUATION_LINK_FAILURE',history=dict(initial_kernel_compile_failed=True,one_config_corrected_continuation_link_failed=True,total_kernel_make_invocations=2,helper_compiles_total=1,helper_compiles_this_continuation=0,retries_after_new_blocker=0),config_gate='exactly two ancestor TEE selections; all other failed config values equal',config_sha256=sha(O/'.config'),undefined_symbols=sorted(set(re.findall(r"undefined reference to `([^']+)'",'\n'.join(lines)))),error_contexts=contexts,devapc_TEE_branch=dict(object_bytes=dev.stat().st_size,object_sha256=sha(dev),TEE_message_present=True,REE_message_absent=True,probe_no_REE_irq_call=True,devm_clk_get_call_present=True,runtime_unqualified=True),selected_config=selected,source_changes_from_failed=changed,prepared_and_failed_config_sources_preserved=True,helper_and_initramfs_reused_byte_identical=True,source_symlink_now_owned=Path(os.readlink(O/'source'))==K,Image_exists=(O/'arch/arm64/boot/Image.gz-dtb').exists(),vmlinux_exists=(O/'vmlinux').exists(),System_map_exists=(O/'System.map').exists(),compiled_DT_exists=(O/'arch/arm64/boot/dts/mediatek/asus-p00a.dtb').exists(),package_created=False,PLAN_calls=0,decoder_tests=0,device_contact=False,partial_output_preserved=str(O))
(E/'link-failure-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
files={};paths={'evidence/kernel-compile.log':log,'artifacts/resolved-after-make.config':O/'.config','source/asus_entry_tag.h':K/'arch/arm64/kernel/asus_entry_tag.h','artifacts/init':R/'helper/init','artifacts/ramdisk.wrapped':R/'artifacts/ramdisk.wrapped','artifacts/initramfs.cpio.gz':R/'artifacts/initramfs.cpio.gz'}
for p in E.glob('*'):
 if p.is_file():paths['evidence/'+p.name]=p
for n in ['utsrelease.h','compile.h']:
 p=O/'include/generated'/n
 if p.exists():paths['evidence/partial-'+n]=p
for n,p in paths.items():d=p.read_bytes();files[n]=dict(data=base64.b64encode(d).decode(),sha256=hashlib.sha256(d).hexdigest())
print(json.dumps(dict(files=files,failure=record)))
