#!/usr/bin/env python3
"""Read-only offline verification. Prints JSON; optional output must be new."""
import argparse
import json
from pathlib import Path
import shlex
import struct
import subprocess
from bootformat import *

SOURCE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidates',type=Path,required=True)
    ap.add_argument('--recovery',type=Path,required=True)
    ap.add_argument('--kernel',type=Path,required=True)
    ap.add_argument('--tools',type=Path,required=True)
    ap.add_argument('--evidence',type=Path)
    a=ap.parse_args()
    manifest=json.loads((a.candidates/'manifest.json').read_text())
    stock=a.recovery.read_bytes();assert sha(stock)==RECOVERY_SHA
    header,stockkernel,stockramdisk,trailer=parse_image(stock)
    kernel=a.kernel.read_bytes();assert sha(kernel)==KERNEL_SHA
    images={n:(a.candidates/n).read_bytes() for n in manifest['images']}
    parsed={n:parse_image(data) for n,data in images.items()}
    control=parsed['UNTESTED-stock-control.img'];probe=parsed['UNTESTED-asus49-probe.img']
    assert control[1]==stockkernel
    assert probe[1][512:]==kernel
    assert control[2]==probe[2] and not control[3] and not probe[3]
    for n,data in images.items():
        assert len(data)==manifest['images'][n]['bytes'] and sha(data)==manifest['images'][n]['sha256']
        changed=[i for i,(x,y) in enumerate(zip(header,parsed[n][0])) if x!=y]
        assert all(8<=i<12 or 16<=i<20 or 64<=i<576 or 576<=i<608 for i in changed)
        cmd=parsed[n][0][64:576].split(b'\0')[0]
        assert cmd==header[64:576].split(b'\0')[0].replace(
            b'androidboot.selinux=permissive',b'androidboot.selinux=enforcing')
        assert b'permissive' not in cmd
    cpio,extra=ungzip(control[2][512:]);assert not extra
    entries=parse_cpio(cpio)
    expected={'dev','proc','sys','tmp','config','sbin','system','system/bin',
              'init','sbin/adbd','sbin/ueventd','sbin/recovery','system/bin/sh',
              'file_contexts.bin','property_contexts','seapp_contexts',
              'service_contexts','sepolicy','adb_keys','init.rc','default.prop','ueventd.rc'}
    assert set(entries)==expected
    assert entries['sbin/ueventd'][3]==b'../init'
    old=parse_cpio(ungzip(stockramdisk[512:])[0])
    for n in ['init','sbin/adbd','file_contexts.bin','property_contexts','seapp_contexts','service_contexts']:
        assert entries[n]==old[n]
    for n in ['init','sbin/adbd','sbin/recovery','system/bin/sh']:elf_static(entries[n][3])
    assert entries['sbin/recovery'][3]==entries['system/bin/sh'][3]==(a.tools/'diag').read_bytes()
    for n,(mode,uid,gid,data) in entries.items():
        assert sha(data)==manifest['entries'][n]['sha256']
        assert mode&0o170000 in (0o040000,0o100000,0o120000)
        assert not mode&0o6000
    rc=entries['init.rc'][3].decode()
    services=[];mounts=[]
    allowed={'on','start','export','mount','restorecon','write','mkdir','symlink',
             'powerctl','service','seclabel','user','group','disabled','oneshot','socket'}
    for line in rc.splitlines():
        tokens=shlex.split(line,comments=True)
        if not tokens:continue
        assert tokens[0] in allowed,tokens
        if tokens[0]=='service':services.append(tokens[1:])
        if tokens[0]=='write':
            assert tokens[1] in {'/sys/fs/selinux/enforce','/proc/sys/kernel/panic',
                '/proc/sys/kernel/panic_on_oops','/sys/devices/platform/mt_usb/cmode'} or \
                tokens[1].startswith('/sys/class/android_usb/android0/') or \
                tokens[1].startswith('/config/usb_gadget/g1/')
        if tokens[0]=='mount':
            mounts.append(tokens[1:])
            assert tokens[1:4] in [['tmpfs','tmpfs','/tmp'],['configfs','none','/config'],
                                   ['functionfs','adb','/dev/usb-ffs/adb']]
    assert services==[['deadline','/sbin/recovery','--deadline'],
        ['ueventd','/sbin/ueventd'],['diagnostic','/sbin/recovery','--collect'],
        ['adbd','/sbin/recovery','--adbd']]
    assert 'import ' not in rc and 'insmod ' not in rc and 'mount_all' not in rc
    assert 'start deadline' in rc.split('on init')[0]
    assert 'write /sys/fs/selinux/enforce 1' in rc.split('start deadline')[0]
    props=dict(x.split('=',1) for x in entries['default.prop'][3].decode().splitlines())
    assert props['ro.adb.secure']=='1' and props['ro.secure']=='1' and props['ro.debuggable']=='0'
    assert props['service.adb.tcp.port']=='0'
    policy=a.candidates/'diagnostic-sepolicy'
    assert entries['sepolicy'][3]==policy.read_bytes()
    queries=[]
    def query(s,t,c,required=(),denied=(),process=False):
        src=f'u:r:{s}:s0';dst=f'u:{"r" if process else "object_r"}:{t}:s0'
        result=subprocess.check_output([str(a.tools/'policy_query'),str(policy),src,dst,c],text=True).strip()
        perms=set(result.split('allowed=')[1].split(' ')[0].strip(',').split(','))
        assert set(required)<=perms,(result,required)
        assert not set(denied)&perms,(result,denied)
        assert 'recovery_permissive=0 policy_version=30' in result
        queries.append(result)
    query('recovery','rootfs','file',['open','read','execute','entrypoint'])
    query('init','recovery','process',['transition'],process=True)
    query('recovery','recovery','capability',['sys_boot'],process=True)
    query('recovery','tmpfs','dir',['search','write','add_name'])
    query('recovery','tmpfs','file',['open','create','write','read'])
    query('init','configfs','dir',['search','write','add_name','create'])
    query('init','configfs','file',['open','write'])
    query('init','configfs','lnk_file',['create'])
    query('adbd','adb_keys_file','file',['read','open'])
    query('adbd','rootfs','file',['read','open','execute','entrypoint','execute_no_trans'])
    query('adbd','selinuxfs','file',['read','open'])
    query('adbd','functionfs','dir',['search'])
    query('adbd','shell','process',['transition'],process=True)
    query('shell','shell_exec','file',['entrypoint','execute','read','open'])
    for s in ['shell','adbd']:
        query(s,'tmpfs','dir',['search','read','open'])
        query(s,'tmpfs','file',['read','open'],['write','append','create'])
        for t in ['block_device','boot_block_device','recovery_block_device','userdata_block_device']:
            query(s,t,'blk_file',denied=['write','append','create'])
    transitions=[]
    for s,c in [('init','dir'),('recovery','file')]:
        result=subprocess.check_output([str(a.tools/'policy_query'),str(policy),
            f'u:r:{s}:s0','u:object_r:tmpfs:s0',c,'--transition'],text=True).strip()
        assert result=='u:object_r:tmpfs:s0'
        transitions.append({'source':s,'target':'tmpfs','class':c,'result':result})
    negatives=[]
    bad=bytearray(images['UNTESTED-stock-control.img']);bad[576]^=1
    for label,data in [('wrong_boot_id',bytes(bad)),('partition_overflow',bytes(PARTITION_SIZE+1))]:
        try:parse_image(data)
        except AssertionError:negatives.append(label)
        else:raise AssertionError('Accepted invalid image '+label)
    for name in ['../escape','/absolute']:
        bad=make_cpio({name:(0o100644,0,0,b'bad')})
        try:parse_cpio(bad)
        except AssertionError:negatives.append(name)
        else:raise AssertionError('Accepted unsafe cpio path')
    report={'passed':True,'image_hashes':manifest['images'],
            'identical_minimal_ramdisk':True,'preserved_stock_kernel':True,
            'only_header_sizes_id_and_enforcing_cmdline_changed':True,'asus_signature_removed':True,
            'exact_ramdisk_allowlist':True,'ramdisk_entries':len(entries),
            'services':services,'mounts':mounts,'policy_checks':queries,
            'report_type_transitions':transitions,
            'negative_cases_rejected':negatives,
            'hardware_or_emulator_execution':False,'ready_for_supervised_stock_control':False}
    value=json.dumps(report,indent=2)+'\n'
    if a.evidence:
        with a.evidence.open('x') as f:f.write(value)
    print(value)

if __name__=='__main__':main()
