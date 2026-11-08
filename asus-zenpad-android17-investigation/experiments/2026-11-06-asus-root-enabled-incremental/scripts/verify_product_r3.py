"""Real r8 compiler, link, installed ELF, sensor and BPF SYSTEM provenance.

Reads Ninja text/logs; never invokes a build engine. Qualified probe ELFs cannot
satisfy these gates. Completion remains host-only, with runtime checks pending.
"""
import datetime
import hashlib
import re
import struct
import subprocess
from pathlib import Path
from integrate import need, sha, read, safe

BINARIES = {
    'system/bin/bpfloader': ('system/bpf/loader/bpfloader/', ['system/bpf/loader/bpfloader.rs']),
    'system/bin/vold': ('system/vold/vold/', ['system/vold/model/PublicVolume.cpp']),
    'system/vendor/lib64/hw/sensors.mt8163.so': ('device/asus/p00a/sensors/sensors.mt8163/', ['device/asus/p00a/sensors/sensors.c', 'device/asus/p00a/sensors/accel_protocol.c']),
    'system/vendor/lib64/hw/ACCOUNT_REDACTED': ('hardware/interfaces/sensors/1.0/default/android.hardware.sensors@1.0-impl/', ['hardware/interfaces/sensors/1.0/default/Sensors.cpp']),
    'system/vendor/bin/hw/android.hardware.sensors@1.0-service': ('hardware/interfaces/sensors/1.0/default/android.hardware.sensors@1.0-service/', ['hardware/interfaces/sensors/1.0/default/service.cpp']),
}

def elf(path, machine=183):
    need(path.is_file() and not path.is_symlink(), 'Missing real ELF: ' + str(path))
    with path.open('rb') as f: data=f.read(64)
    need(len(data)==64 and data[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',data,18)[0]==machine,
         'Wrong ELF architecture: ' + str(path))
    return sha(path)

def image_hash(image, relative, debugfs):
    # stderr is small for debugfs cat; payload streams through SHA256.
    process=subprocess.Popen([str(debugfs),'-R','cat /'+relative,str(image)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    h=hashlib.sha256()
    for data in iter(lambda:process.stdout.read(1024*1024),b''):h.update(data)
    err=process.stderr.read().decode(errors='replace')
    need(process.wait()==0 and 'File not found' not in err,'SYSTEM file unreadable: '+relative+' '+err)
    return h.hexdigest()

def installed(product, relative, image, debugfs, expected=None):
    p=safe(product,relative)
    need(p.is_file() and not p.is_symlink(),'Missing installed payload: '+relative)
    digest=sha(p)
    need(expected is None or digest==expected,'Installed source bytes mismatch: '+relative)
    need(image_hash(image,relative,debugfs)==digest,'SYSTEM payload mismatch: '+relative)
    return {'path':relative,'bytes':p.stat().st_size,'sha256':digest,'system_bytes_verified':True}

def log_entries(path, targets):
    rows={}
    with path.open() as f:
        need(f.readline().strip()=='# ninja log v5','Unsupported actual Ninja log')
        for line in f:
            parts=line.rstrip('\n').split('\t')
            if len(parts)==5 and parts[3] in targets:
                rows[parts[3]]={'start_ms':int(parts[0]),'end_ms':int(parts[1]),'step_end_time_ns':int(parts[2]),'command_hash':parts[4]}
    return rows

def chain(edges, start):
    seen=set();queue=[start]
    while queue:
        node=queue.pop()
        if node in seen:continue
        seen.add(node)
        queue.extend(x for x in edges.get(node,{}).get('inputs',[]) if x in edges)
    return seen

def execution_record(aosp, target, entries, commands, start, fresh, source=None):
    # entries is an explicit controlled-incremental lineage Session. No current
    # Ninja-log membership or new timestamp is imposed on admitted prior outputs.
    return entries.record(target, source)

def verify(plan, root, raw, debugfs, readelf, apex):
    a=Path(plan['aosp']);p=Path(plan['product_out'])
    selected=read(plan['bpf_qualified_selection'])
    system_bpf={x['install_path']:x for x in selected['objects'] if x['install_path'].startswith('system/')}
    need(len(system_bpf)==12,'Qualified platform/vendor BPF selection changed')
    installable=set((p/'.installable_files').read_text().split())
    need(set(BINARIES)|set(system_bpf)<=installable,'Missing selected sensor/platform install targets')
    filelist=set((p/'obj/PACKAGING/system_intermediates/file_list.txt').read_text().split())
    required=set(BINARIES)|set(system_bpf)
    need(all(rel.removeprefix('system/') in filelist or rel in filelist for rel in required),'Final SYSTEM file list omits required payload')
    bpf_outputs={t for row in selected['objects'] for t in row['graph_output_chain'] if t.startswith('out/soong/.intermediates/')}
    from cache_lineage import Session
    from graph_context import selected_graph
    lineage=Session(root,plan)
    graph,provenance=selected_graph(a,lineage.catalog,lineage.rows)
    start=None;logs=lineage
    # All 38 explicit compiled-map rows and all 23 qualified baseline rows remain
    # mandatory, including outputs not revisited by the installed binary loops.
    admitted={target:lineage.record(target) for target in lineage.rows}
    commands={target:row['commands'] for target,row in admitted.items()}
    channel_receipts={'prior_r8':lineage.map['r8_phase_pins'],
                      'current_native_closure':lineage.final_closure()}
    full_log=Path(plan['selected_incremental_log'])
    toolchains={}
    for lines in commands.values():
        for command in lines:
            for name in re.findall(r'(prebuilts/[^\s\"\';|&]+/(?:clang\+\+|clang|rustc|ld\.lld))(?=[\s\"\';|&]|$)',command):
                tool=safe(a,name);need(tool.is_file(),'Missing actual compiler/linker tool: '+name);toolchains[name]=sha(tool)
    need(any(x.endswith('/rustc') for x in toolchains) and any(x.endswith(('/clang','/clang++')) for x in toolchains),'Actual compiler tool provenance missing')
    checked=[];compilers=[];links=[]
    for rel,(module,sources) in BINARIES.items():
        target='out/target/product/p00a/'+rel
        closure=chain(graph,target)
        need(target in graph,'No install graph edge: '+rel)
        intermediates=[t for t in closure if t.startswith('out/soong/.intermediates/') and module in t]
        need(intermediates,'No real Soong module ancestry: '+rel)
        payload=installed(p,rel,raw,debugfs);elf(p/rel)
        # At least one real Soong stripped output must be byte-identical to installed.
        matches=[t for t in intermediates if (a/t).is_file() and sha(a/t)==payload['sha256']]
        need(matches,'Installed ELF differs from Soong outputs: '+rel)
        unstripped=[t for t in intermediates if '/unstripped/' in t and Path(t).name==Path(rel).name]
        need(len(unstripped)==1,'Ambiguous/missing real linker output: '+rel)
        link=unstripped[0];elf(a/link)
        def build_id(path):
            result=subprocess.run([str(readelf),'-n',str(path)],capture_output=True,text=True)
            need(result.returncode==0,'ELF build-id inspection failed')
            ids=re.findall(r'Build ID:\s*([0-9a-f]+)',result.stdout)
            need(len(ids)==1,'Missing/ambiguous ELF build ID: '+str(path));return ids[0]
        need(build_id(a/link)==build_id(p/rel),'Stripped/linker build IDs disagree: '+rel)
        fresh=rel in ('system/bin/bpfloader','system/bin/vold','system/vendor/lib64/hw/sensors.mt8163.so')
        links.append(execution_record(a,link,logs,commands,start,fresh))
        for source in sources:
            candidates=[t for t in closure if source in graph[t]['inputs'] and t.startswith('out/soong/')]
            need(candidates,'No compiler dependency on reviewed source: '+source)
            evidence=[]
            for output in candidates:
                evidence.append(execution_record(a,output,logs,commands,start,fresh,source))
            compilers.append({'source':source,'sha256':sha(a/source),'outputs':evidence})
        payload['soong_byte_matches']=matches;checked.append(payload)
    forbidden={x['sha256'] for name,x in read(plan['bpf_supplement_manifest'])['files'].items() if name.startswith('elf/')}
    need(next(x for x in checked if x['path']=='system/bin/bpfloader')['sha256'] not in forbidden,'Qualified fixture ELF cannot ship as product bpfloader')
    for rel,row in system_bpf.items():
        elf(p/rel,247)
        payload=installed(p,rel,raw,debugfs)
        # Unchanged, qualified platform objects stay exact. Previously absent vendor
        # object is required now and must have a genuine graph-produced predecessor.
        if 'sha256' in row:need(payload['sha256']==row['sha256'],'Qualified BPF object changed; runtime requalification required: '+rel)
        outputs=[t for t in row['graph_output_chain'][1:] if t.startswith('out/soong/.intermediates/') and (a/t).is_file() and sha(a/t)==payload['sha256']]
        need(outputs,'BPF object has no real compiled output: '+rel)
        payload['compiler_execution']=[execution_record(a,t,logs,commands,start,'sha256' not in row) for t in outputs]
        payload['compiled_byte_matches']=outputs;checked.append(payload)
    apex_archives={}
    for row in selected['objects']:
        rel=row['install_path']
        if not rel.startswith('apex/'):continue
        module=Path(rel).parts[1]
        if module not in apex_archives:
            archives=[f for partition in ['system','system/product','system/system_ext','system/vendor'] for suffix in ['.apex','.capex'] if (f:=p/partition/'apex'/(module+suffix)).is_file()]
            need(len(archives)==1,'Ambiguous/missing final BPF APEX: '+module)
            archive=archives[0];apex_archives[module]=installed(p,str(archive.relative_to(p)),raw,debugfs)
        final=apex/rel.removeprefix('apex/')
        digest=elf(final,247)
        classified=next(x for x in lineage.matrix['rows'] if x['install_path']==rel)
        if classified['kind']=='QUALIFIED_BASELINE_ARTIFACT':
            need(digest==classified['qualified_sha256'],'Qualified APEX BPF changed; existing runtime requalification required: '+rel)
        outputs=[t for t in row['graph_output_chain'][1:] if t.startswith('out/soong/.intermediates/') and (a/t).is_file() and sha(a/t)==digest]
        need(outputs,'Extracted final APEX BPF differs from actual compiled output: '+rel)
        checked.append({'path':rel,'sha256':digest,'compiled_byte_matches':outputs,'compiler_execution':[execution_record(a,t,logs,commands,start,digest!=row.get('sha256')) for t in outputs],'container_system_bytes_verified':True,'matches_supplement_fixture':digest==row.get('sha256'),'runtime_verified':False})
    need(len([x for x in checked if '/etc/bpf/' in x['path']])==26,'Final selected BPF payload coverage incomplete')
    stage=Path(plan['staging'])/'product-device/sensors'
    checked.append(installed(p,'system/vendor/etc/init/init.p00a-accelerometer.rc',raw,debugfs,sha(stage/'init.p00a-accelerometer.rc')))
    checked.append(installed(p,'system/vendor/etc/init/ACCOUNT_REDACTED',raw,debugfs,sha(a/'hardware/interfaces/sensors/1.0/default/ACCOUNT_REDACTED')))
    checked.append(installed(p,'system/vendor/etc/permissions/android.hardware.sensor.accelerometer.xml',raw,debugfs,sha(a/'frameworks/native/data/etc/android.hardware.sensor.accelerometer.xml')))
    import xml.etree.ElementTree as ET
    manifest=p/'system/vendor/etc/vintf/manifest.xml'
    sensor=[h for h in ET.parse(manifest).getroot().findall('hal') if h.findtext('name')=='android.hardware.sensors']
    need(len(sensor)==1 and sensor[0].get('format')=='hidl' and sensor[0].findtext('transport')=='hwbinder','Wrong final sensor VINTF instance')
    need([f.text for f in sensor[0].findall('fqname')]==['@1.0::ISensors/default'] and not sensor[0].findall('version') and not sensor[0].findall('interface'),'Wrong sensor interface instance')
    checked.append(installed(p,'system/vendor/etc/vintf/manifest.xml',raw,debugfs))
    return {'payloads':checked,'apex_archives':apex_archives,'compiler_outputs':compilers,'link_outputs':links,'actual_build_graph':provenance,'build_log_sha256':sha(full_log),'toolchain_sha256':toolchains,'native_command_channel_receipts':channel_receipts,'admitted_native_outputs':admitted,'bpf_classification':lineage.matrix,'bpf_runtime_requalification_required':[x for x in lineage.matrix['rows'] if x['runtime_requalification_required']],'host_bpf_checks_scope':'ELF/compiler/graph/final-container bytes only; no kernel runtime acceptance','prior_r7_execution_accepted':[],'fixture_binary_installed':False,'sensor_runtime_verified':False,'platform_bpf_property_service_verified':False,'flash_ready':False}
