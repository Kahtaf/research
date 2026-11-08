from pathlib import Path
import subprocess,json,resource,os
R=Path('/srv/android/asus-bmc156-accelerometer-r1');T=R/'tests';T.mkdir(exist_ok=True)
s=(R/'source/kernel/drivers/misc/mediatek/sensors-1.0/accelerometer/accel.c').read_text();i=s.index('static int acc_enable_and_batch(');fn=s[i:s.index('\n}',i)+2]
preamble='''#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <errno.h>
#define ACC_INVALID_VALUE -1
#define atomic_read(p) (*(p))
#define atomic_set(p,v) (*(p)=(v))
#define pr_err(...) ((void)0)
#define pr_debug(...) ((void)0)
#define smp_mb() ((void)0)
#define do_div(n,b) ((n)/=(b))
static int stop_count,start_count,cancel_count,enable_count,disable_count,batch_count;
static bool fail_enable,fail_batch,hardware_on;
static int enable_driver(int en){if(en){enable_count++;hardware_on=true;if(fail_enable)return -EIO;}else{disable_count++;hardware_on=false;}return 0;}
static int batch_driver(int flag,int64_t ns,int64_t latency){assert(!flag && ns>=10000000 && !latency);batch_count++;return fail_batch?-EIO:0;}
struct acc_context {
 int acc_pause,enable,power,delay,hrTimer,report;
 int64_t delay_ns,latency_ns;
 bool is_acc_need_restore_polling,is_active_data,is_active_nodata,is_polling_run,is_first_data_after_enable;
 struct {int x,y,z;} drv_data;
 struct {bool is_report_input_direct,is_support_batch;int (*enable_nodata)(int);int (*batch)(int,int64_t,int64_t);} acc_ctl;
};
static struct acc_context *acc_context_obj;
static void stopTimer(int *t){(void)t;stop_count++;}
static void cancel_work_sync(int *w){(void)w;cancel_count++;}
static void startTimer(int *t,int delay,bool first){(void)t;assert(delay>=10 && first);start_count++;}
'''
end='''
static int checks;
#define CHECK(x) do{assert(x);checks++;}while(0)
int main(void){
 struct acc_context c={.delay_ns=20000000,.acc_ctl={.enable_nodata=enable_driver,.batch=batch_driver}};acc_context_obj=&c;
 CHECK(!acc_enable_and_batch() && disable_count==1 && c.delay_ns==20000000);
 c.enable=1;c.is_active_data=true;fail_enable=true;
 CHECK(acc_enable_and_batch()==-EIO && hardware_on && c.power==0);
 /* acc_store_active rolls requested state back after the failed enable. */
 c.enable=0;c.is_active_data=false;fail_enable=false;
 CHECK(!acc_enable_and_batch() && !hardware_on && disable_count==2 && c.delay_ns==20000000);
 c.enable=1;c.is_active_data=true;
 CHECK(!acc_enable_and_batch() && hardware_on && c.power==1 && c.is_polling_run && c.delay==20 && start_count==1 && batch_count==1);
 c.delay_ns=50000000;CHECK(!acc_enable_and_batch() && c.delay==50 && batch_count==2 && start_count==1);
 c.acc_pause=1;c.is_acc_need_restore_polling=false;
 CHECK(acc_enable_and_batch()==-EBUSY && !c.is_acc_need_restore_polling);c.acc_pause=0;
 c.enable=0;c.is_active_data=false;
 CHECK(!acc_enable_and_batch() && !hardware_on && c.power==0 && !c.is_polling_run && stop_count==1 && cancel_count==1 && c.delay_ns==50000000);
 c.enable=1;c.is_active_data=true;fail_batch=true;
 CHECK(acc_enable_and_batch()==-EIO && c.power==1 && hardware_on);
 c.enable=0;c.is_active_data=false;fail_batch=false;
 CHECK(!acc_enable_and_batch() && !hardware_on && c.power==0);
 printf("actual core enable/batch/failure recovery: %d assertions passed (mock driver/timer)\\n",checks);
}
'''
(T/'core_state.c').write_text(preamble+fn+end);os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
cmd=['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=undefined,bounds',str(T/'core_state.c'),'-o',str(T/'core_state')]
p=subprocess.run(cmd,capture_output=True,text=True);print(p.stdout,p.stderr);assert not p.returncode

def limits():resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(30,30))
p=subprocess.run([str(T/'core_state')],capture_output=True,text=True,preexec_fn=limits,timeout=35);print(p.stdout,p.stderr)
(R/'evidence/core-state-test.json').write_text(json.dumps(dict(command=cmd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr,one_cpu=True,address_space_bytes=1024**3),indent=2)+'\n');assert not p.returncode
