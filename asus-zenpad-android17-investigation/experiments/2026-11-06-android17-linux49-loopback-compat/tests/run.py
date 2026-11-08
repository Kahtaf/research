#!/usr/bin/env python3
"""Compile unchanged production bodies with explicit host doubles. No kernel or Android execution."""
from pathlib import Path
import re,hashlib,json,subprocess,platform,resource,os
R=Path(__file__).resolve().parents[1];O=R/'artifacts/host';O.mkdir(parents=True,exist_ok=True)
C=R/'inputs/frozen/inputs/Connectivity/bpf/progs/netd.c';H=C.with_suffix('.h');c=C.read_text();h=H.read_text();records=[]
def fn(s,name,path):
 m=re.search(r'^(?:function|procedure|static inline) [^\n]*\b'+name+r'\(',s,re.M);assert m,name
 start=m.start();brace=s.index('{',m.end());depth=1;i=brace+1
 while depth:
  depth+=(s[i]=='{')-(s[i]=='}');i+=1
 body=s[start:i];records.append(dict(name=name,source=str(path.relative_to(R)),line=s.count('\n',0,start)+1,sha256=hashlib.sha256(body.encode()).hexdigest()));return body+'\n'
def typedef(name):
 m=re.search(r'^typedef struct \{(?:(?!^typedef struct \{).)*?^\} '+name+r';\nSTRUCT_SIZE\([^\n]+',h,re.M|re.S);assert m,name
 records.append(dict(name=name,source=str(H.relative_to(R)),line=h.count('\n',0,m.start())+1,sha256=hashlib.sha256(m[0].encode()).hexdigest()));return m[0]+'\n'
defs='\n'.join(x for x in h.splitlines() if re.match(r'#define (PERMISSION_(?:COUNT|BIT_\w+)|UIDS_PER_INT64|CHUNK_INT64_COUNT|CHUNK_UID_COUNT|UID_PERMISSION_MASK)\b',x))
base=defs+'\n'+'''typedef __UINT8_TYPE__ uint8_t;
typedef __UINT16_TYPE__ uint16_t;
typedef __UINT32_TYPE__ uint32_t;
typedef __UINT64_TYPE__ uint64_t;
typedef uint16_t __be16;
typedef uint32_t __be32;
#define STRUCT_SIZE(name,size) _Static_assert(sizeof(name)==(size), "size")
struct in6_addr { union { uint8_t s6_addr[16]; uint32_t s6_addr32[4]; }; };
'''
for name in ['LocalNetAccessKey','L4SStorage','LnpCache','LoopbackCache','SkStorageValue','UidPermissionChunk','SkbIpPacketData']:base+=typedef(name)
base+='''_Static_assert(__builtin_offsetof(SkStorageValue,uid)==12,"uid");
_Static_assert(__builtin_offsetof(SkStorageValue,loopback_cache)==96,"cache");
_Static_assert(__builtin_offsetof(LoopbackCache,result)==26,"result");
'''
(O/'abi.c').write_text(base)
code=base+'\n'+(R/'tests/doubles.h').read_text()+'\n'
code+=fn(h,'is_system_uid',H)
for name in ['get_chunk_permissions','loopback_metrics_enabled','loopback_checks_enabled','can_force_loopback','uids_have_loopback_permissions','should_block_loopback_access']:code+=fn(c,name,C)
code+='#define LOOPBACK_CACHE_EXPIRATION_NS (10ULL * 1000ULL * 1000ULL)\n'+fn(c,'should_block_loopback_access_cached',C)
code+=fn(c,'get_app_permissions',C)+fn(c,'inet_socket_create',C)
code+=(R/'tests/main.c').read_text();(O/'production_test.c').write_text(code)
def limit():
 resource.setrlimit(resource.RLIMIT_CPU,(30,30))
 # Darwin RLIMIT_AS is not a reliable physical-memory cap; this tiny native harness allocates <2MiB.
 if platform.system()!='Darwin':resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
log=[]
def run(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=45,preexec_fn=limit);log.append(dict(command=cmd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr));(R/'evidence/host-test-attempts.json').write_text(json.dumps(log,indent=2)+'\n');assert p.returncode==0,p.stderr;return p
version=run(['clang','--version']).stdout
run(['clang','-std=c2x','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined',str(O/'production_test.c'),'-o',str(O/'production_test')])
run([str(O/'production_test')])
run(['clang','-target','aarch64-linux-gnu','-std=c2x','-ffreestanding','-nostdinc','-Wall','-Wextra','-Werror','-c',str(O/'abi.c'),'-o',str(O/'abi-aarch64.o')])
result=dict(status='PASS: host policy contracts and ARM64 layout only',host=platform.platform(),compiler=version,limits={'cpu_seconds_per_child':30,'wall_seconds_per_child':45,'Darwin_memory':'RLIMIT_AS not enforced; no kernel/QEMU execution; static mocked state <2MiB','parallel_jobs':1},extractions=records,commands=log,boundaries=['Kernel socket lookup, verifier, RCU, refcounts, BTF and network namespaces are NOT executed.','Helper doubles expose production call contracts; they do not establish kernel compatibility.','ARM64 object compiles original selected struct bodies against freestanding scalar/address ABI; not a kernel translation unit.'])
(R/'evidence/host-tests.json').write_text(json.dumps(result,indent=2)+'\n');print(log[2]['stdout'].strip());print(result['status'])
