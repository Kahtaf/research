#!/usr/bin/env python3
"""Local-only stock policy, image, source and binary evidence. No device tools."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import zlib

S=Path(__file__).resolve().parents[1]
W=S.parent
PROBE=S/'artifacts/build-v1/policy_probe'
TRANSITION=W/'2026-11-06-asus-android17-os-rescue/artifacts/tools-final/policy_query'
KERNEL=W/'2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18'
def sha(b):return hashlib.sha256(b).hexdigest()
def record(p):return dict(path=str(p.relative_to(W)),sha256=sha(p.read_bytes()),bytes=p.stat().st_size)

def isolation(event,args):
    if event.startswith('socket.') or event in ('os.system','os.exec','os.posix_spawn'):
        raise RuntimeError('Offline audit forbids '+event)
    if event=='subprocess.Popen' and Path(args[0]).resolve() not in (PROBE,TRANSITION):
        raise RuntimeError('Only fixed local read-only policy query tools can execute')
sys.addaudithook(isolation)

def extract_cpio(data,wanted):
    pos=0
    while pos+110<=len(data):
        h=data[pos:pos+110];assert h[:6]==b'070701'
        fields=[int(h[6+i*8:14+i*8],16) for i in range(13)]
        size,ns=fields[6],fields[11];assert 0<ns<4096 and size<=32*1024*1024
        name=data[pos+110:pos+110+ns];assert name[-1:]==b'\0'
        pos=(pos+110+ns+3)&~3;value=data[pos:pos+size];assert len(value)==size
        if name==wanted.encode()+b'\0':return value
        pos=(pos+size+3)&~3
    raise ValueError('cpio member not found')

def fixed_image(image,stock):
    assert len(image)==8654848 and sha(image)=='7d74dfcaf4b2793453906799d721bfd95a401c564f6698b1c646e18bee918ea5'
    assert image[:8]==stock[:8]==b'ANDROID!'
    n=struct.unpack_from('<I',image,8)[0]
    kernel=image[2048:2048+n]
    assert kernel==stock[2048:2048+n]
    assert sha(kernel)=='b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880'
    assert sha(image+bytes(16740352-len(image)))=='6c6a3f534646ed30257c21c7d91be65ea1b8844ef6aa2d0bd3c11545f62db925'
    return dict(candidate_sha256=sha(image),wrapped_kernel_sha256=sha(kernel),full_partition_sha256=sha(image+bytes(16740352-len(image))))

def main():
    backups=W/'2026-11-05-asus-boot-access-audit/artifacts/device-backup'
    initial=(backups/'initial/boot.bin').read_bytes()
    assert initial==(backups/'verify/boot.bin').read_bytes()
    assert sha(initial)=='7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316'
    n,_,rn=struct.unpack_from('<III',initial,8);ro=2048+(n+2047)//2048*2048
    ramdisk=initial[ro:ro+rn];assert ramdisk[8:40].split(b'\0')[0]==b'ROOTFS'
    z=zlib.decompressobj(31);raw=z.decompress(ramdisk[512:],64*1024*1024)
    assert z.eof and not z.unconsumed_tail
    policy=extract_cpio(raw,'sepolicy')
    assert sha(policy)=='873141c3874066341dcb4e2c7be4eb3f664686635ee3f84d2c4100f557ae740f'
    assert policy==(S/'artifacts/stock-boot.sepolicy').read_bytes()
    result=dict(device_contacted=False,status='BLOCKED',boot_backups_match=True,
                boot_sha256=sha(initial),policy_sha256=sha(policy),policy_queries=[])
    for target,cls,perm in [('u:r:shell:s0','capability','sys_boot'),
                            ('u:object_r:kernel:s0','security','setenforce'),
                            ('u:object_r:selinuxfs:s0','file','read'),
                            ('u:object_r:selinuxfs:s0','file','write')]:
        args=[str(PROBE),str(S/'artifacts/stock-boot.sepolicy'),'u:r:shell:s0',target,cls,perm]
        p=subprocess.run(args,capture_output=True,text=True,timeout=10,check=True)
        result['policy_queries'].append(dict(source='u:r:shell:s0',target=target,cls=cls,permission=perm,**json.loads(p.stdout)))
    q=result['policy_queries'][0];assert not q['allowed'] and not q['source_permissive'] and q['permission_bit']==1<<22
    args=[str(TRANSITION),str(S/'artifacts/stock-boot.sepolicy'),'u:r:shell:s0',
          'u:object_r:shell_data_file:s0','process','--transition']
    p=subprocess.run(args,capture_output=True,text=True,timeout=10,check=True)
    assert p.stdout.strip()=='u:r:shell:s0'
    result['shell_data_file_exec_transition']=dict(argv=args,result=p.stdout.strip(),
        limitation='Saved policy default transition for shell_data_file; current helper inode label was not probed')
    proof=W/'2026-11-05-asus-root-hardware-validation/evidence/final-root-helper-check.txt'
    result['captured_root_context']=[x for x in proof.read_text().splitlines() if x.startswith('uid=')]
    assert result['captured_root_context']==['uid=0(root) gid=0(root) groups=0(root) context=u:r:shell:s0']
    source_lines={
        'kernel/reboot.c':[(278,306),(338,348)],
        'kernel/capability.c':[(374,387)],
        'security/selinux/hooks.c':[(1547,1583),(2059,2069)],
        'include/linux/proc_ns.h':[(30,44)],
    }
    excerpts=[]
    for name,ranges in source_lines.items():
        path=KERNEL/name;lines=path.read_text().splitlines()
        for a,b in ranges:excerpts.append(f'{name}:{a}\n'+'\n'.join(f'{i+1}: {lines[i]}' for i in range(a-1,b)))
    (S/'evidence/kernel-permission-path.txt').write_text('\n\n'.join(excerpts)+'\n')
    saved=json.loads((W/'2026-11-06-asus-programmatic-recovery-audit/evidence/rtc-one-shot-static-findings.json').read_text())
    lk=(W/'2026-11-05-asus-boot-access-audit/sources/firmware/lk.bin').read_bytes()
    assert sha(lk)==saved['lk_sha256']
    result['lk_regions']={}
    for name,r in saved['regions'].items():
        a=int(r['start'],16)-0x41e00000+512;b=int(r['end'],16)-0x41e00000+512
        assert sha(lk[a:b])==r['bytes_sha256']
        result['lk_regions'][name]=dict(start=r['start'],end=r['end'],sha256=sha(lk[a:b]))
    stock=(backups/'initial/recovery.bin').read_bytes()
    assert stock==(backups/'verify/recovery.bin').read_bytes() and sha(stock)=='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
    candidate=W/'2026-11-06-asus-android17-os-rescue/artifacts/candidate-final/UNTESTED-stock-control.img'
    image=candidate.read_bytes();result['fixed_image']=fixed_image(image,stock)
    # Negative fixtures stay in evidence as byte mutation recipes, no large duplicate images.
    result['negative_image_tests']=[]
    for label,offset in [('wrong_ramdisk',len(image)-2048),('wrong_kernel',2048+512)]:
        mutation=bytearray(image);mutation[offset]^=1
        try:fixed_image(mutation,stock)
        except AssertionError:result['negative_image_tests'].append(dict(name=label,offset=offset,xor=1,refused=True))
        else:raise AssertionError('Mutated candidate accepted')
    gpt_path=W/'2026-11-05-asus-root-hardware-validation/artifacts/private/asus-primary-gpt.bin'
    gpt=gpt_path.read_bytes();assert sha(gpt)=='f87e70586706b06d029a2bc8521f1b8ae9176873cba1e5b4281cbaca816742ae'
    header=gpt[512:1024];hs,crc=struct.unpack_from('<II',header,12);hh=bytearray(header[:hs]);hh[16:20]=bytes(4)
    assert header[:8]==b'EFI PART' and zlib.crc32(hh)==crc
    lba,count,size,entries_crc=struct.unpack_from('<QIII',header,72)
    entries=gpt[lba*512:lba*512+count*size];assert zlib.crc32(entries)==entries_crc
    geometry=[]
    for i in range(count):
        ent=entries[i*size:(i+1)*size];name=ent[56:128].decode('utf-16le').rstrip('\0')
        if name in ('para','recovery','cache'):
            start,end=struct.unpack_from('<QQ',ent,32)
            geometry.append(dict(name=name,index=i+1,node=f'/dev/block/mmcblk0p{i+1}',start_sector=start,sectors=end-start+1))
    result['saved_gpt_geometry']=geometry
    assert next(x for x in geometry if x['name']=='para')['index']==12
    fstab=extract_cpio(raw,'fstab.mt8163').decode()
    result['stock_boot_fstab_misc']=[x for x in fstab.splitlines() if '/misc ' in x]
    # Normal boot fstab may omit /misc; exact stock recovery fstab supplies the mapping.
    rks,_,rrs=struct.unpack_from('<III',stock,8);rro=2048+(rks+2047)//2048*2048
    rr=zlib.decompress(stock[rro+512:rro+rrs],31)
    result['stock_recovery_fstab_misc']=[x for x in extract_cpio(rr,'etc/recovery.fstab').decode().splitlines() if '/misc ' in x]
    assert result['stock_recovery_fstab_misc']==['/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/para /misc emmc defaults defaults']
    result['bcb_offset']='NOT DERIVED: partition mapping proved, offset and current content remain separate outstanding gates'
    result['namespace_limit']='Initial namespace inums checked in source. Build config has CONFIG_NAMESPACES unset; exact boot kernel has no located IKCFG_ST. Candidate requires proc namespace links and fails closed if unavailable; not deployable.'
    inputs=[proof,PROBE,TRANSITION,candidate,gpt_path,W/'2026-11-06-asus-recovery-control-wifi/source/recovery_control.py',
            W/'2026-11-06-asus-wifi-device-access/scripts/root_shell_wifi.py',
            W/'2026-11-05-asus-root-hardware-validation/sources/mtk-su-mirror-b',
            W/'2026-11-06-asus-android17-os-rescue/source/observer.py',
            W/'2026-11-06-asus-recovery-control-wifi/evidence/reviewed-stock-control.json',
            *[KERNEL/name for name in source_lines]]
    result['inputs']=[record(p) for p in inputs]
    result['blocker']='Captured mtk-su root retains enforcing shell domain, with sys_boot denied. Direct RESTART2 cannot pass ns_capable/CAP_SYS_BOOT in unmodified saved stock policy. No policy/context bypass implemented or approved.'
    (S/'evidence/audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],sys_boot_allowed=q['allowed'],shell_permissive=q['source_permissive'],device_contacted=False)))

if __name__=='__main__':main()
