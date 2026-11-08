"""Tiny controls using actual extracted writers with deterministic host-only primitives."""
from pathlib import Path
import ast,json,subprocess,re
import decode_pmic as d
R=Path(__file__).resolve().parents[1];E=R/'evidence';T=E/'host-controls';T.mkdir(exist_ok=True)
prior=R.parent/'2026-11-07-asus-linux49-power-supply-phase-capture'
tree=ast.parse((prior/'scripts/check_encoding.py').read_text())
pre=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='pre' for t in n.targets))
s=(R/'source/arch/arm64/kernel/asus_retained_trace.c').read_text();hexcode=s[s.index('static void cap_hex('):s.index('\n/* The latch')];code=s[s.index('/* Independent scheduler capture:'):s.index('static void __init cap_init(')]
asm='asm volatile("isb; mrs %0, cntvct_el0" : "=r" (raw));';assert code.count(asm)==4;code=code.replace(asm,'raw = ++ticks;')
interface=(prior/'source/ps-interface.inc').read_text().split('#ifdef')[0]+(R/'source/pmic-interface.inc').read_text().split('#ifdef')[0]
linked=json.loads((E/'linked-capture.json').read_text());fn=int(linked['symbols']['power_supply_changed_work']['address'],16);callback=int(linked['symbols']['battery_get_property']['address'],16);callers=linked['pmic_callers']
main=r'''
#define PSY 0xffffffc012340000ULL
#define WORK (PSY+0x2e0)
static void selectpid(int pid){
 struct task_struct prev=task;task.pid=pid;task.prio=120;task.policy=0;task.flags=PF_WQ_WORKER;
 memset(task.comm,0,16);memcpy(task.comm,pid==119?"kworker/0:3":"kworker/0:1",11);
 fake_irq=1;pc=2;asus_capture_switch(&prev,0,0,0,3);pc=0;fake_irq=0;
}
static void step(struct asus_pmic_capture *c,int code,int sample,int poll,u32 status){
 int oldirq=fake_irq;unsigned int oldpc=pc;
 asus_capture_pmic_step(c,code,sample,poll,status);
 if(fake_irq!=oldirq||pc!=oldpc||pm_lock)exit(81);
}
int main(int argc,char **argv){
 static char area[SW_SIZE+WD_SIZE+PS_SIZE+PM_SIZE] __attribute__((aligned(64)));
 struct asus_ps_capture body,property;struct asus_pmic_capture p,a,b,n;
 int k,s;const u32 none=0x80000000U;
 sw_init(area);wd_init(area+SW_SIZE);ps_init(area+SW_SIZE+WD_SIZE);pm_init(area+SW_SIZE+WD_SIZE+PS_SIZE);
 sw_area=area;wd_area=area+SW_SIZE;ps_area=area+SW_SIZE+WD_SIZE;pm_area=area+SW_SIZE+WD_SIZE+PS_SIZE;task.pid=1;
 selectpid(119);asus_capture_work_enter(FUNCTION,WORK);
 asus_capture_ps_begin(&body,1,WORK,PSY,"battery",0,1,0,NULL);
 for(k=2;k<=12;k++)asus_capture_ps_step(&body,k,k==3?1:0,(k==7||k==11)?0:U64_MAX);
 asus_capture_ps_begin(&property,40,0,PSY,"battery",CALLBACK,66,0,NULL);
 asus_capture_pmic_begin(&p,NULL,1,0,0,PRESENT_CALLER);
 step(&p,2,-1,-1,none);step(&p,3,-1,-1,none);step(&p,4,-1,-1,none);
 if(!strcmp(argv[1],"present_pending"))goto done;
 step(&p,5,-1,-1,0);step(&p,9,-1,-1,0);
 asus_capture_pmic_begin(&a,NULL,20,6,5,ADC_CALLER);
 for(k=21;k<=30;k++){if(k==22||k==25)continue;step(&a,k,-1,-1,none);}
 asus_capture_pmic_begin(&b,&a,60,0,0,PREPARE_CALLER);
 step(&b,61,-1,0,none);fake_irq=1;pc=1;step(&b,62,-1,0,none);step(&b,63,-1,0,none);
 if(!strcmp(argv[1],"prepare_pending")){fake_irq=0;pc=0;goto done;}
 step(&b,64,-1,0,0);step(&b,69,-1,0,0);fake_irq=0;pc=0;step(&b,70,-1,0,0);step(&b,72,-1,0,0);step(&b,79,-1,0,0);
 step(&a,31,-1,-1,0);step(&a,32,-1,-1,none);step(&a,33,-1,-1,0);
 for(s=0;s<5;s++){
  step(&a,34,s,-1,none);step(&a,35,s,-1,0);step(&a,36,s,-1,none);step(&a,37,s,-1,0);step(&a,38,s,-1,none);
  if(s==0&&!strcmp(argv[1],"nested")){
   asus_capture_pmic_begin(&n,NULL,20,0,0,ADC_CALLER);step(&n,22,-1,-1,(u32)-22);step(&n,59,-1,-1,(u32)-22);
  }
  if(s==0&&!strcmp(argv[1],"interleave")){
   selectpid(42);asus_capture_pmic_begin(&n,NULL,1,0,0,PRESENT_CALLER);step(&n,2,-1,-1,none);step(&n,7,-1,-1,(u32)-61);step(&n,9,-1,-1,(u32)-61);selectpid(119);
  }
  if(s==0&&!strcmp(argv[1],"adc_pending"))goto done;
  step(&a,39,s,-1,none);step(&a,40,s,0,none);
  if(s==0&&!strcmp(argv[1],"nested"))goto done;
  step(&a,41,s,0,0);step(&a,42,s,0,none);step(&a,47,s,0,none);
 }
 step(&a,48,5,0,0);step(&a,49,5,0,0);step(&a,50,5,0,0);step(&a,51,5,0,0);step(&a,59,5,0,0);
 if(!strcmp(argv[1],"unrelated")){
  asus_capture_pmic_begin(&n,NULL,1,0,0,0xffffff8008000100ULL);step(&n,2,-1,-1,none);step(&n,3,-1,-1,none);step(&n,4,-1,-1,none);
 }
 done:if(fake_irq||ps_lock||wd_lock||pm_lock)return 82;
 fwrite(area,1,sizeof(area),stdout);return 0;
}
'''
for key,value in [('FUNCTION',fn),('CALLBACK',callback),('PRESENT_CALLER',callers['present_returns'][0]),('ADC_CALLER',callers['voltage_adc_returns'][0]),('PREPARE_CALLER',(callers['voltage_adc_returns'][0] if callers['prepare_inlined'] else callers['prepare_returns'][0]))]:main=main.replace(key,hex(value)+'ULL')
(T/'writer.c').write_text(pre+interface+hexcode+code+main)
q=subprocess.run(['cc','-std=gnu11','-O2','-Wall','-Werror',str(T/'writer.c'),'-o',str(T/'writer')],capture_output=True,text=True);(T/'compile.txt').write_text(q.stdout+q.stderr);q.check_returncode()
# Retain exactly the old synthetic clock fixture encoder, with fresh UUID.
legacy_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='legacy')
legacy_code=ast.get_source_segment((prior/'scripts/check_encoding.py').read_text(),legacy_node)
ns={'d':d};exec(legacy_code,ns)
fixtures={};results={}
for mode in ['positive','present_pending','adc_pending','prepare_pending','nested','interleave','unrelated']:
 data=ns['legacy']()+subprocess.check_output([str(T/'writer'),mode]);fixtures[mode]=data;out=d.decode(data)
 assert out['status']=='FINITE_PMIC_CAPTURE',(mode,out.get('reason'),out['target'])
 if mode in ['interleave','unrelated']:assert out['target']['status']=='UNKNOWN',(mode,out['target'])
 else:
  assert out['target']['status']=='JOINED_FINITE_PMIC_STAGE',(mode,out['target'])
  expected={'positive':59,'present_pending':4,'adc_pending':38,'prepare_pending':63,'nested':40}[mode]
  assert out['target']['code']==expected,(mode,out['target'])
 if mode=='prepare_pending':assert out['snapshots']['prepare']['preempt']==1 and out['snapshots']['prepare']['context']==15
 if mode=='nested':assert len({r['token'] for r in out['records'] if r['code'] in (20,22,59,38,39,40)})==2
 if mode=='interleave':assert any(p['pid']==42 for p in out['pairs']) or out['snapshots']['present']['pid']==42
 (T/(mode+'.bin')).write_bytes(data);(T/(mode+'-decoded.json')).write_text(json.dumps(out,indent=2)+'\n');results[mode]=dict(status=out['status'],target=out['target'],bounds=out['bounds'])
for mode,pos in [('torn_tail',d.BASE+d.OFFSET+6*d.ROW+552),('torn_header',d.BASE+64+160),('guard',d.BASE+320),('sticky_busy',d.BASE+256+24),('wrap_slot',d.BASE+d.OFFSET+9)]:
 data=bytearray(fixtures['adc_pending']);data[pos]^=1;out=d.decode(data);assert out['status']=='UNKNOWN',(mode,out);results[mode]=dict(status=out['status'],reason=out.get('reason'))
(T/'writer').unlink()
(E/'encoding-controls.json').write_text(json.dumps(dict(status='PASS',actual_source_extracted=True,host_only_substitutions='Kernel publication primitives stubbed; four raw counter reads replaced by deterministic increments; no physical evidence',controls=results),indent=2)+'\n')
print(json.dumps({k:v['status'] for k,v in results.items()},indent=2))
