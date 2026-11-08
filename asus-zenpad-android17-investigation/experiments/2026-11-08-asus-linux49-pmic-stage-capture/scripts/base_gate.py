from pathlib import Path
import json,hashlib,re,datetime,difflib
R=Path(__file__).resolve().parents[1];ref=R.parent/'2026-11-06-asus-linux49-probe-review/source/kernel';base=R/'source/base';p='drivers/misc/mediatek/power/mt8163/'
def function(s,name):
 m=re.search(r'\b'+name+r'\([^;{}]*\)\s*\{',s);assert m,name
 a=s.rfind('\n',0,m.start())+1;i=s.index('{',m.start());depth=1;j=i+1
 while depth:
  depth+=(s[j]=='{')-(s[j]=='}');j+=1
 return s[a:j]
checks={};diffs=[]
for n,funcs in [(p+'asus_p00a/pmic_battery.inc',['p00a_pmic_result','p00a_pmic_prepare_adc','asus_p00a_pmic_present','asus_p00a_pmic_adc']),(p+'asus_p00a/battery_diag.c',['p00a_measurement_get_property','asus_p00a_battery_get_property']),(p+'pmic_mt6323.c',['pmic_read_interface','pmic_read_interface_nolock','pmic_config_interface','pmic_config_interface_nolock'])]:
 a=(ref/n).read_text();b=(base/n).read_text();c={}
 for f in funcs:
  x,y=function(a,f),function(b,f);assert x==y,('STOP substantive reference function discrepancy; review before edit',n,f)
  c[f]=dict(reference_actual_C_byte_identical=True,sha256=hashlib.sha256(y.encode()).hexdigest())
 checks[n]=dict(reference_sha256=hashlib.sha256(a.encode()).hexdigest(),actual_sha256=hashlib.sha256(b.encode()).hexdigest(),whole_file_identical=a==b,functions=c)
 if a!=b:diffs.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='reference/'+n,tofile='base/'+n))
s=(base/(p+'pmic_mt6323.c')).read_text();assert '#include "asus_p00a/pmic_battery.inc"' in s and '#define ADC_COUNT_TIMEOUT    100' in s
for n,needle in [(p+'.pmic_mt6323.o.cmd','asus_p00a/pmic_battery.inc'),(p+'asus_p00a/.battery_diag.o.cmd','asus_p00a/battery_diag.c')]:assert needle in (base/'out-provenance'/n).read_text()
assert 'battery_diag.o' in (base/(p+'asus_p00a/Makefile')).read_text()
d=(R/'evidence/base-callflow.disasm').read_text()
for target in ['asus_p00a_pmic_present','asus_p00a_pmic_adc','asus_p00a_battery_get_property','battery_get_property','__pm_stay_awake','mutex_lock','_raw_spin_lock_irqsave','_raw_spin_unlock_irqrestore','regmap_read','pmic_config_interface_nolock','pmic_config_interface','__const_udelay','usleep_range','mutex_unlock','__pm_relax']:assert '<'+target+'>' in d,target
assert 'mov\tw0, #0x6' in d and 'mov\tw1, #0x5' in d
# prepare is inlined into ADC and read-nolock wrappers fold to regmap_read.
report=dict(status='PASS_BEFORE_EDIT_PROVENANCE_GATE',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),C_reference_comparison=checks,source_ELF_comparison='scoped linked call flow, never C-vs-ELF bytes',include_compile_provenance='actual out/source, compiler .cmd includes, built-in object and vmlinux link commands saved',linked_order='battery_get_property -> asus_p00a_battery_get_property (measurement helper inlined); enum66 -> present -> conditional adc(channel6,samples5); ADC awake -> mutex -> inlined prepare spin/read/config/unlock/sleep bounded100 -> VBUF -> trigger0/1 -> udelay300 -> read/sleep bounded100 per sample -> calculation -> mutex unlock -> relax -> int status',benign_differences=['static measurement and prepare helpers inlined; no standalone symbols','nolock read helpers inline to regmap_read, preserving existing error-only printk paths','compiler duplicates error unlock blocks and transforms bounded counter to countdown','config PREEMPT/SMP supports four CPUs but admitted runtime nr_cpu_ids must be one, as prior captures'],invalidating_path_discrepancy=False,root_cause_inferred=False)
(R/'evidence/base-provenance-gate.json').write_text(json.dumps(report,indent=2)+'\n');(R/'evidence/reference-base.diff').write_text(''.join(diffs));print(report['status'])
