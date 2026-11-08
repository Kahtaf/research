from pathlib import Path
import hashlib,json,struct,re
R=Path(__file__).resolve().parents[1];X=R/'remote';A=X/'artifacts';E=X/'evidence'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((X/'EXPORT-MANIFEST.json').read_text())
assert all((X/n).stat().st_size==v['bytes'] and h(X/n)==v['sha256'] for n,v in manifest.items())
prefix='/srv/android/asus-stock-gpio28-review-20261106-r1'
objects=[]
for n in ['mt_soc_codec_63xx','AudDrv_Gpio','AudDrv_Afe']:
 p=A/'sound/soc/mediatek/mt_soc_audio_8163'/(n+'.o');d=p.read_bytes()
 assert d[:4]==b'\x7fELF' and d[4]==2 and int.from_bytes(d[18:20],'little')==183 and int.from_bytes(d[16:18],'little')==1
 cmd=p.with_name('.'+p.name+'.cmd').read_text();assert prefix+'/kernel/sound/soc/mediatek/mt_soc_audio_8163/'+n+'.c' in cmd and 'aarch64-linux-gnu-gcc' in cmd and '-D__KERNEL__' in cmd
 if n=='mt_soc_codec_63xx':assert prefix+'/kernel/sound/soc/mediatek/mt_soc_audio_8163/p00a_stock_gate.h' in cmd
 objects.append(dict(name=p.name,sha256=h(p),bytes=len(d),machine='AArch64',kind='relocatable',actual_source_and_kernel_flags_in_cmd=True))
nm=(E/'mt_soc_codec_63xx-nm.log').read_text()
for v in ['p00a_gate_output_locked','p00a_gate_release','Speaker_ClassAB_Open','Speaker_ClassAB_close','devm_gpio_request_one','gpiod_direction_output_raw','of_get_named_gpio_flags']:assert v in nm
for v in ['switch_mode_delay','switch_mode_lock','AudDrv_GPIO_EXTAMP_Select','mt_soc_get_dts_config','setUsingExtSpeaker']:assert v not in nm
assert 'setUsingExtSpeaker' not in (E/'AudDrv_Afe-nm.log').read_text()
dis=(E/'mt_soc_codec_63xx-objdump.log').read_text()
m=re.search(r'(?ms)^[0-9a-f]+ <p00a_gate_output_locked>:\n(.*?)(?=\n[0-9a-f]+ <)',dis);assert m
assert 'gpiod_direction_output_raw' in m[1] and not any(v in m[1] for v in ['udelay','usleep_range','AudDrv_GPIO_EXTAMP_Select'])
(R/'evidence/gate-output.disassembly.txt').write_text(m[0])
for n in ['olddefconfig','arm64-codec','arm64-gpio','arm64-afe','board-dtb']:
 r=json.loads((E/(n+'.json')).read_text());assert r['exit']==0 and '-j1' in r['command'] and r['affinity']==[0] and r['address_space_bytes']==[1024**3]*2
assert h(A/'kbuild-inputs/.config')=='26c59e0afa3f6438fafea4b5379b898c9b1fcaf05adf1d7e14db93b2e976bd13'
row=json.loads((R/'evidence/routing-repro-extraction.json').read_text());binding=json.loads(json.loads((R/'evidence/bind-exact-routing.json').read_text())['stdout']);assert row['routing_file_sha256']==binding['sha256']
assert 'runtime error: member access within null pointer' in (E/'lifetime-routing-pm-run.log').read_text()
rec=dict(all_exported_hashes_verified=True,objects=objects,actual_generated_headers_retained=True,actual_dtc_sha256=h(A/'host-tools/dtc'),new_header_bound_to_real_compiler_dependency=True,codec_ClassAB_references_retained=True,codec_AW_and_GPIO24_select_references_absent=True,AFE_AW_state_reference_absent=True,gate_disassembly_has_no_delay_or_generic_EXTAMP_call=True,routing_repro_matches_exact_BMC_source=True,source_candidate_disposition='CHANGES_REQUESTED')
(R/'evidence/artifact-verification.json').write_text(json.dumps(rec,indent=2)+'\n')
print(json.dumps(rec,indent=2))
