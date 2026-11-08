"""One behavior comparison of the actual before/after predicate bodies."""
from pathlib import Path
import hashlib, json, re, subprocess
R = Path(__file__).resolve().parents[1]
D = 'drivers/misc/mediatek/video/mt8163/dispsys/'
def function(s):
    return re.search(r'static int disp_is_intr_enable\(.*?\n\}', s, re.S).group()
enum = re.search(r'enum DISP_REG_ENUM \{.*?\n\};', (R/'source/base'/D/'ddp_hal.h').read_text(), re.S).group()
before = function((R/'source/base'/D/'ddp_drv.c').read_text()).replace('disp_is_intr_enable', 'before')
after = function((R/'source'/D/'ddp_drv.c').read_text()).replace('disp_is_intr_enable', 'after')
c = '#include <assert.h>\n#include <stdio.h>\n' + enum + '''
static unsigned int dispsys_irq[DISP_REG_NUM];
static int logs;
static const char *ddp_get_reg_module_name(int i) { return i == 2 ? "RDMA0" : "RDMA1"; }
#define pr_notice(...) do { logs++; printf(__VA_ARGS__); } while (0)
''' + before + '\n' + after + '''
int main(void) {
 for (int i=0; i<DISP_REG_NUM; i++) {
  dispsys_irq[i]=100+i;
  int old=before(i), fresh=after(i);
  assert(fresh == ((i==DISP_REG_RDMA0 || i==DISP_REG_RDMA1) ? 0 : old));
  if (i==DISP_REG_RDMA0 || i==DISP_REG_RDMA1) assert(old==1);
 }
 assert(logs==2);
 assert(after(-1)==before(-1));
 assert(after(DISP_REG_NUM)==before(DISP_REG_NUM));
 return 0;
}
'''
(R/'qa/predicate.c').write_text(c)
q=subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(R/'qa/predicate.c'),'-o',str(R/'qa/predicate')],capture_output=True,text=True)
(R/'qa/predicate-compile.log').write_text(q.stdout+q.stderr);q.check_returncode()
q=subprocess.run([str(R/'qa/predicate')],capture_output=True,text=True)
(R/'qa/predicate.stdout').write_text(q.stdout);q.check_returncode()
(R/'evidence/predicate-check.json').write_text(json.dumps(dict(status='PASS',actual_before_after_function_bodies=True,only_changed_returns=['DISP_REG_RDMA0','DISP_REG_RDMA1'],all_other_enum_values_and_default_preserved=True,log_calls_per_RDMA_match=1,synthetic_IRQs_not_runtime_receipts=True,source_sha256=hashlib.sha256(c.encode()).hexdigest()),indent=2)+'\n')
print(q.stdout)
