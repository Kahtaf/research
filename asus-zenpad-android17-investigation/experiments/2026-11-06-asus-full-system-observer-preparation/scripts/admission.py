"""Untrusted receipt boundary. Production trust starts at an external parent admission pin."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import os
import re
import stat
import struct

PATHS = ('/system/build.prop', '/system/bin/init', '/system/bin/run-as',
         '/system/vendor/etc/selinux/vendor_file_contexts')
GENUINE = 'GENUINE_COMPLETED_PRODUCT'
FIXTURE = 'FIXTURE_ONLY'
KERNEL_SHA = 'c59e030cdfc3e752eeddbbf62d091ae9760c94d5fbf780a22824e004ec872080'
CONFIG_SHA = '0426746d90db074dd026ae5d383e1cde27d587020699d5dc9af4faac0b54489f'
CREATION_PINS = {
 'build_image': 'fb4282af1552d445b175bea8018105ef22002fa5e108519b843229069296cc94',
 'mkuserimg': '8bda1a67fa742f06d8a23b905e544b3b0b327a83484df1f0b3c61c93b08468b1',
 'mke2fs_config': 'ad58a58dcdd24d85055814ca9cac67db89d4e67c434e96774bdce0d0a007d067'}
NEW_REMOTE = '/srv/android/asus-full-system-observer-preparation-20261106'
OLD_REMOTE = '/srv/android/asus-sdk37-system-ext4-qualification-20261106'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def keys(value, expected, where):
    need(type(value) is dict and set(value) == set(expected), 'Missing/unknown fields: ' + where)


def digest(value):
    need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None,
         'Require lowercase SHA256')
    return value


def integer(value, minimum, maximum, name):
    need(type(value) is int and minimum <= value <= maximum, 'Invalid ' + name)
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def identity(st):
    return dict(dev=st.st_dev, ino=st.st_ino, bytes=st.st_size, mode=stat.S_IMODE(st.st_mode),
                mtime_ns=st.st_mtime_ns, ctime_ns=st.st_ctime_ns)


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def ordinary(path, maximum=None):
    need(type(path) is str and Path(path).is_absolute(), 'Require absolute ordinary-file path')
    need(str(Path(path)) == path and '..' not in Path(path).parts, 'Noncanonical path')
    need(Path(path).resolve(strict=True) == Path(path), 'Symlinked input path is forbidden')
    fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    st = os.fstat(fd)
    try:
        need(stat.S_ISREG(st.st_mode), 'Require ordinary file: ' + path)
        need(maximum is None or st.st_size <= maximum, 'Oversized receipt/source')
    except Exception:
        os.close(fd)
        raise
    return fd, st


def pinned_bytes(ref, maximum=4*1024*1024):
    keys(ref, ('path', 'sha256'), 'pinned reference')
    pin = digest(ref['sha256'])
    fd, before = ordinary(ref['path'], maximum)
    try:
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            data = stream.read(maximum + 1)
        need(sha(data) == pin and identity(before) == identity(os.fstat(fd)),
             'Pinned receipt/source mismatch or changed input: ' + ref['path'])
        return data
    finally:
        os.close(fd)


def document(ref):
    return json.loads(pinned_bytes(ref, 1024*1024), object_pairs_hook=no_duplicates)


def file_records(records, fields, name):
    need(type(records) is list and len(records) == 4, 'Require exactly four ' + name)
    by_path = {}
    for row in records:
        keys(row, ('path', *fields), name)
        need(row['path'] in PATHS and row['path'] not in by_path, 'Unapproved/duplicate public target')
        by_path[row['path']] = row
    need(set(by_path) == set(PATHS), 'Missing fixed public file')
    return tuple(by_path[path] for path in PATHS)


def validate_expectations(content, metadata, scope, build_id, complete_pin, source_pin, source):
    common = ('schema', 'scope', 'build_id', 'complete_sha256', 'source_binding_sha256', 'producer', 'files')
    keys(content, common, 'public-content receipt')
    keys(metadata, (*common, 'fs_config_cpp_sha256', 'product_file_contexts_sha256',
                    'fs_config_overrides_sha256', 'resolver_tools', 'resolution_receipts'), 'resolved-metadata receipt')
    for obj, schema, producer in [
        (content, 'asus-public-content/v1', 'coherent-installed-public-output-capture'),
        (metadata, 'asus-resolved-public-metadata/v1', 'fs_config+selabel_lookup')]:
        need(obj['schema'] == schema and obj['scope'] == scope and obj['build_id'] == build_id,
             'Wrong receipt scope/schema/coherent build')
        need(obj['complete_sha256'] == complete_pin and obj['source_binding_sha256'] == source_pin,
             'Content/metadata is not bound to this complete/source group')
        fixture_producers = {'asus-public-content/v1':'fixture-known-input-bytes', 'asus-resolved-public-metadata/v1':'fixture-known-canned-rules'}
        need(obj['producer'] == (producer if scope == GENUINE else fixture_producers[schema]), 'Wrong expectation producer; image extraction is not an origin')
    for role in ('fs_config_cpp', 'product_file_contexts'):
        need(metadata[role + '_sha256'] == source['source_roles'][role]['sha256'],
             'Resolved metadata source mismatch: ' + role)
    need(metadata['fs_config_overrides_sha256'] == sha(canonical(source['fs_config_overrides'])),
         'Device fs_config override inventory mismatch')
    keys(metadata['resolver_tools'], ('fs_config', 'selabel_lookup'), 'resolver tools')
    for tool in metadata['resolver_tools'].values():
        digest(tool)
    need(type(metadata['resolution_receipts']) is list and len(metadata['resolution_receipts']) == 1,
         'Missing exact source-resolution execution receipt')
    resolution = document(metadata['resolution_receipts'][0])
    status = ('fs_config_exit_code','selabel_exit_code') if scope == GENUINE else ('fixture_formatter_exit_code',)
    keys(resolution, ('schema','scope','build_id','complete_sha256','source_binding_sha256',
                      'fs_config_cpp_sha256','product_file_contexts_sha256','fs_config_overrides_sha256',
                      'resolver_tools','files','stdout',*status), 'metadata resolution execution')
    need(resolution['schema'] == ('asus-public-metadata-resolution/v1' if scope == GENUINE else 'asus-fixture-known-resolution/v1'),
         'Synthetic resolution cannot enter production')
    for key in ('scope','build_id','complete_sha256','source_binding_sha256','fs_config_cpp_sha256',
                'product_file_contexts_sha256','fs_config_overrides_sha256','resolver_tools'):
        need(resolution[key] == metadata[key], 'Metadata resolution group/source mismatch: '+key)
    need(all(type(resolution[k]) is int and resolution[k] == 0 for k in status),
         'Metadata resolver did not complete successfully')
    need(canonical(resolution['files']) == canonical(metadata['files']), 'Resolved metadata values differ from execution receipt')
    keys(resolution['stdout'], ('fs_config','selabel_lookup'), 'resolution stdout references')
    fs_lines = pinned_bytes(resolution['stdout']['fs_config']).decode().splitlines()
    label_lines = pinned_bytes(resolution['stdout']['selabel_lookup']).decode().splitlines()
    need(len(fs_lines) == len(label_lines) == 4, 'Resolver must report exactly four fixed paths')
    for row,fs_line,label_line in zip(metadata['files'],fs_lines,label_lines):
        fields=fs_line.split();labels=label_line.split()
        need(len(fields)==5 and fields[0]=='/'+row['path'].lstrip('/') and
             fields[1]==str(row['uid']) and fields[2]==str(row['gid']) and
             fields[3]==format(row['mode'],'04o') and fields[4]=='capabilities='+hex(row['capability_mask']),
             'Canonical fs_config output differs from metadata')
        need(labels==[row['path'],row['selinux_label']], 'Canonical selabel output differs from metadata')
    contents = file_records(content['files'], ('bytes', 'sha256'), 'content records')
    metas = file_records(metadata['files'], ('uid', 'gid', 'mode', 'capability_mask', 'selinux_label'),
                         'metadata records')
    result = []
    for c, m in zip(contents, metas):
        size = integer(c['bytes'], 1, 16777216, 'public file size')
        label = m['selinux_label']
        need(type(label) is str and re.fullmatch(r'u:object_r:[a-zA-Z0-9_]+:s0', label) is not None,
             'Invalid/missing resolved SELinux label')
        caps = integer(m['capability_mask'], 0, 2**64-1, 'resolved capability mask')
        cap_bytes = struct.pack('<IIIII', 0x02000001, caps & 0xffffffff, 0, caps >> 32, 0) if caps else None
        result.append(dict(path=c['path'], bytes=size, sha256=digest(c['sha256']),
                           uid=integer(m['uid'], 0, 2**32-1, 'uid'),
                           gid=integer(m['gid'], 0, 2**32-1, 'gid'),
                           mode=integer(m['mode'], 0, 0o7777, 'mode'),
                           selinux_hex=(label.encode() + b'\0').hex(),
                           capability_hex=cap_bytes.hex() if cap_bytes else None))
    need(sum(r['bytes'] for r in result) <= 32*1024*1024, 'Public read budget exceeded')
    return tuple(result)


@dataclass(frozen=True)
class Admitted:
    scope: str
    build_id: str
    admission_sha256: str
    expectations_sha256: str
    files: tuple
    raw_path: str
    raw_identity: dict
    raw_sha256: str
    system_path: str
    system_identity: dict
    system_sha256: str
    complete_sha256: str


def load_production(path, pin):
    """No raw image is opened until the complete external receipt group is admitted."""
    admission = document(dict(path=str(Path(path).absolute()), sha256=digest(pin)))
    return load_group(admission, pin, GENUINE)


def load_group(admission, pin, scope):
    keys(admission, ('schema', 'scope', 'decision', 'build_id', 'kernel_sha256', 'config_sha256',
                     'complete', 'terminal', 'source_binding', 'public_content', 'resolved_metadata'),
         'parent admission')
    need(admission['schema'] == 'asus-fs-parent-admission/v1' and admission['scope'] == scope,
         'Fixture/unrecognized admission cannot enter production')
    need(admission['decision'] == ('ACCEPT_COHERENT_PRODUCT_INPUTS' if scope == GENUINE else 'FIXTURE_TEST_ONLY'),
         'Missing explicit parent admission decision')
    build_id = admission['build_id']
    need(type(build_id) is str and re.fullmatch('[a-zA-Z0-9_.-]{1,100}', build_id) is not None,
         'Invalid coherent build id')
    need(admission['kernel_sha256'] == KERNEL_SHA and admission['config_sha256'] == CONFIG_SHA,
         'Kernel/config selection differs from qualification')
    docs = {role: document(admission[role]) for role in
            ('complete', 'terminal', 'source_binding', 'public_content', 'resolved_metadata')}
    complete, terminal, source = (docs[k] for k in ('complete', 'terminal', 'source_binding'))
    cp = admission['complete']['sha256'];sp = admission['source_binding']['sha256']
    status_fields = ('build_exit_code','host_validation_exit_code') if scope == GENUINE else ('fixture_setup_exit_code','fixture_fsck_exit_code')
    keys(terminal, ('schema', 'scope', 'build_id', *status_fields,
                    'complete_sha256', 'source_binding_sha256', 'sdk', 'native_phase_receipts'), 'terminal receipt')
    need(terminal['schema'] == ('asus-native-host-terminal/v1' if scope == GENUINE else 'asus-fixture-terminal/v1') and terminal['scope'] == scope and
         terminal['build_id'] == build_id and terminal['complete_sha256'] == cp and
         terminal['source_binding_sha256'] == sp and type(terminal['sdk']) is int and terminal['sdk'] == 37,
         'Terminal validation group mismatch')
    need(all(type(terminal[field]) is int and terminal[field] == 0 for field in status_fields),
         'Native build/host validation or fixture preparation did not succeed')
    need(type(terminal['native_phase_receipts']) is list and len(terminal['native_phase_receipts']) >= 1,
         'Missing pinned terminal phase receipt')
    for ref in terminal['native_phase_receipts']:
        pinned_bytes(ref)
    if scope == GENUINE:
        need(complete.get('elf_init_policy_neverallows_vintf_apex_host_checks_passed') is True and
             not complete.get('fixture_only', False), 'Missing genuine host completion; fixture cannot be promoted')
    else:
        need(complete.get('fixture_only') is True and complete.get('fixture_preparation_passed') is True,
             'Fixture-only completion tag/preparation receipt missing')
    keys(source, ('schema', 'scope', 'build_id', 'sdk', 'capture_root', 'source_roles', 'fs_config_overrides',
                  'raw_identity', 'system_image'), 'source binding')
    need(source['schema'] == 'asus-fs-source-binding/v1' and source['scope'] == scope and
         source['build_id'] == build_id and type(source['sdk']) is int and source['sdk'] == 37,
         'Source binding group mismatch')
    roles = ('plan', 'boardconfig', 'build_image', 'mkuserimg', 'mke2fs_config', 'fs_config_cpp',
             'platform_file_contexts', 'product_file_contexts')
    if scope == GENUINE:roles += ('system_rule','system_image_info')
    keys(source['source_roles'], roles, 'required public source roles')
    capture = Path(source['capture_root'])
    need(capture.is_absolute(), 'Require frozen public capture root')
    captured = {}
    for role, ref in source['source_roles'].items():
        keys(ref, ('path', 'sha256', 'source_path'), 'public source reference')
        need(Path(ref['path']).is_relative_to(capture), 'Public source outside coherent frozen capture')
        captured[role] = pinned_bytes({k:ref[k] for k in ('path','sha256')})
    if scope == GENUINE:
        for role, expected in CREATION_PINS.items():
            need(source['source_roles'][role]['sha256'] == expected, 'Changed creation source needs review: ' + role)
        plan = json.loads(captured['plan'], object_pairs_hook=no_duplicates)
        aosp, device = plan['aosp'], plan['device']
        expected_paths = dict(boardconfig=device+'/BoardConfig.mk', build_image=aosp+'/build/make/tools/releasetools/build_image.py',
                              mkuserimg=aosp+'/system/extras/ext4_utils/mkuserimg_mke2fs.py',
                              mke2fs_config=aosp+'/system/extras/ext4_utils/mke2fs.conf',
                              fs_config_cpp=aosp+'/system/core/libcutils/fs_config.cpp',
                              platform_file_contexts=aosp+'/system/sepolicy/private/file_contexts',
                              product_file_contexts=plan['product_out']+'/obj/ETC/file_contexts.bin_intermediates/file_contexts.bin')
        expected_paths['system_image_info']=plan['product_out']+'/obj/PACKAGING/system_intermediates/system_image_info.txt'
        graph_path=Path(source['source_roles']['system_rule']['source_path'])
        need(graph_path.is_relative_to(Path(aosp)/'out') and graph_path.suffix=='.ninja' and len(captured['system_rule'])>0, 'Missing actual generated SYSTEM rule binding')
        properties={}
        for line in captured['system_image_info'].decode().splitlines():
            if not line.strip() or line.startswith('#'):continue
            key,sep,value=line.partition('=');need(bool(sep) and key not in properties, 'Malformed/duplicate SYSTEM creation property');properties[key]=value
        relative_out=str(Path(plan['product_out']).relative_to(Path(aosp)))
        selected=dict(system_fs_type='ext4',fs_type='ext4',system_size='3753902080',ext_mkuserimg='mkuserimg_mke2fs',
                      extfs_sparse_flag='-s',system_selinux_fc=relative_out+'/obj/ETC/file_contexts.bin_intermediates/file_contexts.bin',
                      root_dir=relative_out+'/root')
        need(all(properties.get(k)==v for k,v in selected.items()), 'Changed/missing genuine SYSTEM creation selection')
        need(properties.get('ext4_share_dup_blocks','false')!='true' and properties.get('system_journal_size','0')=='0', 'Unqualified creation flags')
        for role, original in expected_paths.items():
            need(source['source_roles'][role]['source_path'] == original, 'Plan-resolved public source path mismatch: '+role)
    need(type(source['fs_config_overrides']) is list, 'Require explicit override inventory, including empty')
    for ref in source['fs_config_overrides']:
        need(Path(ref['path']).is_relative_to(capture), 'Override outside frozen public source capture')
        pinned_bytes(ref)
    raw = complete['raw_system']
    need(type(raw) is dict and raw.get('all_zero_ranges_written') is True,
         'Missing parent materialized raw artifact')
    raw_path = raw['path'];digest(raw['sha256']);digest(complete['source_system_sha256'])
    expected_raw_bytes = 3753902080 if scope == GENUINE else integer(raw['bytes'], 1, 64*1024*1024, 'fixture bytes')
    need(type(raw['bytes']) is int and raw['bytes'] == expected_raw_bytes, 'Wrong raw partition size')
    need(Path(raw_path).is_absolute() and Path(raw_path).parent == Path(admission['complete']['path']).parent,
         'Raw path must be the owner complete.json sibling, never a CLI target')
    keys(source['system_image'], ('path', 'sha256', 'identity'), 'completed system image')
    system = source['system_image']
    need(system['sha256'] == complete['source_system_sha256'], 'Source image digest binding mismatch')
    for value in (source['raw_identity'], system['identity']):
        keys(value, ('dev', 'ino', 'bytes', 'mode', 'mtime_ns', 'ctime_ns'), 'immutable image identity')
        for v in value.values():integer(v, 0, 2**64-1, 'image identity')
    need(source['raw_identity']['bytes'] == raw['bytes'] and source['raw_identity']['mode'] & 0o222 == 0,
         'Raw identity size/read-only mode mismatch')
    if scope == GENUINE:
        for value in (raw_path, system['path'], str(capture)):
            need(not any(Path(value).is_relative_to(Path(root)) for root in (NEW_REMOTE, OLD_REMOTE)),
                 'Known synthetic fixture namespace cannot enter production')
    rows = validate_expectations(docs['public_content'], docs['resolved_metadata'], scope, build_id, cp, sp, source)
    expectations_pin = sha(canonical({'scope':scope, 'build_id':build_id, 'complete_sha256':cp,
                                      'source_binding_sha256':sp, 'files':rows}))
    return Admitted(scope, build_id, digest(pin), expectations_pin, rows, raw_path, source['raw_identity'],
                    raw['sha256'], system['path'], system['identity'], system['sha256'], cp)
