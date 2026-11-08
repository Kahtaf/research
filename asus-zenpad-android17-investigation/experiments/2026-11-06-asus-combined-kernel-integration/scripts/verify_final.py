from pathlib import Path
import hashlib,json,subprocess,shutil,datetime,fcntl,re
R=Path('/srv/android/asus-build-continuation');E=R/'integration-r5';B=R/'build';K=R/'kernel';H=Path('/srv/android/asus-network-runtime/handoff-r1')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,j):(E/n).write_text(json.dumps(j,indent=2)+'\n')
def config(p):
 d={}
 for l in p.read_text().splitlines():
  if l.startswith('CONFIG_'):k,v=l.split('=',1);d[k]=v
  elif l.startswith('# CONFIG_') and l.endswith(' is not set'):d[l.split()[1]]='n'
 return d
with (R/'logs/kernel.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert (R/'logs/kernel-r5.exit-code').read_text().strip()=='0'
 assert (R/'logs/kernel-r5.complete').is_file()
 for line in (R/'logs/kernel-r5.sha256').read_text().splitlines():
  h,p=line.split(None,1);assert sha(Path(p))==h
 result=subprocess.run(['python3',str(R/'scripts/verify_kernel.py'),'r5',str(B)],capture_output=True,text=True)
 (E/'dt-verifier.log').write_text(result.stdout+result.stderr);assert result.returncode==0,result.stderr
 dt=json.loads((R/'logs/kernel-r5.evidence.json').read_text());assert dt['charging_opt_in_absent'] and not dt['hardware_validated']
 prior=json.loads((R/'evidence/combined-release.json').read_text());assert dt['dtb_sha256']==prior['dtb_sha256'];assert dt['profiles']==prior['profiles'] and dt['settings']==prior['settings']
 cfg=config(B/'.config');r4=config(E/'preserved-r4/.config');r3=config(R/'inputs/soc.config')
 assert cfg==r4,'Unexpected config drift from accepted physical r4'
 assert sha(B/'.config')=='067090e03ad762344308cebd0a71274d9943e299ded6707051ebfdc075dd045f'
 baseline=json.loads((R/'evidence/runtime-config-baseline.json').read_text());rows={k:dict(expected=v['physical'],actual=cfg.get(k,'n')) for k,v in baseline.items()}
 assert len(rows)==58 and all(v['actual']==v['expected'] for v in rows.values())
 for opt in ['FILE_LOCKING','BLK_CGROUP','CPUSETS']:assert cfg.get('CONFIG_'+opt)=='y'
 for opt in ['DUMMY','VETH','NAMESPACES','NET_NS']:assert cfg.get('CONFIG_'+opt,'n')=='n'
 core=json.loads((H/'evidence/network-config-equivalence.json').read_text())['core']
 for opt,row in core.items():assert cfg.get(opt,'n')==row['physical'],opt
 fcfg=json.loads((Path('/srv/android/asus-firstboot-runtime/evidence/firstboot-config-equivalence-r3.json')).read_text())['options']
 for row in fcfg:assert cfg.get(row['option'],'n')==row['expected'],row['option']
 save('config-receipt.json',dict(sha256=sha(B/'.config'),unchanged_from_r4=True,runtime_prerequisites=rows,network_core={k:dict(expected=v['physical'],actual=cfg.get(k,'n')) for k,v in core.items()},firstboot_selected_options=len(fcfg),firstboot_selected_options_equal=True,firstboot_runtime_parity=False,enabled=['CONFIG_FILE_LOCKING','CONFIG_BLK_CGROUP','CONFIG_CPUSETS'],virtual_only_disabled=['CONFIG_DUMMY','CONFIG_VETH','CONFIG_NAMESPACES','CONFIG_NET_NS']))
 names=['mtk_wcn_stp_send_data','mtk_wcn_wmt_func_on','wlanProbe','Charger_Detect_Init','Charger_Detect_Release','asus_p00a_bc12_type','asus_p00a_charge_publish','asus_p00a_charge_source_changed','asus_p00a_charge_request','asus_p00a_soc_read','asus_p00a_soc_capacity','blkcg_init_queue','cpuset_css_online','bpf_skb_load_bytes_relative','bpf_skb_load_bytes_relative_proto','trie_map_ops','trie_lookup_elem','trie_update_elem']
 symbols={}
 for line in (B/'System.map').read_text().splitlines():
  addr,typ,name=line.split()
  if name in names:symbols[name]=dict(address=addr,type=typ)
 assert set(symbols)==set(names),set(names)-set(symbols)
 assert all(symbols[n]['type'] not in ['w','W','v','V','U'] for n in names)
 for n in ['Charger_Detect_Init','Charger_Detect_Release','asus_p00a_charge_publish','asus_p00a_charge_request']:assert symbols[n]['type']=='T'
 save('symbols.json',symbols)
 active_board=Path('/srv/android/lineage24/device/asus/p00a/BoardConfig.mk').read_text()
 expected_addition='\ninclude device/asus/p00a/connectivity/BoardConfig-connectivity.mk\nBOARD_VENDOR_SEPOLICY_DIRS += device/asus/p00a/radio/sepolicy\nDEVICE_MANIFEST_FILE += device/asus/p00a/radio/manifest-bluetooth.xml\n'
 assert (E/'product-device/BoardConfig.mk').read_text()==active_board+expected_addition,'Unexpected BoardConfig candidate change'
 source=json.loads((E/'source-receipt.json').read_text())
 for p,row in source['changes'].items():assert sha(K/p)==row['after']
 assert sha(E/'combined-from-active-soc.patch')==source['patch_sha256']
 for src,name in [(B/'arch/arm64/boot/Image.gz-dtb','Image.gz-dtb'),(B/'.config','resolved.config'),(B/'include/config/kernel.release','kernel.release'),(R/'logs/kernel-r5.evidence.json','dt-receipt.json'),(R/'logs/kernel-r5.dtb','asus-p00a.dtb')]:
  shutil.copy2(src,E/name);assert sha(src)==sha(E/name)
 (E/'build-logs').mkdir(exist_ok=True)
 for p in (R/'logs').glob('kernel-r5.*'):shutil.copy2(p,E/'build-logs'/p.name)
 status={}
 for pid in [78673,132874,1048560]:
  p=Path('/proc')/str(pid)
  status[str(pid)]={'exists':p.exists()}
  if p.exists():status[str(pid)].update(stat=(p/'stat').read_text(),cmdline=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode())
 aosp=Path('/srv/android/asus-device-product/logs/full-build-r5.log')
 with aosp.open('rb') as f:f.seek(max(0,aosp.stat().st_size-4000));tail=f.read().decode(errors='replace')
 save('final-process-status.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),processes=status,aosp_log_bytes=aosp.stat().st_size,aosp_log_tail=tail,aosp_exit_marker_exists=Path('/srv/android/asus-device-product/logs/full-build-r5.exit-code').exists()))
 manifest=dict(status='Compiled and statically verified physical combined kernel; staged integration only',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),compile_exit=0,started=(R/'logs/kernel-r5.started').read_text().strip(),finished=(R/'logs/kernel-r5.finished').read_text().strip(),max_jobs=4,image={'file':'Image.gz-dtb','bytes':(E/'Image.gz-dtb').stat().st_size,'sha256':sha(E/'Image.gz-dtb')},config_sha256=sha(E/'resolved.config'),kernel_release=(E/'kernel.release').read_text().strip(),dtb_sha256=dt['dtb_sha256'],charging_permission_absent=True,source_receipt_sha256=sha(E/'source-receipt.json'),staged_product_receipt_sha256=sha(E/'staged-product-receipt.json'),runtime_source_receipt_sha256=sha(E/'runtime-source-preservation.json'),active_kernel_files_unchanged=source['active_source_files_verified'],declared_source_changes=len(source['changes']),new_source_delta=len(source['declared_new_delta']),targeted_network_handoff_accepted=True,firstboot_file_locking_parity_accepted=False,physical_boot_verified=False,full_product_ready=False,device_operations='PLAN_ONLY; parent-owned',automatic_AOSP_integration_started=False,remaining=['Firstboot r7 FILE_LOCKING=y runtime parity rerun and qualification','Optional whole-loader patch12 frozen qualified supplement or equivalent product validation','Original AOSP r5 terminal verification before active integration','Full SDK37 product compile, strict ELF/init/SELinux/VINTF/Google byte and image fit checks','Corrected whole-BOOT LK-aware initrd packaging owned separately','Physical firstboot with nearby fallback; parent owns all device work','Full policy/Java/WiFi/metrics/Google/root/hardware runtime verification'])
 save('manifest.json',manifest)
 print(json.dumps(manifest,indent=2))
