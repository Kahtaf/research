"""Offline decoder; parent independently attests full installed p10 and fresh stock boot."""
from pathlib import Path
import argparse,json,re
R=Path(__file__).resolve().parents[1]
I=json.loads((R/'evidence/identity.json').read_text())
P=json.loads((R/'evidence/packaging-receipt.json').read_text())
RELEASE='4.9.337-asus-p00a-experimental-g717bb3c9e13c-dirty'
CLOCK_PATH='kernel-syscall:syscall(SYS_clock_gettime);vDSO-bypassed;control='+I['control_uuid']+';loop=pure-compute-normal-final-only'
EVENT=re.compile(r' phase=(\w+) stage=([\w.-]+) op=([\w.:-]+) path=(\S+) rc=(-?\d+) errno=(\d+) value=(.*)$')

# Exact final checksum; independently re-evaluated against the delivered loop in focused checks.
CHECKSUM = 'e4ca7075'

def irq_snapshot(events, phase):
    rows=[e for e in events if e['phase']==phase and e['op']=='interrupts.arch_timer']
    end=[e for e in events if e['phase']==phase and e['op']=='interrupts.snapshot' and e['stage']=='complete']
    parsed=[]
    for e in rows:
        m=re.fullmatch(r'irq=(\d+) counts=(\d+(?:,\d+)*) cpus=(\d+) controller=(GIC|GICv2|GIC-0) hwirq=(\d+) trigger=(absent|Level|Edge) name=arch_timer',e['value'])
        if not m or e['stage']!='actual' or e['path']!='/proc/interrupts' or e['rc'] or e['errno']:
            return dict(status='UNKNOWN',detail='malformed arch_timer record',records=rows)
        counts=list(map(int,m[2].split(',')))
        if len(counts)!=int(m[3]) or not 1<=len(counts)<=16:return dict(status='UNKNOWN',detail='CPU count mismatch',records=rows)
        parsed.append(dict(irq=int(m[1]),hwirq=int(m[5]),counts=counts))
    complete=False
    if len(end)==1:
        e=end[0];m=re.fullmatch(r'bytes=(\d+) read_calls=(\d+) lines=(\d+) arch_found=(\d+) emitted=(\d+) parse_or_read_errors=(\d+) eof=([01])',e['value'])
        complete=bool(m and e['path']=='/proc/interrupts' and e['errno']==0 and
                      0<=int(m[1])<=32768 and 0<int(m[2])<=8 and 0<=int(m[3])<=256 and
                      int(m[4])==int(m[5])==e['rc']==len(rows) and 0<=len(rows)<=8 and
                      m[6]=='0' and m[7]=='1' and all(r['pos']<e['pos'] for r in rows) and
                      len({r['hwirq'] for r in parsed})==len(parsed) and
                      not any(r['stage'] in ('bounded','error') and r['op'].startswith('interrupts.') for r in events if r['phase']==phase))
    return dict(status='COMPLETE' if complete else 'UNKNOWN',records=rows,parsed=parsed,completion=end)


def decode(text,installed_full_sha256=None,fresh_boot_reference=None,complete_console_reference=None):
    result=dict(status='UNKNOWN_STOP',control_accepted=False,compute_cap_published=False,
                control_uuid=I['control_uuid'],prefix_ids_reused=True,normal_policy_verified=False,normal_policy='UNKNOWN',
                compute_completion='UNKNOWN',complete_after_irq='UNKNOWN',completion_write_return='UNKNOWN',
                physical_binding=dict(exact_full_p10=installed_full_sha256==P['full_p10']['sha256'],
                                      fresh_stock_boot_reference=fresh_boot_reference,complete_console_reference=complete_console_reference),
                timer_observations={},
                limit='Positive 2M+complete afterIRQ proves this compute instance and completion write returned; no prior-500k-write causality, elapsed time, rootcause, stability, timer pass or Android17 readiness. Missing afterIRQ spans write tail, proc open/read/processing/publication, not uniquely printk. Absence is UNKNOWN.')
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
        if any(e['op']=='runnable.progress' for e in events):raise ValueError('intermediate progress belongs to prior variant; final-only control refused')
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
        result['timer_observations']=dict(alarm_marker_observed=bool(alarm),alarm_status='OBSERVED' if alarm else 'UNKNOWN',alarm_final_flag=flag,irq_growth='UNKNOWN',
            irq_records=[e for e in events if e['phase'] in ('before','after') and e['op'] in ('interrupts.arch_timer','interrupts.snapshot')],
            interpretation='Independent observations; absence of alarm does not mean timer failure; no elapsed-time measurement.')
        initial=one('observe','end','clock_gettime','loop.initial',False)
        original=one('observe','actual','sched.original','pid0',False)
        invalid=[e for e in events if e['stage']=='invalid']
        if invalid:
            result.update(status='CONTROL_INVALID',normal_policy='REFUSED',detail='Explicit refusal; no compute acceptance.',invalid_records=invalid);return result
        forbidden=[e for e in events if e['op'].startswith(('sched.boost','sched.restore')) or e['op']=='clock_gettime.final']
        if forbidden:raise ValueError('forbidden FIFO/restore/final-clock records for this control')
        if not initial or not original:raise ValueError('missing initial clock or original scheduler; publication UNKNOWN')
        if not ok(initial) or not re.fullmatch(r'\d+\.\d{9}',initial['value']):raise ValueError('initial direct clock did not publish success')
        if not ok(original) or original['value']!='getparam_rc=0 getparam_errno=0 priority=0':raise ValueError('normal original policy/priority unverified')
        if not ib['pos']<initial['pos']<original['pos']:raise ValueError('scheduler query before initial clock success')
        result['normal_policy_verified']=True
        result['normal_policy']='VERIFIED_SCHED_OTHER_PRIORITY0'
        last=original['pos']
        loop=one('observe','complete','runnable.loop','CLOCK_MONOTONIC',False)
        if not loop:raise ValueError('completion marker absent; publication UNKNOWN')
        expected='control='+I['control_uuid']+' iterations=2000000 checksum='+CHECKSUM+' reason=compute-cap'
        if not ok(loop) or loop['value']!=expected or loop['pos']<=last:raise ValueError('stale/malformed completion or checksum/order mismatch')
        if any(e['pos']<loop['pos'] for e in events if e['phase'] in ('after','finish')):raise ValueError('after/finish precedes compute completion')
        result.update(compute_cap_published=True,compute_completion='PUBLISHED',iterations=2000000,checksum=CHECKSUM)
        before=irq_snapshot(events,'before');after=irq_snapshot(events,'after')
        result['timer_observations'].update(before_irq=before,after_irq=after,irq_growth='UNKNOWN')
        if before['status']==after['status']=='COMPLETE':
            bp={r['hwirq']:r['counts'] for r in before['parsed']};ap={r['hwirq']:r['counts'] for r in after['parsed']}
            if bp and bp.keys()==ap.keys() and all(len(bp[k])==len(ap[k]) and all(y>=x for x,y in zip(bp[k],ap[k])) for k in bp):
                deltas={str(k):[y-x for x,y in zip(bp[k],ap[k])] for k in bp}
                result['timer_observations'].update(irq_growth='GROWTH_OBSERVED' if any(any(v) for v in deltas.values()) else 'NO_GROWTH_OBSERVED',irq_deltas=deltas)
        complete_after=after['status']=='COMPLETE'
        if complete_after:result.update(complete_after_irq='PUBLISHED',completion_write_return='PROVEN_BY_SAME_THREAD_AFTER_IRQ')
        bound=installed_full_sha256==P['full_p10']['sha256'] and all(v and v.strip() for v in [fresh_boot_reference,complete_console_reference])
        result.update(status=('COMPUTE_AND_AFTER_IRQ_PUBLISHED' if complete_after else 'COMPUTE_PUBLISHED_AFTER_IRQ_UNKNOWN') if bound else 'PUBLISHED_COMPUTE_CAP_PENDING_PHYSICAL_BINDING',
                      control_accepted=bound,
                      physical_attestation='Parent supplies exact readback hash, fresh stock boot and complete single-console horizon references; decoder does not independently observe device or reference contents.')
        return result
    except ValueError as exc:
        result.update(status='UNKNOWN_STOP',control_accepted=False,detail=str(exc));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('console',type=Path)
    p.add_argument('--installed-full-sha256');p.add_argument('--fresh-stock-boot-reference');p.add_argument('--complete-console-reference')
    a=p.parse_args();print(json.dumps(decode(a.console.read_text(errors='replace'),a.installed_full_sha256,a.fresh_stock_boot_reference,a.complete_console_reference),indent=2))
