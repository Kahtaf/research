from pathlib import Path
import os,resource,json,subprocess as s,hashlib,difflib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
O=Path('/srv/android/asus-linux49-power-supply-filter-20261106');(O/'source/legacy-candidate.c').write_bytes((O/'source/postimage.c').read_bytes());(O/'artifacts/legacy-candidate.o').write_bytes((O/'artifacts/postimage.o').read_bytes());(O/'evidence/legacy-build-binding.json').write_bytes((O/'evidence/build-binding.json').read_bytes());(O/'evidence/legacy-compiler.json').write_bytes((O/'evidence/compiler.json').read_bytes())
src=(O/'source/preimage.c').read_text();start=src.index('    // The first character');end=src.index('\n}\n',start)
body='''    uint64_t buf[2] = {};
    uint32_t offset;
#define CHECK_PREFIX(i) do { \\
    if (bpf_skb_load_bytes(skb, (i), &buf, LENGTH_0SUBSYSTEM_EQUAL)) goto accept; \\
    uint64_t v = (buf[0] ^ HEX_0SUBSYST) | (buf[1] ^ HEX_EM_EQUAL); \\
    asm ("" : "+r" (v)); \\
    if (!v) { offset = (i) + LENGTH_0SUBSYSTEM_EQUAL; goto found; } \\
} while (0)
'''+''.join('    '+' '.join(f'CHECK_PREFIX({i});' for i in range(j,min(j+4,256)))+'\n' for j in range(32,256,4))+'''#undef CHECK_PREFIX
accept:
    return skb->len;
found:
    if (bpf_skb_load_bytes(skb, offset, &buf, LENGTH_POWER_SUPPLY0)) return 0;
    uint64_t v = (buf[0] ^ HEX_POWER_SU) | (buf[1] ^ HEX_PPLY0);
    asm ("" : "+r" (v));
    if (v) return 0;
    return skb->len;'''
post=src[:start]+body+src[end:];(O/'source/postimage.c').write_text(post);rel='hardware/interfaces/health/utils/libhealthloop/filterPowerSupplyEvents.c';(O/'snapshot'/rel).write_text(post);(O/'source/filter.patch').write_text(''.join(difflib.unified_diff(src.splitlines(True),post.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel)))
cmd=json.loads((O/'evidence/compiler.json').read_text())[2]['argv'];p=s.run(cmd,cwd=O/'snapshot',capture_output=True,text=True);(O/'evidence/shared-helper-compile.json').write_text(json.dumps(dict(argv=cmd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0,p.stderr
strip=json.loads((O/'evidence/compiler.json').read_text())[3]['argv'];p=s.run(strip,capture_output=True,text=True);assert p.returncode==0
print('SHARED_HELPER_BUILT',hashlib.sha256((O/'artifacts/postimage.o').read_bytes()).hexdigest())
