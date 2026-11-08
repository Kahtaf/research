"""Offline decoder; parent independently attests full installed p10 and fresh stock boot."""
from pathlib import Path
import argparse,json,re
R=Path(__file__).resolve().parents[1]
I=json.loads((R/'evidence/identity.json').read_text())
P=json.loads((R/'evidence/packaging-receipt.json').read_text())
RELEASE='4.9.337-asus-p00a-experimental-g717bb3c9e13c-dirty'
CLOCK_PATH='kernel-syscall:syscall(SYS_clock_gettime);vDSO-bypassed;control='+I['control_uuid']+';loop=pure-compute-normal'
EVENT=re.compile(r' phase=(\w+) stage=([\w.-]+) op=([\w.:-]+) path=(\S+) rc=(-?\d+) errno=(\d+) value=(.*)$')

def checksums():
    out={};x=0x6d2b79f5
    for n in range(1,2000001):
        x=((x*1664525+1013904223)&0xffffffff)^n
        if n in (500000,1000000,1500000,2000000):out[n]=f'{x:08x}'
    return out
CHECKSUMS=checksums()

def decode(text,installed_full_sha256=None,fresh_boot_reference=None):
    result=dict(status='UNKNOWN_STOP',control_accepted=False,compute_cap_published=False,
                control_uuid=I['control_uuid'],prefix_ids_reused=True,conditional_progress=[],
                physical_binding=dict(exact_full_p10=installed_full_sha256==P['full_p10']['sha256'],
                                      fresh_stock_boot_reference=fresh_boot_reference),
                timer_observations={},
                limit='2M bounded arithmetic progress only; no sustained 1.5s, timer pass, clock rootcause, system stability or Android17 claim. Missing marker is UNKNOWN publication, never CPU lockup or publication-failure proof.')
    try:
        if installed_full_sha256 is not None and installed_full_sha256!=P['full_p10']['sha256']:
            raise ValueError('wrong full-p10 binding')
        entry='ASUS49-ENTRY run='+I['kernel_uuid']+' stage=stext-preargs release='+RELEASE
        if text.count(entry)!=1 or text.count(I['mode'])!=1 or text.index(entry)>=text.index(I['mode']):
            raise ValueError('missing/duplicate/out-of-order reused entry/mode; prefixes alone never fresh identity')
        if re.search(r'A49(?:CAP1|SW2|WD1|PS1|PM1|DL1) uuid=',text):raise ValueError('unexpected old hot protocol')
        events=[];alarm=[];mode_pos=next(n for n,l in enumerate(text.splitlines()) if I['mode'] in l)
        for pos,line in enumerate(text.splitlines()):
            if 'ASUS49-SYSCLOCK run=' not in line:continue
            if I['helper_prefix'] not in line:raise ValueError('mixed helper prefix identity')
            tail=line.split(I['helper_prefix'],1)[1]
            if tail==I['helper_alarm_suffix']:alarm.append(pos);continue
            m=EVENT.fullmatch(tail)
            if not m:raise ValueError('malformed helper record')
            phase,stage,op,path,rc,err,value=m.groups()
            events.append(dict(pos=pos,phase=phase,stage=stage,op=op,path=path,rc=int(rc),errno=int(err),value=value))
        if len(alarm)>1:raise ValueError('duplicate one-shot alarm')
        def one(phase,stage,op,path,required=True):
            rows=[e for e in events if (e['phase'],e['stage'],e['op'],e['path'])==(phase,stage,op,path)]
            if len(rows)>1 or (required and not rows):raise ValueError('missing/duplicate '+op+':'+stage)
            return rows[0] if rows else None
        def ok(e):return e and e['rc']==e['errno']==0
        pid=one('setup','actual','getpid','-');release=one('setup','actual','uname.release','-')
        if (pid['rc'],pid['errno'],pid['value'])!=(1,0,'PID1-required') or not ok(release) or release['value']!=RELEASE:
            raise ValueError('PID1/release mismatch')
        path=one('observe','actual','clock.path','CLOCK_MONOTONIC')
        if not ok(path) or path['value']!=CLOCK_PATH:raise ValueError('fresh control UUID/loop value absent or stale; prefix alone rejected')
        ab=one('observe','begin','alarm.nominal1s.timer-dependent','-');ae=one('observe','end','alarm.nominal1s.timer-dependent','-')
        ib=one('observe','begin','clock_gettime','loop.initial')
        if not mode_pos<pid['pos']<release['pos']<ab['pos']<ae['pos']<path['pos']<ib['pos']:
            raise ValueError('setup/observe order mismatch')
        flag=one('finish','actual','alarm.final-flag','SIGALRM',False)
        result['timer_observations']=dict(alarm_marker_observed=bool(alarm),alarm_final_flag=flag,
            irq_records=[e for e in events if e['phase'] in ('before','after') and e['op'] in ('interrupts.arch_timer','interrupts.snapshot')],
            interpretation='Independent observations; absence of alarm does not mean timer failure; no elapsed-time measurement.')
        initial=one('observe','end','clock_gettime','loop.initial',False)
        original=one('observe','actual','sched.original','pid0',False)
        invalid=[e for e in events if e['stage']=='invalid']
        if invalid:
            result.update(status='CONTROL_INVALID',detail='Explicit refusal; no compute acceptance.',invalid_records=invalid);return result
        forbidden=[e for e in events if e['op'].startswith(('sched.boost','sched.restore')) or e['op']=='clock_gettime.final']
        if forbidden:raise ValueError('forbidden FIFO/restore/final-clock records for this control')
        if not initial or not original:raise ValueError('missing initial clock or original scheduler; publication UNKNOWN')
        if not ok(initial) or not re.fullmatch(r'\d+\.\d{9}',initial['value']):raise ValueError('initial direct clock did not publish success')
        if not ok(original) or original['value']!='getparam_rc=0 getparam_errno=0 priority=0':raise ValueError('normal original policy/priority unverified')
        if not ib['pos']<initial['pos']<original['pos']:raise ValueError('scheduler query before initial clock success')
        progress=[e for e in events if e['op']=='runnable.progress'];last=original['pos'];milestones=[]
        loop=one('observe','complete','runnable.loop','CLOCK_MONOTONIC',False)
        for e in progress:
            m=re.fullmatch(r'iterations=(500000|1000000|1500000) checksum=([0-9a-f]{8})',e['value'])
            if not m or not ok(e) or (e['phase'],e['stage'],e['path'])!=('observe','actual','CLOCK_MONOTONIC'):
                raise ValueError('bad arithmetic progress record')
            n=int(m[1]);milestones.append(n)
            if m[2]!=CHECKSUMS[n] or e['pos']<=last or (loop and e['pos']>=loop['pos']):raise ValueError('wrong checksum/progress order')
            last=e['pos']
        if len(progress)>3 or milestones!=sorted(set(milestones)):raise ValueError('excess/duplicate progress')
        result['conditional_progress']=progress
        if not loop:raise ValueError('completion marker absent; publication UNKNOWN')
        expected='control='+I['control_uuid']+' iterations=2000000 checksum='+CHECKSUMS[2000000]+' reason=compute-cap'
        if not ok(loop) or loop['value']!=expected or loop['pos']<=last:raise ValueError('stale/malformed completion or checksum/order mismatch')
        if any(e['pos']<loop['pos'] for e in events if e['phase'] in ('after','finish')):raise ValueError('after/finish precedes compute completion')
        result['compute_cap_published']=True
        bound=installed_full_sha256==P['full_p10']['sha256'] and bool(fresh_boot_reference and fresh_boot_reference.strip())
        result.update(status='BOUNDED_NORMAL_COMPUTE_PROGRESS' if bound else 'PUBLISHED_COMPUTE_CAP_PENDING_PHYSICAL_BINDING',
                      control_accepted=bound,iterations=2000000,checksum=CHECKSUMS[2000000],
                      physical_attestation='Parent-supplied exact readback hash and fresh stock boot reference; decoder does not independently observe device.')
        return result
    except ValueError as exc:
        result.update(status='UNKNOWN_STOP',control_accepted=False,detail=str(exc));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('console',type=Path)
    p.add_argument('--installed-full-sha256');p.add_argument('--fresh-stock-boot-reference')
    a=p.parse_args();print(json.dumps(decode(a.console.read_text(errors='replace'),a.installed_full_sha256,a.fresh_stock_boot_reference),indent=2))
