"""Small synthetic emitter/filter/parser controls; no target input."""
from pathlib import Path
import importlib.util,json,re,subprocess,sys
R=Path(__file__).resolve().parents[1];S=R/'source';i=json.loads((R/'evidence/identity.json').read_text())
s=(S/'arch/arm64/kernel/asus_retained_trace.c').read_text();h=(S/'include/linux/asus_retained_trace.h').read_text()
enum=h[h.index('enum asus_sparse_wdt_event {'):h.index('};',h.index('enum asus_sparse_wdt_event {'))+2]
f=s[s.index('static bool sparse_prefix('):s.index('/* Keep the first text;')]
e=(S/'emitter.inc').read_text()
code='#include <stdbool.h>\n#include <stdio.h>\n#include <stdint.h>\n#include <string.h>\n#include <assert.h>\ntypedef uint32_t u32;\n#define noinline\n#define notrace\n#define scnprintf snprintf\n'+(S/'arch/arm64/kernel/asus_entry_tag.h').read_text()+enum+'\n'+f+'''
static unsigned int writes;
void asus_retained_trace_write(const char *text, unsigned int len) {
 assert(len < 288 && len == strlen(text)); assert(sparse_admit(text,len));
 ++writes; puts(text);
}
'''+e+'''
int main(void) {
 unsigned int n;
 for(n=0;n<=ASUS_WDT_RESTART;n++) asus_sparse_wdt_record(n,n==ASUS_WDT_PROBE_DONE ? 0 : -12,1,0,0x1234UL);
 assert(writes==11); asus_sparse_wdt_record(999,0,0,0,0); assert(writes==11);
 assert(sparse_admit(ASUS_SPARSE_MODE,sizeof(ASUS_SPARSE_MODE)-1));
 assert(!sparse_admit("ordinary printk",15));
 assert(!sparse_admit("ASUS49-WDT run=e6799dac-43cb-4222-8ab6-5119397460b6 event=probe",64));
 assert(!sparse_admit(ASUS_SPARSE_WDT_PREFIX "\\tbad",sizeof(ASUS_SPARSE_WDT_PREFIX)+3));
 assert(!sparse_admit(ASUS_SPARSE_WDT_PREFIX,0));
 return 0;
}
'''
qa=R/'evidence';(qa/'synthetic-controls.c').write_text(code)
q=subprocess.run(['cc','-Wall','-Wextra','-Werror',str(qa/'synthetic-controls.c'),'-o',str(qa/'synthetic-controls')],capture_output=True,text=True)
(qa/'controls-compile.stderr').write_text(q.stderr);q.check_returncode()
q=subprocess.run([str(qa/'synthetic-controls')],capture_output=True,text=True);q.check_returncode();(qa/'synthetic-emitter.txt').write_text(q.stdout)
sys.path.insert(0,str(R/'scripts'));import decode_sparse as d
entry=json.loads((S/'arch/arm64/kernel/asus_entry_tag.h').read_text().splitlines()[0].split(' ',2)[2]).rstrip('\n')
base=entry+'\n'+i['mode']+'\n';prefix=i['watchdog_prefix']
text=base+prefix+'event=probe route=mtk_wdt_probe caller=0000000000001234\n'+prefix+'event=stop before=00000001 after=00000000 en_before=1 en_after=0 caller=0000000000001234\n'+prefix+'event=probe_done rc=0 req_mode=00040001 req_irq_en=00000000\n'
a=d.decode(text);assert a['liveness']['status']=='UNKNOWN_STOP' and a['watchdog']['probe_entry']=='RECORDED' and len(a['watchdog']['stop'])==len(a['watchdog']['request_snapshot'])==1
assert '0000000000001234' not in json.dumps(a)
assert d.decode(base)['watchdog']['status']=='RECORD_ABSENT'
assert d.decode(text.replace(i['mode'],'wrong mode'))['watchdog']['status']=='UNKNOWN_IDENTITY'
assert d.decode(text+'\n'+prefix+'event=stop torn')['watchdog']['status']=='UNKNOWN_MALFORMED_RECORD'
assert d.decode(text.replace('en_before=1','en_before=0'))['watchdog']['status']=='UNKNOWN_MALFORMED_RECORD'
x=d.decode(base+prefix+'event=error site=map rc=-12\n')['watchdog'];assert x['early_errors'][0]['fatal_to_probe'] and x['probe_entry']=='RECORD_ABSENT'
x=d.decode(base+prefix+'event=restart route=mtk_reset_handler caller=0000000000001234\n')['watchdog'];assert x['restart'][0]['status']=='OBSERVED_RESTART_ENTRY'
assert d.decode(base+q.stdout)['watchdog']['status']=='RECORDS_OBSERVED'
# Reverse only observational additions, then compare all driver tokens, including policies.
new=(S/'drivers/watchdog/mtk_wdt.c').read_text();old=(S/'base/drivers/watchdog/mtk_wdt.c').read_text()
z=re.sub(r'\tasus_sparse_wdt_record\([^;]+;\n','',new)
z=z.replace('#include <linux/asus_retained_trace.h>\n','').replace('u32 reg, before, after;','u32 reg;').replace('\tbefore = reg;\n','').replace('\tafter = readl(wdt_base + WDT_MODE);\n','').replace('\tu32 req_mode, req_irq_en;\n','')
for line in ['\treq_mode = ioread32(mtk_wdt->wdt_base + WDT_REQ_MODE);\n','\treq_irq_en = ioread32(mtk_wdt->wdt_base + WDT_REQ_IRQ_EN);\n']:z=z.replace(line,'')
def tokens(t):
 t=re.sub(r'/\*.*?\*/','',t,flags=re.S)
 return re.sub(r'[\s{}]','',t)
assert tokens(z)==tokens(old),'original driver statements/branches/order changed'
result=dict(status='PASS_TINY_SYNTHETIC_CONTROLS',emitter_valid_codes=11,emitter_max_synthetic_bytes=max(map(len,q.stdout.splitlines())),invalid_event_no_write=True,filter_rejects_ordinary_stale_control=True,parser_pre_PID1_facts_independent_of_UNKNOWN_liveness=True,parser_absence_error_stop_snapshot_restart_distinct=True,parser_malformed_stale_and_EN_mismatch_controls=True,raw_callers_withheld=True,original_driver_tokens_after_observation_removal_identical=True,physical=False)
(qa/'local-controls.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
