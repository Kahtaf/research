from pathlib import Path
import os,resource,json,hashlib,subprocess as s,shlex,gzip,difflib,struct
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
O=Path('/srv/android/asus-linux49-power-supply-filter-20261106');O.mkdir(exist_ok=False)
for x in ['source','evidence','snapshot','artifacts','scripts']:(O/x).mkdir()
A=Path('/srv/android/lineage24');rel='hardware/interfaces/health/utils/libhealthloop/filterPowerSupplyEvents.c';src=(A/rel).read_text();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(A/rel)=='371ca11052920914dffddccfc1c143f0a4ca253bb51fa3ecd5f2c2c9ebd2df2f'
with gzip.open('/srv/android/asus-reviewed-build-kit/r8/attempt/native-evidence/bootimage/verbose.log.gz','rt') as f:
 original=next(l.split('PWD=/proc/self/cwd ',1)[1].strip() for l in f if 'PWD=/proc/self/cwd ' in l and 'filterPowerSupplyEvents.c' in l and '--target=bpf' in l)
args=shlex.split(original);args[0]=str(A/args[0]);dep=O/'evidence/discovery.d';discover=list(args)
for opt,val in [('-MF',str(dep)),('-o',str(O/'artifacts/discovery.o'))]:discover[discover.index(opt)+1]=val
discover.remove('-c');discover.remove('-MD');discover.insert(1,'-M');p=s.run(discover,cwd=A,capture_output=True,text=True);(O/'evidence/dependency-discovery.json').write_text(json.dumps(dict(argv=discover,exit=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2));assert p.returncode==0
paths=shlex.split(dep.read_text().replace('\\\n',' '))[1:];pins={}
for name in paths:
 path=Path(name);path=path if path.is_absolute() else A/path
 dest=O/'snapshot'/path.relative_to(A);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes());pins[str(path.relative_to(A))]=dict(sha256=sha(path),bytes=path.stat().st_size)
(O/'source/preimage.c').write_text(src)
start=src.index('    // The first character');end=src.index('\n}\n',start)
body='''    // Length guards preserve helper-OOB acceptance before a complete prefix.
    // Three overlapping network-order words cover all eleven prefix bytes.
    uint32_t offset;
#define CHECK_PREFIX(i) do { \\
    if (skb->len < (i) + LENGTH_0SUBSYSTEM_EQUAL) return skb->len; \\
    if (load_word(skb, (i)) == 0x00535542 && \\
        load_word(skb, (i) + 4) == 0x53595354 && \\
        load_word(skb, (i) + 7) == 0x54454d3d) { \\
        offset = (i) + LENGTH_0SUBSYSTEM_EQUAL; goto found; \\
    } \\
} while (0)
'''+''.join('    '+' '.join(f'CHECK_PREFIX({i});' for i in range(j,min(j+4,256)))+'\n' for j in range(32,256,4))+'''#undef CHECK_PREFIX
    return skb->len;
found:;
    uint64_t buf[2] = {};
    if (bpf_skb_load_bytes(skb, offset, &buf, LENGTH_POWER_SUPPLY0)) return 0;
    uint64_t v = (buf[0] ^ HEX_POWER_SU) | (buf[1] ^ HEX_PPLY0);
    asm ("" : "+r" (v));
    if (v) return 0;
    return skb->len;'''
post=src[:start]+body+src[end:];post=post.replace('DEFINE_BPF_PROG("skfilter/power_supply"','unsigned long long load_word(const struct __sk_buff* skb, unsigned long long offset)\n    asm("llvm.bpf.load.word");\n\nDEFINE_BPF_PROG("skfilter/power_supply"');(O/'source/postimage.c').write_text(post);(O/'source/filter.patch').write_text(''.join(difflib.unified_diff(src.splitlines(True),post.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel)))
commands=[]
for mode in ['preimage','postimage']:
 (O/'snapshot'/rel).write_bytes((O/'source'/(mode+'.c')).read_bytes());cmd=list(args)
 for opt,val in [('-MF',str(O/'artifacts'/(mode+'.d'))),('-o',str(O/'artifacts'/(mode+'.unstripped.o')))]:cmd[cmd.index(opt)+1]=val
 p=s.run(cmd,cwd=O/'snapshot',capture_output=True,text=True);commands.append(dict(mode=mode,argv=cmd,cwd=str(O/'snapshot'),exit=p.returncode,stdout=p.stdout,stderr=p.stderr));(O/'evidence/compiler.json').write_text(json.dumps(commands,indent=2));assert p.returncode==0,p.stderr
 cmd=[str(A/'prebuilts/clang/host/linux-x86/clang-r584948b/bin/llvm-strip'),'-g',str(O/'artifacts'/(mode+'.unstripped.o')),'-o',str(O/'artifacts'/(mode+'.o'))];p=s.run(cmd,capture_output=True,text=True);commands.append(dict(argv=cmd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0
 for kind in ['objdump','readelf']:
  cmd=[str(A/('prebuilts/clang/host/linux-x86/clang-r584948b/bin/llvm-'+kind)),*(['-d'] if kind=='objdump' else ['-a']),str(O/'artifacts'/(mode+'.o'))];p=s.run(cmd,capture_output=True,text=True);(O/'evidence'/(mode+'-'+kind+'.txt')).write_text(p.stdout+p.stderr)
(O/'evidence/compiler.json').write_text(json.dumps(commands,indent=2));(O/'evidence/build-binding.json').write_text(json.dumps(dict(original_command=original,source_pre_sha256=sha(O/'source/preimage.c'),source_post_sha256=sha(O/'source/postimage.c'),dependencies=pins,toolchain={str(Path(args[0]).relative_to(A)):sha(Path(args[0])), 'llvm-strip':sha(A/'prebuilts/clang/host/linux-x86/clang-r584948b/bin/llvm-strip')},elfs={p.name:sha(p) for p in (O/'artifacts').glob('*.o')},snapshot_only_writes=True),indent=2));print('BUILD_COMPLETE',json.loads((O/'evidence/build-binding.json').read_text())['elfs'])
