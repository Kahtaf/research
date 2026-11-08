"""Owned observer generation and bounded execution; no arbitrary commands from receipts."""
from pathlib import Path
import gzip
import hashlib
import json
import os
import re
import resource
import signal
import stat
import subprocess
from admission import CONFIG_SHA, KERNEL_SHA, GENUINE, NEW_REMOTE, identity, ordinary, need, sha
from check_system_header import inspect

ROOT = Path(NEW_REMOTE)
TOOLS = ROOT/'immutable'
SOURCES = Path(__file__).resolve().parents[1]/'source'


def bounded():
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    signal.alarm(90)


def check_owned_output(path):
    path = Path(path)
    need(path.is_absolute() and path.is_relative_to(ROOT/'runs') and '..' not in path.parts,
         'Output must be a fresh directory inside the owned runs prefix')
    need(not path.exists(), 'Preserve existing run/output')
    # Reject symlinked ancestors, including a symlink resolving outside the prefix.
    need(path.parent.resolve().is_relative_to(ROOT.resolve()), 'Output ancestor escapes owned prefix')
    return path


def pinned_runtime():
    pins = json.loads((ROOT/'immutable-pins.json').read_text())
    for row in pins:
        p = TOOLS/row['relative']
        need(p.is_file() and sha(p.read_bytes()) == row['sha256'], 'Frozen tool/source drift: '+str(p))
    need(sha((TOOLS/'Image').read_bytes()) == KERNEL_SHA and
         sha((TOOLS/'sources/.config').read_bytes()) == CONFIG_SHA, 'Kernel/config pin mismatch')
    return sha((ROOT/'immutable-pins.json').read_bytes())


def headers_and_identity(admitted):
    for path, expected in [(admitted.raw_path, admitted.raw_identity), (admitted.system_path, admitted.system_identity)]:
        fd, st = ordinary(path)
        os.close(fd)
        need(identity(st) == expected, 'Admitted image identity changed: '+path)
    raw = inspect(admitted.raw_path, admitted.raw_identity['bytes'])
    original = inspect(admitted.system_path, admitted.raw_identity['bytes'])
    need(raw['format'] == 'raw' and raw['file_bytes'] == admitted.raw_identity['bytes'] and
         raw['superblock_sha256'] == original['superblock_sha256'] and
         raw['filesystem_bytes'] == original['filesystem_bytes'], 'Original/raw header mismatch')
    return raw, original


def cbytes(value):
    return '{'+','.join(str(n) for n in value)+'}'


def header_text(admitted, header):
    lines = ['/* Generated only after complete admission; no default expectation data. */',
             '#define INPUT_SCOPE '+json.dumps(admitted.scope),
             '#define ADMISSION_SHA256 '+json.dumps(admitted.admission_sha256),
             '#define EXPECTATIONS_SHA256 '+json.dumps(admitted.expectations_sha256),
             '#define EXPECTED_RAW_BYTES '+str(admitted.raw_identity['bytes'])+'ULL',
             '#define EXPECTED_FILESYSTEM_BYTES '+str(header['filesystem_bytes'])+'ULL',
             'static const unsigned char expected_superblock_sha256[32]='+cbytes(bytes.fromhex(header['superblock_sha256']))+';',
             'static const struct expected_file expected_files[4]={']
    for row in admitted.files:
        label = bytes.fromhex(row['selinux_hex'])
        cap = bytes.fromhex(row['capability_hex']) if row['capability_hex'] is not None else b''
        lines.append('{'+','.join([str(row['bytes'])+'ULL', str(row['uid'])+'U', str(row['gid'])+'U',
                                  str(row['mode'])+'U', cbytes(bytes.fromhex(row['sha256'])),
                                  str(len(label)), cbytes(label), str(len(cap) if cap else -1),
                                  cbytes(cap or b'\0')])+'},')
    return '\n'.join(lines+['};',''])


def command(cmd, log, env):
    with log.open('x') as out:
        out.write(json.dumps(cmd)+'\n');out.flush()
        try:
            code = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
                                  timeout=90, preexec_fn=bounded, env=env).returncode
            return dict(exit=code, timed_out=False)
        except subprocess.TimeoutExpired:
            return dict(exit=None, timed_out=True)


def environment(output):
    env = os.environ.copy()
    env.update(LD_LIBRARY_PATH=str(TOOLS/'lib64'), TMPDIR=str(output/'tmp'),
               LC_ALL='C', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    return env


def pack_init(init, output):
    with gzip.GzipFile(filename=str(output), mode='wb', compresslevel=1, mtime=0) as stream:
        offset = 0
        def entry(name, mode, data=b'', major=0, minor=0):
            nonlocal offset
            n = name.encode()+b'\0';fields=[1,mode,0,0,1,0,len(data),0,0,major,minor,len(n),0]
            h=b'070701'+''.join(f'{v:08x}'for v in fields).encode()+n
            for b in (h, bytes(-(offset+len(h))%4)):
                stream.write(b);offset+=len(b)
            stream.write(data);offset+=len(data);pad=bytes(-offset%4);stream.write(pad);offset+=len(pad)
        for name in ('dev','proc','sys','mnt'):entry(name, stat.S_IFDIR|0o755)
        entry('dev/console',stat.S_IFCHR|0o600,major=5,minor=1)
        entry('init',stat.S_IFREG|0o755,init.read_bytes());entry('TRAILER!!!',0)


def generate(admitted, output):
    output = check_owned_output(output)
    tool_manifest = pinned_runtime()
    raw, original = headers_and_identity(admitted)
    output.mkdir(parents=True);(output/'tmp').mkdir()
    (output/'expectations.h').write_text(header_text(admitted, raw))
    for name in ('observer.c','sha256.h'):(output/name).write_bytes((SOURCES/name).read_bytes())
    tc=TOOLS/'toolchain'
    compiler=[str(TOOLS/'bin/aarch64-linux-gnu-gcc'), '-B'+str(TOOLS/'compiler-bin')+'/',
              '-nostdinc','-isystem',str(tc/'gcc-include'),'-isystem',str(tc/'include'),
              '-static','-nostdlib','-fno-use-linker-plugin','-O2','-Wall','-Wextra','-Werror',
              '-MD','-MF',str(output/'headers.d'), str(tc/'lib/crt1.o'),str(tc/'lib/crti.o'),
              str(tc/'gcc/crtbeginT.o'),str(output/'observer.c'),'-Wl,--start-group',
              str(tc/'gcc/libgcc.a'),str(tc/'gcc/libgcc_eh.a'),str(tc/'lib/libc.a'),
              '-Wl,--end-group',str(tc/'gcc/crtend.o'),str(tc/'lib/crtn.o'),'-o',str(output/'init')]
    result=command(compiler, output/'compile.log', environment(output))
    need(result == dict(exit=0,timed_out=False), 'Observer compile failed; preserve compile.log')
    pack_init(output/'init',output/'observer.cpio.gz')
    receipt=dict(scope=admitted.scope,build_id=admitted.build_id,admission_sha256=admitted.admission_sha256,
                 expectations_sha256=admitted.expectations_sha256,tool_manifest_sha256=tool_manifest,
                 owner_raw_sha256=admitted.raw_sha256,owner_system_sha256=admitted.system_sha256,
                 owner_whole_images_rehashed=False,headers=dict(raw=raw,original=original),compiler=result,
                 generated={n:sha((output/n).read_bytes())for n in ('observer.c','sha256.h','expectations.h','init','observer.cpio.gz')})
    (output/'generation.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def qemu_argv(admitted, output):
    return [str(TOOLS/'bin/qemu-system-aarch64'),'-machine','virt,gic-version=3', '-cpu','cortex-a53',
            '-accel','tcg,thread=single,tb-size=16','-smp','1','-m','384','-nographic','-monitor','none',
            '-no-reboot','-nic','none','-kernel',str(TOOLS/'Image'),'-initrd',str(output/'observer.cpio.gz'),
            '-blockdev',json.dumps({'driver':'file','filename':admitted.raw_path,'node-name':'system-file','read-only':True}),
            '-blockdev',json.dumps({'driver':'raw','file':'system-file','node-name':'system-raw','read-only':True}),
            '-device','virtio-blk-device,drive=system-raw',
            '-append','console=ttyAMA0 rdinit=/init panic=-1 loglevel=7 selinux=0']


def execute(admitted, output):
    output=Path(output);generation=json.loads((output/'generation.json').read_text())
    need(generation['scope']==admitted.scope and generation['admission_sha256']==admitted.admission_sha256 and
         generation['expectations_sha256']==admitted.expectations_sha256,'Generation/admission mismatch')
    for n,pin in generation['generated'].items():need(sha((output/n).read_bytes())==pin,'Generated observer drift')
    pinned_runtime();headers_and_identity(admitted)
    before={p:identity(os.stat(p,follow_symlinks=False))for p in (admitted.raw_path,admitted.system_path)}
    cmd=qemu_argv(admitted,output);terminal=command(cmd,output/'serial.log',environment(output))
    serial=(output/'serial.log').read_text(errors='replace')
    results=re.findall(r'^FULL_SYSTEM_FS_RESULT failures=([0-9]+) scope=([A-Z_]+)\r?$',serial,re.M)
    exits=re.findall(r'^FULL_SYSTEM_FS_EXIT status=([0-9]+) scope=([A-Z_]+)\r?$',serial,re.M)
    after={p:identity(os.stat(p,follow_symlinks=False))for p in (admitted.raw_path,admitted.system_path)}
    # There is no negative kernel error in a full-image observer run.
    kernel_errors=bool(re.search(r'EXT4-fs (?:error|warning)|I/O error|Buffer I/O|unsupported optional features|Kernel panic',serial,re.I))
    passed=(terminal==dict(exit=0,timed_out=False) and results==[('0',admitted.scope)] and
            exits==[('0',admitted.scope)] and before==after and not kernel_errors)
    result=dict(scope=admitted.scope,filesystem_observer_passed=passed,production_image_accepted=False,
                qemu=terminal,observer_results=results,observer_actual_exits=exits,host_before=before,host_after=after,
                identities_unchanged=before==after,kernel_errors=kernel_errors,whole_images_rehashed=False,
                admission_sha256=admitted.admission_sha256,expectations_sha256=admitted.expectations_sha256,
                limits=dict(host_cpus=1,process_as_bytes=1024**3,process_cpu_seconds=60,wall_seconds=90,
                            guest_mib=384,guest_vcpus=1,nic=False),
                final_host_e2fsck_separate_required=True,physical_GO=False,flash_ready=False)
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result
