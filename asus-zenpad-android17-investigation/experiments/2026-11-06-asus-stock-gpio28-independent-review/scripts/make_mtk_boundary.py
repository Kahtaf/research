from pathlib import Path
import re,json,hashlib
R=Path(__file__).resolve().parents[1];S=R/'inputs'
def fn(text,name):
 m=re.search(r'(?m)^static (?:int|void|unsigned int) '+name+r'\([^;]*?\)\s*\n\{',text);assert m,name
 start=m.start();p=m.end();n=1
 while n:n+=(text[p]=='{')-(text[p]=='}');p+=1
 return text[start:p]+'\n'
p=S/'inputs/api/drivers/pinctrl/mediatek/pinctrl-mtk-common.c';src=p.read_text()
pre='''
#define CONFIG_PINCTRL_MTK_NO_UPSTREAM 1
#define BIT(n) (1U<<(n))
#define SET_ADDR(a,p) ((a)+(p)->devdata->port_align)
#define CLR_ADDR(a,p) ((a)+2*(p)->devdata->port_align)
struct pinctrl_dev {int dummy;};struct pinctrl_gpio_range {int dummy;};
struct gpio_chip {int base;};
struct mtk_pinctrl;
struct mtk_data {unsigned port_mask,port_shf,dir_offset,dout_offset,port_align;void *pin_dir_grps,*pin_dout_grps;void (*spec_dir_set)(struct mtk_pinctrl *,unsigned *,unsigned,bool);};
struct mtk_pinctrl {struct mtk_data *devdata;};
static struct mtk_data mtk_data={.port_mask=0xf,.port_shf=4,.dir_offset=0,.dout_offset=0x400,.port_align=4};
static struct mtk_pinctrl pctl_data={&mtk_data};
static struct gpio_chip mtk_chip={.base=43};static struct pinctrl_dev mtk_pctldev;
static int mtk_error_mode,mtk_write_failures;
static struct mtk_pinctrl *pinctrl_dev_get_drvdata(struct pinctrl_dev *p){(void)p;return &pctl_data;}
static struct mtk_pinctrl *gpiochip_get_data(struct gpio_chip *p){(void)p;return &pctl_data;}
static void *mtk_get_regmap(struct mtk_pinctrl *p,unsigned pin){(void)p;CHECK(pin==28);return &pctl_data;}
static int regmap_write(void *p,unsigned addr,unsigned val){CHECK(p==&pctl_data);(void)addr;(void)val;if(mtk_error_mode){mtk_write_failures++;return -EIO;}return 0;}
static int mtk_pinctrl_set_gpio_direction(struct mtk_pinctrl *p,unsigned a,bool b){(void)p;(void)a;(void)b;CHECK(false);return -EIO;}
static void mtk_pinctrl_set_gpio_output(struct mtk_pinctrl *p,unsigned a,int b){(void)p;(void)a;(void)b;CHECK(false);}
'''
parts=[fn(src,n) for n in ['mtk_get_port','mtk_pmx_gpio_set_direction','mtk_gpio_set']]
mid='''static int pinctrl_gpio_direction_output(unsigned pin){CHECK(pin==71);return mtk_pmx_gpio_set_direction(&mtk_pctldev,NULL,28,false);}\n'''
post=fn(src,'mtk_gpio_direction_output')
s=(S/'tests/contract.c').read_text().replace('int main(void){','static int original_main(void){')
s=s.replace('static int gpiod_direction_output_raw',pre+'\n'.join(parts)+mid+post+'\nstatic int gpiod_direction_output_raw')
needle="if(output_errors){output_errors--;return -EIO;}return 0;}"
assert needle in s
s=s.replace(needle,"if(output_errors){output_errors--;return -EIO;}if(mtk_error_mode)return mtk_gpio_direction_output(&mtk_chip,28,value);return 0;}")
s+='''
int main(void){
 CHECK(original_main()==0);
 reset();mtk_error_mode=1;CHECK(core_probe()==0);CHECK(mtk_write_failures==2);
 CHECK(set(1)==1&&get()==1&&!p00a_gate_fault);CHECK(mtk_write_failures==4);
 CHECK(set(0)==1&&get()==0&&!p00a_gate_fault);CHECK(mtk_write_failures==6);
 detach();CHECK(free_calls==1);mtk_error_mode=0;
 printf("PASS MT8163 real callback error-boundary counterexample: 6 injected regmap failures, GPIO APIs report success, command cache follows API; no electrical observation\\n");
 return 0;
}
'''
(S/'tests/mtk-boundary.c').write_text(s)
(R/'evidence/mtk-boundary-extraction.json').write_text(json.dumps(dict(source=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),functions={n:hashlib.sha256(fn(src,n).encode()).hexdigest() for n in ['mtk_get_port','mtk_pmx_gpio_set_direction','mtk_gpio_set','mtk_gpio_direction_output']},real_config_no_upstream=True,mt8163_pin_dir_grps_and_pin_dout_grps='NULL in actual platform data; verified independently',injection='regmap_write returns -EIO in fake register boundary; actual callback bodies retained'),indent=2)+'\n')
print('Generated actual MT8163 callback fault counterexample')
