"""One observability-only revision of the exact existing C reporter."""
from pathlib import Path
import difflib

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT.parent / '2026-11-07-asus-linux49-usb-ram-report/source/init.c'
original = ORIGINAL.read_text()
source = original


def replace(old, new):
    global source
    assert source.count(old) == 1, old
    source = source.replace(old, new)


replace('#include <sys/utsname.h>', '#include <sys/utsname.h>\n#include <sys/sysmacros.h>')
replace('static uint8_t fat[FAT_BYTES];', r'''#define LOG_REV "ASUS-RAM-FAILLOG-20261107-R1"
#define LOG_NODE "/reporter-kmsg"
#define LOG_RECORDS 64
static int logfd=-1;
static volatile sig_atomic_t log_count;
static volatile sig_atomic_t log_sink_errno;
/* RAM-only record of sink failure; unavailable kmsg cannot survive reboot. */
static char log_ram[8192];
static size_t log_ram_used;
static void log_event(const char *event,const char *op,const char *path,int error){
 int saved=errno;char line[512];
 if(log_count<LOG_RECORDS){
  log_count++;
  int n=snprintf(line,sizeof(line),"<6>" LOG_REV " event=%s op=%s path=%s errno=%d\n",event,op,path,error);
  if(n>0&&(size_t)n<sizeof(line)){
   ssize_t w=logfd>=0?write(logfd,line,(size_t)n):-1;int e=errno;
   if(w!=n&&(size_t)n<=sizeof(log_ram)-log_ram_used){memcpy(log_ram+log_ram_used,line,(size_t)n);log_ram_used+=(size_t)n;}
   if(logfd>=0&&w!=n){
    int k=snprintf(line,sizeof(line),"<6>" LOG_REV " event=fail op=kmsg.write path=" LOG_NODE " errno=%d\n",w<0?e:0);
    if(k>0&&(size_t)k<=sizeof(log_ram)-log_ram_used){memcpy(log_ram+log_ram_used,line,(size_t)k);log_ram_used+=(size_t)k;}
   }
  }
 }
 errno=saved;
}
static int log_call(const char *op,const char *path,int result){
 if(result<0)log_event("fail",op,path,errno);return result;
}
static int log_guard(const char *op,const char *path,int failed){
 if(failed)log_event("fail",op,path,0);return failed;
}
static void log_open(void){
 int saved=errno;
 int made=mknod(LOG_NODE,S_IFCHR|0600,makedev(1,11));int make_error=made<0?errno:0;
 /* Never open an unexpected preexisting node. This is initial RAM root. */
 if(!made)logfd=open(LOG_NODE,O_WRONLY|O_CLOEXEC|O_NOFOLLOW|O_NONBLOCK);
 int open_error=logfd<0?errno:0;
 if(!made)(void)unlink(LOG_NODE);
 if(logfd>=0&&log_ram_used){ssize_t w=write(logfd,log_ram,log_ram_used);if(w<0)log_sink_errno=errno;}
 log_event("entry","logger",LOG_NODE,0);
 if(make_error)log_event("fail","mknod",LOG_NODE,make_error);
 if(!made&&open_error)log_event("fail","open",LOG_NODE,open_error);
 log_event(logfd>=0?"ready":"unavailable","kmsg-sink",LOG_NODE,logfd>=0?0:(make_error?make_error:open_error));
 errno=saved;
}
static void log_uname(void){
 struct utsname u;int saved=errno;
 if(uname(&u))log_event("fail","uname","-",errno);
 else{
  const char *values[]={u.sysname,u.release,u.version,u.machine};
  const char *names[]={"uname.sysname","uname.release","uname.version","uname.machine"};
  for(unsigned j=0;j<4;j++){
   size_t n=strnlen(values[j],65);int valid=n>0&&n<65;
   for(size_t i=0;i<n;i++)if((unsigned char)values[j][i]<32||(unsigned char)values[j][i]>126)valid=0;
   if(valid)log_event("actual",names[j],values[j],0);
   else log_event("fail",names[j],"invalid-public-field",0);
  }
 }
 errno=saved;
}
static void log_watchdog(void){
 /* Async-signal-safe: no stdio, errno formatting, locks, or retry. */
 static const char line[]="<6>" LOG_REV " event=reboot op=SIGALRM path=- errno=0\n";
 int saved=errno;if(logfd>=0){ssize_t w=write(logfd,line,sizeof(line)-1);if(w<0)log_sink_errno=errno;}errno=saved;
}
static void log_watchdog_return(int error){
 char line[160]="<6>" LOG_REV " event=reboot-return op=SIGALRM path=- errno=";
 char digits[16];unsigned v=(unsigned)error;size_t used=sizeof("<6>" LOG_REV " event=reboot-return op=SIGALRM path=- errno=")-1,n=0;
 do{digits[n++]=(char)('0'+v%10);v/=10;}while(v);
 while(n)line[used++]=digits[--n];line[used++]='\n';
 if(logfd>=0){ssize_t w=write(logfd,line,used);if(w<0)log_sink_errno=errno;}
}
static uint8_t fat[FAT_BYTES];''')
replace('if(getpid()!=1||uname(&u)||clean_uname(&u))return -1;', 'if(log_guard("pid1","-",getpid()!=1)||log_call("uname","-",uname(&u))||log_guard("clean_uname","-",clean_uname(&u)))return -1;')
replace('if(p<=0||(size_t)p>=sizeof(product))return -1;', 'if(log_guard("snprintf.product","-",p<=0||(size_t)p>=sizeof(product)))return -1;')
replace('if(n<=0||(size_t)n>=sizeof(report))return -1;', 'if(log_guard("snprintf.report","-",n<=0||(size_t)n>=sizeof(report)))return -1;')
replace(''' int fd=open(path,O_WRONLY|O_CLOEXEC|O_NOFOLLOW);if(fd<0)return -1;
 size_t n=strlen(value);ssize_t w=write(fd,value,n);int c=close(fd);
 return w==(ssize_t)n&&!c?0:-1;''', ''' int fd=open(path,O_WRONLY|O_CLOEXEC|O_NOFOLLOW);if(fd<0){log_event("fail","put.open",path,errno);return -1;}
 size_t n=strlen(value);ssize_t w=write(fd,value,n);int we=w<0?errno:0;int c=close(fd);int ce=c?errno:0;
 if(w!=(ssize_t)n)log_event("fail",w<0?"put.write":"put.write.short",path,we);
 if(c)log_event("fail","put.close",path,ce);
 return w==(ssize_t)n&&!c?0:-1;''')
replace(''' char b[256];int fd=open(path,O_RDONLY|O_CLOEXEC|O_NOFOLLOW);if(fd<0)return -1;
 ssize_t n=read(fd,b,sizeof(b)-1);int c=close(fd);if(n<0||n>=255||c)return -1;
 if(n&&b[n-1]=='\\n')n--;b[n]=0;return strcmp(b,want)?-1:0;''', ''' char b[256];int fd=open(path,O_RDONLY|O_CLOEXEC|O_NOFOLLOW);if(fd<0){log_event("fail","equals.open",path,errno);return -1;}
 ssize_t n=read(fd,b,sizeof(b)-1);int re=n<0?errno:0;int c=close(fd);int ce=c?errno:0;
 if(n<0)log_event("fail","equals.read",path,re);
 if(n>=255)log_event("fail","equals.read.bound",path,0);
 if(c)log_event("fail","equals.close",path,ce);
 if(n<0||n>=255||c)return -1;
 if(n&&b[n-1]=='\\n')n--;b[n]=0;int mismatch=strcmp(b,want);
 if(mismatch)log_event("fail","equals.mismatch",path,0);return mismatch?-1:0;''')
replace(''' if(fd<0)return -1;
 int rc=-1;
 if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_nlink!=1||st.st_size!=0||fstatfs(fd,&fs)||fs.f_type!=TMPFS_MAGIC)goto done;
 if(write(fd,fat,sizeof(fat))!=(ssize_t)sizeof(fat)||fchmod(fd,0444)||fstat(fd,&st)||st.st_size!=FAT_BYTES||(st.st_mode&0777)!=0444)goto done;
 rc=0;
 done:if(close(fd))rc=-1;return rc;''', ''' if(fd<0){log_event("fail","ram.open",RAMFILE,errno);return -1;}
 int rc=-1;
 if(log_call("ram.fstat",RAMFILE,fstat(fd,&st))||log_guard("ram.regular",RAMFILE,!S_ISREG(st.st_mode))||log_guard("ram.nlink",RAMFILE,st.st_nlink!=1)||log_guard("ram.empty",RAMFILE,st.st_size!=0)||log_call("ram.fstatfs",RAMFILE,fstatfs(fd,&fs))||log_guard("ram.tmpfs",RAMFILE,fs.f_type!=TMPFS_MAGIC))goto done;
 ssize_t w=write(fd,fat,sizeof(fat));
 if(w!=(ssize_t)sizeof(fat)){log_event("fail",w<0?"ram.write":"ram.write.short",RAMFILE,w<0?errno:0);goto done;}
 if(log_call("ram.fchmod",RAMFILE,fchmod(fd,0444))||log_call("ram.fstat",RAMFILE,fstat(fd,&st))||log_guard("ram.size",RAMFILE,st.st_size!=FAT_BYTES)||log_guard("ram.mode",RAMFILE,(st.st_mode&0777)!=0444))goto done;
 rc=0;
 done:if(log_call("ram.close",RAMFILE,close(fd)))rc=-1;return rc;''')
replace('if(!n||n>=cap){bad=1;break;}', 'if(!n||n>=cap){log_event("fail","udc.name.bound","/sys/class/udc",0);bad=1;break;}')
replace("if((unsigned char)e->d_name[i]<33||(unsigned char)e->d_name[i]>126||e->d_name[i]=='/'){bad=1;break;}", "if((unsigned char)e->d_name[i]<33||(unsigned char)e->d_name[i]>126||e->d_name[i]=='/'){log_event(\"fail\",\"udc.name.guard\",\"/sys/class/udc\",0);bad=1;break;}")
replace('''   if(errno)bad=1;
   if(closedir(d))bad=1;
   if(bad||count>1)return -1;''', '''   if(errno){log_event("fail","udc.readdir","/sys/class/udc",errno);bad=1;}
   if(log_call("udc.closedir","/sys/class/udc",closedir(d)))bad=1;
   if(log_guard("udc.unique","/sys/class/udc",bad||count>1))return -1;''')
replace('''  }else if(errno!=ENOENT)return -1;
  struct timespec t={0,100000000};if(clock_nanosleep(CLOCK_MONOTONIC,0,&t,NULL))return -1;
 }
 return -1;''', '''  }else if(errno!=ENOENT){log_event("fail","udc.opendir","/sys/class/udc",errno);return -1;}
  struct timespec t={0,100000000};int r=clock_nanosleep(CLOCK_MONOTONIC,0,&t,NULL);
  if(r){log_event("fail","udc.clock_nanosleep","-",r);return -1;}
 }
 log_event("fail","udc.absence.timeout","/sys/class/udc",0);return -1;''')
replace(''' if(getpid()!=1)return -1;
 if(mount(NULL,"/",NULL,MS_REC|MS_PRIVATE,NULL)||''', ''' log_event("stage","setup.entry","-",0);
 if(log_guard("pid1","-",getpid()!=1))return -1;
 if(log_call("mount","/",mount(NULL,"/",NULL,MS_REC|MS_PRIVATE,NULL))||''')
for fs, path, opts in [('tmpfs','/dev','"mode=0755,size=1m"'), ('tmpfs','/ram','"mode=0700,size=4m"'), ('proc','/proc','NULL'), ('sysfs','/sys','NULL'), ('configfs','/config','NULL')]:
    expr = f'mount("{fs}","{path}","{fs}",MS_NOSUID|MS_NODEV|MS_NOEXEC,{opts})'
    replace(expr, f'log_call("mount","{path}",{expr})')
replace(' if(make_fat()||ram_report()||unique_udc(udc,sizeof(udc)))return -1;', ''' log_event("stage","mounts.ready","-",0);
 if(make_fat()||ram_report())return -1;
 log_event("stage","ram.ready","/ram/probe.img",0);
 if(unique_udc(udc,sizeof(udc)))return -1;
 log_event("stage","udc.selected","/sys/class/udc",0);''')
for path in ['G', 'G "strings/0x409"', 'G "configs/c.1"', 'G "functions/mass_storage.usb0"']:
    expr = f'mkdir({path},0700)'
    replace(expr, f'log_call("mkdir",{path},{expr})')
replace(' if(put(G "idVendor","0x0b05")', ' log_event("stage","gadget.fresh",G,0);\n if(put(G "idVendor","0x0b05")')
replace(' if(equals(LUN "file","")', ' log_event("stage","descriptors.ready",G,0);\n if(equals(LUN "file","")')
replace(' if(put(LUN "file",RAMFILE)', ' log_event("stage","lun.attach",LUN "file",0);\n if(put(LUN "file",RAMFILE)')
replace('symlink(G "functions/mass_storage.usb0",G "configs/c.1/mass_storage.usb0")', 'log_call("symlink",G "configs/c.1/mass_storage.usb0",symlink(G "functions/mass_storage.usb0",G "configs/c.1/mass_storage.usb0"))')
replace('equals(LUN "ro","1")||put(G "UDC",udc)', 'equals(LUN "ro","1")||(log_event("stage","udc.bind",G "UDC",0),put(G "UDC",udc))')
replace(''' return 0;
}
static void disable(void){(void)put(G "UDC","\\n");}''', ''' log_event("stage","udc.bound",G "UDC",0);return 0;
}
static void disable(void){log_event("stage","disable",G "UDC",0);(void)put(G "UDC","\\n");}''')
replace(' (void)signo;(void)reboot(RB_AUTOBOOT);', ''' (void)signo;log_watchdog();int r=reboot(RB_AUTOBOOT);int e=r<0?errno:0;
 log_watchdog_return(e);''')
replace('if(sigemptyset(&sa.sa_mask)||sigaction(SIGALRM,&sa,NULL))return -1;', 'if(log_call("sigemptyset","-",sigemptyset(&sa.sa_mask))||log_call("sigaction","SIGALRM",sigaction(SIGALRM,&sa,NULL)))return -1;')
replace(''' if(arm_watchdog()){(void)reboot(RB_AUTOBOOT);return;}
 if(clock_gettime(CLOCK_MONOTONIC,&end)){(void)reboot(RB_AUTOBOOT);return;}
 end.tv_sec+=60;
 if(setup())disable();
 int r;do{r=clock_nanosleep(CLOCK_MONOTONIC,TIMER_ABSTIME,&end,NULL);}while(r==EINTR);
 disable();(void)reboot(RB_AUTOBOOT);''', ''' if(arm_watchdog()){log_open();log_event("reboot","watchdog.arm.failed","-",0);(void)log_call("reboot","watchdog.arm.failed",reboot(RB_AUTOBOOT));return;}
 if(clock_gettime(CLOCK_MONOTONIC,&end)){int e=errno;log_open();log_event("fail","clock_gettime","-",e);log_event("reboot","clock.failed","-",0);(void)log_call("reboot","clock.failed",reboot(RB_AUTOBOOT));return;}
 end.tv_sec+=60;
 log_open();log_uname();
 int setup_rc=setup();log_event(setup_rc?"setup.return.-1":"setup.return.0","setup","-",0);
 if(setup_rc)disable();
 int r;do{r=clock_nanosleep(CLOCK_MONOTONIC,TIMER_ABSTIME,&end,NULL);}while(r==EINTR);
 if(r)log_event("fail","deadline.clock_nanosleep","-",r);
 disable();log_event("reboot","deadline","-",0);(void)log_call("reboot","deadline",reboot(RB_AUTOBOOT));''')
(ROOT / 'source/init.c').write_text(source)
(ROOT / 'source/init.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), source.splitlines(True), fromfile=str(ORIGINAL.relative_to(ROOT.parent)), tofile='source/init.c')))
print('Created logging-only source and exact source diff')
