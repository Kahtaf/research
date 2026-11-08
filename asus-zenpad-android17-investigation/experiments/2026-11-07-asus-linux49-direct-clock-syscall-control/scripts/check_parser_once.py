"""One host check of the exact production number/timer_line bodies with GIC-0."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];E=R/'evidence'
assert not (E/'parser-check.json').exists(),'One parser check only'
s=(R/'source/init.c').read_text();body=s[s.index('static int number('):s.index('static void timer_snapshot(')]
prefix='''#include <stdio.h>
#include <string.h>
static unsigned emitted;
static char result[512];
static void event(const char*a,const char*b,const char*c,long d,int e,const char*v){(void)a;(void)b;(void)c;(void)d;(void)e;emitted++;snprintf(result,sizeof(result),"%s",v);}
'''
tail='''int main(void){
 char line[]="  2: 171 GIC-0 30 Level arch_timer";
 if(timer_line(line)||emitted!=1||strcmp(result,"irq=2 counts=171 cpus=1 controller=GIC-0 hwirq=30 trigger=Level name=arch_timer"))return 1;
 puts(result);return 0;
}
'''
(E/'parser-harness.c').write_text(prefix+body+tail)
cmd=['cc','-Os','-Wall','-Wextra','-o',str(E/'parser-harness'),str(E/'parser-harness.c')]
q=subprocess.run(cmd,capture_output=True,text=True)
(E/'parser-compile.log').write_text(q.stdout+q.stderr);q.check_returncode()
p=subprocess.run([str(E/'parser-harness')],capture_output=True,text=True)
(E/'parser-run.log').write_text(p.stdout+p.stderr)
rec=dict(production_bodies_sha256=hashlib.sha256(body.encode()).hexdigest(),compile_exit=q.returncode,run_exit=p.returncode,cases=1,input='2: 171 GIC-0 30 Level arch_timer',output=p.stdout.strip(),raw_proc_input=False)
(E/'parser-check.json').write_text(json.dumps(rec,indent=2)+'\n');p.check_returncode()
print(json.dumps(rec,indent=2))
