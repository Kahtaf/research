"""Identity-based owned lineage checks; no process-group operations."""
from pathlib import Path
import os
import signal

def snapshot():
    rows = {}
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            if proc.stat().st_uid != os.getuid(): continue
            stat = (proc/'stat').read_text().split(') ',1)[1].split()
            rows[int(proc.name)] = {'pid':int(proc.name),'state':stat[0],'ppid':int(stat[1]),'start_ticks':int(stat[19]),'comm':(proc/'comm').read_text().strip()}
        except (FileNotFoundError,ProcessLookupError,PermissionError): pass
    return rows

def related(prefix, aosp=None):
    rows = snapshot(); roots = set(); names = {'soong_ui','soong_build','ckati','ninja','ninja-build','siso'}
    for pid,row in rows.items():
        if pid == os.getpid(): continue
        proc=Path('/proc')/str(pid)
        try:
            args=(proc/'cmdline').read_bytes()
            try: cwd=os.readlink(proc/'cwd')
            except OSError: cwd=''
            reasons=[]
            if str(prefix).encode() in args or cwd == str(prefix): reasons.append('owned-prefix-command-or-cwd')
            for fd in (proc/'fd').iterdir():
                try: target=os.readlink(fd)
                except OSError: continue
                if target.startswith(str(prefix)+'/logs/'): reasons.append('owned-log-descriptor'); break
            if aosp and row['comm'] in names and (cwd == str(aosp) or cwd.startswith(str(aosp)+'/')): reasons.append('same-source-tree-native-engine')
            if reasons: row['reasons']=reasons; roots.add(pid)
        except (FileNotFoundError,ProcessLookupError,PermissionError): continue
    selected=set(roots)
    while True:
        more={pid for pid,row in rows.items() if row['ppid'] in selected}
        if more <= selected: break
        selected |= more
    return [rows[pid] for pid in sorted(selected)]

def stop_owned_handles(prefix, child):
    """At the eight-hour bound, signal exact owned pidfds, never a process group."""
    rows=related(prefix); handles=[]
    for row in rows:
        if row['state']=='Z': continue
        try:
            fd=os.pidfd_open(row['pid'])
            current=snapshot().get(row['pid'])
            if not current or current['start_ticks']!=row['start_ticks']: os.close(fd); continue
            handles.append((row,fd))
        except ProcessLookupError: pass
    for row,fd in reversed(handles):
        try: signal.pidfd_send_signal(fd,signal.SIGKILL)
        except ProcessLookupError: pass
        finally: os.close(fd)
    child.wait(timeout=30)
    return [row for row,_ in handles]
