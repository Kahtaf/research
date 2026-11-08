from pathlib import Path
import subprocess,json,os,resource
R=Path('/srv/android/asus-bmc156-accelerometer-r1');s=(R/'source/kernel/drivers/misc/mediatek/sensors-1.0/accelerometer/bmc156_acc/bmc156_acc.c').read_text()
def fn(name):
 i=s.index('static int '+name+'(');return s[i:s.index('\n}',i)+2]
macros=s[s.index('#define BMA255_AXIS_X'):s.index('struct data_resolution')]
harness='''#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
#include <assert.h>
#include "bmc156_acc.h"
typedef uint8_t u8; typedef int16_t s16; typedef int32_t s32;
#define pr_err(...) ((void)0)
#define pr_debug(...) ((void)0)
#define GRAVITY_EARTH_1000 9807
#define SENSOR_STATUS_ACCURACY_MEDIUM 2
#define SENSOR_STATUS_UNRELIABLE 0
struct i2c_client {int dummy;};
struct data_resolution {int sensitivity;};
struct cvt {int sign[3],map[3];};
struct bma255_i2c_data {struct i2c_client *client; struct data_resolution *reso; struct cvt cvt; s16 cali_sw[3]; bool calibrated,suspended; int lock;};
static struct bma255_i2c_data *obj_i2c_data;
static int operation_lock;
static bool sensor_power;
static bool sensor_power_valid=true;
#define mutex_lock(x) ((void)(x))
#define mutex_unlock(x) ((void)(x))
static uint8_t bytes[6];static int failure;
static int write_count,fail_write_at;
#define mdelay(x) ((void)(x))
static void *i2c_get_clientdata(struct i2c_client *c){(void)c;return obj_i2c_data;}
static int bma_i2c_write_block(struct i2c_client *c,u8 a,u8 *v,u8 n){(void)c;(void)a;(void)v;assert(n==1);write_count++;return write_count==fail_write_at ? -EIO : 0;}
static uint32_t get_unaligned_le32(const void *v) {const uint8_t *p=v;return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static int bma_i2c_read_block(struct i2c_client *c,u8 addr,u8 *out,u8 n) {(void)c;if(failure)return failure;if(n==1){out[0]=0;return 0;}assert(addr==BMA255_REG_DATAXLOW && n==6);memcpy(out,bytes,n);return 0;}
'''+macros+fn('BMA255_ReadData')+'\n'+fn('BMA255_SetPowerMode')+'\n'+fn('bmc156_get_data')+'\n'+fn('bmc156_set_cali')+'''
static unsigned checks;
#define CHECK(x) do {assert(x);checks++;}while(0)
static void raw(unsigned axis,int n) {unsigned v=((unsigned)n&4095)<<4;bytes[axis*2]=v;bytes[axis*2+1]=v>>8;}
int main(void) {
 struct i2c_client client={0};struct data_resolution res={512};
 struct bma255_i2c_data obj={.client=&client,.reso=&res,.cvt={{-1,1,-1},{0,1,2}}};
 obj_i2c_data=&obj;sensor_power=true;int x,y,z,status;
 for(int i=-2048;i<=2047;i++) {
  raw(0,i);raw(1,-1);raw(2,512);s16 decoded[3];
  CHECK(BMA255_ReadData(&client,decoded)==0 && decoded[0]==i && decoded[1]==-1 && decoded[2]==512);
  CHECK(!bmc156_get_data(&x,&y,&z,&status) && x==-i*9807/512 && y==-9807/512 && z==-9807 && status==0);
 }
 failure=-EIO;x=123;y=234;z=345;CHECK(bmc156_get_data(&x,&y,&z,&status)==-EIO && x==123 && y==234 && z==345);failure=0;
 obj.suspended=true;CHECK(bmc156_get_data(&x,&y,&z,&status)==-EAGAIN);obj.suspended=false;
 sensor_power=false;CHECK(bmc156_get_data(&x,&y,&z,&status)==-EAGAIN);
 uint8_t cal[12]={1,0,0,0,255,255,255,255,250,0,0,0};
 CHECK(bmc156_set_cali(cal,11)==-EINVAL);
 CHECK(!bmc156_set_cali(cal,12) && obj.cali_sw[0]==-1 && obj.cali_sw[1]==-1 && obj.cali_sw[2]==-250);
 CHECK(!bmc156_set_cali(cal,12) && obj.cali_sw[2]==-250);
 cal[8]=251;CHECK(bmc156_set_cali(cal,12)==-ERANGE && obj.cali_sw[2]==-250);cal[8]=250;
 sensor_power=true;CHECK(bmc156_set_cali(cal,12)==-EBUSY);
 raw(0,0);raw(1,0);raw(2,512);
 CHECK(!bmc156_get_data(&x,&y,&z,&status) && x==9807/512 && y==-9807/512 && z==-262*9807/512 && status==2);
 CHECK(!BMA255_SetPowerMode(&client,false) && !sensor_power && sensor_power_valid && write_count==2);
 CHECK(!BMA255_SetPowerMode(&client,false) && write_count==2);
 fail_write_at=4;CHECK(BMA255_SetPowerMode(&client,true)<0 && !sensor_power_valid);
 CHECK(bmc156_get_data(&x,&y,&z,&status)==-EIO);
 CHECK(bmc156_set_cali(cal,12)==-EIO);
 fail_write_at=0;CHECK(!BMA255_SetPowerMode(&client,false) && write_count==6 && sensor_power_valid && !sensor_power);
 printf("OEM extracted decode/calibration/direction/scale: %u assertions passed (mock I2C)\\n",checks);
}
'''
T=R/'tests';T.mkdir(exist_ok=True);(T/'kernel_math.c').write_text(harness)
cmd=['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=undefined,bounds','-fno-omit-frame-pointer','-I'+str(R/'source/kernel/drivers/misc/mediatek/sensors-1.0/accelerometer/bmc156_acc'),str(T/'kernel_math.c'),'-o',str(T/'kernel_math')]
p=subprocess.run(cmd,capture_output=True,text=True);print(p.stdout,p.stderr);assert p.returncode==0
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
def limits(): resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3)); resource.setrlimit(resource.RLIMIT_CPU,(30,30))
p=subprocess.run([str(T/'kernel_math')],capture_output=True,text=True,preexec_fn=limits,timeout=35);print(p.stdout,p.stderr);assert p.returncode==0
(R/'evidence/kernel-math-test.json').write_text(json.dumps(dict(command=cmd,exit=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2)+'\n')
