/* Independent fault injection at the helper's documented mock boundary.
 * There is no real Linux syscall implementation in this executable. */
#include <stdio.h>
#include <string.h>
#include <assert.h>
#define DIAG_TEST
#include "probe/diag.c"
static char out[REPORT_LIMIT+1],path[256];
static usize bytes;
static int done,published,scenario;
static long call(long n,long a,long b,long c,long d,long e,long f) {
 (void)d;(void)e;(void)f;
 switch(n) {
 case 174:return 0;
 case 113:((struct timespec64*)b)->sec=0;((struct timespec64*)b)->nsec=0;return 0;
 case 115:return 0;
 case 56:
  snprintf(path,sizeof(path),"%s",(char*)b);done=0;
  if(c&1)return 9;
  if(scenario==1 && !strcmp(path,"/proc/cmdline"))return -13;
  return 10;
 case 57:return 0;
 case 63: {
  if(scenario==0)return -5;
  if(done++)return 0;
  const char *s="ok\n";
  if(!strcmp(path,"/proc/version"))s="Linux version 4.9.337-test\n";
  if(!strcmp(path,"/proc/cmdline"))s="androidboot.serialno=DEVICE_SERIAL_REDACTED\n";
  if(!strcmp(path,"/sys/fs/selinux/enforce"))s=scenario==2?"0\n":"1\n";
  if(!strcmp(path,"/proc/self/attr/current"))s="u:r:recovery:s0";
  if(!strcmp(path,"/sys/class/power_supply/battery/uevent") && scenario==3)return -5;
  usize z=strlen(s);if(z>(usize)c)z=c;memcpy((void*)b,s,z);return z;
 }
 case 64:assert(a==9);assert(bytes+(usize)c<=REPORT_LIMIT);memcpy(out+bytes,(void*)b,c);bytes+=c;out[bytes]=0;return c;
 case 61:return scenario==4?-5:0;
 case 116:return -1;
 case 52:return 0;
 case 38:published++;return 0;
 default:return -38;
 }
}
int main(void) {
 char *args[]={"/sbin/recovery","--collect"};
 for(scenario=0;scenario<5;scenario++) {
  bytes=0;out[0]=0;published=0;int rc=diag_main(2,args);
  printf("scenario=%d rc=%d published=%d end=%d read_error=%d open_error=%d enforcing_zero=%d\n",scenario,rc,published,strstr(out,"END_DIAGNOSTIC")!=NULL,strstr(out,"read errno=")!=NULL,strstr(out,"open errno=")!=NULL,strstr(out,"[ /sys/fs/selinux/enforce ]\n0")!=NULL);
  assert(rc==0 && published==1 && strstr(out,"END_DIAGNOSTIC"));
 }
}
