"""Sequential offline finite host tests. Every generated fixture stays NONDEPLOYABLE.

No source regeneration, network, target compiler, shell, packaging or device access.
Run once per retained evidence directory; failed invocations are preserved too.
"""
from pathlib import Path
import difflib, hashlib, json, os, platform, resource, shutil, signal
import struct, subprocess, sys, time
from freeze import inventory, pin

R = Path(__file__).resolve().parents[1]
N = R / 'NONDEPLOYABLE'
T = N / 'tests'
STAMP = time.strftime('%Y%m%d-%H%M%S')
E = R / 'evidence' / ('run-' + STAMP)
E.mkdir()
RUN = N / ('run-' + STAMP)
RUN.mkdir()
(RUN / 'tmp').mkdir()
START = time.monotonic()
GIB = 1024**3
COMMANDS = []
ENV = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
           VECLIB_MAXIMUM_THREADS='1', MKL_NUM_THREADS='1',
           LLVM_PARALLEL_LINK_JOBS='1', PYTHONDONTWRITEBYTECODE='1')
ENV.pop('CPATH', None)
ENV.pop('C_INCLUDE_PATH', None)
ENV.pop('LIBRARY_PATH', None)
ENV['TMPDIR'] = str(RUN / 'tmp')

def save(p, value):
    p.write_text(json.dumps(value, indent=2) + '\n')

def setup_limits():
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32*1024**2, 32*1024**2))
    # Darwin may reject all three: don't convert that into a fictitious hard cap.
    for name in ['RLIMIT_AS', 'RLIMIT_DATA', 'RLIMIT_RSS']:
        try:
            resource.setrlimit(getattr(resource, name), (GIB, GIB))
        except (OSError, ValueError):
            pass

def run(cmd, name, expect=0, wall=20):
    assert time.monotonic() - START < 300, 'overall 300 second test limit'
    # Sequential child groups only. ps sampling is an observation/kill backstop,
    # not a kernel memory controller and can miss transient peaks.
    stdout, stderr = E/(name+'.stdout'), E/(name+'.stderr')
    rss_peak = 0
    with stdout.open('wb') as out, stderr.open('wb') as err:
        t = time.monotonic()
        p = subprocess.Popen([str(x) for x in cmd], cwd=R, env=ENV,
                             stdout=out, stderr=err, start_new_session=True,
                             preexec_fn=setup_limits)
        try:
            while p.poll() is None:
                if time.monotonic()-t > wall or time.monotonic()-START > 300:
                    raise TimeoutError(name)
                ps = subprocess.run(['/bin/ps','-axo','pgid=,rss='],
                                    capture_output=True,text=True,timeout=2)
                rss = sum(int(s[1])*1024 for line in ps.stdout.splitlines()
                          if len(s := line.split()) == 2 and int(s[0]) == p.pid)
                rss_peak = max(rss_peak, rss)
                if rss > GIB:
                    raise MemoryError(name)
                time.sleep(.025)
        except BaseException:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
            raise
    row = dict(name=name,command=[str(x) for x in cmd],returncode=p.returncode,
               expected=expect,wall_seconds=time.monotonic()-t,
               sampled_process_group_peak_rss_bytes=rss_peak,
               cumulative_children_highwater_rss_bytes=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
               stdout=str(stdout.relative_to(R)),stderr=str(stderr.relative_to(R)))
    COMMANDS.append(row)
    save(E/'commands.json', COMMANDS)
    assert p.returncode == expect, (name,p.returncode,stderr.read_text()[-4000:])
    return stdout.read_text()

def limits_probe():
    code = '''import json,resource,os
r={}
for n in ['RLIMIT_CPU','RLIMIT_CORE','RLIMIT_FSIZE','RLIMIT_AS','RLIMIT_DATA','RLIMIT_RSS']:
 k=getattr(resource,n);before=resource.getrlimit(k)
 try:
  v=1073741824 if n in ['RLIMIT_AS','RLIMIT_DATA','RLIMIT_RSS'] else (10 if n=='RLIMIT_CPU' else (0 if n=='RLIMIT_CORE' else 33554432))
  resource.setrlimit(k,(v,v));r[n]={'before':before,'after':resource.getrlimit(k),'set':'accepted'}
 except (OSError,ValueError) as e:r[n]={'before':before,'error':str(e)}
r['sched_setaffinity_available']=hasattr(os,'sched_setaffinity')
print(json.dumps(r))'''
    save(E/'limits.json',json.loads(run([sys.executable,'-c',code],'limits')))

def binding(directory, m):
    directory.mkdir(parents=True,exist_ok=True)
    digest = hashlib.sha256(m).digest()
    p=directory/'terminal_manifest_binding.h'
    p.write_text('/* NONDEPLOYABLE SYNTHETIC HOST TEST ONLY. */\n'
                 'static const unsigned char terminal_manifest_sha[32]={' +
                 ','.join('0x%02x'%x for x in digest)+'};\n')
    return pin(p)

CHUNK=1048576
def record(role,part,size,full,chunks):
    assert len(full)==32 and len(chunks)==32*((size+CHUNK-1)//CHUNK)
    return struct.pack('<IIQ',role,part,size)+full+struct.pack('<I',len(chunks)//32)+chunks

def hash32(b):return hashlib.sha256(b).digest()
def change(m, at):
    b=bytearray(m);b[at]^=1;return bytes(b)

def full_fixture():
    m=(N/'original-stock.manifest').read_bytes()
    assert len(m)==115288 and hashlib.sha256(m).hexdigest()=='605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47'
    out=m[:12]+struct.pack('<I',5)+m[16:]
    for role,part,size in [(2,25,3753902080),(3,9,16740352),(4,26,11331268096)]:
        # Marked synthetic, nonzero unrelated hashes: NOT admitted install inputs.
        out+=record(role,part,size,hash32(('NONDEPLOYABLE whole role%d'%role).encode()),
                    b''.join(hash32(('NONDEPLOYABLE role%d chunk%d'%(role,j)).encode())
                             for j in range((size+CHUNK-1)//CHUNK)))
    assert len(out)==576340 and out[112:115288]==m[112:]
    assert out[:12]==m[:12] and out[16:112]==m[16:112]
    return m,out

def put(root,p,b):
    p=root/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)

CID=b'0123456789abcdef0123456789abcdef' # Explicit public synthetic identity.
SYS=3*CHUNK+512
BOOT=2*CHUNK+512
def raw(n,tag):return (bytes([tag])*CHUNK)*(n//CHUNK)+bytes([tag^0x55])*(n%CHUNK)
def compact_fixture():
    disk=raw(65536,0x44)
    header=b'ASUSR002'+struct.pack('<II',2,5)+hash32(CID)+hash32(disk[:17408])+hash32(disk[-16896:])
    originals={25:raw(SYS,0x31),9:raw(BOOT,0x42)}
    records=[]
    for role,part,n,tag in [(0,25,SYS,0x31),(1,9,BOOT,0x42),
                            (2,25,SYS,0x53),(3,9,BOOT,0x64),
                            (4,26,5*CHUNK+3584,0x75)]:
        b=originals.get(part) if role<2 else raw(n,tag)
        records.append(record(role,part,n,hash32(b),b''.join(hash32(b[i:i+CHUNK]) for i in range(0,n,CHUNK))))
    return header+b''.join(records),originals,disk

def fixture(root,m,small=False,originals=None,disk=None):
    root.mkdir(parents=True,exist_ok=True)
    for p,b in [('rescue.manifest',m),('proc/self/attr/current',b'u:r:os_rescue:s0\n'),
                ('sys/fs/selinux/enforce',b'1\n'),('proc/swaps',b'Filename\tType\tSize\tUsed\tPriority\n')]:put(root,p,b)
    if not small:return
    put(root,'sys/class/block/mmcblk0/device/cid',CID+b'\n')
    put(root,'proc/self/mountinfo',b'1 0 0:1 / / rw - tmpfs tmpfs rw\n')
    put(root,'dev/urandom',b'NONDEPLOYABLE_TOKEN_FIXTURE_BYTES!')
    put(root,'sbin/p10-restore',b'NONDEPLOYABLE host self fixture\n')
    put(root,'dev/block/mmcblk0',disk)
    put(root,'dev/block/mmcblk0p10',raw(8192,0x33))
    (root/'dev/rescue-state').mkdir(parents=True,exist_ok=True)
    for part,data in originals.items():put(root,'dev/block/mmcblk0p%d'%part,data)
    for part,name,start,n in [(0,None,0,65536),(9,'boot',127488,BOOT),
                               (10,'recovery',160184,8192),(25,'system',1072424,SYS)]:
        base='sys/dev/block/179:%d/'%part
        for field,value in [('dev','179:%d'%part),('size',str(n//512)),('start',str(start))]:put(root,base+field,(value+'\n').encode())
        (root/base/'holders').mkdir(parents=True,exist_ok=True)
        if name:
            a=root/'dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name'/name
            a.parent.mkdir(parents=True,exist_ok=True)
            a.symlink_to(root/('dev/block/mmcblk0p%d'%part))
    # No DATA device: successful terminal entry must not read pristine DATA or install roles.

def compile_cmd(output, include, small=False, missing=False, variant=None):
    cmd=['/usr/bin/clang','-std=c11','-O1','-Wall','-Wextra','-Werror',
         '-Wno-unused-function','-Wno-misleading-indentation',
         '-I'+str(N/'include'),'-I'+str(T)]
    if include:cmd+=['-I'+str(include)]
    if small:cmd+=['-DRESCUE_TEST']
    if variant:cmd+=['-D'+variant]
    if missing:cmd+=['-fsyntax-only']
    else:cmd+=['-MD','-MF',str(output)+'.d','-o',str(output)]
    return cmd+[str(T/'integration.c')]

ROWS=[]
def case(binary,name,root,mode='normal',route='daemon'):
    out=run([binary,root,mode,route],name,wall=5)
    r=json.loads(out)
    assert r['writer_opens']==0 and r['pwrites']==0,(name,r)
    assert 'UNEXPECTED' not in r['trace'],(name,r)
    r.update(case=name,route=route,mode=mode,fixture_manifest=pin(root/'rescue.manifest') if (root/'rescue.manifest').exists() else None)
    ROWS.append(r)
    save(E/'cases.json',ROWS)
    return r

def check_full(binary,m,two):
    # Record offsets from the actual immutable original prefix, not guessed table positions.
    offs=[];off=112
    for i in range(5):
        offs.append(off);off+=52+struct.unpack_from('<I',m,off+48)[0]*32
    assert off==len(m)
    def count(n,body):return m[:12]+struct.pack('<I',n)+m[16:112]+body
    variants={'fixture_five':(m,True,True),'frozen_two':(two,True,False),
              'zero':(count(0,b''),True,False),
              'four':(count(4,m[112:offs[4]]),True,False),
              'six':(count(6,m[112:]),False,False),
              'one':(count(1,m[112:offs[1]]),False,False),
              'three':(count(3,m[112:offs[3]]),False,False),
              'bad_magic':(change(m,0),False,False),
              'bad_version':(change(m,8),False,False),
              'short_header':(m[:111],False,False),
              'short_record':(m[:130],False,False),
              'short_chunks':(m[:-1],False,False),
              'oversized':(m+bytes(1048577-len(m)),False,False),
              'trailing':(m+b'x',False,False),
              'missing_data':(m[:offs[4]],False,False),
              'wrong_role':(change(m,offs[2]),False,False),
              'wrong_partition':(change(m,offs[2]+4),False,False),
              'wrong_size':(change(m,offs[2]+8),False,False),
              'wrong_chunks':(change(m,offs[2]+48),False,False),
              'wrong_original_boot':(change(m,offs[1]+16),False,False),
              'wrong_primary_gpt':(change(m,48),False,False),
              'wrong_backup_gpt':(change(m,80),False,False),
              'changed_cid':(change(m,16),True,False),
              'changed_original_system':(change(m,offs[0]+16),True,False),
              'changed_original_table':(change(m,offs[0]+52),True,False),
              'changed_install_full':(change(m,offs[2]+16),True,False),
              'changed_install_table':(change(m,offs[3]+52),True,False),
              'changed_data_full':(change(m,offs[4]+16),True,False),
              'changed_data_table':(change(m,offs[4]+52),True,False)}
    for name,(data,parses,admit) in variants.items():
        d=RUN/'fixtures'/('full-'+name);fixture(d,data)
        for route in ['daemon','helper']:
            r=case(binary,'full-'+name+'-'+route,d,route=route)
            assert (r['parser']==0)==parses,(name,r)
            assert r['execs']==0 and r['proof_bytes']==[[0,0],[0,0]],(name,r)
            if route=='helper':
                assert r['helper']==(85 if admit else 84) and r['self_opens']==int(admit),(name,r)
            else:
                assert r['daemon']==(-1 if parses else 84) and r['identity_entries']==int(admit),(name,r)
                # reset context changed by the independent helper invocation on the next loop not needed;
                # daemon identity doesn't use context_is and no fake domain transition is inferred.
            r['expected_parser_accept']=parses;r['expected_profile_accept']=admit

def check_small(binary,m,originals,disk):
    modes=['normal','uncertain0','uncertain4','uncertain_negative',
           'd_cid','d_gpt','d_backup_gpt','d_enforcing','d_system_head','d_system_tail',
           'd_boot_head','d_boot_tail','only_system_restored','installed_pair',
           'd_system_short','d_boot_io','h_system_tail','h_boot_tail','h_cid','h_gpt',
           'h_system_io','h_boot_short','h_profile','h_manifest_missing','h_swap',
           'h_uid','h_euid','h_context','h_enforcing','h_peeruid','h_peersec','h_lock',
           'copy1','copy2','copy3','dup1','dup2','dup3','exec_fail',
           'nonidle','wrong_opcode','nonempty']
    for mode in modes:
        d=RUN/'fixtures'/('small-'+mode);fixture(d,m,True,originals,disk)
        def corrupt(p,at):
            f=d/p;b=bytearray(f.read_bytes());b[at]^=1;f.write_bytes(b)
        for chosen,p,at in [('d_cid','sys/class/block/mmcblk0/device/cid',0),
                             ('d_gpt','dev/block/mmcblk0',0),('d_backup_gpt','dev/block/mmcblk0',-1),
                             ('d_system_head','dev/block/mmcblk0p25',0),('d_system_tail','dev/block/mmcblk0p25',-1),
                             ('d_boot_head','dev/block/mmcblk0p9',0),('d_boot_tail','dev/block/mmcblk0p9',-1)]:
            if mode==chosen:corrupt(p,at)
        if mode=='d_enforcing':put(d,'sys/fs/selinux/enforce',b'0\n')
        if mode in ['only_system_restored','installed_pair']:put(d,'dev/block/mmcblk0p9',raw(BOOT,0x64))
        if mode=='installed_pair':put(d,'dev/block/mmcblk0p25',raw(SYS,0x53))
        r=case(binary,'small-'+mode,d,mode)
        assert r['parser']==0,(mode,r)
        t=r['trace'];pb=r['proof_bytes']
        if mode=='normal':
            assert r['execs']==1 and r['helper']==86 and r['p10_stops']==1,(mode,r)
            assert pb==[[SYS,BOOT],[SYS,BOOT]],r
            order=['D:identity|','D:system|','D:boot|','D:copy:30|','D:exec|',
                   'H:swaps|','H:manifest|','H:self|','H:identity|','H:system|','H:boot|','H:STOP:p10-readonly|']
            indexes=[t.index(x) for x in order];assert indexes==sorted(indexes),r
            assert r['input_consumed']==12,r # no second queued handoff consumed
        elif mode.startswith('uncertain'):
            assert r['daemon']==-1 and r['execs']==0 and r['identity_entries']==0 and pb==[[0,0],[0,0]],r
        elif mode in ['d_cid','d_gpt','d_backup_gpt','d_enforcing']:
            assert r['daemon']==-1 and r['execs']==0 and 'D:system|' not in t and r['copy_calls']==0,r
        elif mode.startswith('d_') or mode in ['only_system_restored','installed_pair']:
            assert r['daemon']==-1 and r['execs']==0 and r['copy_calls']==0 and r['p10_stops']==0,r
            if mode in ['d_system_head','d_system_tail','installed_pair']:
                assert pb[0]==[SYS,0] and 'D:boot|' not in t,r
            if mode in ['d_boot_head','d_boot_tail','only_system_restored']:assert pb[0]==[SYS,BOOT],r
        elif mode.startswith('h_'):
            assert r['execs']==1 and pb[0]==[SYS,BOOT] and r['p10_stops']==0,r
            assert t.index('D:boot|')<t.index('D:exec|'),r
            if mode in ['h_uid','h_euid','h_context','h_enforcing','h_peeruid','h_peersec','h_lock']:
                assert r['helper']==77 and 'H:manifest|' not in t and pb[1]==[0,0],r
            elif mode in ['h_profile','h_manifest_missing','h_swap']:
                assert r['helper']==84 and 'H:self|' not in t and pb[1]==[0,0],r
            else:
                assert r['helper']==85,r
                if mode in ['h_cid','h_gpt']:assert pb[1]==[0,0],r
                if mode=='h_system_tail':assert pb[1]==[SYS,0] and 'H:boot|' not in t,r
                if mode=='h_boot_tail':assert pb[1]==[SYS,BOOT],r
        elif mode.startswith('copy'):
            n=int(mode[-1]);assert r['daemon']==-1 and r['copy_calls']==n and r['dup_calls']==0 and r['execs']==0,r
            assert t.count('close-copy:')==n-1,r
        elif mode.startswith('dup'):
            assert r['exit']==74 and r['dup_calls']==int(mode[-1]) and r['execs']==0,r
        elif mode=='exec_fail':assert r['exit']==74 and r['execs']==1 and r['helper']==-999,r
        else:
            assert mode in ['nonidle','wrong_opcode','nonempty']
            assert r['daemon']==-1 and r['execs']==0 and r['copy_calls']==0,r
            if mode=='nonidle':assert 'recovery-readonly' in t and pb[0]==[SYS,0],r
        if mode not in ['normal','nonidle'] and not mode.startswith('h_') and mode not in ['exec_fail']:
            assert r['p10_stops']==0,r

def check_separate(bins,full,two,small,originals,disk):
    for geometry in ['full','small']:
        base=full if geometry=='full' else small
        variants={'exact':base,'changed_digest':change(base,-1),'malformed_trailing':base+b'x'}
        if geometry=='full':variants['frozen_two']=two
        for name,m in variants.items():
            d=RUN/'fixtures'/('separate-'+geometry+'-'+name)
            fixture(d,m,geometry=='small',originals,disk)
            for variant,route in [('DAEMON_ONLY','daemon'),('HELPER_ONLY','helper')]:
                r=case(bins/(geometry+'-'+variant),'separate-'+geometry+'-'+name+'-'+route,d,route=route)
                assert (r['parser']==0)==(name!='malformed_trailing'),r
                if name=='exact':
                    if route=='daemon':
                        assert r['execs']==(geometry=='small'),r
                        if geometry=='small':assert r['proof_bytes'][0]==[SYS,BOOT],r
                        else:assert r['identity_entries']==1,r
                    else:
                        assert r['helper']==(86 if geometry=='small' else 85),r
                        if geometry=='small':assert r['proof_bytes'][1]==[SYS,BOOT],r
                        assert r['self_opens']==1,r
                else:
                    assert r['execs']==0 and r['self_opens']==0 and r['identity_entries']==0,r
                    assert r['proof_bytes']==[[0,0],[0,0]],r
                    if route=='helper':assert r['helper']==84,r

def patch_and_pins():
    assert not (R/'source/terminal_manifest_binding.h').exists()
    paths=sorted(p.name for p in (R/'source').iterdir())
    changes=[];chunks=[];rows={}
    for name in paths:
        post=R/'source'/name;pre=R/'baseline'/name
        rows[name]=dict(pre=pin(pre) if pre.exists() else None,post=pin(post))
        if not pre.exists() or pre.read_bytes()!=post.read_bytes():
            changes.append(name)
    assert changes==['handoff.h','p10_restore.c','terminal_profile.h'],changes
    # Reproduce the proposed patch byte-for-byte, including its order/context.
    patch=(R/'inputs/design/terminal-profile.patch.txt').read_bytes()
    (R/'terminal-profile.patch').write_bytes(patch)
    # Validate every hunk by applying the preserved proposal with a small exact
    # unified-diff reader to in-memory preimages (no external source mutation).
    import re
    files={p.name:p.read_text() for p in (R/'baseline').iterdir()}
    lines=patch.decode().splitlines(keepends=True);i=0
    while i<len(lines):
        assert lines[i].startswith('--- ');old=lines[i][4:].strip();new=lines[i+1][4:].strip();i+=2
        name=new.split('/')[-1];source=[] if old=='/dev/null' else files[name].splitlines(keepends=True)
        dest=[];pos=0
        while i<len(lines) and lines[i].startswith('@@'):
            h=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',lines[i]);assert h
            at=int(h[1]);at=0 if at==0 else at-1
            dest+=source[pos:at];pos=at;i+=1
            while i<len(lines) and not lines[i].startswith(('@@','--- ')):
                s=lines[i];assert s[0] in ' +-'
                if s[0] in ' -':assert source[pos]==s[1:],(name,pos);pos+=1
                if s[0] in ' +':dest.append(s[1:])
                i+=1
        dest+=source[pos:];assert ''.join(dest)==(R/'source'/name).read_text(),name
    save(E/'source-prepost.json',rows)

def main():
    before=json.loads((R/'evidence/input-before.json').read_text())
    assert inventory()==before,'original input changed before tests'
    patch_and_pins();limits_probe()
    test_inputs = [Path(__file__), R/'scripts/freeze.py', T/'integration.c',T/'platform.h',
                   N/'include/sys/sysmacros.h',N/'include/linux/fs.h']
    save(E/'test-input-pins.json',{str(p.relative_to(R)):pin(p) for p in test_inputs})
    tool={'uname':platform.uname()._asdict(),'python':sys.version,'python_executable':str(Path(sys.executable).resolve()),
          'python_pin':pin(Path(sys.executable).resolve()),'clang_pin':pin(Path('/usr/bin/clang').resolve()),
          'clang_version':run(['/usr/bin/clang','--version'],'clang-version'),
          'clang_search':run(['/usr/bin/clang','-print-search-dirs'],'clang-search'),
          'actual_clang_pin':pin(Path('/Library/Developer/CommandLineTools/usr/bin/clang')),
          'linker_pin':pin(Path('/Library/Developer/CommandLineTools/usr/bin/ld')),
          'scope':'native host Mach-O only; no Android/ELF target output',
          'environment_threads':{k:ENV[k] for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS','LLVM_PARALLEL_LINK_JOBS']}}
    save(E/'toolchain.json',tool)
    bins=RUN/'bin';bins.mkdir()
    for variant in ['DAEMON_ONLY','HELPER_ONLY']:
        name='missing-production-binding-'+variant
        run(compile_cmd(None,None,missing=True,variant=variant),name,expect=1)
        assert "'terminal_manifest_binding.h' file not found" in (E/(name+'.stderr')).read_text()
    two,full=full_fixture();small,originals,disk=compact_fixture()
    binds={}
    for name,m in [('full',full),('small',small)]:
        directory=RUN/'bindings'/name;binds[name]=dict(manifest_sha256=hashlib.sha256(m).hexdigest(),header=binding(directory,m))
        run(compile_cmd(bins/name,directory,small=name=='small'),'compile-'+name)
        for variant in ['DAEMON_ONLY','HELPER_ONLY']:
            run(compile_cmd(bins/(name+'-'+variant),directory,small=name=='small',variant=variant),
                'compile-'+name+'-'+variant)
    save(E/'fixture-bindings.json',binds)
    # Record native build products and every compiler-listed source/header,
    # including the SDK and the one test binding shared by both separate builds.
    import shlex
    products={};dependencies={}
    for output in sorted(bins.iterdir()):
        if output.suffix=='.d':continue
        products[output.name]=pin(output)
        deptext=Path(str(output)+'.d').read_text().replace('\\\n',' ')
        for name in shlex.split(deptext.split(':',1)[1]):
            p=Path(name).resolve();dependencies[str(p)]=pin(p)
    save(E/'native-product-pins.json',products)
    save(E/'compiled-input-pins.json',dependencies)
    run(compile_cmd(bins/'unused',RUN/'bindings/full',variant='DAEMON_ONLY')[:-1]+['-###',str(T/'integration.c')],
        'clang-driver-trace')
    check_full(bins/'full',full,two)
    check_small(bins/'small',small,originals,disk)
    check_separate(bins,full,two,small,originals,disk)
    # Rehash exact external inputs; never mutate or execute any of their scripts/binaries.
    after=inventory();assert after==before
    save(E/'input-after.json',after)
    save(E/'cases.json',ROWS)
    save(E/'summary.json',dict(passed=True,cases=len(ROWS),
          full_geometry_cases=sum(x['case'].startswith('full-') for x in ROWS),
          small_geometry_cases=sum(x['case'].startswith('small-') for x in ROWS),
          separate_build_cases=sum(x['case'].startswith('separate-') for x in ROWS),
          missing_header_compile_refused=True,original_inputs_unchanged=True,
          seconds=time.monotonic()-START,
          sampled_peak_rss_bytes=max(x['sampled_process_group_peak_rss_bytes'] for x in COMMANDS),
          children_highwater_rss_bytes=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
          runner_highwater_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          bound_scope='serial child groups, one compiler/test at a time, thread env 1, CPU 10s/process, wall <=20s/command (tests 5s), overall 300s, sampled group RSS kill >1GiB; Darwin hard affinity/memory NOT claimed',
          acceptance='software gate only under NONDEPLOYABLE fixture bindings'))
    print('PASS',len(ROWS),'cases;',E.relative_to(R))

try:
    main()
except BaseException as e:
    save(E/'FAILED.json',dict(error=repr(e),cases_completed=len(ROWS),seconds=time.monotonic()-START))
    raise
