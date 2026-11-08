"""One-shot native absence, existing-flock, exact terminal/source binding."""
import datetime
import fcntl
import os
from pathlib import Path
import re
import shlex
import stat
from safeio import Tree, fingerprint, load_bytes, need, relative

NATIVE = {'soong_ui', 'soong_build', 'ckati', 'siso', 'ninja', 'ninja-build', 'kati', 'clang', 'clang++', 'ld.lld', 'rustc', 'sbox', 'apexer', 'apex_compression_tool'}

def live_jobs(pids, proc=Path('/proc')):
    need(proc.is_dir(), 'PROC_UNAVAILABLE', str(proc))
    rows = []
    for path in proc.iterdir():
        if not path.name.isdigit():
            continue
        try:
            state = (path/'stat').read_text().split(') ',1)[1].split()[0]
            comm = (path/'comm').read_text().strip()
            args = (path/'cmdline').read_bytes().split(b'\0')
            build_script = any(Path(os.fsdecode(arg)).name in {'build_full_product.sh', 'soong_ui.bash'} for arg in args)
            native_path = any(arg.startswith((b'/srv/android/lineage24/out/', b'/srv/android/lineage24/prebuilts/',b'prebuilts/clang/',b'out/host/',b'out/soong/')) for arg in args[:1])
            build_script |= comm in {'bash','sh','python3','python'} and any(b'asus-reviewed-build-kit/' in arg and arg.endswith((b'/scripts/build.sh',b'/scripts/integrate.py')) for arg in args)
            if state not in {'Z','X'} and (comm in NATIVE or int(path.name) in pids or build_script or native_path):
                rows.append({'pid': int(path.name), 'comm': comm, 'state': state})
        except (FileNotFoundError, ProcessLookupError):
            continue
        except (PermissionError, ValueError, IndexError) as error:
            raise RuntimeError('PROC_UNREADABLE: cannot establish actual job absence') from error
    return rows

class Guard:
    def __init__(self, profile, probe=live_jobs):
        self.profile, self.probe = profile, probe
        self.fd = None

    def check(self):
        need(not self.probe(self.profile['pids']), 'LIVE_NATIVE_JOB', 'actual native process or recorded build PID still present')
        if self.fd is not None:
            now = os.stat(self.profile['lock'], follow_symlinks=False)
            held = os.fstat(self.fd)
            need(stat.S_ISREG(now.st_mode) and (now.st_dev,now.st_ino) == (held.st_dev,held.st_ino) and now.st_ino == self.profile['lock_inode'], 'LOCK_IDENTITY', 'original lock changed')

    def __enter__(self):
        self.check()
        path = Path(self.profile['lock'])
        tree = Tree(path.parent)
        try:
            parent = tree.parent(path.name)
            try:
                self.fd = os.open(path.name, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            finally:
                os.close(parent)
        finally:
            tree.close()
        try:
            s = os.fstat(self.fd)
            need(stat.S_ISREG(s.st_mode) and s.st_ino == self.profile['lock_inode'], 'LOCK_IDENTITY', 'requires same existing lock inode')
            try:
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise RuntimeError('LOCK_HELD: no waiting or retry') from error
            self.check()
            return self
        except BaseException:
            os.close(self.fd)
            self.fd = None
            raise

    def __exit__(self, *args):
        os.close(self.fd)
        self.fd = None

def variables(data):
    values = {}
    for line in data.decode().splitlines():
        key, sep, value = line.partition('=')
        need(sep and key not in values and re.fullmatch('[A-Z0-9_]+',key), 'VARIABLES', line[:80])
        values[key] = ' '.join(shlex.split(value))
    return values

def terminal(profile, trees, add, scan=None):
    """add(root,path,group,hash_only) pins and journals every read file."""
    def read(root, path, group='terminal'):
        add(root,path,group)
        return trees[root].read(path, 16*1024*1024)
    def obj(root,path,group='terminal'):
        return load_bytes(read(root,path,group))
    kit = trees['kit']
    seal = kit.digest('inputs/kit-pins.json', 16*1024*1024)['sha256']
    need(seal == profile['kit_seal'], 'KIT_SEAL', 'not exact sealed kit')
    pins = obj('kit','inputs/kit-pins.json')
    for name in ('inputs/plan.json','scripts/integrate.py','scripts/build.sh','scripts/validate_completed_product.py','scripts/verify_config_paths.py'):
        add('kit',name,'kit')
        need(kit.digest(name,16*1024*1024)['sha256'] == pins[name], 'KIT_PIN', name)
    plan = obj('kit','inputs/plan.json')
    need(all(plan[k] == profile[k] for k in ('revision','aosp','product_out','lock')), 'KIT_PLAN', 'root/revision mismatch')
    need(plan['run_root'] == profile['kit'], 'KIT_PLAN', 'kit path mismatch')
    launch = obj('kit','attempt/launch.json')
    need(launch == {'revision': profile['revision'], 'lock_inode':profile['lock_inode'], 'supervisor_pid':profile['pids'][0]}, 'LAUNCH', 'wrong exact supervisor/lock/revision')
    try:
        trees['kit'].stat('attempt/FAILED.json')
    except FileNotFoundError:
        pass
    else:
        need(False,'TERMINAL_FAILED','attempt/FAILED.json exists')
    base = 'full-build-' + profile['revision']
    raw = {name:read('logs',base+'.'+name) for name in ('started','finished','complete','exit-code','pid','vars','images.json')}
    need(raw['exit-code'].strip() == b'0', 'TERMINAL_FAILED', 'only genuine successful qualified terminal accepted')
    need(raw['pid'].strip() == str(profile['pids'][1]).encode(), 'BUILD_PID', 'not exact native child')
    dates = [datetime.datetime.fromisoformat(raw[n].decode().strip()) for n in ('started','complete','finished')]
    need(all(d.tzinfo for d in dates) and dates[0] <= dates[1] <= dates[2] <= datetime.datetime.now(datetime.timezone.utc), 'TERMINAL_TIME', 'incoherent terminal timestamps')
    add('logs',base+'.log','terminal-log',True)
    completion = obj('kit','attempt/complete.json')
    need(completion == {'revision':profile['revision'],'host_validation_completed':True,'flash_ready':False}, 'TERMINAL_COMPLETION', 'not exact successful supervisor receipt')
    validation = obj('kit','attempt/validation/complete.json')
    need(validation['kit_pins_sha256'] == seal and validation['elf_init_policy_neverallows_vintf_apex_host_checks_passed'] is True and validation['flash_ready'] is False, 'QUALIFICATION', 'native host qualification missing')
    bound = {
        'integration_receipt_sha256':'attempt/integration.json',
        'product_config_paths_sha256':'attempt/product-config-paths.json',
        'active_source_postimages_sha256':'attempt/validation/source-postimages.json',
    }
    for field, path in bound.items():
        add('kit',path,'binding')
        need(kit.digest(path,16*1024*1024)['sha256'] == validation[field], 'RECEIPT_BINDING', field)
    integration = obj('kit',bound['integration_receipt_sha256'])
    post = obj('kit',bound['active_source_postimages_sha256'])
    paths = obj('kit',bound['product_config_paths_sha256'])
    values = variables(raw['vars'])
    for key,value in profile['configuration'].items():
        need(values.get(key) == value, 'CONFIGURATION', key)
    need(values.get('SELINUX_IGNORE_NEVERALLOWS','') in ('','false'), 'CONFIGURATION', 'neverallows disabled')
    need(paths['source_configuration_paths_verified'] is True and paths['dumpvars_sha256'] == trees['logs'].digest(base+'.vars',16*1024*1024)['sha256'], 'CONFIG_BINDING', 'path receipt/dumpvars mismatch')
    report = load_bytes(raw['images.json'])
    need(report['variables']['PLATFORM_SDK_VERSION'] == '37' and report['system']['sha256'] == validation['source_system_sha256'] and report['boot']['sha256'] == validation['boot']['source_aosp_sha256'], 'IMAGE_RECEIPT_BINDING', 'image receipts disagree (image bytes are not opened)')
    source_pins = []
    def pin_absolute(path,digest):
        for root in ('aosp','kernel'):
            prefix = str(trees[root].root) + '/'
            if path.startswith(prefix):
                rel = relative(path[len(prefix):])
                add(root,rel,'source-integration',True)
                need(trees[root].digest(rel,profile['limits']['file_bytes'],allow_empty=True)['sha256'] == digest,'SOURCE_BINDING',path)
                source_pins.append({'root':root,'path':rel,'sha256':digest})
                return
        need(False,'SOURCE_ROOT',path)
    for rel,item in post['source_postimages'].items():
        pin_absolute(str(trees['kernel'].root)+'/'+relative(rel),item['sha256'])
    need(bool(post['source_postimages']) and post['config_sha256'] == integration['generated_defconfig']['sha256'] == validation['config_sha256'], 'SOURCE_BINDING', 'config or source postimages missing')
    pin_absolute(integration['generated_defconfig']['path'],post['config_sha256'])
    for rel,item in integration['product_after'].items():
        need(set(item) == {'sha256'},'SOURCE_TYPE',rel)
        pin_absolute(plan['device']+'/'+relative(rel),item['sha256'])
    for rel,item in post['connectivity'].items():
        pin_absolute(plan['connectivity']+'/'+relative(rel),item['sha256'])
    pin_absolute(plan['wificond'],post['wificond']['sha256'])
    for name,item in post['platform_sources'].items():
        for rel,change in item['files'].items():
            pin_absolute(plan[name]+'/'+relative(rel),change['after'])
    # Bind every actual policy/configuration directory and VINTF source path.
    for key,entries in paths['policy_dirs'].items():
        need(values.get(key,'').split() == entries,'CONFIG_PATH_BINDING',key)
        for path in entries:
            for rel in (scan('aosp',path) if scan else trees['aosp'].walk(path)):
                add('aosp',rel,'policy-source')
    for key,entries in paths['manifests'].items():
        need(values.get(key,'').split() == entries,'CONFIG_PATH_BINDING',key)
        for path in entries:
            add('aosp',path,'vintf-source')
    return {'kit_seal':seal, 'revision':profile['revision'], 'source_pins':source_pins,
            'configuration':values, 'image_bytes_checked':False,
            'sanitizer_inference_from_variant':False}
