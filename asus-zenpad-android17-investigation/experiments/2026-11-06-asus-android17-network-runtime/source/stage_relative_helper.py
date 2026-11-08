from pathlib import Path
import difflib,json,hashlib
R=Path('/srv/android/asus-network-runtime');K=R/'kernel';changes={};out=R/'staged-relative';out.mkdir(exist_ok=True)
f='include/uapi/linux/bpf.h';old=(R/'staged-lpm'/f).read_text();idx=old.index('__BPF_FUNC_MAX_ID');print(old[idx-200:idx+80]);new=old[:idx]+'BPF_FUNC_skb_load_bytes_relative = 68,\n\t'+old[idx:]
# Published helper selector ABI, independent of command/map numbering.
new += '\n/* Header selectors for bpf_skb_load_bytes_relative(). */\nenum {\n\tBPF_HDR_START_MAC,\n\tBPF_HDR_START_NET,\n};\n' if False else ''
pos=new.rfind('#endif');new=new[:pos]+'/* Header selectors for bpf_skb_load_bytes_relative(). */\nenum {\n\tBPF_HDR_START_MAC,\n\tBPF_HDR_START_NET,\n};\n\n'+new[pos:];changes[f]=(old,new)
f='net/core/filter.c';old=(K/f).read_text();d=(R/'inputs/donor'/f).read_text();start=d.index('BPF_CALL_5(bpf_skb_load_bytes_relative');end=d.index('BPF_CALL_2(bpf_skb_pull_data',start);chunk=d[start:end].replace('ARG_PTR_TO_UNINIT_MEM','ARG_PTR_TO_RAW_STACK').replace('ARG_CONST_SIZE','ARG_CONST_STACK_SIZE');new=old.replace('BPF_CALL_2(bpf_skb_pull_data',chunk+'BPF_CALL_2(bpf_skb_pull_data',1)
# Only the skb program types route to this dispatcher.
start=new.index('sk_filter_func_proto(');pos=new.index('\tcase BPF_FUNC_skb_load_bytes:',start);new=new[:pos]+'\tcase BPF_FUNC_skb_load_bytes_relative:\n\t\treturn &bpf_skb_load_bytes_relative_proto;\n'+new[pos:];changes[f]=(old,new)
patch=''
for f,(old,new) in changes.items():
 p=out/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(new);patch+=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+f,tofile='b/'+f))
(R/'patches/03-skb-relative-load.patch').write_text(patch)
(R/'evidence/relative-helper-stage.json').write_text(json.dumps(dict(donor='a668db21f3cfddc5b73f081c6bb532b1b3351b36',scope='actual skb header relative loads; helper 68; old verifier stack argument types',patch_sha256=hashlib.sha256(patch.encode()).hexdigest()),indent=2)+'\n')
