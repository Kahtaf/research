"""Offline sparse helper decoder. Input stays parent-private; no target access."""
from pathlib import Path
import argparse
import json
import re

R = Path(__file__).resolve().parents[1]
IDENTITY = json.loads((R / 'evidence/identity.json').read_text())
RELEASE = '4.9.337-asus-p00a-experimental-g717bb3c9e13c-dirty'
EVENT = re.compile(r' phase=(\w+) stage=([\w.-]+) op=([\w.:-]+) path=(\S+) rc=(-?\d+) errno=(\d+) value=(.*)$')
TIMER = re.compile(r'irq=(\d+) counts=(\d+(?:,\d+)*) cpus=(\d+) controller=(GIC|GICv2|GIC-0) hwirq=(\d+) trigger=(absent|Level|Edge) name=arch_timer$')
SNAPSHOT = re.compile(r'bytes=(\d+) read_calls=(\d+) lines=(\d+) arch_found=(\d+) emitted=(\d+) parse_or_read_errors=(\d+) eof=([01])$')
LOOP = re.compile(r'delta_ns=(-?\d+) iterations=(\d+) reason=(initial-clock-error|iteration-cap|clock-error|counter-regressed|counter-target) alarm_flag=([01]) clock_error=(\d+) counter_interval_not_wallclock=1$')


def stamp(value, final=False):
    m = re.fullmatch(r'(\d+)\.(\d{9})' + (r' sample-valid=1' if final else ''), value)
    if not m:
        raise ValueError('malformed or invalid clock sample')
    return int(m[1]) * 1000000000 + int(m[2])


def decode_loop(text):
    result = dict(status='UNKNOWN_STOP', physical_admission='parent must independently verify full p10 and fresh stock boot',
                  old_six_protocols='deliberately absent; never admitted', loop=None, irqs={}, alarm_marker=False,
                  limit='Positive supports load/timing sensitivity, not exclusive cause or Android17 readiness. Missing final does not exonerate instrumentation.')
    try:
        entry = 'ASUS49-ENTRY run=' + IDENTITY['run_uuid'] + ' stage=stext-preargs release=' + RELEASE
        if text.count(entry) != 1 or text.count(IDENTITY['mode']) != 1:
            raise ValueError('missing/duplicate fresh entry or exact compile-mode UUID')
        if text.index(entry) >= text.index(IDENTITY['mode']):
            raise ValueError('mode precedes entry')
        if re.search(r'A49(?:CAP1|SW2|WD1|PS1|PM1|DL1) uuid=', text):
            raise ValueError('old hot area inside supplied console horizon')
        prefix = IDENTITY['helper_prefix']
        mode_line = next(i for i, line in enumerate(text.splitlines()) if IDENTITY['mode'] in line)
        events, alarm_positions = [], []
        for pos, line in enumerate(text.splitlines()):
            if prefix not in line:
                continue
            tail = line.split(prefix, 1)[1]
            if tail == IDENTITY['helper_alarm_suffix']:
                alarm_positions.append(pos)
                continue
            m = EVENT.fullmatch(tail)
            if not m:
                raise ValueError('malformed helper record')
            p, s, o, a, rc, err, v = m.groups()
            events.append(dict(phase=p, stage=s, op=o, path=a, rc=int(rc), errno=int(err), value=v, pos=pos))
        def one(phase, stage, op, path, required=True):
            rows = [e for e in events if (e['phase'], e['stage'], e['op'], e['path']) == (phase, stage, op, path)]
            if len(rows) > 1 or (required and not rows):
                raise ValueError('missing/duplicate ' + op + ':' + stage)
            return rows[0] if rows else None
        pid = one('setup', 'actual', 'getpid', '-')
        uname = one('setup', 'actual', 'uname.release', '-')
        if pid['pos'] <= mode_line or len(alarm_positions) > 1:
            raise ValueError('helper predates mode or duplicate one-shot alarm')
        if (pid['rc'], pid['errno'], pid['value']) != (1, 0, 'PID1-required') or uname['rc'] or uname['errno'] or uname['value'] != RELEASE:
            raise ValueError('PID1/release mismatch')
        begin = one('observe', 'actual', 'clock.path', 'CLOCK_MONOTONIC')
        if begin['value'] != 'kernel-syscall:syscall(SYS_clock_gettime);vDSO-bypassed' or begin['rc'] or begin['errno']:
            raise ValueError('unexpected actual clock path')
        ab = one('observe', 'begin', 'alarm.nominal1s.timer-dependent', '-')
        ae = one('observe', 'end', 'alarm.nominal1s.timer-dependent', '-')
        ib = one('observe', 'begin', 'clock_gettime', 'loop.initial')
        initial = one('observe', 'end', 'clock_gettime', 'loop.initial', False)
        if not (pid['pos'] < uname['pos'] < ab['pos'] < ae['pos'] < begin['pos'] < ib['pos']):
            raise ValueError('helper phase order mismatch')
        result['alarm_marker'] = bool(alarm_positions)
        result['begin_and_initial_begin'] = True
        for phase in ['before', 'after']:
            rows = [e for e in events if e['phase'] == phase and e['op'] == 'interrupts.arch_timer']
            snap = one(phase, 'complete', 'interrupts.snapshot', '/proc/interrupts', False)
            counts = {}
            for e in rows:
                m = TIMER.fullmatch(e['value'])
                if not m or e['stage'] != 'actual' or e['path'] != '/proc/interrupts' or e['rc'] or e['errno']:
                    raise ValueError('invalid actual IRQ row')
                irq, cs, cpus, chip, hwirq, trigger = m.groups()
                cs = [int(c) for c in cs.split(',')]
                key = ':'.join([irq, chip, hwirq, trigger])
                if key in counts or int(cpus) != len(cs) or len(cs) != 1:
                    raise ValueError('duplicate or unexpected CPU IRQ row')
                counts[key] = cs
            valid = False
            if snap:
                m = SNAPSHOT.fullmatch(snap['value'])
                valid = bool(m and not snap['errno'] and snap['rc'] == len(rows) and rows and
                             int(m[4]) == int(m[5]) == len(rows) and int(m[6]) == 0 and int(m[7]) == 1 and
                             all(e['pos'] < snap['pos'] for e in rows))
                if phase == 'before' and (not rows or not uname['pos'] < rows[0]['pos'] <= snap['pos'] < ab['pos']):
                    valid = False
            result['irqs'][phase] = dict(counts=counts, snapshot_complete=valid)
        before, after = result['irqs']['before'], result['irqs']['after']
        result['irqs']['growth'] = bool(before['snapshot_complete'] and after['snapshot_complete'] and
            before['counts'].keys() == after['counts'].keys() and
            all(b >= a for k, cs in before['counts'].items() for a, b in zip(cs, after['counts'][k])) and
            any(b > a for k, cs in before['counts'].items() for a, b in zip(cs, after['counts'][k])))
        final = one('observe', 'actual', 'clock_gettime.final', 'CLOCK_MONOTONIC', False)
        loop = one('observe', 'complete', 'runnable.loop', 'CLOCK_MONOTONIC', False)
        if not initial or not final or not loop:
            result['detail'] = 'Unresolved publication/environment: missing initial end, final, or loop completion.'
            return result
        m = LOOP.fullmatch(loop['value'])
        if not m:
            raise ValueError('malformed runnable.loop')
        delta, iterations, reason, flag, error = m.groups()
        delta, iterations, flag, error = map(int, [delta, iterations, flag, error])
        result['loop'] = dict(delta_ns=delta, iterations=iterations, reason=reason, alarm_flag=flag, clock_error=error,
                              initial_rc=initial['rc'], final_rc=final['rc'], loop_rc=loop['rc'])
        if not (ib['pos'] < initial['pos'] < final['pos'] < loop['pos']) or not 0 <= iterations <= 2000000:
            raise ValueError('invalid loop order or iteration count')
        if reason in ['counter-target', 'iteration-cap']:
            if any(e['rc'] or e['errno'] for e in [initial, final, loop]) or error:
                raise ValueError('successful reason with error')
            if stamp(final['value'], True) - stamp(initial['value']) != delta:
                raise ValueError('delta does not match actual samples')
            if reason == 'counter-target' and (delta < 1500000000 or iterations < 1):
                raise ValueError('counter target not reached')
            if reason == 'iteration-cap' and (iterations != 2000000 or not 0 <= delta < 1500000000):
                raise ValueError('inconsistent iteration cap')
            if reason == 'iteration-cap':
                result['status'] = 'VALID_PROGRESS_ITERATION_CAP_NOT_FULL_PASS'
            elif (flag or alarm_positions) and result['irqs']['growth']:
                # Require after snapshot publication after the actual loop result.
                after_snap = one('after', 'complete', 'interrupts.snapshot', '/proc/interrupts')
                if after_snap['pos'] <= loop['pos']:
                    raise ValueError('after IRQ snapshot precedes loop completion')
                result['status'] = 'OBSERVED_COUNTER_TARGET_ALARM_AND_IRQ_PROGRESS'
            else:
                result['status'] = 'VALID_LOOP_TARGET_INCOMPLETE_ALARM_OR_IRQ_EVIDENCE'
        else:
            result['status'] = 'ACTUAL_LOOP_COMPLETION_WITH_ERROR_OR_REGRESSION_STOP'
        return result
    except ValueError as e:
        result['status'] = 'UNKNOWN_STOP'
        result['detail'] = str(e)
        return result



def decode(text):
    result = decode_loop(text)
    result.update(control_accepted=False, scheduling={}, conditional_progress=[],
                  limit='Verified FIFO execution changes work ordering; no scheduling cause, calibrated walltime, timer-deadness, storage-under-RT or fullOS claim. Missing output remains UNKNOWN.')
    try:
        if not result.get('begin_and_initial_begin'):return result
        events=[]
        for pos,line in enumerate(text.splitlines()):
            if IDENTITY['helper_prefix'] not in line:continue
            m=EVENT.fullmatch(line.split(IDENTITY['helper_prefix'],1)[1])
            if m:
                phase,stage,op,path,rc,err,value=m.groups()
                events.append(dict(pos=pos,phase=phase,stage=stage,op=op,path=path,rc=int(rc),errno=int(err),value=value))
        def one(op,stage='actual',required=True):
            rows=[e for e in events if (e['phase'],e['stage'],e['op'],e['path'])==('observe',stage,op,'pid0')]
            if len(rows)>1 or (required and not rows):raise ValueError('missing/duplicate '+op)
            return rows[0] if rows else None
        invalid=[e for e in events if e['phase']=='observe' and e['stage']=='invalid' and e['op']=='sched.control']
        result['scheduling']={op:one(op,required=False) for op in ['sched.original','sched.boost','sched.boost.observed','sched.restore','sched.restored']}
        if invalid:
            result.update(status='CONTROL_INVALID',detail='Explicit baseline/boost/restoration refusal; no clean acceptance.',invalid_records=invalid)
            return result
        def query(e,policy,priority):
            return bool(e and e['rc']==policy and e['errno']==0 and e['value']==f'getparam_rc=0 getparam_errno=0 priority={priority}')
        original,boost,observed,restore,restored=[result['scheduling'][op] for op in ['sched.original','sched.boost','sched.boost.observed','sched.restore','sched.restored']]
        initial_records=[e for e in events if e['phase']=='observe' and e['stage']=='end' and e['op']=='clock_gettime' and e['path']=='loop.initial']
        initial_ok=bool(len(initial_records)==1 and not initial_records[0]['rc'] and not initial_records[0]['errno'] and original and initial_records[0]['pos']<original['pos'])
        boost_ok=bool(initial_ok and query(original,0,0) and boost and boost['rc']==boost['errno']==0 and
                      boost['value']=='requested_policy=1 requested_priority=1' and query(observed,1,1) and
                      original['pos']<boost['pos']<observed['pos'])
        progress=[e for e in events if e['phase']=='observe' and e['op']=='runnable.progress']
        thresholds=[]
        for e in progress:
            m=re.fullmatch(r'iterations=(500000|1000000|1500000) delta_ns=(-?\d+)',e['value'])
            if not m or e['stage']!='actual' or e['path']!='CLOCK_MONOTONIC' or e['rc'] or e['errno']:raise ValueError('invalid progress record')
            thresholds.append(int(m[1]))
        if len(progress)>3 or thresholds!=sorted(set(thresholds)):raise ValueError('duplicate/out-of-order/excess progress')
        if boost_ok and all(observed['pos']<e['pos'] and (not restore or e['pos']<restore['pos']) for e in progress):
            result['conditional_progress']=progress
        accepted=one('sched.control','accepted',False)
        if not (boost_ok and restore and restore['rc']==restore['errno']==0 and
                restore['value']=='requested_policy=0 requested_priority=0' and query(restored,0,0) and
                accepted and accepted['rc']==accepted['errno']==0 and
                accepted['value']=='boost-and-restore-verified;loop-outcome-separate' and
                observed['pos']<restore['pos']<restored['pos']<accepted['pos']):
            result.update(status='UNKNOWN_SCHEDULING_COMPLETION',detail='Missing/failed/unverified boost or final restoration; progress is conditional publication only.')
            return result
        finals=[e for e in events if e['op']=='clock_gettime.final']
        after=[e for e in events if e['phase']=='after']
        initial=[e for e in events if e['phase']=='observe' and e['stage']=='end' and e['op']=='clock_gettime' and e['path']=='loop.initial']
        if len(initial)!=1 or initial[0]['rc'] or initial[0]['errno'] or not initial[0]['pos']<original['pos']:raise ValueError('scheduling baseline precedes successful initial clock')
        if not finals or accepted['pos']>=finals[0]['pos'] or any(e['pos']<=accepted['pos'] for e in after):raise ValueError('restoration acceptance must precede final/after routines')
        if result['status']=='UNKNOWN_STOP':return result
        result['control_accepted']=True
        if result['status'].startswith(('VALID_','OBSERVED_')):result['status']='FIFO_'+result['status']
        return result
    except ValueError as exc:
        result.update(status='UNKNOWN_STOP',control_accepted=False,detail=str(exc))
        return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('console', type=Path)
    args = p.parse_args()
    print(json.dumps(decode(args.console.read_text(errors='replace')), indent=2))
