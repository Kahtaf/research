from pathlib import Path
import json,re,hashlib
O=Path(__file__).resolve().parent.parent;E=O/'evidence/remote';a=json.loads((E/'evidence/final-audit-owned.json').read_text());c=json.loads((E/'evidence/capture.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['run-r3-actual','run-r4-metadata-crud','run-r2-mandatory-malformed'];logs={n:(E/n/'serial.log').read_text() for n in names};actual,meta,negative=(logs[n] for n in names)
qa={}
for n,t in logs.items():
 r=json.loads((E/n/'result.json').read_text());qa[n+'_serial_hash']=sha(E/n/'serial.log')==r['log_sha256'];qa[n+'_complete']=r['complete'] and not r['timeout'] and r['qemu_exit']==0
qa['maps31']=len(re.findall(r'MAP_INFO .*ok=1',meta))==31 and len(re.findall(r'MAP_CRUD .*ok=1 restored=1',meta))==31 and 'EXEC_RESULT /system/bin/loader_probe rc=0' in meta
qa['handler']=all(s in actual for s in ['HANDLER_INIT ok=1','HANDLER_TAG tag=0 forbidden=-1 untag=0','EXEC_RESULT /system/bin/handler_probe rc=0'])
qa['policy10']=len(re.findall(r'POLICY_PACKET .*passed=1',actual))==10 and 'POLICY_RESULT failures=0' in actual
qa['network60']=len(re.findall(r'NETWORK_PACKET .*passed=1',actual))==60 and not re.search(r'NETWORK_PACKET .*passed=0',actual) and 'NETWORK_PATH_RESULT failures=0' in actual
qa['local_prefix4_EPERM_before_TX']=len(re.findall(r'NETWORK_PACKET .*phase=local_prefix_denied .*tx=-1 rx=-1 errno=1 passed=1',actual))==4
qa['malformed_actual_rejection']='netd.o too small: 29' in negative and 'EXEC_RESULT /apex/com.android.tethering/bin/netbpfload rc=134' in negative and 'CONNECTIVITY_MAINLINE_DONE present=0' in negative
qa['wholechain_failure_preserved']='EXEC_RESULT /apex/com.android.tethering/bin/netbpfload rc=121' in actual and 'CRITICAL FAILURE LOADING BPF PROGRAMS FROM /vendor/etc/bpf' in actual and 'CONNECTIVITY_MAINLINE_DONE present=1' in actual
qa['exact_final_inputs']=True
for n in ['run-r3-actual','run-r4-metadata-crud']:
 inp=json.loads((E/n/'inputs.json').read_text())
 for row in c['objects']:qa['exact_final_inputs'] &= inp[row['install_path']]==row['current_sha256']
 for path,row in c['loaders'].items():qa['exact_final_inputs'] &= inp[path]==row['sha256']
qa['frozen_receipts_identical']=all(sha(E/'evidence'/n)==sha(O.parent/'2026-11-06-asus-final-bpf-runtime/evidence/remote/evidence'/n) for n in ['capture.json','final-audit.json','final-host-binding.json'])
qa['fixture_source_binary_reproduction']=all(x['match'] for x in json.loads((E/'evidence/init-source-reproduction.json').read_text()))
qa['allocation_within_512MiB']=a['allocation_bytes']<512*1024**2
assert all(qa.values()),qa
plain=re.sub(r'\x1b\[[0-9;]*m','',actual);lines=plain.splitlines();start=next(i for i,x in enumerate(lines) if 'Processing ELF object /apex/com.android.tethering/etc/bpf/mainline/netd.o' in x);end=next(i for i in range(start,len(lines)) if 'Loaded object: /apex/com.android.tethering/etc/bpf/mainline/netd.o' in lines[i]);selection=lines[start:end+1];(O/'evidence/genuine-loader-netd-selection.txt').write_text('\n'.join(selection)+'\n')
programs=re.findall(r'netd.o \(([^)]+)\) returned fd: (\d+)', '\n'.join(selection));maps=[x for x in meta.splitlines() if x.startswith('MAP_INFO')]
report=dict(status='PASS_SCOPED_FINAL_CONNECTIVITY_NETD_RUNTIME',unit_complete=True,no_children=True,connectivity_runtime_acceptance=True,whole_platform_acceptance=False,overall_boot_go=False,physical_go=False,flash_go=False,remote_prefix='/srv/android/asus-final-netd-runtime-20261106',final_image=c['raw_before'],raw_full_hash_not_repeated=True,raw_stat_and_frozen_receipts_unchanged=True,objects=[r for r in c['objects'] if Path(r['install_path']).name in ['netd.o','netd@funcs.o']],loader=c['loaders']['apex/com.android.tethering/bin/netbpfload'],kernel_sha256=a['kernel_sha256'],config_sha256=a['config_sha256'],properties=a['properties'],active_programs=programs,active_map_metadata=maps,tests=dict(metadata_CRUD=dict(maps=31,exit=0,run='run-r4-metadata-crud',loader='immutable direct genuine helper, fresh guest'),handler=dict(exit=0,run='run-r3-actual'),policy=dict(cases=10,exit=0),network=dict(cases=60,exit=0,local_prefix_pretransmit_EPERM_cases=4),mandatory_malformed=dict(run='run-r2-mandatory-malformed',file='netd.o',replacement_bytes=29,loader_exit=134,signal='SIGABRT',message='file .../netd.o too small: 29',mainline_done=False)),wholechain=dict(exit=121,mainline_done=True,blocker='unchanged final vendor filter cc68...; no filter candidate touched',setproperty_exit125='historical only; not reached here'),runs={n:a['runs'][n] for n in names},qa=qa,allocation_bytes=a['allocation_bytes'],limits=['No Android init/property-service/linker namespace integration; generic historical property_info and unlabelled property area; every seed value read back through Bionic.', 'ro.bpf.allow_legacy_kernel=true is copied exactly from the final product, not newly enabled. No ro.bpf.kver_override or readiness property seed.', 'Final netd@funcs.o is hash-bound and present, not selected on Linux4.9; captured source requires kernel6.6.118 for funcs.', 'Final Connectivity loader is bound to installed APEX bytes; no independent full compiler/source attestation for that loader.', 'Fixture dynamic libraries and consumer probes are immutable qualified captures, not a full final Android userspace closure.', 'Cross-profile loopback and UID permission migration remain OPEN/FAILED. No policy flags disabled or hooks backported.', 'Whole platform optional metrics/uprobestats and aconfig warnings remain outside scoped acceptance; vendor filter still fails critically.'],attempts=['Initial runs: unusable-label return treated as fatal; no product result claimed.', 'r2 actual: intentional captured loader map-reuse abort; 44 packets pass, missing iptables caused four extra failures.', 'r3 metadata: missing required BPFFS pin directories; no map qualification claimed.', 'Final fixes only populate owned fixture context, sequence fresh-map tests, and reuse immutable captured iptables/ip6tables.'])
(O/'evidence/final-report.json').write_text(json.dumps(report,indent=2)+'\n');(O/'evidence/qa-results.json').write_text(json.dumps(qa,indent=2)+'\n')
resources=[]
for n in names:
 t=(E/n/'host-resources.txt').read_text();resources.append(f"{n}: {re.search(r'Elapsed .*?: (.*)',t).group(1)}, peak RSS {re.search(r'Maximum resident set size \(kbytes\): (\d+)',t).group(1)} KiB")
(O/'report.md').write_text('''# Final-byte Connectivity/netd qualification

**PASS for the scoped Connectivity/netd runtime tests. Whole-platform/boot/physical/flash approval remains false.** Exact final `netd.o` (`863f3d2e79e804559c90ec145f23210d48f841777bb646a5f3f4b45952aad4b8`) and `netd@funcs.o` (`b5f8f4bf79dfbd6403405163b768a3307b43fd30d90b19ac3fd2260d746ff9c4`) were present with genuine installed Connectivity loader `2bf5e22c967a3e2ab38ef0699056616346fd3dceae230f5950e9f4de82839985`. Every one of the frozen 26-object closure hashes matches the actual and map-test initramfs inputs.

The genuine loader loaded netd's seven selected programs and created its maps, then marked mainline loading complete. Its subsequent unchanged platform/vendor chain failed critically on final `filterPowerSupplyEvents.o`, exit121. This is **not a whole-chain pass**. Neither the vendor repair candidate nor its worker was consulted. Genuine SetProperty exit125 remains historical; this run never reaches it.

Results:

- 31 selected netd map metadata checks and 31 CRUD/restore checks passed in a fresh guest using the immutable genuine loader helper; exit0.
- Genuine BpfHandler initialization/tag/forbidden-tag/untag passed; exit0.
- 10 IPv4/IPv6 doze/standby allow/deny packets passed; exit0.
- 60 routed packet cases passed over veth and tun, covering IPv4/IPv6 TCP, UDP, DNS wire answers, doze, VPN lockdown, wrong/allowed IIF, local-prefix denial/host exception/removal, and xt_bpf user/admin penalty policies; network probe exit0.
- All four local-prefix denials returned `tx=-1`, `errno=EPERM` before transmission. VPN ingress denials instead allow outgoing transmission and prevent delivery, as expected.
- Separately replacing mandatory netd.o with 29 malformed bytes made the **genuine final installed loader** log `netd.o too small: 29`, abort with SIGABRT (harness exit134), and leave mainline_done absent. This qualifies malformed-file rejection, not graceful recovery or a valid-ELF verifier negative. Downstream failed probes in that negative guest are expected, not positive qualifications.

Actual final SYSTEM `/system/build.prop` SHA `985595ce4c8c20600ca942c8d3475f92bea8d1f2199bec74aa21abc16a16f5ce` supplies SDK37, sdk_full37.0, codename **Baklava**, and userdebug. Its existing `ro.bpf.allow_legacy_kernel=true` is retained exactly; no new policy relaxation. `ro.board.first_api_level` is absent and is not invented from vendor `ro.product.first_api_level=23`. The genuine loader default applies. Captured `/system/etc/init/netbpfload.rc` and the actual source_apex_version symlink `373399999` yield API3705 through the real probe code. Property names/values/source hashes and read sites are exported. No readiness property is seeded; no kernel-version override is set.

The exact funcs object remains in the closure. Genuine Linux4.9 selection uses netd.o. Captured loader source gates funcs on Linux6.6.118; no execution claim is made for the unselected variant, ring buffers, or sk_storage. See `evidence/genuine-loader-netd-selection.txt` for actual selected maps/programs and skips. The final installed loader is byte-bound through the APEX; independent full C++ source/compiler provenance is not claimed.

The minimal fixture has no Android property service or complete linker configuration/SELinux property labeling. Bionic property-area creation reports an xattr failure on devtmpfs; the area remains usable and all five actual product values are added and read back successfully. Generic captured property_info and immutable qualified dynamic libraries/probes are retained. No namespace owner's Android-init fixture was duplicated. Missing platform aconfig storage remains a disclosed pre-existing whole-platform boundary; it did not block these Connectivity checks. Cross-profile loopback and UID permission migration remain **OPEN/FAILED**; flags and hooks were not changed.

Earlier attempts are preserved: property-area return handling stopped the first guests; r2 exposed the captured loader's explicit abort on map reuse plus absent firewall binaries; r3 metadata lacked BPFFS pin directories. The final packet guest includes genuine immutable iptables/ip6tables, and map tests run in a fresh guest with required directories. These are owned fixture corrections. Versioned init sources were recompiled at the original source pathname and reproduced both final guest init hashes exactly.

All QEMU runs use one vCPU,384MiB,TCG single thread,no external NIC,one host CPU affinity,1GiB address-space limit,and a finite90-second timeout. All completed without timeout/manual host signals. Final acceptance runs:

'''+ '\n'.join('- '+x for x in resources)+f'''

Owned remote allocation at final audit: {a['allocation_bytes']} bytes (<512MiB). Only tiny fixture init/property-seed code was compiled; no Ninja/Soong/kernel/native product build or active source/output write occurred. Existing guest network harness internally terminates its own virtual peer/relay processes; no external/device/worker process was signalled.

Raw SYSTEM was neither copied nor rehashed: frozen pre/post capture/runtime SHA04b4 receipts were reused, its0444 size/inode/mtime rechecked, and every small extracted object/loader rehashed. Original frozen receipts are byte-identical. No credentials were copied.

Parent acceptance boundary: accept these exact-byte scoped netd behavior results and the malformed negative. Whole-platform loading still requires the separate vendor-filter repair and future authorized exact-final-byte retest. Android init/property-service/linker namespace integration and the known cross-profile/UID-migration failures remain with their owners. No boot, physical-device, flash, or service-ready GO follows.

Reproduction: review `scripts/`, `evidence/final-report.json`, and final run command/input/resource/log receipts under `evidence/remote/`. Existing run paths are immutable; choose a new owned run name before rerunning. Never substitute historical c523/25ccea netd bytes or seed guessed build values.
''')
readme=(O/'README.md').read_text().replace('Status: In progress. Bounded fixture-only work; no children, product writes, device operations or boot/flash approval.','Status: Complete. Scoped Connectivity/netd runtime PASS:31 maps,70 policy/network cases,and genuine malformed-file rejection. Whole-platform vendor loading remains blocked; no boot/physical/flash GO. No children or product writes.')
(O/'README.md').write_text(readme)
print(json.dumps(dict(status=report['status'],qa=qa,resources=resources,allocation=a['allocation_bytes']),indent=2))
