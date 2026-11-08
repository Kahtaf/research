"""One joined synthetic fixture and bounded corruption/refusal mutations."""
from pathlib import Path
import ast,json,subprocess,hashlib
import decode_delay as d
R=Path(__file__).resolve().parents[1];T=R/'evidence/controls'
prior=R.parent/'2026-11-08-asus-linux49-pmic-stage-capture';p0=R.parent/'2026-11-07-asus-linux49-power-supply-phase-capture/scripts/check_encoding.py';oldtree=ast.parse(p0.read_text());tree=ast.parse((prior/'scripts/check_encoding.py').read_text())
pre=next(ast.literal_eval(n.value) for n in oldtree.body if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='pre' for t in n.targets))
main=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='main' for t in n.targets))
linked=json.loads((R/'evidence/linked-capture.json').read_text());symbols=linked['symbols'];routes=linked['delay_callers'];callers=linked['pmic_callers']
pre+='\n#define asus_p00a_battery_get_property ((void*)'+symbols['asus_p00a_battery_get_property']['address']+'UL)\n#define asus_p00a_pmic_adc ((void*)'+symbols['asus_p00a_pmic_adc']['address']+'UL)\n#define __const_udelay ((void*)'+hex(routes['const_symbol'])+'UL)\n'
s=(R/'source/arch/arm64/kernel/asus_retained_trace.c').read_text();hexcode=s[s.index('static void cap_hex('):s.index('\n/* The latch')];code=s[s.index('/* Independent scheduler capture:'):s.index('static void __init cap_init(')]
code=code.replace('asm volatile("isb; mrs %0, cntvct_el0" : "=r" (raw));','raw = ++ticks;')
code=code.replace('pm_record(c, code, sample, poll, status, false,\n   (unsigned long)__builtin_return_address(0));','pm_record(c, code, sample, poll, status, false, '+hex(routes['pre_return'])+'UL);').replace('(unsigned long)__builtin_return_address(0)',hex(routes['calc_site'])+'UL')
interface=(R.parent/'2026-11-07-asus-linux49-power-supply-phase-capture/source/ps-interface.inc').read_text().split('#ifdef')[0]+(prior/'source/pmic-interface.inc').read_text().split('#ifdef')[0]
main=main.replace('SW_SIZE+WD_SIZE+PS_SIZE+PM_SIZE','SW_SIZE+WD_SIZE+PS_SIZE+PM_SIZE+DL_SIZE')
main=main.replace('pm_init(area+SW_SIZE+WD_SIZE+PS_SIZE);','pm_init(area+SW_SIZE+WD_SIZE+PS_SIZE);dl_init(area+SW_SIZE+WD_SIZE+PS_SIZE+PM_SIZE);')
main=main.replace('pm_area=area+SW_SIZE+WD_SIZE+PS_SIZE;','pm_area=area+SW_SIZE+WD_SIZE+PS_SIZE;dl_area=area+SW_SIZE+WD_SIZE+PS_SIZE+PM_SIZE;')
main=main.replace('int k,s;','int k,s;u64 g;')
needle='step(&a,38,s,-1,none);'
add=r'''
  asus_capture_delay_calc(1288500,52000,250,16750500000000UL,3900,CONST_RETURN);
  g=asus_capture_delay_begin(3900,DELAY_RETURN);
  if(g!=dl_gen||!g)exit(83);
  asus_capture_delay_point(g,0,0,0,3900);asus_capture_delay_point(g,1,0,100,3900);
  asus_capture_delay_point(g,2,1,100,3900);
  if(s==3){asus_capture_delay_point(g,3,256,110,3900);goto done;}
  asus_capture_delay_point(g,6,2,4000,3900);
'''
main=main.replace(needle,needle+add)
for key,value in [('FUNCTION',int(symbols['power_supply_changed_work']['address'],16)),('CALLBACK',int(symbols['battery_get_property']['address'],16)),('PRESENT_CALLER',callers['present_returns'][0]),('ADC_CALLER',callers['voltage_adc_returns'][0]),('PREPARE_CALLER',callers['prepare_returns'][0]),('CONST_RETURN',routes['const_return']),('DELAY_RETURN',routes['delay_return'])]:main=main.replace(key,hex(value)+'UL')
# Use a fresh synthetic PID, deliberately different from historical PID119.
main=main.replace('119','73')
(T/'joined-writer.c').write_text(pre+interface+hexcode+code+main)
q=subprocess.run(['cc','-std=gnu11','-O2','-Wall','-Werror',str(T/'joined-writer.c'),'-o',str(T/'joined-writer')],capture_output=True,text=True);(T/'joined-compile.txt').write_text(q.stdout+q.stderr);q.check_returncode()
node=next(n for n in oldtree.body if isinstance(n,ast.FunctionDef) and n.name=='legacy');ns={'d':__import__('decode_pmic')};exec(ast.get_source_segment(p0.read_text(),node),ns)
data=ns['legacy']()+subprocess.check_output([str(T/'joined-writer'),'delay_pending']);out=d.decode(data)
(T/'joined-decoded.json').write_text(json.dumps(out,indent=2)+'\n');assert out['status']=='FINITE_DELAY_CAPTURE',out.get('reason')
assert out['target']['pid']==73 and out['target']['generation']==4 and out['target']['sample']==3 and out['target']['stages']==[0,1,2,3]
(T/'joined.bin').write_bytes(data);results={'joined_current_sample':dict(status=out['status'],target=out['target'])}
base=data.index(('A49DL1 uuid='+d.UUID).encode())
for name,offset in [('guard',320),('loss',256+24),('generation_tail',64+160),('stale_slot_generation',1152+2*192+9),('PMIC_token_join',384+9+17),('unadvertised_slot',1152+4*192+9),('calculation_product',960+9+4*17)]:
 bad=bytearray(data);bad[base+offset]^=1;got=d.decode(bad);assert got['status']=='UNKNOWN',(name,got);results[name]=dict(status=got['status'],reason=got.get('reason'))
# Validate actual fixed writer's overlap and wrap loss through the new parser.
for name in ['overlap','overflow']:
 bad=data[:base]+(T/(name+'.bin')).read_bytes()
 got=d.decode(bad);assert got['status']=='UNKNOWN';results[name]=dict(status=got['status'],reason=got.get('reason'))
(T/'joined-writer').unlink()
(R/'evidence/decoder-controls.json').write_text(json.dumps(dict(status='PASS',actual_writers=True,synthetic=True,fixture_sha256=hashlib.sha256(data).hexdigest(),host_substitutions='four preexisting raw samples deterministic, kernel publication/cache/context stubs, static code-address and return-site operands from actual linked candidate; no target data',controls=results),indent=2)+'\n');print(json.dumps({k:v['status'] for k,v in results.items()},indent=2))
