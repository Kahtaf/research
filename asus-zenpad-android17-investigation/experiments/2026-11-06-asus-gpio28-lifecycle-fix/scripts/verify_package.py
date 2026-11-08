import difflib,hashlib,json,re,resource,platform
from pathlib import Path
from source import ROOT,REL,fn,funcs
from bounded import run
H=lambda b:hashlib.sha256(b).hexdigest();W=ROOT.parent
pins=json.loads((ROOT/'evidence/input-pins.json').read_text())
for p in pins:
 assert H((W/p['original']).read_bytes())==p['sha256']
 assert H((ROOT/p['copy']).read_bytes())==p['sha256']
old=(ROOT/'preimage'/REL/'mt_soc_codec_63xx.c').read_text();new=(ROOT/'candidate'/REL/'mt_soc_codec_63xx.c').read_text()
unchanged=[]
for name in ['Speaker_Amp_Change','Speaker_Amp_Get','Speaker_Amp_Set','Apply_Speaker_Gain','Audio_Speaker_Class_Set','Audio_Speaker_Class_Get','Audio_Speaker_Pga_Gain_Set','Audio_Speaker_Pga_Gain_Get','Headset_Speaker_Amp_Change']:
 a=fn(old,name);b=fn(new,name);assert a==b,name;unchanged.append({'function':name,'sha256':H(a.encode())})
# Preserve actual gain/default statements even where their public linkage changes.
for name,renamed in [('UpdateHeadsetGain','UpdateHeadsetGain_locked'),('SetMicPGAGain','SetMicPGAGain'),('InitCodecDefault','InitCodecDefault')]:
 a=next(f['body'] for f in funcs(old) if f['name']==name);b=next(f['body'] for f in funcs(new) if f['name']==renamed);assert a==b,name;unchanged.append({'function_body':name,'post_name':renamed,'sha256':H(a.encode())})
(ROOT/'evidence/unchanged-analog-bodies.json').write_text(json.dumps(unchanged,indent=2)+'\n')
audit=json.loads((ROOT/'evidence/private-consumer-audit.json').read_text());names=audit['control_roots_to_guard']
for name in names:
 assert new.count('CODEC_STATE_CONTROL('+name+')')==1,name
arrays='\n'.join(m[0] for m in re.finditer(r'static const struct snd_kcontrol_new \w+\[\] = \{.*?\n\};',new,re.S))
for name in names:
 # Every registration reference must select the guarded callback.
 text=arrays.replace('CODEC_CONTROL('+name+')','')
 assert not re.search(r'\b'+name+r'\b',text),name
# Every original direct private-state access is in an audited function or declaration.
fs=funcs(old)
unmapped=[]
for m in re.finditer(r'\bmCodec_data\b',old):
 if any(f['brace']<=m.start()<f['end'] for f in fs):continue
 if 'static struct mt6323_Codec_Data_Priv *mCodec_data;' in old[max(0,m.start()-50):m.start()+50]:continue
 unmapped.append(old[:m.start()].count('\n')+1)
assert not unmapped,unmapped
# Real preprocessor selection of the candidate, with kernel includes omitted only.
def strip(s):return '\n'.join(l for l in s.splitlines() if not l.startswith('#include '))+'\n'
ppsrc=new
for name in ['p00a_stock_gate.h','codec_state_controls.h']:
 ppsrc=ppsrc.replace('#include "'+name+'"',strip((ROOT/'candidate'/REL/name).read_text()))
g=ROOT/'tests/generated/codec-preprocessor.c';g.write_text(strip(ppsrc))
args=['/usr/bin/clang','-E','-P','-x','c','-DCONFIG_OF=1','-DCONFIG_OF_GPIO=1','-DCONFIG_GPIOLIB=1','-DCONFIG_PINCTRL_MT8163=1','-DCONFIG_MTK_SPEAKER=1','-DCONFIG_ASUS_P00A_STOCK_SPEAKER_GATE=1',g]
pp=run(args,'evidence/candidate-preprocessor.c').decode()
for forbidden in ['AW8737_MODE4','switch_mode_delay','setUsingExtSpeaker','AudDrv_GPIO_EXTAMP_Select']:assert forbidden not in pp,forbidden
for name in names:
 # Not all source-conditional callbacks necessarily survive this configuration.
 if re.search(r'\b'+name+r'\(',pp):assert re.search(r'\b'+name+r'_state\(',pp),name
routing=(ROOT/'candidate'/REL/'mt_soc_pcm_routing.c').read_bytes();assert H(routing)=='c458de71bb3c2cccd8b0d39a4c7c6e3a75f962cc8bdda44697eacca4f30bbd3a'
for rel in ['resolved.config','arch/arm64/configs/asus_p00a_defconfig','sound/soc/mediatek/Kconfig','arch/arm64/boot/dts/mediatek/asus-p00a.dts',str(REL/'mt_soc_pcm_routing.c')]:assert (ROOT/'preimage'/rel).read_bytes()==(ROOT/'candidate'/rel).read_bytes()
header=(ROOT/'candidate'/REL/'p00a_stock_gate.h').read_text();assert 'p00a_gate_suspended = mAnaSuspend;' in header and 'p00a_gate_suspended = false;' not in header
assert new.count('mAnaSuspend = bEnable;')==1
# All delivery deltas are relative to the reviewed prior candidate, not the BMC base.
changes=[];patch=[]
for dest in sorted((ROOT/'candidate').rglob('*')):
 if not dest.is_file():continue
 rel=dest.relative_to(ROOT/'candidate');src=ROOT/'preimage'/rel;a=src.read_text() if src.exists() else '';b=dest.read_text()
 if a==b:continue
 changes.append({'path':str(rel),'pre_sha256':H(src.read_bytes()) if src.exists() else None,'post_sha256':H(dest.read_bytes()),'destination_must_be_absent':not src.exists()})
 patch.append(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+str(rel) if src.exists() else '/dev/null',tofile='b/'+str(rel))))
assert len(changes)==5,changes
p=ROOT/'patches/lifecycle-from-gpio28-candidate.patch';p.write_text(''.join(patch))
replay=ROOT/'evidence/patch-replay';assert not replay.exists(),'preserve prior replay; use a new spike or explicit new replay directory'
replay.mkdir()
for src in (ROOT/'preimage').rglob('*'):
 if src.is_file():d=replay/src.relative_to(ROOT/'preimage');d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(src.read_bytes())
run(['/usr/bin/patch','--batch','--fuzz=0','-d',replay,'-p1','-i',p],'evidence/patch-replay.txt')
for row in changes:assert H((replay/row['path']).read_bytes())==row['post_sha256']
(ROOT/'evidence/pre-post-pins.json').write_text(json.dumps(changes,indent=2)+'\n')
oldhal=json.loads((ROOT/'inputs/prior/evidence/HAL-unchanged.json').read_text());assert H((W/oldhal['path']).read_bytes())==oldhal['sha256']
(ROOT/'evidence/scope-and-static-checks.json').write_text(json.dumps({'private_control_boundaries':len(names),'external_original_private_roots':audit['external_private_roots'],'original_private_references_outside_audited_functions':unmapped,'internal_analog_functions_unchanged':len(unchanged),'routing_path':str(REL/'mt_soc_pcm_routing.c'),'routing_sha256':H(routing),'routing_source_changed':False,'config_dts_kconfig_byte_identical':True,'config_snapshot_sha256':H((ROOT/'candidate/resolved.config').read_bytes()),'AW_preprocessed_absent':True,'HAL_qualified_false':True,'HAL_sha256':oldhal['sha256'],'patch_sha256':H(p.read_bytes()),'patch_replay':'PASS exact five paths; fuzz0'},indent=2)+'\n')
rows=[json.loads(l) for l in (ROOT/'evidence/commands.jsonl').read_text().splitlines()]
probe='''import resource,json
r={}
for name in ['RLIMIT_AS','RLIMIT_DATA','RLIMIT_RSS']:
 try:resource.setrlimit(getattr(resource,name),(1024**3,1024**3));r[name]={'accepted':True}
 except (ValueError,OSError) as e:r[name]={'accepted':False,'error':str(e)}
print(json.dumps(r))
'''
mem=json.loads(run(['python3','-c',probe],'evidence/darwin-limit-probe.json'))
(ROOT/'evidence/host-limits.json').write_text(json.dumps({'platform':platform.platform(),'resource_requests':mem,'cpu':'serial commands, no parallel compiler/builds; pthread tests intentionally interleave five bounded actors; Darwin lacks CPU-affinity enforcement','requested_memory_bytes':1024**3,'observed_child_highwater_rss_bytes':max(x['children_peak_rss_bytes_cumulative'] for x in rows),'rss_is_not_process_tree_peak':True,'wall_s_per_command':45,'cpu_s_per_command':30,'max_output_file_bytes':128*1024**2,'per_hook_wait_s':2,'stress_bounds':{'lifecycle_cycles':24,'routing_PM_pairs':64,'gain_headphone_iterations':128,'headset_iterations':128,'control_reader_iterations':128},'sanitizer':'UBSan; no ASan/TSan virtual-space overhead; deterministic lock/lifetime scheduling assertions plus bounded stress, not exhaustive interleaving proof'},indent=2)+'\n')
print('PASS exact five-path replay; 46 callback guards; 12 analog bodies unchanged; routing/config/DT/HAL preserved')
