from pathlib import Path
import os,resource,re,json,subprocess as s,struct,hashlib
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
O=Path('/srv/android/asus-linux49-power-supply-filter-20261106');template=(O/'scripts/test_template.c').read_text();bodies=[]
for mode,name in [('preimage','original_body'),('postimage','candidate_body')]:
 src=(O/'source'/(mode+'.c')).read_text();src='\n'.join(l for l in src.splitlines() if not l.startswith('#include'));src=src.replace('(void*)BPF_FUNC_skb_load_bytes','mock_read').replace('skfilter_power_supply',name)
 if mode=='postimage':src=src.replace('static long (*bpf_skb_load_bytes)', 'static long (*candidate_read)').replace('bpf_skb_load_bytes(skb','candidate_read(skb')
 bodies.append(src)
(O/'source/oracle_test.c').write_text(template.replace('/*PRODUCTION_BODIES*/','\n'.join(bodies)))
commands=[]
for arch,compiler,extra in [('host','gcc',[]),('guest','aarch64-linux-gnu-gcc',['-static'])]:
 cmd=[compiler,*extra,'-O2','-Wall','-Wextra',str(O/'source/oracle_test.c'),'-o',str(O/'artifacts'/('test-'+arch))];p=s.run(cmd,capture_output=True,text=True);commands.append(dict(argv=cmd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr));assert p.returncode==0,p.stderr
p=s.run([str(O/'artifacts/test-host')],capture_output=True,text=True);(O/'evidence/host-oracle.log').write_text(p.stdout+p.stderr);commands.append(dict(argv=[str(O/'artifacts/test-host')],exit=p.returncode));assert p.returncode==0
baseline=Path('/srv/android/asus-final-bpf-runtime-20261106/capture/root/system/vendor/etc/bpf/filterPowerSupplyEvents.o');assert hashlib.sha256(baseline.read_bytes()).hexdigest()=='cc68c75c5046f450586fb6337d2b216dd22933e2b33357d54d5f37794e07cd1c'
for mode,p in [('baseline',baseline),('candidate',O/'artifacts/postimage.o')]:
 b=p.read_bytes();off=struct.unpack_from('<Q',b,40)[0];sz,num,idx=struct.unpack_from('<HHH',b,58);ss=[struct.unpack_from('<IIQQQQIIQQ',b,off+i*sz) for i in range(num)];strings=b[ss[idx][4]:ss[idx][4]+ss[idx][5]]
 for sec in ss:
  name=strings[sec[0]:].split(b'\0',1)[0]
  if name==b'skfilter/power_supply':(O/'artifacts'/(mode+'-insns')).write_bytes(b[sec[4]:sec[4]+sec[5]]);print(mode,'instructions',sec[5]//8);assert mode=='baseline' or sec[5]//8<=4096
(O/'evidence/test-build.json').write_text(json.dumps(commands,indent=2));print(p.stdout if hasattr(p,'stdout') else 'TEST_PREPARED')
