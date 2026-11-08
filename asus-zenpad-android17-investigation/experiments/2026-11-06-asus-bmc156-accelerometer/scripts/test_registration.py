from pathlib import Path
import subprocess,json,os,resource
R=Path('/srv/android/asus-bmc156-accelerometer-r1');T=R/'tests';T.mkdir(exist_ok=True)
s=(R/'source/kernel/drivers/misc/mediatek/sensors-1.0/hwmon/sensor_attributes/sensor_attr.c').read_text();i=s.index('int sensor_attr_register(');fn=s[i:s.index('\n}',i)+2]
preamble='''#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <errno.h>
#include <sys/types.h>
struct list_head {int unused;};
struct sensor_attr_t {int minor;void *parent,*this_device; const char *name;struct list_head list;};
static int sensor_attr_mtx,sensor_attr_major=250,sensor_attr_class;
static struct list_head sensor_attr_list;
static struct sensor_attr_t other={.minor=0};
static int existing,queue_error,device_error,queue_live,device_calls,registered;
#define mutex_lock(p) ((void)(p))
#define mutex_unlock(p) ((void)(p))
#define list_for_each_entry(p,h,m) for((void)(h),p=existing?&other:NULL;p;p=NULL)
#define MKDEV(ma,mi) ((dev_t)((ma)*256+(mi)))
#define IS_ERR(p) ((intptr_t)(p)<0)
#define PTR_ERR(p) ((int)(intptr_t)(p))
static int sensor_event_register(int n){assert(n==0);if(queue_error)return queue_error;queue_live=1;return 0;}
static void sensor_event_deregister(int n){assert(n==0 && queue_live);queue_live=0;}
static void *device_create(int cls,void *parent,dev_t dev,void *data,const char *fmt,const char *name){(void)cls;(void)parent;(void)dev;(void)data;(void)fmt;(void)name;assert(queue_live);device_calls++;return device_error?(void *)(intptr_t)device_error:(void *)1;}
static void list_add(struct list_head *a,struct list_head *b){(void)a;(void)b;registered++;}
'''
end='''
int main(void){struct sensor_attr_t m={.minor=0,.name="m_acc_misc"};
existing=1;assert(sensor_attr_register(&m)==-EBUSY && !queue_live && !device_calls);
existing=0;queue_error=-ENOMEM;assert(sensor_attr_register(&m)==-ENOMEM && !queue_live && !device_calls);
queue_error=0;device_error=-ENODEV;assert(sensor_attr_register(&m)==-ENODEV && !queue_live && !registered && !m.this_device);
device_error=0;assert(!sensor_attr_register(&m) && queue_live && registered==1 && m.this_device);
printf("actual registration failure/order: 4 scenarios passed (mock kernel services)\\n");}
'''
(T/'registration.c').write_text(preamble+fn+end)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
cmd=['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=undefined,bounds',str(T/'registration.c'),'-o',str(T/'registration')]
p=subprocess.run(cmd,capture_output=True,text=True);print(p.stdout,p.stderr);assert not p.returncode

def limits():resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(30,30))
p=subprocess.run([str(T/'registration')],capture_output=True,text=True,preexec_fn=limits,timeout=35);print(p.stdout,p.stderr)
(R/'evidence/registration-test.json').write_text(json.dumps(dict(command=cmd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr,one_cpu=True,address_space_bytes=1024**3),indent=2)+'\n');assert not p.returncode
