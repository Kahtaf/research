from pathlib import Path
import json,hashlib,difflib,re
from base_gate import function
R=Path(__file__).resolve().parents[1];i=json.loads((R/'evidence/identity.json').read_text());u=i['run_uuid'];old_u='431dfb9c-8b78-4c8c-bd74-cc556adcf8b0'
assert json.loads((R/'evidence/base-provenance-gate.json').read_text())['status']=='PASS_BEFORE_EDIT_PROVENANCE_GATE'
p='drivers/misc/mediatek/power/mt8163/asus_p00a/pmic_battery.inc';old=(R/'source/base'/p).read_text();s=old
# All hooks occupy standalone statements. Deleting hooks, the local declaration,
# and the prepare-only parent parameter restores the original token stream.
def hook(code,sample='-1',poll='-1',status='0x80000000U',indent='\t'):
 return f'{indent}asus_capture_pmic_step(&capture, {code}, {sample}, {poll}, {status});'
def retwrap(f,terminal,sample='-1',poll='-1'):
 # A brace scope adds no branch; return expressions remain evaluated once.
 return re.sub(r'(?m)^(\s*)return ([^;]+);',lambda m:m[1]+'{\n'+hook(terminal,sample,poll,m[2],m[1]+'\t')+'\n'+m[1]+'\treturn '+m[2]+';\n'+m[1]+'}',f)
def bracket(f,text,pre,post,sample='-1',poll='-1',status='ret'):
 assert f.count(text)==1,(pre,text)
 indent=re.match(r'\s*',text).group().replace('\n','')
 return f.replace(text,hook(pre,sample,poll,indent=indent)+'\n'+text+'\n'+hook(post,sample,poll,status,indent))
f=function(s,'p00a_pmic_prepare_adc');g=f.replace('(void)','(const struct asus_pmic_capture *parent)',1)
g=g.replace('\tint ret, poll;','\tint ret, poll = -1;\n\tstruct asus_pmic_capture capture;\n\n\tasus_capture_pmic_begin(&capture, parent, 60, 0, 0,\n\t\t(unsigned long)__builtin_return_address(0));')
g=bracket(g,'\t\tspin_lock_irqsave(&pmic_adc_lock, flags);',61,62,poll='poll',status='0x80000000U')
g=bracket(g,'\t\tret = p00a_pmic_result(pmic_read_interface_nolock(AUXADC_CON19,\n\t\t\t&delay, PMIC_RG_ADC_DECI_GDLY_MASK,\n\t\t\tPMIC_RG_ADC_DECI_GDLY_SHIFT));',63,64,poll='poll')
g=bracket(g,'\t\t\tret = p00a_pmic_result(pmic_read_interface_nolock(\n\t\t\t\tAUXADC_ADC19, &busy, 0x7fff, 1));',65,66,poll='poll')
a='\t\t\tif (!ret && !busy)\n\t\t\t\tret = p00a_pmic_result(pmic_config_interface_nolock(\n\t\t\t\t\tAUXADC_CON19, 0, PMIC_RG_ADC_DECI_GDLY_MASK,\n\t\t\t\t\tPMIC_RG_ADC_DECI_GDLY_SHIFT));'
z=a.replace('if (!ret && !busy)\n','if (!ret && !busy) {\n').replace('\t\t\t\tret =',hook(67,poll='poll',indent='\t\t\t\t')+'\n\t\t\t\tret =')+'\n'+hook(68,poll='poll',status='ret',indent='\t\t\t\t')+'\n\t\t\t}';assert a in g;g=g.replace(a,z)
g=bracket(g,'\t\tspin_unlock_irqrestore(&pmic_adc_lock, flags);',69,70,poll='poll');g=g.replace(hook(69,poll='poll',indent='\t\t'),hook(69,poll='poll',status='ret',indent='\t\t'))
g=g.replace('\t\tif (ret)\n\t\t\treturn ret;','\t\tif (ret) {\n'+hook(71,poll='poll',status='ret',indent='\t\t\t')+'\n\t\t\treturn ret;\n\t\t}')
g=g.replace('\t\tif (delay != 1)\n\t\t\treturn 0;','\t\tif (delay != 1) {\n'+hook(72,poll='poll',status='0',indent='\t\t\t')+'\n\t\t\treturn 0;\n\t\t}\n'+hook(73,poll='poll',indent='\t\t'))
g=bracket(g,'\t\tusleep_range(1000, 2000);',74,75,poll='poll',status='0x80000000U');g=g.replace('\treturn -ETIMEDOUT;',hook(76,poll='poll',status='-ETIMEDOUT')+'\n\treturn -ETIMEDOUT;');g=retwrap(g,79,poll='poll');s=s.replace(f,g)
f=function(s,'asus_p00a_pmic_present');g=f.replace('\tint ret;','\tint ret;\n\tstruct asus_pmic_capture capture;\n\n\tasus_capture_pmic_begin(&capture, NULL, 1, 0, 0,\n\t\t(unsigned long)__builtin_return_address(0));\n'+hook(2),1)
g=g.replace('\t\treturn -ENODATA;','\t{\n'+hook(7,status='-ENODATA',indent='\t\t')+'\n\t\treturn -ENODATA;\n\t}',1)
g=bracket(g,'\tret = p00a_pmic_result(pmic_read_interface(CHR_CON7, &value, 0xffff, 0));',4,5)
g=g.replace(hook(4),hook(3)+'\n'+hook(4),1)
a='\t\treturn -ENODATA;';idx=g.rfind(a);g=g[:idx]+g[idx:].replace(a,'\t{\n'+hook(6,status='-ENODATA',indent='\t\t')+'\n\t\treturn -ENODATA;\n\t}',1)
g=retwrap(g,9);s=s.replace(f,g)
f=function(s,'asus_p00a_pmic_adc');g=f.replace('\tint ret, sample, poll;','\tint ret, sample = -1, poll = -1;\n\tstruct asus_pmic_capture capture;\n\n\tasus_capture_pmic_begin(&capture, NULL, 20, channel, samples,\n\t\t(unsigned long)__builtin_return_address(0));',1)
g=g.replace('\t\treturn -EINVAL;','\t{\n'+hook(22,status='-EINVAL',indent='\t\t')+'\n\t\treturn -EINVAL;\n\t}\n'+hook(21)+'\n'+hook(23),1)
g=g.replace('\t\treturn -ENODATA;','\t{\n'+hook(25,status='-ENODATA',indent='\t\t')+'\n\t\treturn -ENODATA;\n\t}\n'+hook(24),1)
g=bracket(g,'\t__pm_stay_awake(pmicAuxadc_irq_lock);',26,27,status='0x80000000U')
g=bracket(g,'\tmutex_lock(&pmic_adc_mutex);',28,29,status='0x80000000U')
g=g.replace('p00a_pmic_prepare_adc();','p00a_pmic_prepare_adc(&capture);')
g=bracket(g,'\tret = p00a_pmic_prepare_adc(&capture);',30,31)
g=bracket(g,'\tret = p00a_pmic_result(pmic_config_interface(AUXADC_CON11, 1,\n\t\t\tPMIC_RG_VBUF_EN_MASK, PMIC_RG_VBUF_EN_SHIFT));',32,33)
g=bracket(g,'\t\tret = p00a_pmic_result(pmic_config_interface(AUXADC_CON22,\n\t\t\t\t0, 1, channel));',34,35,sample='sample')
g=bracket(g,'\t\tret = p00a_pmic_result(pmic_config_interface(AUXADC_CON22,\n\t\t\t\t1, 1, channel));',36,37,sample='sample')
g=bracket(g,'\t\tudelay(300);',38,39,sample='sample',status='0x80000000U')
g=bracket(g,'\t\t\tret = p00a_pmic_result(pmic_read_interface(\n\t\t\t\toutput_reg[channel - 4], &raw, 0xffff, 0));',40,41,sample='sample',poll='poll')
g=g.replace('\t\t\tif (raw & BIT(15))\n\t\t\t\tbreak;','\t\t\tif (raw & BIT(15)) {\n'+hook(42,'sample','poll',indent='\t\t\t\t')+'\n\t\t\t\tbreak;\n\t\t\t}\n'+hook(43,'sample','poll',indent='\t\t\t'))
g=bracket(g,'\t\t\tusleep_range(1000, 2000);',44,45,'sample','poll','0x80000000U')
g=g.replace('\t\t\tret = -ETIMEDOUT;','\t\t\tret = -ETIMEDOUT;\n'+hook(46,'sample','poll','ret','\t\t\t'))
g=g.replace('\t\tsum += raw & 0x7fff;','\t\tsum += raw & 0x7fff;\n'+hook(47,'sample','poll',indent='\t\t'))
g=bracket(g,'\tmutex_unlock(&pmic_adc_mutex);',48,49,'sample','poll','ret')
g=bracket(g,'\t__pm_relax(pmicAuxadc_irq_lock);',50,51,'sample','poll','ret')
g=g.replace(hook(48,'sample','poll'),hook(48,'sample','poll','ret')).replace(hook(50,'sample','poll'),hook(50,'sample','poll','ret'))
g=retwrap(g,59,'sample','poll');s=s.replace(f,g)
s=s.replace('#include <linux/power/asus_p00a_battery.h>','#include <linux/power/asus_p00a_battery.h>\n#include <linux/asus_retained_trace.h>',1)
files={p:s}
for n in ['arch/arm64/kernel/asus_retained_trace.c','include/linux/asus_retained_trace.h','arch/arm64/kernel/asus_entry_tag.h']:
 a=(R/'source/base'/n).read_text();z=a
 if n.endswith('asus_retained_trace.c'):
  z=z.replace(old_u,u);marker='static void __init cap_init(';z=z.replace(marker,(R/'source/pmic_capture.inc').read_text().replace('UUID',u)+marker,1)
  start=z.index(marker);end=z.index('static bool cap_lock(',start);body=z[start:end]
  body=body.replace(' BUILD_BUG_ON(PS_SIZE % 64);',' BUILD_BUG_ON(PS_SIZE % 64);\n BUILD_BUG_ON(PM_SIZE % 64);')
  body=body.replace('CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE','CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE + PM_SIZE')
  body=body.replace(' ps_init(dest + CAP_SIZE + SW_SIZE + WD_SIZE);',' ps_init(dest + CAP_SIZE + SW_SIZE + WD_SIZE);\n pm_init(dest + CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE);')
  body=body.replace(' smp_store_release(&ps_area, dest + CAP_SIZE + SW_SIZE + WD_SIZE);',' smp_store_release(&ps_area, dest + CAP_SIZE + SW_SIZE + WD_SIZE);\n smp_store_release(&pm_area, dest + CAP_SIZE + SW_SIZE + WD_SIZE + PS_SIZE);')
  z=z[:start]+body+z[end:]
 elif n.endswith('asus_retained_trace.h'):z=z.replace('struct task_struct;','struct task_struct;\n'+(R/'source/pmic-interface.inc').read_text(),1)
 else:
  z=z.replace(old_u,u).replace('2d64022664c5ff61296446a41a55186f24247fe9287f03a0ca398a6c26e2e3ab',i['base_compiled_sha256']);i['tag']=z.split('"')[1].replace('\\n','\n');i['capture_tag']='A49CAP1 uuid='+u
 files[n]=z
pins={};diff=[]
for n,z in files.items():
 a=(R/'source/base'/n).read_text();out=R/'source'/n;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(z)
 pins[n]=dict(before=hashlib.sha256(a.encode()).hexdigest(),after=hashlib.sha256(z.encode()).hexdigest());diff.extend(difflib.unified_diff(a.splitlines(True),z.splitlines(True),fromfile='base/'+n,tofile='candidate/'+n))
(R/'source/changes.patch').write_text(''.join(diff));(R/'evidence/source-pins.json').write_text(json.dumps(pins,indent=2)+'\n');(R/'evidence/identity.json').write_text(json.dumps(i,indent=2)+'\n')
print(json.dumps(pins,indent=2))
