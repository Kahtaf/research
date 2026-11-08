from pathlib import Path
import hashlib,json,re,subprocess
R=Path(__file__).resolve().parents[1];S=R/'source';E=R/'evidence'
p=S/'drivers/soc/mediatek/mtk-pmic-wrap.c';s=p.read_text();base=(S/'base/drivers/soc/mediatek/mtk-pmic-wrap.c').read_text()
def function(text,name):
 m=re.search(r'static (?:inline )?(?:int|bool|void) '+name+r'\(',text);a=m.start();b=text.index('{',a);depth=1;i=b+1
 while depth:
  depth+=(text[i]=='{')-(text[i]=='}');i+=1
 return text[a:i]
old=function(base,'pwrap_timeout_ns');new=function(s,'pwrap_timeout_ns')
assert new.replace(',\n\t\tunsigned long long *last_clock','').replace('\n\t*last_clock = cur_time;','')==old
for n in ['pwrap_read','pwrap_write','pwrap_leave_fsm_vldclr','pwrap_is_fsm_idle','pwrap_is_fsm_vldclr']:assert function(s,n)==function(base,n)
harness='''#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <errno.h>
typedef uint32_t u32;
struct pmic_wrapper { int unused; };
static unsigned clocks, reads, records;
static int scenario;
static unsigned long long captured_start,captured_last;
static u32 captured_iterations;
static bool captured_ready;
#define PWRAP_POLL_BUDGET 16777216U
static unsigned long long sched_clock(void) {
 unsigned n=clocks++;
 if (!n) return 100;
 if (scenario==1) return 10000100ULL;
 if (scenario==3) return 99;
 return 100;
}
static bool readiness(struct pmic_wrapper *p) {
 ++reads;
 return (scenario==0 && reads==3) ||
        (scenario==4 && reads==PWRAP_POLL_BUDGET+1U);
}
static void pwrap_backstop_record(unsigned long long start,unsigned long long last,
 u32 iterations,bool (*fp)(struct pmic_wrapper *),bool ready) {
 ++records;captured_start=start;captured_last=last;captured_iterations=iterations;captured_ready=ready;
}
'''+function(s,'pwrap_timeout_ns')+'\n'+function(s,'pwrap_wait_for_state')+'''
int main(void) {
 struct pmic_wrapper wrp;
 for (scenario=0;scenario<5;++scenario) {
  clocks=reads=records=0;
  int rc=pwrap_wait_for_state(&wrp,readiness);
  if (scenario==0) {assert(rc==0 && clocks==4 && reads==3 && !records);}
  if (scenario==1) {assert(rc==-ETIMEDOUT && clocks==2 && reads==1 && !records);}
  if (scenario>=2) {
   assert(rc==(scenario==4?0:-ETIMEDOUT));
   assert(clocks==PWRAP_POLL_BUDGET+1U && reads==PWRAP_POLL_BUDGET+1U && records==1);
   assert(captured_start==100 && captured_last==(scenario==3?99:100));
   assert(captured_iterations==PWRAP_POLL_BUDGET && captured_ready==(scenario==4));
  }
  printf("case=%d rc=%d clocks=%u readiness=%u records=%u PASS\\n",scenario,rc,clocks,reads,records);
 }
}
'''
(E/'production-loop-harness.c').write_text(harness)
cmd=['cc','-O2','-std=c99','-Wall','-Wextra','-Wno-unused-parameter',str(E/'production-loop-harness.c'),'-o',str(E/'production-loop-harness')]
p=subprocess.run(cmd,text=True,capture_output=True);(E/'loop-compile.stderr').write_text(p.stderr);p.check_returncode()
p=subprocess.run([str(E/'production-loop-harness')],text=True,capture_output=True,timeout=30);(E/'production-loop-results.txt').write_text(p.stdout+p.stderr);p.check_returncode()
result=dict(passed=True,production_functions_extracted_verbatim=['pwrap_timeout_ns','pwrap_wait_for_state'],actual_budget=16777216,cases=['ready on third read','deadline first, final not ready','equal clock exhausts','regressing below original caller start exhausts','budget final readiness succeeds'],original_timeout_computations_identical=True,original_read_write_recovery_bodies_identical=True,compiler_command=cmd,limits='Host mocked clock/readiness/record sink only; no kernel or physical elapsed-time assertion')
(E/'loop-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(p.stdout)
