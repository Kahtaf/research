"""Offline canonical cold watchdog facts plus an independent sparse liveness outcome.
Raw callers stay in the parent-private input; only a pinned genuine map yields names.
"""
from pathlib import Path
import argparse,bisect,gzip,hashlib,json,re
from decode_liveness import decode as decode_liveness
R=Path(__file__).resolve().parents[1]
I=json.loads((R/'evidence/identity.json').read_text())
H=re.compile(r'[0-9a-f]{8}')
CALLER=r'([0-9a-f]{16})'
PATTERNS={
 'probe':re.compile(r'event=probe route=mtk_wdt_probe caller='+CALLER),
 'error':re.compile(r'event=error site=(alloc|map|watchdog_register|reboot_notifier|restart_handler|pm_notifier|reset_controller) rc=(-?[1-9][0-9]*)'),
 'stop':re.compile(r'event=stop before=([0-9a-f]{8}) after=([0-9a-f]{8}) en_before=([01]) en_after=([01]) caller='+CALLER),
 'probe_done':re.compile(r'event=probe_done rc=0 req_mode=([0-9a-f]{8}) req_irq_en=([0-9a-f]{8})'),
 'restart':re.compile(r'event=restart route=mtk_reset_handler caller='+CALLER),
}
def load_map(path):
 data=path.read_bytes()
 if path.suffix=='.gz':data=gzip.decompress(data)
 pin=json.loads((R/'evidence/System.map-uncompressed.json').read_text())['uncompressed']
 if len(data)!=pin['bytes'] or hashlib.sha256(data).hexdigest()!=pin['sha256']:
  raise ValueError('map differs from this candidate genuine uncompressed pin')
 # Keep all addresses as range boundaries; only text symbols may name callers.
 rows=[]
 for line in data.decode().splitlines():
  a,t,n=line.split();rows.append((int(a,16),t,n))
 return sorted(rows)
def symbol(caller,rows):
 if rows is None:return dict(caller_symbol='UNSYMBOLIZED_PARENT_PRIVATE',caller_route='UNKNOWN')
 # ARM64 LR is the return PC. Subtract one instruction to name its callsite.
 pc=int(caller,16)-4;starts=[r[0] for r in rows];p=bisect.bisect_right(starts,pc)-1
 if p<0 or p+1>=len(rows) or rows[p][1].lower()!='t' or not rows[p][0]<=pc<rows[p+1][0]:
  return dict(caller_symbol='UNRESOLVED_PARENT_PRIVATE',caller_route='UNKNOWN')
 a,_,n=rows[p]
 return dict(caller_symbol=n+'+0x'+format(pc-a,'x'),caller_route=n)
def decode_watchdog(text,rows=None):
 out=dict(status='UNKNOWN_IDENTITY',probe_entry='RECORD_ABSENT',early_errors=[],stop=[],request_snapshot=[],restart=[],
          source_contract='source-pins.json + compiled entry/mode identity; no runtime hardware acceptance claim',
          limit='Absence never proves not called. EN is one readback instant. Caller is an immediate entry route, not original requester or preloader producer. Sink may drop, tear, or perturb records.')
 # Full entry literal is the compiled identity; watchdog admission does not require PID1.
 tag=(R/'source/arch/arm64/kernel/asus_entry_tag.h').read_text().splitlines()[0]
 entry=json.loads(tag.split(' ',2)[2]).rstrip('\n')
 if text.count(entry)!=1 or text.count(I['mode'])!=1 or text.index(entry)>=text.index(I['mode']):return out
 mode_end=text.index(I['mode'])+len(I['mode']);records=[]
 for line in text.splitlines():
  if I['watchdog_prefix'] not in line:continue
  if not line.startswith(I['watchdog_prefix']) or text.index(line)<mode_end:
   out['status']='UNKNOWN_MALFORMED_RECORD';return out
  tail=line[len(I['watchdog_prefix']):]
  matches=[(k,p.fullmatch(tail)) for k,p in PATTERNS.items() if p.fullmatch(tail)]
  if len(matches)!=1:
   out['status']='UNKNOWN_MALFORMED_RECORD';return out
  event,m=matches[0];records.append((event,m))
 # Commit facts only after every fresh-prefix record is canonical.
 out['status']='RECORDS_OBSERVED' if records else 'RECORD_ABSENT'
 for event,m in records:
  if event=='probe':
   out['probe_entry']='RECORDED';out.setdefault('probe_callers',[]).append(symbol(m[1],rows))
  elif event=='error':out['early_errors'].append(dict(status='RECORDED_ERROR',site=m[1],rc=int(m[2]),fatal_to_probe=m[1] in ['alloc','map','watchdog_register']))
  elif event=='stop':
   before,after=int(m[1],16),int(m[2],16)
   if (before&1,after&1)!=(int(m[3]),int(m[4])):
    return dict(status='UNKNOWN_MALFORMED_RECORD',detail='EN fields do not match MODE values; no watchdog facts admitted')
   caller=symbol(m[5],rows)
   out['stop'].append(dict(status='RECORDED_STOP_BEFORE_AFTER',mode_before='0x'+m[1],mode_after='0x'+m[2],en_before=bool(before&1),en_after=bool(after&1),actual_probe_route=caller['caller_route']=='mtk_wdt_probe',**caller))
  elif event=='probe_done':out['request_snapshot'].append(dict(status='RECORDED_REQUEST_SNAPSHOT_AND_PROBE_RETURN',probe_rc=0,req_mode='0x'+m[1],req_irq_en='0x'+m[2],register_offsets=dict(req_mode='0x30',req_irq_en='0x34')))
  elif event=='restart':out['restart'].append(dict(status='OBSERVED_RESTART_ENTRY',entry_route='mtk_reset_handler',**symbol(m[1],rows)))
 out['record_states']=dict(probe=out['probe_entry'],errors='RECORDED_ERROR' if out['early_errors'] else 'RECORD_ABSENT',stop='RECORDED_STOP_BEFORE_AFTER' if out['stop'] else 'RECORD_ABSENT',request_snapshot='RECORDED_REQUEST_SNAPSHOT' if out['request_snapshot'] else 'RECORD_ABSENT',restart='OBSERVED_RESTART_ENTRY' if out['restart'] else 'RECORD_ABSENT')
 return out
def decode(text,rows=None):
 return dict(liveness=decode_liveness(text),watchdog=decode_watchdog(text,rows),physical_admission='Parent independently binds complete installed p10 readback and fresh stock boot; this parser supplies neither.')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('console',type=Path);p.add_argument('--system-map',type=Path)
 a=p.parse_args();rows=load_map(a.system_map) if a.system_map else None
 print(json.dumps(decode(a.console.read_text(errors='replace'),rows),indent=2))
