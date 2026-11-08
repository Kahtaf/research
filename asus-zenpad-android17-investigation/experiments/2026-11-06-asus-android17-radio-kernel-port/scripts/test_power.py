#!/usr/bin/env python3
"""Execute exact production power transaction bodies with failing bus primitives."""
import pathlib,subprocess,hashlib,json
r=pathlib.Path(__file__).resolve().parents[1];p=r/'stagedpatches/kernel-input/drivers/misc/mediatek/connectivity/common/conn_soc/mt8163/mtk_wcn_consys_hw.c';s=p.read_text();a=s.index('static bool p00a_vcn18_on');b=s.index('INT32 mtk_wcn_consys_hw_gpio_ctrl(',a);body=s[a:b];a=s.index('static unsigned int p00a_vcn33_users');b=s.index('\n#else\nINT32 mtk_wcn_consys_hw_bt_paldo_ctrl',a);body+=s[a:b]
out=r/'evidence/host';out.mkdir(exist_ok=True)
pre=r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
typedef unsigned UINT32;
typedef int INT32;
#define EPROBE_DEFER 517
#define DEFINE_MUTEX(x) int x
#define mutex_lock(x) ((void)(x))
#define mutex_unlock(x) ((void)(x))
#define WMT_PLAT_ERR_FUNC(...) ((void)0)
#define ANALDO_CON19 19
#define ANALDO_CON16 16
#define DIGLDO_CON11 11
#define PMIC_VCN28_ON_CTRL_MASK 1
#define PMIC_VCN28_ON_CTRL_SHIFT 0
#define PMIC_VCN33_ON_CTRL_BT_MASK 1
#define PMIC_VCN33_ON_CTRL_BT_SHIFT 0
#define PMIC_VCN_1V8_LP_MODE_SET_MASK 1
#define PMIC_VCN_1V8_LP_MODE_SET_SHIFT 0
#define CONSYS_CHIP_ID_OFFSET 8
#define CONSYS_MCU_CFG_ACR_OFFSET 0x110
#define CONSYS_MCU_CFG_ACR_MBIST_BIT (1u<<18)
#define CONSYS_REG_READ(x) ((x)==8 ? simulated_chip : 0)
#define CONSYS_REG_WRITE(x,y) ((void)(x),(void)(y))
struct { uintptr_t mcu_base; } conn_reg;
static void *my_pdev=(void*)1, *rstc;
static int reg_VCN18=0, reg_VCN28=1, reg_VCN33_BT=2;
static int rails[3], domain, callno, fail_at;
static unsigned simulated_chip=0x8163;
static int step(void) { return ++callno==fail_at ? -EIO : 0; }
static void pmic_lock(void) {}
static void pmic_unlock(void) {}
static int pmic_config_interface(unsigned r,unsigned v,unsigned m,unsigned sh) {
 (void)r;(void)v;(void)m;(void)sh;return step();
}
static int regulator_set_voltage(int r,int lo,int hi) {(void)r;(void)lo;(void)hi;return step();}
static int regulator_enable(int r) {int ret=step();if(!ret)rails[r]++;return ret;}
static int regulator_disable(int r) {int ret=step();if(!ret)rails[r]--;return ret;}
static int reset_control_assert(void *p) {(void)p;return step();}
static int reset_control_deassert(void *p) {(void)p;return step();}
static int mtk_wcn_consys_power_on(void) {int ret=step();if(!ret)domain++;return ret;}
static int mtk_wcn_consys_power_off(void) {domain--;return step();}
static void udelay(int n) {(void)n;}
static void msleep(int n) {(void)n;}
'''
post=r'''
static void clear(void) {
 assert(!rails[0] && !rails[1] && !rails[2] && !domain);
 callno=fail_at=0;simulated_chip=0x8163;
}
int main(void) {
 for (int co=0;co<=1;co++) {
  clear();int ret=mtk_wcn_consys_hw_reg_ctrl(1,co);fprintf(stderr,"co=%d ret=%d flags=%d %d %d %d\n",co,ret,p00a_vcn18_on,p00a_vcn28_on,p00a_domain_on,p00a_vcn28_hw);assert(!ret);int forward=callno;
  assert(rails[0]==1 && rails[1]==!co && domain==1);
  assert(mtk_wcn_consys_hw_reg_ctrl(1,co)==-EBUSY);
  assert(!mtk_wcn_consys_hw_reg_ctrl(0,co));clear();
  for(int fail=1;fail<=forward;fail++) {
   clear();fail_at=fail;assert(mtk_wcn_consys_hw_reg_ctrl(1,co)<0);clear();
  }
  simulated_chip=0;assert(mtk_wcn_consys_hw_reg_ctrl(1,co)==-ETIMEDOUT);clear();
 }
 assert(!mtk_wcn_consys_hw_bt_paldo_ctrl(1));assert(rails[2]==1);
 assert(!mtk_wcn_consys_hw_bt_paldo_ctrl(1));assert(rails[2]==1);
 assert(!mtk_wcn_consys_hw_wifi_paldo_ctrl(1));assert(rails[2]==1);
 assert(!mtk_wcn_consys_hw_bt_paldo_ctrl(0));assert(rails[2]==1);
 assert(!mtk_wcn_consys_hw_wifi_paldo_ctrl(0));clear();
 for(int fail=1;fail<=3;fail++) {
  clear();fail_at=fail;assert(mtk_wcn_consys_hw_wifi_paldo_ctrl(1)<0);
  assert(!p00a_vcn33_users);clear();
 }
 my_pdev=0;assert(mtk_wcn_consys_hw_reg_ctrl(1,0)==-EPROBE_DEFER);
 assert(mtk_wcn_consys_hw_wifi_paldo_ctrl(1)==-EPROBE_DEFER);
 puts("production power transitions and forward-failure rollback checks passed");
}
'''
c=out/'power-test.c';c.write_text(pre+body+post);exe=out/'power-test'
subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(c),'-o',str(exe)],check=True)
pres=subprocess.run([str(exe)],capture_output=True,text=True);print(pres.stdout,pres.stderr);pres.check_returncode()
(r/'evidence/power-tests.json').write_text(json.dumps({'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'extracted_body_sha256':hashlib.sha256(body.encode()).hexdigest(),'result':pres.stdout.strip(),'primitives':'simulated regulators, reset, PMIC and power domain; no hardware test'},indent=2)+'\n')
