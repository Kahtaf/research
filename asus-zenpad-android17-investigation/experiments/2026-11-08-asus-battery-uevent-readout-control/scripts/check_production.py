from pathlib import Path
import json,subprocess,re
R=Path(__file__).resolve().parents[1];S=R/'source';E=R/'evidence'
def body(s,name):
 a=re.search(r'\b'+re.escape(name)+r'\(',s).start();b=s.index('{',a);j=b+1;depth=1
 while depth:depth+=(s[j]=='{')-(s[j]=='}');j+=1
 return s[a:j]
sysfs=(S/'drivers/power/supply/power_supply_sysfs.c').read_text();core=(S/'drivers/power/supply/power_supply_core.c').read_text()
record=sysfs[sysfs.index('static atomic_t battery_uevent_omissions'):sysfs.index('int power_supply_uevent(')]
head=r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <stddef.h>
#include <errno.h>
typedef uint32_t u32; typedef int pid_t; typedef struct {int v;} atomic_t;
#define ATOMIC_INIT(x) {x}
#define atomic_read(p) ((p)->v)
#define atomic_inc_return(p) (++(p)->v)
#define cmpxchg(p,a,z) ({int old=*(p); if(old==(a))*(p)=(z);old;})
#define smp_store_release(p,v) (*(p)=(v))
#define smp_load_acquire(p) (*(p))
#define noinline
#define notrace
#define ASUS_BATTERY_UEVENT_PREFIX "ASUS49-BUEV run=test v=1 "
#define GFP_KERNEL 0
#define KOBJ_CHANGE 2
#define PSY_EVENT_PROP_CHANGED 1
#define U64_MAX UINT64_MAX
#define likely(x) (x)
#define READ_ONCE(x) (x)
#define container_of(p,t,m) ((t*)((char*)(p)-offsetof(t,m)))
#define dev_dbg(...) ((void)0)
#define asus_capture_ps_begin(...) ((void)0)
#define asus_capture_ps_step(...) ((void)0)
struct task {int pid;}; static struct task task={17};
#define current (&task)
#define task_pid_nr(t) ((t)->pid)
static int held,irqoff,atomicctx,allocations,frees,getters,envcalls,name_error,property_error,publications,returned,class_calls,notifier_calls,led_calls,relax_calls;
static char retained[192];
#define in_task() 1
#define in_atomic() (atomicctx)
#define irqs_disabled() (irqoff)
#define spin_lock_irqsave(p,f) do{assert(!held);held=1;irqoff=1;f=0;}while(0)
#define spin_unlock_irqrestore(p,f) do{assert(held);held=0;irqoff=0;}while(0)
static unsigned int scnprintf(char *s,size_t n,const char *fmt,...){va_list a;va_start(a,fmt);int z=vsnprintf(s,n,fmt,a);va_end(a);return z<0?0:((size_t)z<n?z:n-1);}
static void asus_retained_trace_write(char *s,unsigned int n){assert(!held&&!irqoff&&!atomicctx&&returned);assert(n<sizeof(retained));memcpy(retained,s,n);retained[n]=0;publications++;}
struct work_struct {int x;}; struct device;
struct kobject {struct device *dev;};
struct device {void *data;struct kobject kobj;};
struct power_supply_desc {const char *name;int num_properties;int *properties;};
struct power_supply {struct power_supply_desc *desc;struct device dev;struct work_struct changed_work;int changed_lock;bool changed;};
struct kobj_uevent_env {char name[64];int properties;};
struct device_attribute {struct {const char *name;} attr;};
static struct device_attribute power_supply_attrs[]={{{"voltage_now"}},{{"temp"}}};
struct asus_ps_capture {int x;};
static void *dev_get_drvdata(struct device *d){return d->data;}
static int add_uevent_var(struct kobj_uevent_env *e,const char *fmt,...){envcalls++;if(!strcmp(fmt,"POWER_SUPPLY_NAME=%s")){if(name_error)return name_error;va_list a;va_start(a,fmt);vsnprintf(e->name,sizeof(e->name),fmt,a);va_end(a);}else e->properties++;return 0;}
static unsigned long get_zeroed_page(int f){allocations++;return (unsigned long)calloc(1,4096);}
static void free_page(unsigned long p){frees++;free((void*)p);}
static char *kstruprdup(const char*s,int f){return strdup(s);}
#define kfree(p) free(p)
static int power_supply_show_property(struct device*d,struct device_attribute*a,char *p){getters++;if(property_error)return property_error;strcpy(p,"123\n");return 4;}
'''
workerhead=r'''
static int power_supply_class,power_supply_notifier;
static int __power_supply_changed_work(struct device*d,void*p){return 0;}
static int class_for_each_device(int cls,void*x,void*p,void*cb){assert(!held&&!irqoff);class_calls++;return 0;}
static int atomic_notifier_call_chain(int*p,int ev,void*psy){assert(!held&&!irqoff);notifier_calls++;return 0;}
static void power_supply_update_leds(struct power_supply*p){assert(!held&&!irqoff);led_calls++;}
static void pm_relax(struct device*d){assert(held&&irqoff);relax_calls++;}
static int kobject_uevent(struct kobject*k,int event){struct kobj_uevent_env env={0};assert(!held&&!irqoff&&event==KOBJ_CHANGE);int rc=power_supply_uevent(k->dev,&env);returned=1;return rc;}
'''
tail=r'''
static int props[]={0,1};
static struct power_supply_desc desc={"battery",2,props};
static struct power_supply psy;
static void reset(void){held=irqoff=atomicctx=allocations=frees=getters=envcalls=name_error=property_error=publications=returned=class_calls=notifier_calls=led_calls=relax_calls=0;battery_uevent_omissions.v=0;battery_uevent_state=0;memset(&battery_uevent_skip,0,sizeof(battery_uevent_skip));memset(&psy,0,sizeof(psy));psy.desc=&desc;psy.dev.data=&psy;psy.dev.kobj.dev=&psy.dev;desc.name="battery";retained[0]=0;}
int main(void){
 struct kobj_uevent_env env={0};
 reset();assert(power_supply_uevent(&psy.dev,&env)==0);assert(!strcmp(env.name,"POWER_SUPPLY_NAME=battery")&&!env.properties&&!allocations&&!getters&&battery_uevent_omissions.v==1&&!publications);
 // An earlier registration hit cannot provide the worker's first/correlation.
 psy.changed=true;power_supply_changed_work(&psy.changed_work);assert(publications==1&&strstr(retained,"first=2 before=1 after=2 same_task=1 uevent_rc=0"));assert(!held&&!irqoff&&!psy.changed&&class_calls==1&&notifier_calls==1&&led_calls==1&&relax_calls==1);
 psy.changed=true;returned=0;power_supply_changed_work(&psy.changed_work);assert(publications==1&&relax_calls==2&&getters==0);
 reset();desc.name="usb";env=(struct kobj_uevent_env){0};assert(power_supply_uevent(&psy.dev,&env)==0);assert(!strcmp(env.name,"POWER_SUPPLY_NAME=usb")&&env.properties==2&&getters==2&&allocations==1&&frees==1&&battery_uevent_omissions.v==0);
 reset();name_error=-ENOMEM;env=(struct kobj_uevent_env){0};assert(power_supply_uevent(&psy.dev,&env)==-ENOMEM&&!allocations&&!getters&&!battery_uevent_omissions.v);
 reset();desc.name="usb";property_error=-EIO;env=(struct kobj_uevent_env){0};assert(power_supply_uevent(&psy.dev,&env)==-EIO&&getters==1&&allocations==1&&frees==1);
 // A different task cannot supply the armed worker record; refusal is final.
 reset();bool armed=asus_battery_uevent_begin(&psy);task.pid=18;power_supply_uevent(&psy.dev,&env);task.pid=17;returned=1;asus_battery_uevent_publish(armed,0);assert(!publications);power_supply_uevent(&psy.dev,&env);atomicctx=1;asus_battery_uevent_publish(armed,0);atomicctx=0;asus_battery_uevent_publish(armed,0);assert(!publications&&battery_uevent_state==5);
 puts("PASS actual production uevent, recorder and changed_work bodies: matched omission; original unmatched/error paths; scoped once-only unlocked post-return publication and unchanged cleanup");return 0;
}
'''
c=head+record+'int '+body(sysfs,'power_supply_uevent')+'\n'+workerhead+'static void '+body(core,'power_supply_changed_work')+'\n'+tail
(E/'production-harness.c').write_text(c)
p=subprocess.run(['cc','-std=gnu11','-O2','-Wno-incompatible-pointer-types',str(E/'production-harness.c'),'-o',str(R/'tmp/production-harness')],capture_output=True,text=True);(E/'production-compile.txt').write_text(p.stdout+p.stderr);p.check_returncode()
p=subprocess.run([str(R/'tmp/production-harness')],capture_output=True,text=True);(E/'production-check.txt').write_text(p.stdout+p.stderr);p.check_returncode()
(E/'production-check.json').write_text(json.dumps(dict(passed=True,actual_production_bodies=['power_supply_uevent','power_supply_changed_work','asus_battery_uevent_begin','battery_uevent_omitted','asus_battery_uevent_publish'],mocked_boundaries=True,physical_evidence=False),indent=2)+'\n');print(p.stdout)
