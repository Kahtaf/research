#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <sys/stat.h>
#include <unistd.h>
static void die(const char*s){perror(s);sync();reboot(RB_POWER_OFF);_exit(1);}
static void put(const char*src,const char*dst,int existing,mode_t mode,gid_t gid){struct stat st={0};if(existing&&stat(dst,&st))die("stat");int a=open(src,O_RDONLY),b=open(dst,O_WRONLY|O_TRUNC|(existing?0:O_CREAT|O_EXCL),mode);if(a<0||b<0)die(dst);char buf[16384];ssize_t n;while((n=read(a,buf,sizeof(buf)))>0){ssize_t k=0;while(k<n){ssize_t w=write(b,buf+k,n-k);if(w<1)die("write");k+=w;}}if(n<0)die("read");close(a);if(existing){struct timespec ts[]={st.st_atim,st.st_mtim};if(futimens(b,ts))die("times");}else if(fchown(b,0,gid)||fchmod(b,mode))die("mode");if(fsync(b))die("fsync");close(b);printf("PATCHED path=%s existing=%d\n",dst,existing);}
int main(void){setvbuf(stdout,NULL,_IONBF,0);mkdir("/dev",0755);mkdir("/proc",0755);mkdir("/sys",0755);mkdir("/mnt",0755);if(mount("devtmpfs","/dev","devtmpfs",0,NULL)||mount("proc","/proc","proc",0,NULL)||mount("sysfs","/sys","sysfs",0,NULL))die("pseudo");for(int i=0;i<50&&access("/dev/vda",F_OK);i++)usleep(100000);if(mount("/dev/vda","/mnt","ext4",MS_NOATIME|MS_NODIRATIME,NULL))die("COW mount");put("/vendor.fstab","/mnt/system/vendor/etc/fstab.mt8163",1,0,0);put("/init.rc","/mnt/system/etc/init/hw/init.rc",1,0,0);put("/candidate","/mnt/system/bin/linkerconfig",0,0755,2000);put("/observer","/mnt/system/bin/actual-runtime-observer",0,0755,2000);put("/observer.rc","/mnt/system/etc/init/actual-runtime-observer.rc",0,0644,0);sync();if(umount("/mnt"))die("umount");puts("COW_PATCH_COMPLETE modified=2 added=3");reboot(RB_POWER_OFF);return 0;}
