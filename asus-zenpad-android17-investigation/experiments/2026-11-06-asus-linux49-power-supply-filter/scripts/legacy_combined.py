from pathlib import Path
import os,resource,json,subprocess as s,hashlib,difflib,re
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
O=Path('/srv/android/asus-linux49-power-supply-filter-20261106')
for a,b in [('source/postimage.c','source/shared-helper-candidate.c'),('artifacts/postimage.o','artifacts/shared-helper-candidate.o')]: (O/b).write_bytes((O/a).read_bytes())
src=(O/'source/legacy-candidate.c').read_text();src=src.replace('''    if (load_word(skb, (i)) == 0x00535542 && \\
        load_word(skb, (i) + 4) == 0x53595354 && \\
        load_word(skb, (i) + 7) == 0x54454d3d) { \\''','''    uint64_t v = (load_word(skb, (i)) ^ 0x00535542) | \\
                 (load_word(skb, (i) + 4) ^ 0x53595354) | \\
                 (load_word(skb, (i) + 7) ^ 0x54454d3d); \\
    asm ("" : "+r" (v)); \\
    if (!v) { \\''')
src=re.sub(r'static long \(\*bpf_skb_load_bytes\).*?\(void\*\)BPF_FUNC_skb_load_bytes;\n','',src,flags=re.S)
a=src.index('found:;');b=src.index('\n}\n',a);src=src[:a]+'''found:
    if (skb->len < offset + LENGTH_POWER_SUPPLY0) return 0;
    uint64_t v = (load_word(skb, offset) ^ 0x706f7765) |
                 (load_word(skb, offset + 4) ^ 0x725f7375) |
                 (load_word(skb, offset + 8) ^ 0x70706c79) |
                 load_byte(skb, offset + 12);
    asm ("" : "+r" (v));
    if (v) return 0;
    return skb->len;'''+src[b:]
(O/'source/postimage.c').write_text(src);rel='hardware/interfaces/health/utils/libhealthloop/filterPowerSupplyEvents.c';(O/'snapshot'/rel).write_text(src);pre=(O/'source/preimage.c').read_text();(O/'source/filter.patch').write_text(''.join(difflib.unified_diff(pre.splitlines(True),src.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel)))
cmd=json.loads((O/'evidence/compiler.json').read_text())[2]['argv'];p=s.run(cmd,cwd=O/'snapshot',capture_output=True,text=True);(O/'evidence/legacy-combined-compile.json').write_text(json.dumps(dict(argv=cmd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0,p.stderr
cmd=json.loads((O/'evidence/compiler.json').read_text())[3]['argv'];p=s.run(cmd,capture_output=True,text=True);assert p.returncode==0;print('BUILT',hashlib.sha256((O/'artifacts/postimage.o').read_bytes()).hexdigest())
