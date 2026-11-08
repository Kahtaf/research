#include "common.h"
#include "sd_mount.h"
#include <sys/vfs.h>
#include <time.h>
#include <stdarg.h>
#include <stddef.h>

/* No block-device opens, mount calls, subprocesses, generic paths or retry loop. */
typedef struct {uint64_t size;uint32_t part,count;unsigned char full[32];const unsigned char *chunks;} Source;
static Source rows[MAX_IMAGES];
static unsigned char manifest[MAX_MANIFEST],mid[32],data[CHUNK],reply[CHUNK],p10[32];
static size_t manifest_len;static unsigned roles[3],role_count,image_count;
static int role_fds[3]={-1,-1,-1},card=-1,bundle=-1,report=-1,attempt=-1;
enum { PLAN, ONLINE, OFFLINE };
static int execute_mode,rollback=-1,inverse=-1,active_role=-1,mutation_possible;
static unsigned completed;static long daemon_pid;static char run_hex[65],mid_hex[65],trigger[256];
static char arm_hex[65];
static const char *failure="unspecified failure";
#define REQUIRE(condition, message) do {if(!(condition)){failure=(message);return -1;}} while(0)
static void hex(const unsigned char *p,char *out){for(int i=0;i<32;i++)snprintf(out+i*2,3,"%02x",p[i]);}
static int unhex(const char *s,unsigned char *out){for(int i=0;i<32;i++){unsigned a,b;char x=s[i*2],y=s[i*2+1];
 if(x>='0'&&x<='9')a=x-'0';else if(x>='a'&&x<='f')a=x-'a'+10;else return -1;
 if(y>='0'&&y<='9')b=y-'0';else if(y>='a'&&y<='f')b=y-'a'+10;else return -1;out[i]=(a<<4)|b;}return 0;}
static int regular(int fd,off_t length,dev_t dev){struct stat s;return !fstat(fd,&s)&&S_ISREG(s.st_mode)&&s.st_size==length&&s.st_nlink==1&&(!dev||s.st_dev==dev);}
static int ram_file(const char *name,void *buf,size_t min,size_t max,size_t *len){
 int fd=open(name,O_RDONLY|O_CLOEXEC|O_NOFOLLOW|O_NONBLOCK);struct stat s;struct statfs fs;
 REQUIRE(fd>=0,"required RAM input unavailable");
 int ok=!fstat(fd,&s)&&S_ISREG(s.st_mode)&&s.st_uid==0&&!(s.st_mode&0222)&&s.st_nlink==1&&s.st_size>=(off_t)min&&s.st_size<=(off_t)max&&
  !fstatfs(fd,&fs)&&(fs.f_type==0x01021994||fs.f_type==0x858458f6)&&!exact_read(fd,buf,(size_t)s.st_size);
 close(fd);REQUIRE(ok,"RAM input must be immutable root-owned ordinary ramfs/tmpfs file");*len=(size_t)s.st_size;return 0;
}
static uint64_t size_for(unsigned part){
#ifdef SD_FRONTEND_TEST
 return part==9?17:part==25?CHUNK+7:CHUNK+355840;
#else
 return part==9?16740352:part==25?3753902080ULL:11331268096ULL;
#endif
}
static int parse_manifest(void){
 REQUIRE(manifest_len>=112&&!memcmp(manifest,"ASUSR002",8)&&u32(manifest+8)==2,"ASUSR002 required");
 image_count=u32(manifest+12);REQUIRE(image_count==2||image_count==4||image_count==5,"no admitted image roles");
 size_t off=112;for(unsigned i=0;i<image_count;i++){
  REQUIRE(off+52<=manifest_len,"truncated manifest");Source *r=&rows[i];r->part=u32(manifest+off+4);r->size=u64(manifest+off+8);r->count=u32(manifest+off+48);memcpy(r->full,manifest+off+16,32);
  REQUIRE(u32(manifest+off)==i&&r->part==(i==4?26:i%2?9:25)&&r->size==size_for(r->part)&&r->count==(r->size+CHUNK-1)/CHUNK&&r->count<=MAX_CHUNKS,"fixed manifest geometry/role mismatch");
  off+=52;REQUIRE(off+(size_t)r->count*32<=manifest_len,"truncated chunk table");r->chunks=manifest+off;off+=(size_t)r->count*32;
 }
 REQUIRE(off==manifest_len,"manifest trailing bytes");hash(manifest,manifest_len,mid);hex(mid,mid_hex);
 if(rollback<0){REQUIRE(image_count==5,"normal install needs parent-admitted five-role RAM manifest; stock pair is not Android17 admission");roles[0]=2;roles[1]=4;roles[2]=3;role_count=3;}
 else {REQUIRE((unsigned)rollback<image_count,"rollback role unavailable");roles[0]=(unsigned)rollback;role_count=1;}
 REQUIRE(inverse<0||(rollback>=0&&(unsigned)inverse<image_count),"explicit rollback inverse source invalid");return 0;
}
static double seconds(void){struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))return 0;return t.tv_sec+t.tv_nsec/1e9;}
static int transfer(int fd,void *buf,size_t n,int writing,double deadline){
 unsigned char *p=buf;while(n){double left=deadline-seconds();REQUIRE(left>0,"phase deadline expired; no retry");
  struct pollfd f={.fd=fd,.events=writing?POLLOUT:POLLIN};int z=poll(&f,1,(int)(left*1000)+1);
  if(z<0&&errno==EINTR)continue;REQUIRE(z>0,"socket deadline/error; no retry");
  ssize_t k=writing?send(fd,p,n,MSG_NOSIGNAL|MSG_DONTWAIT):recv(fd,p,n,MSG_DONTWAIT);
  if(k<0&&(errno==EINTR||errno==EAGAIN))continue;REQUIRE(k>0,"socket lost; outcome unknown; no retry");p+=k;n-=(size_t)k;
 }return 0;
}
static int request(int fd,unsigned op,const void *p,unsigned n,double deadline){unsigned char h[12];memcpy(h,"RSC1",4);put32(h+4,op);put32(h+8,n);
 return transfer(fd,h,12,1,deadline)||transfer(fd,(void*)p,n,1,deadline)?-1:0;}
static int response(int fd,unsigned op,unsigned min,unsigned max,unsigned *length,double deadline){unsigned char h[12];
 if(transfer(fd,h,12,0,deadline))return -1;unsigned n=u32(h+8);
 REQUIRE(!memcmp(h,"RSC1",4)&&u32(h+4)==op&&n>=min&&n<=max&&n<=CHUNK,"daemon error or malformed response; stop");
 if(transfer(fd,reply,n,0,deadline))return -1;if(length)*length=n;return 0;
}
static int connect_daemon(void){
 int fd=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);REQUIRE(fd>=0,"socket unavailable");
 struct sockaddr_un a={.sun_family=AF_UNIX};strcpy(a.sun_path,"/dev/socket/os_rescue");
 if(connect(fd,(void*)&a,sizeof(a))){close(fd);failure="protected daemon unavailable; no retry";return -1;}
 struct ucred cred;socklen_t len=sizeof(cred);char sec[128]={0};socklen_t sn=sizeof(sec)-1;
 if(getsockopt(fd,SOL_SOCKET,SO_PEERCRED,&cred,&len)||len!=sizeof(cred)||cred.uid!=0||
    getsockopt(fd,SOL_SOCKET,SO_PEERSEC,sec,&sn)||!sn||sn>=sizeof(sec)){close(fd);failure="daemon peer authentication failed";return -1;}
 sec[sn]=0;if(strcmp(sec,"u:r:os_rescue:s0")){close(fd);failure="daemon SELinux peer mismatch";return -1;}
 return fd;
}
static int status_bound(int fd,int first){
 unsigned n;double until=seconds()+30;
 if(request(fd,1,NULL,0,until)||response(fd,0x81,1,1023,&n,until))return -1;reply[n]=0;
 char state[16],manifest_hex[65],run[65];unsigned armed,chunk;int uncertain,enforce,pid,used=0;
 int fields=sscanf((char*)reply,"state=%15s armed=%u writer=idle uncertain_image=%d enforcing=%d protocol=1 max_chunk=%u no_reboot=1 peer_uid=2000 peer_sec=u:r:shell:s0 daemon_pid=%d manifest=%64s run=%64s\n%n",state,&armed,&uncertain,&enforce,&chunk,&pid,manifest_hex,run,&used);
 unsigned char nonce[32];
 REQUIRE(fields==8&&used==(int)n&&(!strcmp(state,"IDLE")||!strcmp(state,"FROZEN"))&&armed==image_count&&enforce==1&&chunk==CHUNK&&pid>0&&strlen(manifest_hex)==64&&!strcmp(manifest_hex,mid_hex)&&strlen(run)==64&&!unhex(run,nonce),"daemon status/actual RAM manifest binding failed");
 unsigned nonzero=0;for(int i=0;i<32;i++)nonzero|=nonce[i];REQUIRE(nonzero,"daemon run nonce unavailable");
 REQUIRE(uncertain>=-1&&(uncertain<0||(unsigned)uncertain<image_count),"invalid daemon uncertainty");
 REQUIRE(uncertain<0||(inverse>=0?uncertain==inverse:uncertain==(int)roles[0]),"daemon requires deliberate same-image reconciliation or explicit rollback inverse");
 REQUIRE(inverse<0||uncertain==inverse,"inverse requires daemon's actual uncertain image");
 if(first){daemon_pid=pid;strcpy(run_hex,run);}else REQUIRE(pid==daemon_pid&&!strcmp(run,run_hex),"daemon restarted; old trigger invalid");
 return 0;
}
static int safe_dir(int parent,const char *name,dev_t dev){
 int fd=openat(parent,name,O_RDONLY|O_DIRECTORY|O_CLOEXEC|O_NOFOLLOW);struct stat s;
 if(fd<0||fstat(fd,&s)||!S_ISDIR(s.st_mode)||(dev&&s.st_dev!=dev)){if(fd>=0)close(fd);failure="fixed directory unavailable or filesystem changed";return -1;}return fd;
}
static int read_fixed(int dir,const char *name,void *buf,size_t size,dev_t dev){
 int fd=openat(dir,name,O_RDONLY|O_CLOEXEC|O_NOFOLLOW|O_NONBLOCK);REQUIRE(fd>=0,"required fixed card file unavailable");
 int rc=regular(fd,(off_t)size,dev)&&!exact_read(fd,buf,size);close(fd);REQUIRE(rc,"card file shape/length/read failed");return 0;
}
static int chunk_read(int dir,const Source *r,unsigned i,unsigned char *out){
 unsigned n=r->size-(uint64_t)i*CHUNK>CHUNK?CHUNK:(unsigned)(r->size-(uint64_t)i*CHUNK);char name[24];snprintf(name,sizeof(name),"%06u.raw",i);
 int fd=openat(dir,name,O_RDONLY|O_CLOEXEC|O_NOFOLLOW|O_NONBLOCK);unsigned char h[32];
 if(fd<0){REQUIRE(errno==ENOENT,"chunk open failed (symlinks and special files forbidden)");memset(out,0,n);}
 else {int ok=regular(fd,n,makedev(179,33))&&!exact_read(fd,out,n);
#ifdef SD_FRONTEND_TEST
  /* Tests use ordinary fixture directories; production always requires SD st_dev. */
  if(!ok){lseek(fd,0,SEEK_SET);ok=regular(fd,n,0)&&!exact_read(fd,out,n);}
#endif
  close(fd);REQUIRE(ok,"chunk exact length/ordinary-file check failed");}
 hash(out,n,h);REQUIRE(!memcmp(h,r->chunks+i*32,32),"missing/nonzero/corrupt chunk; source digest mismatch");return (int)n;
}
static int shape(int dir,int role){
 int dupfd=openat(dir,".",O_RDONLY|O_DIRECTORY|O_CLOEXEC|O_NOFOLLOW);REQUIRE(dupfd>=0,"directory unavailable");DIR *d=fdopendir(dupfd);if(!d){close(dupfd);failure="directory unavailable";return -1;}
 int ok=1;errno=0;struct dirent *e;while((e=readdir(d))){const char *n=e->d_name;if(!strcmp(n,".")||!strcmp(n,".."))continue;
  if(role<0){if(!strcmp(n,"manifest.sha256")||!strcmp(n,"execute.trigger"))continue;int known=0;for(unsigned j=0;j<role_count;j++){char want[16];snprintf(want,sizeof(want),"role-%u",roles[j]);if(!strcmp(n,want))known=1;}if(known)continue;}
  else {unsigned index;int used=0;if(sscanf(n,"%6u.raw%n",&index,&used)==1&&used==10&&strlen(n)==10&&index<rows[role].count){char want[24];snprintf(want,sizeof(want),"%06u.raw",index);if(!strcmp(n,want))continue;}}
  ok=0;break;
 }if(errno)ok=0;closedir(d);REQUIRE(ok,"unexpected bundle/directory entry");return 0;
}
static int card_open(void){
 REQUIRE(sd_mounts_safe(1),"fixed removable SD mount/independent sysfs identity failed");
 int root=open("/",O_RDONLY|O_DIRECTORY|O_CLOEXEC);REQUIRE(root>=0,"root unavailable");int mnt=safe_dir(root,"mnt",0);close(root);if(mnt<0)return -1;card=safe_dir(mnt,"rescue-sd",makedev(179,33));close(mnt);if(card<0)return -1;
 struct statfs fs;REQUIRE(!fstatfs(card,&fs)&&fs.f_type==0x4d44,"source must be fixed removable FAT filesystem");
 bundle=safe_dir(card,"asus-rescue",makedev(179,33));if(bundle<0)return -1;
 report=safe_dir(card,"asus-rescue-report",makedev(179,33));if(report<0)return -1;
 char binding[65];if(read_fixed(bundle,"manifest.sha256",binding,65,makedev(179,33)))return -1;
 REQUIRE(!memcmp(binding,mid_hex,64)&&binding[64]=='\n',"card bundle does not match actual daemon RAM manifest");if(shape(bundle,-1))return -1;
 for(unsigned j=0;j<role_count;j++){char name[16];snprintf(name,sizeof(name),"role-%u",roles[j]);role_fds[j]=safe_dir(bundle,name,makedev(179,33));if(role_fds[j]<0||shape(role_fds[j],roles[j]))return -1;}
 return 0;
}
static int preflight(void){
 uint64_t present=0,logical=0;for(unsigned j=0;j<role_count;j++){
  const Source *r=&rows[roles[j]];SHA full;sha_init(&full);for(unsigned i=0;i<r->count;i++){
   int n=chunk_read(role_fds[j],r,i,data);if(n<0)return -1;sha_add(&full,data,n);
   char name[24];struct stat s;snprintf(name,sizeof(name),"%06u.raw",i);if(!fstatat(role_fds[j],name,&s,AT_SYMLINK_NOFOLLOW))present+=n;
  }unsigned char h[32];sha_end(&full,h);REQUIRE(!memcmp(h,r->full,32),"complete reconstructed raw image hash mismatch");logical+=r->size;
 }
 printf("source_payload_bytes=%llu logical_output_bytes=%llu filesystem_overhead_and_reports_extra=1\n",(unsigned long long)present,(unsigned long long)logical);return 0;
}
static int record(const char *format,...){
 char buf[1024];va_list ap;va_start(ap,format);int n=vsnprintf(buf,sizeof(buf),format,ap);va_end(ap);
 REQUIRE(n>=0&&(size_t)n<sizeof(buf)&&!exact_write(attempt,buf,(size_t)n)&&!fsync(attempt),"card report publication failed; stop");return 0;
}
static int recovery_readback(int fd){
 SHA s;sha_init(&s);uint64_t size=size_for(9);for(unsigned i=0;(uint64_t)i*CHUNK<size;i++){
  unsigned char payload[8],h[32];put32(payload,10);put32(payload+4,i);unsigned n=size-(uint64_t)i*CHUNK>CHUNK?CHUNK:(unsigned)(size-(uint64_t)i*CHUNK);double until=seconds()+600;
  if(request(fd,6,payload,8,until)||response(fd,0x86,32,32,NULL,until))return -1;memcpy(h,reply,32);
  if(response(fd,0x87,n,n,NULL,until))return -1;unsigned char got[32];hash(reply,n,got);REQUIRE(!memcmp(h,got,32),"recovery transport digest failed");sha_add(&s,reply,n);
 }unsigned char h[32];sha_end(&s,h);
 if(execute_mode==OFFLINE)memcpy(p10,h,32);
 else REQUIRE(!memcmp(h,p10,32),"actual recovery differs from immutable parent RAM pin");
 return 0;
}
static int write_role(int fd,unsigned j){
 unsigned role=roles[j];const Source *r=&rows[role];unsigned char payload[104],token[32],same[MAX_CHUNKS];memcpy(payload,mid,32);memcpy(payload+32,p10,32);put32(payload+64,role);
 unsigned op=2,n=68;if(inverse>=0){op=8;n=104;put32(payload+68,(unsigned)inverse);memcpy(payload+72,r->full,32);}
 double until=seconds()+600;
 if(request(fd,op,payload,n,until)||response(fd,0x82,32+r->count,32+r->count,NULL,until))return -1;
 memcpy(token,reply,32);memcpy(same,reply+32,r->count);for(unsigned i=0;i<r->count;i++)REQUIRE(same[i]<=1,"invalid reconciliation bitmap");
 if(record("RECONCILED role=%u\n",role))return -1;
 mutation_possible=1;until=seconds()+600;if(request(fd,3,token,32,until)||response(fd,0x83,0,0,NULL,until))return -1;
 for(unsigned i=0;i<r->count;i++){
  int count=chunk_read(role_fds[j],r,i,data);if(count<0)return -1;
  until=seconds()+60;if(request(fd,same[i]?7:4,same[i]?NULL:data,same[i]?0:(unsigned)count,until)||response(fd,0x84,8,8,NULL,until))return -1;
  REQUIRE(u32(reply)==i&&u32(reply+4)<=1&&(!same[i]||u32(reply+4)==1),"invalid chunk acknowledgment");
 }
 until=seconds()+600;if(request(fd,5,NULL,0,until)||response(fd,0x85,32,32,NULL,until))return -1;
 REQUIRE(!memcmp(reply,r->full,32),"full target readback digest mismatch");
 if(request(fd,9,r->full,32,until)||response(fd,0x89,32,32,NULL,until))return -1;
 REQUIRE(!memcmp(reply,r->full,32),"final result acknowledgment mismatch");
 char h[65];hex(r->full,h);if(record("OBSERVED_FULL_READBACK_AND_FINAL_ACK role=%u sha256=%s\n",role,h))return -1;
 completed++;mutation_possible=0;return 0;
}
static void selection_text(char *out,size_t n){
 if(rollback<0)snprintf(out,n,"install:2,4,3");else snprintf(out,n,"rollback:%d:inverse:%d",rollback,inverse);
}
static int pairing_text(const char *text,char *out){
 unsigned char id[32];REQUIRE(text[64]=='\n'&&!unhex(text,id),"RAM arm must be exactly 64 lowercase hex plus LF");
 memcpy(out,text,64);out[64]=0;return 0;
}
static void make_trigger(const char *selection){
 snprintf(trigger,sizeof(trigger),"%s ASUSR002 %s %s %s\n",execute_mode==OFFLINE?"OFFLINE-PREARMED":"EXECUTE",mid_hex,execute_mode==OFFLINE?arm_hex:run_hex,selection);
}
static int check_trigger(const char *actual,size_t n){
 REQUIRE(n==strlen(trigger)&&!memcmp(actual,trigger,n),"exact profile/manifest/pairing/selection card trigger required");return 0;
}
static int begin_attempt(const char *selection){
 /* A durable existing report survives daemon reboot, irrespective of arm/run. */
 attempt=openat(report,"attempt.txt",O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
 REQUIRE(attempt>=0,"new exclusive attempt report required; never automatically restart/replay");
 if(record("OUTCOME=UNKNOWN profile=%s manifest=%s run=%s arm=%s selection=%s\n",execute_mode==OFFLINE?"OFFLINE-PREARMED":"ONLINE",mid_hex,run_hex,execute_mode==OFFLINE?arm_hex:"none",selection))return -1;
 REQUIRE(!fsync(report),"durable UNKNOWN attempt directory publication failed");return 0;
}
static int run(void){
 REQUIRE(getuid()==2000&&context_is("u:r:shell:s0")&&enforcing(),"requires init-launched UID2000 shell domain, SELinux enforcing");
 if(ram_file("/rescue.manifest",manifest,112,MAX_MANIFEST,&manifest_len)||parse_manifest())return -1;
 int fd=connect_daemon();if(fd<0)return -1;if(status_bound(fd,1)){close(fd);return -1;}
 close(fd);fd=-1; /* No socket is held idle across whole-source preflight. */
 char selection[64];selection_text(selection,sizeof(selection));
 if(execute_mode==OFFLINE){
  char arm[65];size_t length;if(ram_file("/rescue.sd.arm",arm,65,65,&length)||pairing_text(arm,arm_hex))return -1;
 }
 make_trigger(selection);
 printf("mode=%s manifest=%s daemon_pid=%ld run=%s order=%s\nrequired_execute_trigger=%s",execute_mode==OFFLINE?"OFFLINE-PREARMED":execute_mode==ONLINE?"EXECUTE":"PLAN",mid_hex,daemon_pid,run_hex,selection,trigger);fflush(stdout);
 if(card_open()||preflight())return -1;
 if(execute_mode==PLAN){puts("PLAN complete; no reconciliation or mutation requested");return 0;}
 char actual[256];if(read_fixed(bundle,"execute.trigger",actual,strlen(trigger),makedev(179,33))||check_trigger(actual,strlen(trigger)))return -1;
 if(execute_mode==ONLINE){
  char pin[65];size_t length;if(ram_file("/rescue.recovery.sha256",pin,65,65,&length))return -1;
  REQUIRE(pin[64]=='\n'&&!unhex(pin,p10),"immutable parent recovery pin invalid");
 }
 if(begin_attempt(selection))return -1;
 /* Deliberate post-preflight connection; never rebind to a restarted daemon. */
 fd=connect_daemon();if(fd<0)return -1;if(status_bound(fd,0)){close(fd);return -1;}
 if(recovery_readback(fd)){close(fd);return -1;}
 char baseline[65];hex(p10,baseline);
 if(record("RECOVERY_BASELINE sha256=%s bytes=%llu binding=%s independent_admission_proven=0\n",baseline,(unsigned long long)size_for(9),execute_mode==OFFLINE?"runtime-stability":"parent-independent-pin")){close(fd);return -1;}
 for(unsigned j=0;j<role_count;j++){
  active_role=(int)roles[j];if(j){fd=connect_daemon();if(fd<0)return -1;if(status_bound(fd,0)){close(fd);return -1;}}
  if(!sd_mounts_safe(1)){close(fd);failure="SD mount identity changed";return -1;}
  if(write_role(fd,j)){close(fd);return -1;}close(fd);
 }
 if(record("OBSERVED_SEQUENCE_COMPLETE roles=%u historical_report_does_not_authorize_retry=1\n",completed)||fsync(report))return -1;
 puts("live_result=COMPLETE full_readback_and_final_ack_received=1 no_reboot=1");return 0;
}
#ifndef SD_FRONTEND_LIBRARY
int main(int argc,char **argv){
 for(int i=1;i<argc;i++){
  if(!strcmp(argv[i],"--execute")&&execute_mode==PLAN)execute_mode=ONLINE;
  else if(!strcmp(argv[i],"--offline-prearmed")&&execute_mode==PLAN)execute_mode=OFFLINE;
  else if(!strcmp(argv[i],"--rollback-system")&&rollback<0)rollback=0;
  else if(!strcmp(argv[i],"--rollback-boot")&&rollback<0)rollback=1;
  else if(!strncmp(argv[i],"--inverse-from=",15)&&inverse<0&&strlen(argv[i])==16&&argv[i][15]>='0'&&argv[i][15]<='4')inverse=argv[i][15]-'0';
  else {fputs("usage: sd_frontend [--execute|--offline-prearmed] [--rollback-system|--rollback-boot] [--inverse-from=0..4]\n",stderr);return 64;}
 }
 signal(SIGPIPE,SIG_IGN);int rc=run();if(rc){const char *saved=failure;
  if(attempt>=0)(void)record("STOP outcome=UNKNOWN role=%d completed=%u mutation_possible=%d error=%s\n",active_role,completed,mutation_possible,saved);
  fprintf(stderr,"STOP: %s; completed=%u mutation_possible=%d; no continuation/retry/reboot\n",saved,completed,mutation_possible);
 }
 if(attempt>=0)close(attempt);if(report>=0)close(report);if(bundle>=0)close(bundle);if(card>=0)close(card);
 for(unsigned j=0;j<role_count;j++)if(role_fds[j]>=0)close(role_fds[j]);return rc?1:0;
}
#endif
