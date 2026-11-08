#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <sys/xattr.h>
#include <unistd.h>
static void fail(const char *s){perror(s);sync();reboot(RB_POWER_OFF);_exit(1);}
static void meta(const char *p,const char *phase){struct stat st;char x[256]={0};if(stat(p,&st)){printf("META phase=%s path=%s absent errno=%d\n",phase,p,errno);return;}ssize_t n=getxattr(p,"security.selinux",x,255);printf("META phase=%s path=%s ino=%lu mode=%o uid=%u gid=%u size=%ld atime=%ld.%09ld mtime=%ld.%09ld ctime=%ld.%09ld label=%s xattr_bytes=%ld\n",phase,p,st.st_ino,st.st_mode,st.st_uid,st.st_gid,st.st_size,st.st_atim.tv_sec,st.st_atim.tv_nsec,st.st_mtim.tv_sec,st.st_mtim.tv_nsec,st.st_ctim.tv_sec,st.st_ctim.tv_nsec,n<0?"ERROR":x,n);}
static void put(const char *src,const char *dst,int existing,mode_t mode,uid_t uid,gid_t gid,const char *label){(void)label;meta(dst,"before");struct stat orig={0};if(existing&&stat(dst,&orig))fail("stat original");int in=open(src,O_RDONLY);if(in<0)fail(src);int out=open(dst,O_WRONLY|O_TRUNC|(existing?0:O_CREAT|O_EXCL),mode);if(out<0)fail(dst);char buf[8192];ssize_t n;while((n=read(in,buf,sizeof(buf)))>0){ssize_t pos=0;while(pos<n){ssize_t w=write(out,buf+pos,n-pos);if(w<=0)fail("write");pos+=w;}}if(n<0)fail("read");close(in);if(!existing){if(fchown(out,uid,gid)||fchmod(out,mode))fail("metadata");}else{struct timespec ts[]={orig.st_atim,orig.st_mtim};if(futimens(out,ts))fail("futimens");}if(fsync(out))fail("fsync");close(out);meta(dst,"after");}
int main(void){setvbuf(stdout,NULL,_IONBF,0);mkdir("/dev",0755);mkdir("/proc",0755);mkdir("/sys",0755);mkdir("/mnt",0755);if(mount("devtmpfs","/dev","devtmpfs",0,NULL))fail("devtmpfs");if(mount("proc","/proc","proc",0,NULL)||mount("sysfs","/sys","sysfs",0,NULL))fail("pseudo");for(int i=0;i<50&&access("/dev/vda",F_OK);i++)usleep(100000);if(mount("/dev/vda","/mnt","ext4",MS_NOATIME|MS_NODIRATIME,NULL))fail("system COW mount");
put("/vendor.fstab","/mnt/system/vendor/etc/fstab.mt8163",1,0,0,0,NULL);
put("/observer","/mnt/system/bin/actual-runtime-observer",0,0755,0,2000,"u:object_r:shell_exec:s0");
put("/observer.rc","/mnt/system/etc/init/actual-runtime-observer.rc",0,0644,0,0,"u:object_r:system_file:s0");
sync();if(umount("/mnt"))fail("umount");puts("COW_PATCH_COMPLETE files_changed=1 files_added=2");reboot(RB_POWER_OFF);return 0;}
