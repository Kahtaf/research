#!/usr/bin/env python3
"""Execute real ARM64 ELF / extracted LK Thumb instructions in Unicorn only.

No host subprocess, sockets or device operations are permitted after imports.
All Linux syscalls and PMIC reads/writes terminate at explicit Python stubs.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys
import traceback
import capstone
import unicorn
from unicorn import Uc, UC_ARCH_ARM64, UC_ARCH_ARM, UC_MODE_ARM, UC_MODE_THUMB, UC_HOOK_INTR, UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X3, UC_ARM64_REG_X8, UC_ARM64_REG_SP
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC

S=Path(__file__).resolve().parents[1]
W=S.parent

def isolation(event,args):
    if event.startswith(('socket.','subprocess.','os.exec','os.spawn','os.posix_spawn')) or event in ('os.system','pty.spawn'):
        raise RuntimeError('Offline QA forbids '+event)
    if event=='open' and isinstance(args[0],str) and args[0].startswith(('/dev/','/proc/','/sys/')):
        raise RuntimeError('Offline QA forbids host device/proc/sys reads')
sys.addaudithook(isolation)

def sha(b):return hashlib.sha256(b).hexdigest()
def cstring(u,p):
    b=bytearray()
    for _ in range(256):
        c=u.mem_read(p+len(b),1)
        if c==b'\0':return bytes(b).decode()
        b+=c
    raise AssertionError('Unterminated syscall argument')

def native(case):
    data=(S/'artifacts/build-v1/entry').read_bytes()
    assert data[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',data,18)[0]==183
    entry,phoff=struct.unpack_from('<QQ',data,24)
    phsize,phnum=struct.unpack_from('<HH',data,54)
    u=Uc(UC_ARCH_ARM64,UC_MODE_ARM); u.mem_map(0x200000,0x200000)
    for i in range(phnum):
        typ,flags,off,va,pa,fs,ms,align=struct.unpack_from('<IIQQQQQQ',data,phoff+i*phsize)
        assert typ not in (2,3), 'Dynamic ELF is forbidden'
        if typ==1:
            assert 0x200000<=va and va+ms<=0x400000
            u.mem_write(va,data[off:off+fs])
    u.mem_map(0x700000,0x20000);u.reg_write(UC_ARM64_REG_SP,0x71f000)
    u.mem_write(0x71f000,struct.pack('<Q',case.get('argc',1)))
    records=[];state=dict(enforce=case.get('enforce','1'),reads=0,exit=None)
    def intr(u,no,user):
        n=u.reg_read(UC_ARM64_REG_X8)
        a,b,c,d=[u.reg_read(r) for r in (UC_ARM64_REG_X0,UC_ARM64_REG_X1,UC_ARM64_REG_X2,UC_ARM64_REG_X3)]
        row=dict(syscall=n,args=[a,b,c,d]);records.append(row)
        if n in (174,175):ret=case.get('uid' if n==174 else 'euid',0)
        elif n==56:
            path=cstring(u,b);row['path']=path
            assert path=='/sys/fs/selinux/enforce' and c in (0xa0000,0xa0001)
            ret=-13 if case.get('open_denied') or (c&1 and case.get('write_open_denied')) else 10
        elif n==63:
            assert a==10 and c==2
            state['reads']+=1
            v=state['enforce']
            if case.get('last_read_permissive') and state['reads']==2:v='0'
            u.mem_write(b,v.encode());ret=-13 if case.get('read_denied') else len(v)
        elif n==57:
            assert a==10;ret=-5 if case.get('close_denied') else 0
        elif n==64:
            assert a==10 and c==1 and bytes(u.mem_read(b,c))==b'1'
            ret=case.get('write_result',1)
            if ret==1 and not case.get('write_ignored'):state['enforce']='1'
        elif n==78:
            path=cstring(u,b);row['path']=path
            expect={'/proc/self/ns/pid':'pid:[4026531836]','/proc/self/ns/user':'user:[4026531837]'}
            assert path in expect
            value='pid:[999]' if case.get('bad_pid') and path.endswith('/pid') else expect[path]
            if case.get('bad_user') and path.endswith('/user'):value='user:[999]'
            u.mem_write(c,value.encode());ret=len(value)
        elif n==142:
            assert state['enforce']=='1'
            assert (a,b,c)==(0xfee1dead,672274793,0xa1b2c3d4)
            assert cstring(u,d)=='recovery'
            row['literal']='recovery';ret=case.get('reboot_result',-1)
            if ret=='nonreturning':u.emu_stop();return
        elif n==94:
            state['exit']=a;u.emu_stop();return
        else:raise AssertionError('Unexpected native syscall '+str(n))
        u.reg_write(UC_ARM64_REG_X0,ret&((1<<64)-1))
    u.hook_add(UC_HOOK_INTR,intr);u.emu_start(entry,0,count=20000)
    requests=[x for x in records if x['syscall']==142]
    assert len(requests)<=1
    return dict(case=case,exit=state['exit'],reboot_requests=len(requests),syscalls=records)

class LK:
    def __init__(self,pdn=0x10,busy_reads=0,drop_write=False,assert_result=0,boot_mode=0,charger=False,vbat=3800):
        self.u=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
        self.u.mem_map(0x41e00000,0x100000)
        image=(W/'2026-11-05-asus-boot-access-audit/sources/firmware/lk.bin').read_bytes()
        assert sha(image)=='c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765'
        self.u.mem_write(0x41e00000,image[512:])
        self.u.mem_map(0x50000000,0x20000)
        self.u.mem_write(0x41e77678,struct.pack('<I',0x41e78000))
        self.u.mem_write(0x41e78004,struct.pack('<I',boot_mode))
        self.pdn=pdn;self.busy=busy_reads;self.drop=drop_write;self.assert_result=assert_result
        self.charger=charger;self.vbat=vbat;self.rtc_checks=0
        self.writes=[];self.reads=[];self.calls=[];self.stop=None
        self.u.hook_add(UC_HOOK_CODE,self.code)
    def code(self,u,pc,size,user):
        if pc in (0x41e0326a,0x41e032ce,0x41e031ec,0x50010000,0x41e00190):
            self.stop=hex(pc);u.emu_stop();return
        if pc==0x41e07f8c:self.rtc_checks+=1
        if pc==0x41e06acc:
            a=u.reg_read(UC_ARM_REG_R0);ptr=u.reg_read(UC_ARM_REG_R1)
            assert a in (0x8000,0x8002,0x802c,0x802e,0x8030,0x8032)
            self.reads.append(a)
            if a==0x802c:v=self.pdn
            elif a==0x8000:
                v=0x40 if self.busy else 0
                if self.busy>0:self.busy-=1
            else:v=0
            u.mem_write(ptr,struct.pack('<I',v));self.ret(0);return
        if pc==0x41e06adc:
            a=u.reg_read(UC_ARM_REG_R0);v=u.reg_read(UC_ARM_REG_R1)
            assert a in (0x802c,0x803c)
            self.writes.append((a,v))
            if a==0x802c and not self.drop:self.pdn=v
            self.ret(0);return
        # Explicit outside-function stubs. None are claimed as firmware executed.
        zeros={0x41e20980,0x41e05c7c,0x41e2071c,0x41e082fc,0x41e05bf4,
               0x41e05b64,0x41e39b6c,0x41e393ac,0x41e13d68}
        if self.charger:
            zeros.remove(0x41e13d68)
            zeros.update((0x41e13ca4,0x41e24dac,0x41e07364))
            if pc==0x41e0707c:
                self.calls.append(hex(pc));self.ret(self.vbat);return
        if pc in zeros or pc==0x41e13c40:
            self.calls.append(hex(pc));self.ret(self.assert_result if pc==0x41e13c40 else 0);return
        allowed=((0x41e08320,0x41e0834c),(0x41e03b70,0x41e03bc6),
                 (0x41e07f8c,0x41e08024),(0x41e07f1c,0x41e07f46),
                 (0x41e031a8,0x41e031ec),
                 *(([(0x41e13d68,0x41e13dd8)]) if self.charger else []))
        assert any(a<=pc<b for a,b in allowed),f'Unmodeled firmware branch {pc:x}'
    def ret(self,value):
        self.u.reg_write(UC_ARM_REG_R0,value)
        self.u.reg_write(UC_ARM_REG_PC,self.u.reg_read(UC_ARM_REG_LR))
    def run(self,addr,count=10000):
        self.stop=None
        self.u.reg_write(UC_ARM_REG_SP,0x5000f000)
        self.u.reg_write(UC_ARM_REG_LR,0x50010001)
        self.u.reg_write(UC_ARM_REG_R0,0)
        self.u.reg_write(UC_ARM_REG_R4,0x41e6500c)
        self.u.reg_write(UC_ARM_REG_R5,0)
        self.u.reg_write(UC_ARM_REG_R6,0x41e77678)
        self.u.emu_start(addr|1,0,count=count)
        return self.u.reg_read(UC_ARM_REG_R0)
    def cached(self):return struct.unpack('<I',self.u.mem_read(0x41e68500,4))[0]

def main():
    result=dict(device_contacted=False,emulator=unicorn.__version__,capstone=capstone.__version__,
                boundary='Actual compiled ELF and saved LK instructions; all syscalls and PMIC accesses stubbed; no Linux, hardware or complete boot emulation')
    try:
        cases=[({'argc':2},90),({'uid':2000},91),({'euid':2000},91),
               ({'open_denied':True},92),({'enforce':'0','write_open_denied':True},92),
               ({'enforce':'0','write_result':0},93),({'enforce':'0','write_result':-13},93),
               ({'enforce':'0','write_ignored':True},93),({'read_denied':True},93),
               ({'close_denied':True},93),({'bad_pid':True},94),({'bad_user':True},95),
               ({'last_read_permissive':True},96),({},97),({'enforce':'0'},97),
               ({'reboot_result':-22},98),({'reboot_result':0},98),({'reboot_result':'nonreturning'},None)]
        result['native']=[]
        for c,expected in cases:
            r=native(c);result['native'].append(r)
            assert r['exit']==expected,(c,r['exit'],expected)
            assert r['reboot_requests']==(1 if expected in (97,98,None) else 0)
        lk=LK();total=0
        for pdn in range(65536):
            lk.pdn=pdn;lk.reads=[]
            actual=lk.run(0x41e08320)
            assert lk.stop=='0x50010000' and actual==int((pdn&0x30)==0x10)
            assert lk.reads==[0x802c] and not lk.writes
            total+=1
        result['predicate_exhaustive_inputs']=total
        result['one_shot_cases']=[]
        for pdn in (0x10,0x11,0x50,0x90,0x110,0x8010,0xffdf):
            lk=LK(pdn,busy_reads=3)
            lk.run(0x41e03b70);assert lk.cached()==2
            ret=lk.run(0x41e07f8c)
            assert ret==1 and lk.pdn==pdn&0xffef and lk.cached()==2
            assert lk.writes==[(0x802c,pdn&0xffef),(0x803c,1)]
            assert lk.run(0x41e08320)==0
            result['one_shot_cases'].append(dict(pdn1=pdn,after=lk.pdn,cached_mode=lk.cached(),writes=lk.writes))
        for pdn in (0,0x20,0x30):
            lk=LK(pdn);assert lk.run(0x41e07f8c)==0 and not lk.writes
        lk=LK(busy_reads=-1);lk.run(0x41e07f8c,count=1000)
        assert lk.stop is None and lk.reads.count(0x8000)>20
        result['busy_never_clears']='Real firmware commit remained in polling loop at instruction budget; not a firmware timeout'
        lk=LK(drop_write=True);assert lk.run(0x41e07f8c)==1 and lk.pdn==0x10
        assert lk.run(0x41e08320)==1
        result['dropped_pmic_write']='Real firmware returns success in this stub scenario although request remains; no PMIC success proof'
        result['main_fragment']=[]
        for cfg,stop in [({},'0x41e031ec'),({'assert_result':1},'0x41e032ce'),({'boot_mode':100},'0x41e0326a')]:
            lk=LK(**cfg);lk.run(0x41e031a8)
            assert lk.stop==stop and lk.cached()==2
            assert bool(lk.writes)==(not cfg)
            result['main_fragment'].append(dict(stub_inputs=cfg,stop=stop,writes=lk.writes,external_stub_calls=lk.calls))
        result['actual_charger_fragment']=[]
        for vbat,stop,checks in [(3800,'0x41e031ec',2),(3000,'0x41e00190',1)]:
            lk=LK(charger=True,vbat=vbat);lk.run(0x41e031a8)
            assert lk.stop==stop and lk.cached()==2 and lk.rtc_checks==checks
            assert lk.writes==[(0x802c,0),(0x803c,1)]
            result['actual_charger_fragment'].append(dict(stub_vbat=vbat,stop=stop,
                rtc_checks=checks,writes=lk.writes,external_stub_calls=lk.calls,
                note='Real charger function calls rtc_boot_check at 0x41e13d94 before low-battery decision; poweroff implementation not executed'))
        result['status']='PASS'
    except BaseException:
        result['status']='FAIL';result['traceback']=traceback.format_exc();raise
    finally:
        (S/'evidence/offline-boundary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],native_cases=len(cases),predicate_cases=total,device_contacted=False)))

if __name__=='__main__':main()
