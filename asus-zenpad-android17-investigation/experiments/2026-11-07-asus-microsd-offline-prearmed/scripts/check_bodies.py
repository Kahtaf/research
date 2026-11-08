from pathlib import Path
r = Path(__file__).resolve().parents[1]
s = (r/'source/rescue.c').read_text()
session = s[s.index('static int session(int c){'):s.index('static int serve(void){')]
assert session == (r/'inputs/reviewed-session.c').read_text()
assert (r/'source/recovery_phase.h').read_bytes() == (r/'inputs/reviewed-recovery_phase.h').read_bytes()
f = (r/'source/sd_frontend.c').read_text()
run = f[f.index('static int run(void){'):f.index('#ifndef SD_FRONTEND_LIBRARY')]
assert run.index('close(fd);fd=-1;') < run.index('preflight()') < run.index('begin_attempt(selection)') < run.index('fd=connect_daemon();',run.index('begin_attempt(selection)')) < run.index('status_bound(fd,0)') < run.index('recovery_readback(fd)') < run.index('RECOVERY_BASELINE') < run.index('write_role(fd,j)')
print('PASS exact accepted daemon session/header; production preflight-close, durable-attempt, reconnect, baseline-before-write ordering')
