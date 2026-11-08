"""Bounded startup regressions. Reuse the exact runner's resource/fixture helpers.
Its automatic main is omitted; copied production C/H is never altered.
"""
from pathlib import Path
import hashlib,json,shlex,sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
runner=(R/'scripts/run_tests.py').read_text()
marker='\ntry:\n    main()\nexcept BaseException as e:'
assert runner.count(marker)==1
scope={'__file__':str(R/'scripts/run_tests.py'),'__name__':'review_helpers'}
exec(compile(runner.split(marker)[0],str(R/'scripts/run_tests.py'),'exec'),scope)
globals().update({k:v for k,v in scope.items() if not k.startswith('__')})

def compile_adversarial(output,include,small=True,variant=None):
 cmd=compile_cmd(output,include,small=small,variant=variant)
 assert cmd[-1]==str(T/'integration.c')
 return cmd[:-1]+[str(T/'adversarial.c')]

def check(r,mode):
 t=r['trace'];pb=r['proof_bytes']
 assert r['parser']==0 and r['writer_opens']==0 and r['pwrites']==0,(mode,r)
 if mode.startswith('uncertain_'):
  assert r['daemon']==-1 and r['execs']==0 and r['identity_entries']==0 and r['copy_calls']==0 and pb==[[0,0],[0,0]],r
  return
 assert r['execs']==1 and pb[0]==[SYS,BOOT] and r['copy_calls']==3 and r['dup_calls']==3 and r['input_consumed']==12,r
 assert t.index('D:boot|')<t.index('D:copy:30|')<t.index('D:exec|'),r
 if mode=='normal':
  assert r['helper']==86 and r['p10_stops']==1 and pb[1]==[SYS,BOOT] and r['manifest_loads']==2 and r['self_maps']==1,r
  order=['H:manifest|','H:self|','H:self-map|','H:identity|','H:system|','H:boot|','H:STOP:p10-readonly|']
  assert [t.index(x) for x in order]==sorted(t.index(x) for x in order),r
  return
 assert r['p10_stops']==0,(mode,r)
 if mode.startswith(('h_peer','h_lock')):
  assert r['helper']==77 and r['manifest_loads']==1 and r['self_opens']==0 and pb[1]==[0,0],r
 elif mode.startswith(('x_manifest_','h_swap')):
  assert r['helper']==84 and r['self_opens']==0 and r['self_maps']==0 and pb[1]==[0,0],r
  assert r['manifest_loads']==(1 if mode.startswith('h_swap') else 2),r
 elif mode.startswith('h_self'):
  assert r['helper']==85 and r['self_opens']==1 and r['identity_entries']==1 and pb[1]==[0,0],r
  assert r['self_maps']==int(mode in ['h_self_mmap','h_self_close']),r
 else:
  assert r['helper']==85 and r['self_maps']==1 and r['manifest_loads']==2,r
  expected=[SYS,BOOT] if mode=='h_boot_head' else [SYS,0] if mode in ['h_system_head','h_boot_sys_size','h_boot_alias'] else [0,0]
  assert pb[1]==expected,(mode,expected,r)
  if expected[1]==0:assert 'H:proof:9:' not in t,r

def main():
 before=inventory();assert before==json.loads((R/'evidence/input-before.json').read_text())
 save(E/'input-before.json',before)
 original=R.parent/'2026-11-06-asus-final5role-shared-terminal-gate'
 for d in ['source','baseline','NONDEPLOYABLE/tests','NONDEPLOYABLE/include']:
  for p in (original/d).rglob('*'):
   if p.is_file():assert p.read_bytes()==(R/p.relative_to(original)).read_bytes(),p
 limits_probe()
 small,originals,disk=compact_fixture()
 binds=RUN/'bindings/small';binding(binds,small)
 bins=RUN/'bin';bins.mkdir()
 run(compile_adversarial(bins/'adversarial',binds),'compile-adversarial')
 save(E/'toolchain.json',dict(python=sys.version,python_executable=str(Path(sys.executable).resolve()),python_pin=pin(Path(sys.executable).resolve()),clang_version=run(['/usr/bin/clang','--version'],'clang-version'),clang_pin=pin(Path('/usr/bin/clang')),actual_clang_pin=pin(Path('/Library/Developer/CommandLineTools/usr/bin/clang')),linker_pin=pin(Path('/Library/Developer/CommandLineTools/usr/bin/ld'))))
 modes=['normal','uncertain_min','uncertain_max']
 modes += ['x_manifest_'+v for v in ['zero','two','four','six','magic','truncated','trailing','cid','system_full','system_table','boot_full','boot_table','install_full','install_table','data_full','data_table']]
 modes += ['h_'+v for v in ['peercred_error','peercred_short','peersec_error','peersec_zero','peersec_long','lock_family','lock_named','lock_name','lock_short','lock_long','swap_missing','swap_header','swap_partial','self_missing','self_fstat','self_uid','self_gid','self_mode','self_type','self_links','self_zero','self_oversize','self_mmap','self_close','system_head','boot_head','backup_gpt','system_mount','mount_malformed','system_sys_start','boot_sys_size','system_holder','boot_alias']]
 for mode in modes:
  root=RUN/'fixtures'/mode;fixture(root,small,True,originals,disk)
  if mode=='normal':put(root,'dev/block/mmcblk0p26',b'NONDEPLOYABLE used DATA, no pristine contents')
  r=case(bins/'adversarial','adversarial-'+mode,root,mode)
  check(r,mode)
 # Independent caller checks for first and last digest bytes, using deliberately
 # wrong synthetic test bindings. These are additional to full startup tests.
 for byte in [0,31]:
  wrong=bytearray(hashlib.sha256(small).digest());wrong[byte]^=1
  directory=RUN/'bindings'/('wrong-byte-'+str(byte));directory.mkdir()
  (directory/'terminal_manifest_binding.h').write_text('/* NONDEPLOYABLE INTENTIONALLY WRONG HOST FIXTURE */\nstatic const unsigned char terminal_manifest_sha[32]={'+','.join(str(x) for x in wrong)+'};\n')
  for variant,route in [('DAEMON_ONLY','daemon'),('HELPER_ONLY','helper')]:
   output=bins/('wrong-'+str(byte)+'-'+variant)
   run(compile_adversarial(output,directory,variant=variant),'compile-'+output.name)
   root=RUN/'fixtures'/output.name;fixture(root,small,True,originals,disk)
   r=case(output,output.name,root,route=route)
   assert r['parser']==0 and r['execs']==0 and r['self_opens']==0 and r['identity_entries']==0 and r['proof_bytes']==[[0,0],[0,0]] and r['p10_stops']==0,r
   if route=='helper':assert r['helper']==84,r
 dependencies={};products={}
 for output in bins.iterdir():
  if output.suffix=='.d':continue
  products[output.name]=pin(output)
  for name in shlex.split(Path(str(output)+'.d').read_text().replace('\\\n',' ').split(':',1)[1]):
   p=Path(name).resolve();dependencies[str(p)]=pin(p)
 save(E/'compiled-input-pins.json',dependencies)
 save(E/'native-product-pins.json',products)
 save(E/'test-input-pins.json',{str(p.relative_to(R)):pin(p) for p in [Path(__file__),R/'scripts/run_tests.py',R/'scripts/freeze.py',R/'scripts/extend_harness.py',T/'adversarial.c',T/'adversarial-platform.h']})
 assert inventory()==before
 save(E/'input-after.json',inventory())
 save(E/'summary.json',dict(passed=True,cases=len(ROWS),cross_boundary_cases=len(modes)-2,uncertainty_cases=2,first_last_digest_caller_cases=4,production_writable_opens=0,production_pwrites=0,source_unchanged=True,seconds=time.monotonic()-START,sampled_peak_rss_bytes=max(x['sampled_process_group_peak_rss_bytes'] for x in COMMANDS),children_highwater_rss_bytes=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,runner_highwater_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,bounds='Same sequential finite runner as replicated 114-case suite: CPU10s/child, wall20s/compile and5s/test, overall300s, thread env1, sampled RSS kill>1GiB. Darwin no hard affinity/memory cap.'))
 print('PASS',len(ROWS),'additional cases;',E.relative_to(R))

try:main()
except BaseException as e:
 save(E/'FAILED.json',dict(error=repr(e),cases_completed=len(ROWS),seconds=time.monotonic()-START))
 raise
