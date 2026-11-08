from pathlib import Path
import shutil,difflib
R=Path('/srv/android/asus-network-runtime');I=R/'inputs/Connectivity';S=R/'staged-network';shutil.copytree(I,S)
changes={}
f='bpf/progs/netd.c';old=(I/f).read_text();new=(R/'staged-core-progs/netd.c').read_text()
new=new.replace('// Newer local-network/loopback features require separately qualified helpers.','// This branch requires the relative-load helper and LPM trie backports.')
new=new.replace('KVER_4_9, API(T));\n}\n\n// ----- egress/stats', 'KVER_4_9, API(25Q2));\n}\n\n// ----- egress/stats')
marker='// Local legacy path: retain UID firewall, VPN ingress filtering and accounting.'
start=new.index(marker,new.index(marker)+len(marker));end=new.index('// WARNING:',start)
new=new[:start]+new[start:end].replace('KVER_4_9, API(T)', 'KVER_4_9, API(25Q2)')+new[end:]
new=new.replace('return KVER_IS_AT_LEAST(kver, 4, 19)\n        ? bpf_skb_load_bytes_relative', '// The opt-in 4.9 product carries helper 68 with the upstream semantics.\n    return (KVER_IS_AT_LEAST(kver, 4, 19) || !KVER_IS_AT_LEAST(kver, 4, 14))\n        ? bpf_skb_load_bytes_relative')
new=new.replace('if (!KVER_IS_AT_LEAST(kver, 4, 19)) return false;', 'if (KVER_IS_AT_LEAST(kver, 4, 14) && !KVER_IS_AT_LEAST(kver, 4, 19)) return false;')
changes[f]=(old,new)
f='bpf/loader/NetBpfLoad.cpp';old=(I/f).read_text();new=old.replace('gTolerateLoadFailures','gLegacyKernel')
a=new.index('    // Local: legacy (pre-4.11)');b=new.index('    if (type == BPF_MAP_TYPE_LPM_TRIE',a)
new=new[:a]+'    // The opt-in 4.9 product carries an actual LPM trie backport.\n    if (gLegacyKernel && type == BPF_MAP_TYPE_LPM_TRIE) return true;\n'+new[b:]
a=new.index('    if (type == BPF_MAP_TYPE_LPM_TRIE && !isAtLeastKernelVersion(4, 11))');b=new.index('    if (type == BPF_MAP_TYPE_LRU_HASH',a);new=new[:a]+new[b:]
new=new.replace('        // Local: LRU_HASH is 4.10+. HASH has the same userspace and bpf helper\n        // api, it just doesn\'t evict (inserts fail once full) - fine for the\n        // small cache maps that use it.', '        // These two caches only feed 5.10+ ring-buffer reporting/loopback\n        // programs, disabled on this legacy branch. Preserve their userspace\n        // handles; no active legacy policy relies on HASH eviction semantics.')
new=new.replace('loadObjectOrSkip', 'loadRequiredObject')
a=new.index('    if (loadObject(progPath, gLegacyKernel');b=new.index('\n}',a)
new=new[:a]+'    return loadObject(progPath, gLegacyKernel ? false : useLibbpf);'+new[b:]
changes[f]=(old,new)
f='bpf/netd/BpfHandler.cpp';old=(I/f).read_text();new=old
# Inspect and change the absent-program bypass separately after runtime proof.
for f,(old,new) in changes.items():
 (S/f).write_text(new)
(R/'patches/11-network-policy-and-required-loader.patch').write_text(''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+f,tofile='b/'+f)) for f,(a,b) in changes.items()))
