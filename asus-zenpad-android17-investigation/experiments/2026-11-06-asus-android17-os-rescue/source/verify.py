#!/usr/bin/env python3
"""Offline image/actual binary-policy evaluation and host DAC reproduction."""
import argparse,json,os,stat,subprocess,tempfile
from pathlib import Path
from bootformat import *

def verify(candidate,tools,stock,output):
    manifest=json.loads((candidate/'manifest.json').read_text())
    image=(candidate/'UNTESTED-stock-control.img').read_bytes()
    h,k,r,tail=parse_image(image);sh,sk,sr,st=parse_image(stock.read_bytes())
    assert sha(stock.read_bytes())==RECOVERY_SHA and k==sk and not tail
    assert sha(image)==manifest['images']['UNTESTED-stock-control.img']['sha256']
    entries=parse_cpio(ungzip(r[512:])[0]);old=parse_cpio(ungzip(sr[512:])[0])
    for n in ('init','sbin/adbd','file_contexts.bin','property_contexts','seapp_contexts','service_contexts'):assert entries[n]==old[n]
    assert entries['sbin/ueventd']==(0o120777,0,0,b'../init')
    assert stat.S_ISREG(entries['system/bin/sh'][0]) and stat.S_ISREG(entries['sbin/recovery'][0])
    assert entries['system/bin/sh'][3]==entries['sbin/recovery'][3]==(tools/'diag').read_bytes()
    assert b'androidboot.selinux=enforcing' in h and b'androidboot.selinux=permissive' not in h
    for n in ('init','sbin/adbd','sbin/recovery','system/bin/sh'):elf_static(entries[n][3])
    rc=entries['init.rc'][3].decode();props=entries['default.prop'][3].decode()
    assert not any(v in rc for v in ('mount_all','import ','insmod ','/dev/block','mount ext4','mount configfs'))
    assert 'mount tmpfs tmpfs /tmp nosuid nodev noexec mode=0755,size=1048576' in rc
    assert 'start deadline' in rc.split('on init')[0]
    assert 'ro.secure=1' in props and 'ro.adb.secure=1' in props and 'ro.debuggable=0' in props
    assert entries['adb_keys'][3].count(b'\n')==1 and b' ' not in entries['adb_keys'][3]
    policy=candidate/'diagnostic-sepolicy';assert entries['sepolicy'][3]==policy.read_bytes()
    results=[]
    def decision(src,dst,cls,perms,allowed=True,p=policy):
        run=subprocess.run([str(tools/'policy_constraints'),str(p),src,dst,cls,perms],capture_output=True,text=True)
        assert run.returncode==(0 if allowed else 1),(src,dst,cls,perms,run.stdout,run.stderr)
        results.append(dict(src=src,dst=dst,cls=cls,permissions=perms,expected_allowed=allowed,result=run.stdout))
    def c(typ,obj=False):return 'u:'+('object_r' if obj else 'r')+':'+typ+':s0'
    for s,t,cl,perms in [
        ('init','rootfs','file','relabelfrom'),('init','shell_exec','file','relabelto'),
        ('shell_exec','rootfs','filesystem','associate'),('adbd','shell_exec','file','read,open,execute'),
        ('shell','shell_exec','file','read,open,execute,entrypoint'),('shell','rootfs','dir','search'),
        ('shell','tmpfs','dir','search'),('shell','tmpfs','file','read,open,getattr'),
        ('shell','proc','dir','search'),('shell','proc','file','read,open'),
        ('adbd','rootfs','file','read,open,execute,execute_no_trans'),
        ('adbd','shell_exec','file','getattr'),('adbd','selinuxfs','file','read,open'),
        ('recovery','tmpfs','dir','search,write,add_name,remove_name'),
        ('recovery','tmpfs','file','create,write,open,setattr,rename')]:
        decision(c(s,s=='shell_exec'),c(t,True),cl,perms)
    decision(c('adbd'),c('shell'),'process','transition')
    decision(c('init'),c('recovery'),'process','transition')
    decision(c('recovery'),c('recovery'),'capability','sys_boot')
    decision(c('rootfs',True),c('shell_exec',True),'file','validate:u:r:init:s0')
    decision(c('adbd'),c('shell'),'process','validate:u:r:adbd:s0')
    decision(c('init'),c('shell_exec',True),'file','relabelto',False,candidate/'stock-sepolicy')
    for src in ('adbd','shell'):
        decision(c(src),c('tmpfs',True),'file','write',False)
        for t in ('boot_block_device','system_block_device','recovery_block_device','userdata_block_device','block_device'):
            decision(c(src),c(t,True),'blk_file','write',False)
    # Removing broad adbd report grants is intentional; correctly labeled endpoint transitions.
    decision(c('adbd'),c('tmpfs',True),'file','read',False)
    transitions=[]
    for src,dst,cl,expected in [('adbd','rootfs','process','u:r:adbd:s0'),('adbd','shell_exec','process','u:r:shell:s0'),('recovery','tmpfs','file','u:object_r:tmpfs:s0')]:
        actual=subprocess.check_output([str(tools/'policy_query'),str(policy),c(src),c(dst,True),cl,'--transition'],text=True).strip()
        assert actual==expected;transitions.append(dict(src=src,dst=dst,cls=cl,result=actual))
    # Actual host filesystem syscall semantics, no setuid/root/device calls.
    with tempfile.TemporaryDirectory(dir=output.parent) as td:
        oldmask=os.umask(0o077)
        try:
            path=Path(td)/'pending';fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
            before=stat.S_IMODE(os.fstat(fd).st_mode);assert before==0o600
            os.write(fd,b'complete\nEND_DIAGNOSTIC\n');os.fchmod(fd,0o444)
            after=stat.S_IMODE(os.fstat(fd).st_mode);os.close(fd)
            path.rename(Path(td)/'report');assert after==0o444
            assert (Path(td)/'report').read_bytes().endswith(b'END_DIAGNOSTIC\n')
        finally:os.umask(oldmask)
    full=image+bytes(PARTITION_SIZE-len(image))
    report=dict(passed=True,image_bytes=len(image),image_sha256=sha(image),padded_partition_sha256=sha(full),
        padded_partition_bytes=PARTITION_SIZE,stock_kernel_wrapped_sha256=sha(k),
        actual_host_DAC={'umask':'077','old_creation_mode':oct(before),'explicit_publication_mode':oct(after),'uid2000_execution_tested':False},
        transitions=transitions,constraint_evaluations=results,hardware_or_emulator_executed=False,
        parent_review_required=True)
    with output.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k not in ('constraint_evaluations','transitions')},indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--tools',type=Path,required=True);ap.add_argument('--stock',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();verify(a.candidate,a.tools,a.stock,a.out)
