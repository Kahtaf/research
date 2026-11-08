import remote,json
from pathlib import Path
s=r'''
from pathlib import Path
import sys,json,datetime,hashlib,gzip,re
sys.path.insert(0,'/srv/android/asus-reviewed-build-kit/r8/scripts')
import integrate
A=Path('/srv/android/lineage24');R=Path('/srv/android/asus-reviewed-build-kit/r8');N=Path('/srv/android/asus-reviewed-build-kit/r9')
plan=integrate.read(R/'inputs/plan.json')
r=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),r8_seal=integrate.verify_pins(R),actual_source_audit=integrate.verify_integrated(plan,baseline=True))
assert r['r8_seal']=='f55aedf8ac9d2a513e3663230db0b9d802e72b5df512fc0db6b3714331a7efa4'
def pin(p):return dict(sha256=integrate.sha(p),bytes=p.stat().st_size)
r['preservation']={str(p):pin(p) for p in (R/'attempt').rglob('*') if p.is_file()}
r['logs']={str(p):pin(p) for p in Path(plan['logs']).glob('full-build-r8.*') if p.is_file()}
assert r['logs'][plan['logs']+'/full-build-r8.log']['sha256']=='dde9978375f6e34e8b09676a2cb3245e866486ee254cf5405204b85893b37c38'
assert integrate.sha(R/'attempt/native-evidence/bootimage/siso_failed_commands.sh')=='f942dd841d60dd53582d6d0a8ab403b4095bb8000947d47cfd4bc94fc0b7bbe4'
# Bounded to product compiler modules and the 26 selected BPF graph output paths.
selected=integrate.read(plan['bpf_qualified_selection']);needles=['/bpfloader/','/vold/','/libvold/','/sensors.mt8163/','/android.hardware.sensors@1.0-impl/','/android.hardware.sensors@1.0-service/']
known={t for row in selected['objects'] for t in row['graph_output_chain'] if t.startswith('out/soong/.intermediates/')}
with (A/'out/.ninja_log').open() as f:
 targets={line.split('\t')[3] for line in f if len(line.split('\t'))==5 and (any(n in line.split('\t')[3] for n in needles) or line.split('\t')[3] in known)}
from verify_product_r3 import log_entries
from compiler_channel import commands_for
entries=log_entries(A/'out/.ninja_log',targets);cmds,receipts=commands_for(R,targets,entries)
r['cache_audit']=dict(selected_targets=len(targets),completed_current_join_outputs=len(cmds),native_receipts=receipts,outputs={t:dict(ninja=entries[t],commands=c,output_pin=pin(A/t) if (A/t).is_file() else None,depfile_exists=(A/(t+'.d')).exists()) for t,c in cmds.items()},precise_gate='No frozen per-output execution-time transitive input hashes, dependency database snapshot, graph rules/rsp expansions and toolchain closure receipt exists in r8 capture. Current-byte pins cannot retroactively prove execution-time inputs. Strict freshness remains unchanged; inherited admission must refuse until sound lineage is established.')
# Only WebView .gitattributes-controlled paths; read at most 256 bytes per candidate.
r['webview_pointers']=[]
for abi in ['arm','arm64','x86','x86_64']:
 p=A/f'external/chromium-webview/prebuilt/{abi}/webview.apk';data=p.open('rb').read(256)
 r['webview_pointers'].append(dict(path=str(p.relative_to(A)),selected=abi=='arm64',**pin(p),pointer=data.decode() if data.startswith(b'version https://git-lfs.github.com/spec/v1\n') else None,attributes=(p.parent/'.gitattributes').read_text()))
r['source_scope_pins']={str(p):pin(p) for p in [A/'.repo/manifest.xml',A/'.repo/manifests/default.xml',A/'.repo/manifests/snippets/lineage.xml',A/'.repo/projects/external/chromium-webview/prebuilt/arm64.git/HEAD',A/'.repo/projects/external/chromium-webview/prebuilt/arm64.git/config',A/'external/chromium-webview/Android.bp',A/'device/asus/p00a/connectivity/src/driver_cmd_p00a.c',A/'device/asus/p00a/sepolicy/vendor/file_contexts',A/'device/asus/p00a/prebuilt/Image.gz-dtb',Path(plan['defconfig']),A/'out/.ninja_log']}
r['physical_go']=False
with (N/'evidence/actual-audit.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
r=remote.run(s);Path('2026-11-06-asus-r9-webview-continuation/evidence/actual-audit.json').write_text(r);d=json.loads(r);print(json.dumps({k:v for k,v in d.items() if k not in ['preservation','logs','cache_audit','actual_source_audit']},indent=2));print(json.dumps({k:v for k,v in d['cache_audit'].items() if k!='outputs'},indent=2));print('actual source audit passed')
