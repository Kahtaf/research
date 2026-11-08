"""User-authorized exact obsolete reader cleanup; no process-name signalling."""
from pathlib import Path
import json,subprocess,sys,hashlib,datetime
import remote
R=Path(__file__).resolve().parents[1];needle=str(R.relative_to(R.parent)/'preparation/lfs_scope.py')
def ps(pid):return subprocess.check_output(['ps','-p',str(pid),'-o','pid=,ppid=,uid=,lstart=,command='],text=True).strip()
wrapper=ps(9069);ssh=ps(9071)
assert ' 26862 ' in ' '+wrapper+' ' and needle in wrapper and ' -B '+needle in wrapper
assert ' 9069 ' in ' '+ssh+' ' and 'android@IP_REDACTED python3 -B -' in ssh
assert 'Fri Nov  6 19:01:09 2026' in wrapper and 'Fri Nov  6 19:01:09 2026' in ssh
cwd=subprocess.check_output(['lsof','-a','-p','9069','-d','cwd','-Fn'],text=True)
assert str(R.parent) in cwd
tcp=subprocess.check_output(['lsof','-nP','-a','-p','9071','-iTCP'],text=True)
assert '192.168.68.79:50161->IP_REDACTED:22 (ESTABLISHED)' in tcp
proof=dict(exec_session=73148,local_wrapper=wrapper,local_ssh=ssh,local_cwd=cwd.strip(),local_tcp=tcp.strip(),script_sha256=hashlib.sha256((R/'preparation/lfs_scope.py').read_bytes()).hexdigest())
s=r'''
from pathlib import Path
import os,json,datetime,signal,time
R=Path('/srv/android/asus-reviewed-build-kit/r9');F=Path('/srv/android/asus-reviewed-build-kit/r9-fixtures')
expected_start=datetime.datetime(2026,11,7,0,1,9,tzinfo=datetime.timezone.utc).timestamp();uid=os.getuid();hz=os.sysconf('SC_CLK_TCK')
btime=int(next(l.split()[1] for l in Path('/proc/stat').read_text().splitlines() if l.startswith('btime ')))
this_connection=os.environ['SSH_CONNECTION'].split();graph_names=set(json.loads((F/'product-apk-graph-index.json').read_text())['graph_sha256'])
def identity(pid,detail=True):
 p=Path('/proc')/str(pid);st=p.stat();stat=(p/'stat').read_text().split(') ',1)[1].split();argv=[v.decode() for v in (p/'cmdline').read_bytes().split(b'\0') if v]
 connection=next((v.split(b'=',1)[1].decode() for v in (p/'environ').read_bytes().split(b'\0') if v.startswith(b'SSH_CONNECTION=')),None)
 cwd=os.readlink(p/'cwd');fds=[]
 for fd in (p/'fd').iterdir():
  try:target=os.readlink(fd)
  except FileNotFoundError:continue
  if target.startswith('/srv/android/lineage24/') and target.removeprefix('/srv/android/lineage24/') in graph_names:fds.append(dict(fd=int(fd.name),target=target,inode=fd.stat().st_ino))
 pp=int(stat[1]);parent=Path('/proc')/str(pp)
 try:parent_info=dict(pid=pp,uid=parent.stat().st_uid,comm=(parent/'comm').read_text().strip(),cmdline=(parent/'cmdline').read_bytes().replace(b'\0',b' ').decode().strip())
 except (FileNotFoundError,PermissionError):parent_info=dict(pid=pp,unreadable=True)
 return dict(pid=pid,uid=st.st_uid,state=stat[0],ppid=pp,start_ticks=int(stat[19]),started_utc=datetime.datetime.fromtimestamp(btime+int(stat[19])/hz,datetime.timezone.utc).isoformat(),argv=argv,cwd=cwd,ssh_connection=connection,ninja_fds=fds,parent=parent_info)
candidates=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  if p.stat().st_uid!=uid or (p/'comm').read_text().strip()!='python3':continue
  stat=(p/'stat').read_text().split(') ',1)[1].split();started=btime+int(stat[19])/hz
  if abs(started-expected_start)>5:continue
  row=identity(int(p.name));conn=(row['ssh_connection'] or '').split()
  if len(conn)!=4 or conn[0]!=this_connection[0] or conn[1]!='50161' or conn[3]!='22':continue
  if len(row['argv'])!=3 or Path(row['argv'][0]).name!='python3' or row['argv'][1:]!=['-B','-']:continue
  if row['cwd']!='/home/android' or not row['ninja_fds']:continue
  if row['parent'].get('comm')!='sshd' or 'android@notty' not in row['parent'].get('cmdline',''):continue
  candidates.append(row)
 except (FileNotFoundError,ProcessLookupError,PermissionError):continue
r=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),authorization='User narrow exception: only obsolete execsession73148 lfs_scope.py reader and dedicated transport',local_identity=LOCAL,probe_uid=uid,candidates=candidates,signals=[],native_or_other_worker_touched=False,milestone_unchanged=True)
if len(candidates)!=1:
 r.update(outcome='NOT_SIGNALLED_OWNERSHIP_NOT_UNIQUE',uncertainty='Require one exact UID/start/argv/cwd/parent/SSH-client-port plus graph-FD match')
else:
 before=candidates[0];fresh=identity(before['pid']);assert fresh==before,'Identity changed before TERM'
 pid=before['pid'];os.kill(pid,signal.SIGTERM);r['signals'].append(dict(pid=pid,signal='TERM',identity=before))
 time.sleep(1)
 try:
  after=identity(pid)
  if after['state']=='Z':r.update(outcome='TERMINATED_ZOMBIE_AWAITING_REAP',after=after)
  elif after==before:
   os.kill(pid,signal.SIGKILL);r['signals'].append(dict(pid=pid,signal='KILL',identity=after));time.sleep(1)
   try:r.update(outcome='SIGNALLED_KILL_RECHECK',after=identity(pid))
   except (FileNotFoundError,ProcessLookupError):r.update(outcome='TERMINATED_AFTER_KILL',after=None)
  else:r.update(outcome='TERM_SENT_NO_KILL_IDENTITY_CHANGED',after=after,uncertainty='No KILL after identity drift')
 except (FileNotFoundError,ProcessLookupError):r.update(outcome='TERMINATED_AFTER_TERM',after=None)
with (R/'evidence/obsolete-reader-cleanup.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))
'''
s='LOCAL='+repr(proof)+'\n'+s
r=remote.run(s);(R/'evidence/obsolete-reader-cleanup.json').write_text(r);print(r)
