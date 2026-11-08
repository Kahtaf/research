"""Decode only fixed ASCII capture rows from a parent-provided complete console.
No device access. Raw addresses remain in the parent's local output.
"""
from pathlib import Path
import argparse,json,re
FIELDS=['update','slot','kind','enter','exit','entries','complete','parent','seq_enter','seq_last','stage','raw','function','pc','aux','cpu_enter','cpu_exit']
ROW=384;HEADER=192;ROWS=15;SIZE=HEADER+ROWS*ROW

def decode(data,uuid):
 tag=('A49CAP1 uuid='+uuid+' rows=15 row=384 fields=17 header=192').encode()
 starts=[m.start() for m in re.finditer(re.escape(tag),data)]
 if len(starts)!=1:return dict(status='UNKNOWN',reason='capture identity absent or ambiguous',records=[])
 area=data[starts[0]:starts[0]+SIZE]
 if len(area)!=SIZE or area[127]!=10 or area[191]!=10 or area[128:138] not in (b'A49FAULT 0',b'A49FAULT 1'):
  return dict(status='UNKNOWN',reason='incomplete capture area/header',records=[])
 fault=area[137]!=ord('0');records=[];invalid=[]
 for row in range(ROWS):
  line=area[HEADER+row*ROW:HEADER+(row+1)*ROW]
  expected=('VA49C %02x '%row).encode()
  good=line.startswith(expected) and line[-1:]==b'\n'
  values=[]
  for i in range(len(FIELDS)):
   chunk=line[9+i*17:25+i*17]
   good=good and re.fullmatch(b'[0-9a-f]{16}',chunk) is not None and line[25+i*17:26+i*17]==b' '
   values.append(int(chunk,16) if re.fullmatch(b'[0-9a-f]{16}',chunk) else 0)
  good=good and line[352:368]==line[9:25] and values[0]>0
  good=good and values[1:3]==[row//3,row%3]
  padding=bytearray(line);padding[0:9]=b' '*9
  for i in range(17):padding[9+i*17:25+i*17]=b' '*16
  padding[352:368]=b' '*16;padding[-1]=32
  good=good and all(v==32 for v in padding)
  if not good:invalid.append(row);continue
  d=dict(zip(FIELDS,values));d['row']=row;d['context']='PID1-task' if d['slot']==0 else 'timer-IRQ-CPU'+str(d['slot']-1)
  d['operation']=['ktime_get_ts64','arch_counter_read','timer.event_handler'][d['kind']]
  # Match token's origin, operation and nonzero serial, independent of current CPU.
  def token_ok(t):return t>>8!=0 and t&15==d['slot'] and (t>>4)&15==d['kind']
  if d['entries']==0:
   d['assessment']='UNKNOWN: no captured entry; absence is not nonexecution'
  elif not token_ok(d['enter']) or d['complete']>d['entries'] or (d['exit'] and not token_ok(d['exit'])):
   d['assessment']='UNKNOWN: inconsistent operation token/count';invalid.append(row)
  elif d['enter']==d['exit'] and d['entries']==d['complete'] and d['stage']==4:
   d['assessment']='completed captured operation'
  elif d['enter']!=d['exit'] and d['entries']==d['complete']+1 and d['stage'] in (1,2,3):
   d['assessment']='entered without a matching captured exit; boundary only, no causal/stagnation proof'
  else:
   d['assessment']='UNKNOWN: inconsistent completion state';invalid.append(row)
  d['raw_valid_for_current_entry']=d['kind']==1 and d['enter']==d['exit'] and d['entries']>0
  d['raw_belongs_to_exit_token']=hex(d['exit'])
  d['callback_pc_available']=bool(d['aux']>>32) if d['kind']==2 else None
  records.append(d)
 # A torn row can conceal a completed exit or later entry. Fail closed globally.
 unknown=fault or bool(invalid)
 for d in records:
  if unknown:d['assessment']='UNKNOWN: global loss latch or incomplete/inconsistent row'
 # A counter belongs only to its recorded parent, never to a merely nearby entry.
 by={(d['slot'],d['kind']):d for d in records}
 for d in records:
  if d['kind']==1 and d['entries']:
   p=by.get((d['slot'],2 if d['slot'] else 0))
   d['matches_latest_parent']=bool(p and d['parent']==p['enter'])
 return dict(status='UNKNOWN' if unknown else 'COMPLETE_CAPTURE_ROWS',uuid=uuid,loss_latched=fault,invalid_rows=invalid,records=records,
  limitation='A valid unfinished entry identifies the last captured boundary only. Completion counts are execution counts, not timestamps. No snapshot alone proves duration, stagnation, or root cause.')

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('console',type=Path);p.add_argument('--uuid',required=True);a=p.parse_args()
 print(json.dumps(decode(a.console.read_bytes(),a.uuid),indent=2))
