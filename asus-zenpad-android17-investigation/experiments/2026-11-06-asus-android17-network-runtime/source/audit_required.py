from pathlib import Path
import json,re,hashlib
R=Path('/srv/android/asus-network-runtime');C=R/'inputs/Connectivity';S=R/'staged-network'
java=C/'service/src/com/android/server/BpfNetMaps.java';const=C/'framework/src/android/net/BpfNetMapsConstants.java';handler=C/'bpf/netd/BpfHandler.cpp'
constants=dict(re.findall(r'public static final String (\w+_PATH)\s*=\s*"([^"]+)";',const.read_text()))
entries=[]
for name,path in constants.items():
 if name.endswith('MAP_PATH'):
  lines=[n for n,line in enumerate(java.read_text().splitlines(),1) if name in line and not line.startswith('import')]
  entries.append(dict(name=name,path=path,consumer='BpfNetMaps.java',lines=lines,requirement='map open mandatory when corresponding SDK37 initialization/feature branch executes'))
manifest=dict(java_maps=entries,bpfhandler_required_maps=re.findall(r'RETURN_IF_NOT_OK\(m\w+\.init\((\w+)\)\)',handler.read_text()),bpfhandler_required_programs=['XT_BPF_ALLOWLIST_PROG_PATH','XT_BPF_DENYLIST_PROG_PATH','XT_BPF_EGRESS_PROG_PATH','XT_BPF_INGRESS_PROG_PATH','BPF_EGRESS_PROG_PATH','BPF_INGRESS_PROG_PATH'],optional_legacy_absent=['ring-buffer event delivery, packet trace, local-network note-op event, cross-profile loopback metrics','5.10+ socket storage, sockopt hooks, socket release','4.14+ socket-create BPF hook (stock Android paranoid-network GID check remains; SDK37 permission migration not fully qualified)','offload/DSCP programs with genuine higher min_kver (maps remain)'],source_sha256={str(p.relative_to(C)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [java,const,handler,C/'service/src/com/android/server/ConnectivityService.java']},boundary='Static caller inventory. Runtime report associates these paths with real metadata/read/write opens; Java VM/framework not executed.')
(R/'evidence/required-consumer-inventory.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Java map paths',len(entries),'BpfHandler maps',len(manifest['bpfhandler_required_maps']))
