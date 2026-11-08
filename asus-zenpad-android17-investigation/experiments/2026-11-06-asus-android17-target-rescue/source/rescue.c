#include "common.h"
#ifdef RESCUE_TEST
const char *test_root="";
#endif
typedef struct {int part;const char*alias;uint64_t start,size;} Geometry;
static const Geometry geometry[]={
#if defined(RESCUE_TEST) && !defined(RESCUE_FULL_GEOMETRY)
 {9,"boot",127488,2ULL*CHUNK+512},{10,"recovery",160184,8192},{25,"system",1072424,3ULL*CHUNK+512},{26,"userdata",8404264,5ULL*CHUNK+3584},{0,NULL,0,65536}
#else
 {9,"boot",127488,16740352},{10,"recovery",160184,16740352},{25,"system",1072424,3753902080ULL},{26,"userdata",8404264,11331268096ULL},{0,NULL,0,15634268160ULL}
#endif
};
typedef struct {uint32_t role,part,count;uint64_t size;unsigned char full[32];const unsigned char*chunks;} Image;
static unsigned char manifest[MAX_MANIFEST],manifest_id[32],cid[32],gpt1[32],gpt2[32];
static size_t manifest_size;
static Image images[MAX_IMAGES];static uint32_t image_count;
static unsigned char io_buf[CHUNK] __attribute__((aligned(4096)));
static unsigned char wire[CHUNK] __attribute__((aligned(4096)));
static unsigned char recovery_pin[32];
static int frozen=1,uncertain_image=-1;
#ifdef RESCUE_TEST
static const char*fault;
static int injected(const char*n){return fault&&!strcmp(fault,n);}
#else
#define injected(n) 0
#endif
static const Geometry*geom(int part){for(size_t i=0;i<sizeof(geometry)/sizeof(*geometry);i++)if(geometry[i].part==part)return &geometry[i];return NULL;}
static int readat(int fd,void*b,size_t n,uint64_t off){ssize_t z;do{z=pread(fd,b,injected("shortread")&&n>1?n-1:n,(off_t)off);}while(z<0&&errno==EINTR);return z==(ssize_t)n&&!injected("read")?0:-1;}
static int writeat(int fd,const void*b,size_t n,uint64_t off){ssize_t z;
if(injected("write")){ssize_t partial=pwrite(fd,b,n/2,(off_t)off);(void)partial;return -1;}
do{z=pwrite(fd,b,n,(off_t)off);}while(z<0&&errno==EINTR);return z==(ssize_t)n?0:-1;}
static int flush(int fd){return injected("flush")?-1:fsync(fd);}
static int fd_hash(int fd,uint64_t size,unsigned char*out){SHA s;sha_init(&s);for(uint64_t off=0;off<size;){size_t n=size-off>CHUNK?CHUNK:(size_t)(size-off);if(readat(fd,io_buf,n,off))return -1;sha_add(&s,io_buf,n);off+=n;}sha_end(&s,out);return 0;}
static int empty_dir(const char*n){char p[512];path(p,sizeof(p),n);DIR*d=opendir(p);if(!d)return 0;int ok=1;struct dirent*e;errno=0;while((e=readdir(d)))if(strcmp(e->d_name,".")&&strcmp(e->d_name,".."))ok=0;if(errno)ok=0;closedir(d);return ok;}
static int mounts_clear(void){char p[512],line[8192];path(p,sizeof(p),"/proc/self/mountinfo");FILE*f=fopen(p,"re");if(!f)return 0;int ok=1;while(fgets(line,sizeof(line),f)){unsigned a,b,maj,min;if(!strchr(line,'\n')||sscanf(line,"%u %u %u:%u",&a,&b,&maj,&min)!=4){ok=0;break;}if(maj==179){ok=0;break;}}if(ferror(f))ok=0;fclose(f);return ok;}
static int sysnum(int part,const char*field,uint64_t want){char p[128],t[128],*end;snprintf(p,sizeof(p),"/sys/dev/block/179:%d/%s",part,field);if(read_text(p,t,sizeof(t))<1)return 0;errno=0;unsigned long long x=strtoull(t,&end,10);return !errno&&!*end&&x==want;}
static int validate_fd(int fd,const Geometry*g){
struct stat s,l,a;char n[128],p[512],alias[512],resolved[4096],expected[512],text[64];
if(fstat(fd,&s))return -1;
snprintf(n,sizeof(n),g->part?"/dev/block/mmcblk0p%d":"/dev/block/mmcblk0",g->part);path(p,sizeof(p),n);
if(lstat(p,&l)||l.st_ino!=s.st_ino||l.st_dev!=s.st_dev)return -1;
#ifdef RESCUE_TEST
if(!S_ISREG(s.st_mode)||s.st_size!=(off_t)g->size)return -1;
#else
uint64_t bytes=0;char label[128]={0};
const char*want=g->part==9?"u:object_r:rescue_boot_device:s0":g->part==25?"u:object_r:rescue_system_device:s0":g->part==10?"u:object_r:rescue_recovery_device:s0":g->part==26?"u:object_r:rescue_userdata_device:s0":"u:object_r:rescue_disk_device:s0";
if(fgetxattr(fd,"security.selinux",label,sizeof(label)-1)<1||strcmp(label,want))return -1;
if(!S_ISBLK(s.st_mode)||s.st_uid!=0||s.st_gid!=0||(s.st_mode&0777)!=0600||s.st_rdev!=makedev(179,g->part)||ioctl(fd,BLKGETSIZE64,&bytes)||bytes!=g->size)return -1;
#endif
snprintf(n,sizeof(n),"/sys/dev/block/179:%d/dev",g->part);
snprintf(p,sizeof(p),"179:%d",g->part);
if(read_text(n,text,sizeof(text))<1||strcmp(text,p)||!sysnum(g->part,"size",g->size/512))return -1;
if(g->part&&!sysnum(g->part,"start",g->start))return -1;
snprintf(n,sizeof(n),"/sys/dev/block/179:%d/holders",g->part);if(!empty_dir(n)||!mounts_clear())return -1;
if(g->alias){snprintf(n,sizeof(n),"/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/%s",g->alias);path(alias,sizeof(alias),n);
snprintf(n,sizeof(n),"/dev/block/mmcblk0p%d",g->part);path(expected,sizeof(expected),n);
if(!realpath(alias,resolved)||strcmp(resolved,expected)||stat(alias,&a)||a.st_dev!=s.st_dev||a.st_ino!=s.st_ino||a.st_rdev!=s.st_rdev)return -1;}
return 0;}
static int open_part(int part,int write_mode){const Geometry*g=geom(part);if(!g||(write_mode&&part!=9&&part!=25&&!(part==26&&image_count==5)))return -1;char n[64],p[512];snprintf(n,sizeof(n),part?"/dev/block/mmcblk0p%d":"/dev/block/mmcblk0",part);path(p,sizeof(p),n);int flags=(write_mode?O_RDWR:O_RDONLY)|O_NOFOLLOW|O_CLOEXEC;
#ifndef RESCUE_TEST
flags|=O_DIRECT;
#endif
int fd=open(p,flags);if(fd<0)return -1;if(validate_fd(fd,g)){close(fd);return -1;}return fd;}
static int identity(void){char t[80];unsigned char digest[32];if(!enforcing()||read_text("/sys/class/block/mmcblk0/device/cid",t,sizeof(t))!=32)return -1;
for(int i=0;i<32;i++)if(!((t[i]>='0'&&t[i]<='9')||(t[i]>='a'&&t[i]<='f')))return -1;
hash(t,32,digest);if(memcmp(digest,cid,32))return -1;
int f=open_part(0,0);if(f<0)return -1;int rc=-1;
if(!readat(f,io_buf,17408,0)){hash(io_buf,17408,digest);if(!memcmp(digest,gpt1,32)&&!readat(f,io_buf,16896,geom(0)->size-16896)){hash(io_buf,16896,digest);if(!memcmp(digest,gpt2,32))rc=0;}}
close(f);return rc;}
static int recovery_ok(void){unsigned char h[32];int f=open_part(10,0);if(f<0)return -1;int rc=fd_hash(f,geom(10)->size,h)||memcmp(h,recovery_pin,32);close(f);return rc?-1:0;}
static int load_manifest(void){char p[512];path(p,sizeof(p),"/rescue.manifest");int f=open(p,O_RDONLY|O_NOFOLLOW|O_CLOEXEC);if(f<0)return -1;struct stat st;
if(fstat(f,&st)||!S_ISREG(st.st_mode)||st.st_size<112||st.st_size>MAX_MANIFEST){close(f);return -1;}
manifest_size=(size_t)st.st_size;int rc=exact_read(f,manifest,manifest_size);close(f);if(rc||memcmp(manifest,"ASUSR002",8)||u32(manifest+8)!=2)return -1;
image_count=u32(manifest+12);if(image_count!=0&&image_count!=2&&image_count!=4&&image_count!=5)return -1;
memcpy(cid,manifest+16,32);memcpy(gpt1,manifest+48,32);memcpy(gpt2,manifest+80,32);
size_t off=112;for(uint32_t i=0;i<image_count;i++){if(off+52>manifest_size)return -1;Image*m=&images[i];m->role=u32(manifest+off);m->part=u32(manifest+off+4);m->size=u64(manifest+off+8);memcpy(m->full,manifest+off+16,32);m->count=u32(manifest+off+48);off+=52;
if(m->role!=i||m->part!=(i==4?26:i%2?9:25)||m->size!=geom(m->part)->size||m->count!=(m->size+CHUNK-1)/CHUNK||m->count>MAX_CHUNKS||off+(size_t)m->count*32>manifest_size)return -1;
m->chunks=manifest+off;off+=(size_t)m->count*32;}
if(off!=manifest_size)return -1;
#ifndef RESCUE_TEST
if(image_count){
static const unsigned char expected_boot[32]={0x7b,0xb6,0x85,0x11,0xb1,0xad,0xe3,0x4d,0x24,0xc3,0xe9,0x32,0xda,0x72,0x60,0xe6,0x75,0x3f,0xa8,0x72,0x70,0xbd,0x82,0x49,0xa7,0x21,0x87,0x55,0xa5,0xdf,0x33,0x16};
static const unsigned char expected_primary[32]={0xf8,0x7e,0x70,0x58,0x67,0x06,0xb0,0x6d,0x02,0x9a,0x2b,0xc8,0x52,0x1f,0x1b,0x8a,0xe9,0x17,0x68,0x73,0xcb,0xa1,0xe5,0xb4,0x28,0x1c,0xba,0xca,0x81,0x67,0x42,0xae};
static const unsigned char expected_backup[32]={0x2b,0xf9,0x91,0x12,0x5a,0x74,0xbf,0x36,0x0d,0x0c,0xf4,0xeb,0x21,0x7d,0xf3,0x69,0xba,0x2f,0x78,0xac,0xf3,0xdd,0x31,0x2f,0x26,0xdc,0x76,0x95,0xd2,0xf3,0x17,0x84};
if(memcmp(images[1].full,expected_boot,32)||memcmp(gpt1,expected_primary,32)||memcmp(gpt2,expected_backup,32))return -1;
}
#endif
hash(manifest,manifest_size,manifest_id);return 0;}
static int journal(int index,const char*state){char p[512],q[512],d[512],body[256],mi[65],ri[65];for(int i=0;i<32;i++){snprintf(mi+i*2,3,"%02x",manifest_id[i]);snprintf(ri+i*2,3,"%02x",recovery_pin[i]);}path(p,sizeof(p),"/dev/rescue-state/journal.new");path(q,sizeof(q),"/dev/rescue-state/journal");path(d,sizeof(d),"/dev/rescue-state");
int f=open(p,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);if(f<0)return -1;
int n=snprintf(body,sizeof(body),"%s image=%d manifest=%s p10=%s\n",state,index,mi,ri);int rc=exact_write(f,body,n)||flush(f);if(close(f))rc=-1;
if(injected("publish")||rc||rename(p,q))return -1;
f=open(d,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);if(f<0)return -1;rc=flush(f);close(f);return rc;}
static int clear_pending(void){char p[512],d[512];struct stat st;path(p,sizeof(p),"/dev/rescue-state/journal.new");path(d,sizeof(d),"/dev/rescue-state");
if(lstat(p,&st)){return errno==ENOENT?0:-1;}
if(!S_ISREG(st.st_mode)||st.st_uid!=getuid()||st.st_nlink!=1||unlink(p))return -1;
int fd=open(d,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);if(fd<0)return -1;int rc=flush(fd);close(fd);return rc;}
static int new_token(unsigned char*b){int f=open("/dev/urandom",O_RDONLY|O_CLOEXEC|O_NOFOLLOW);if(f<0)return -1;int rc=exact_read(f,b,32);close(f);return rc;}
static int verify_image(unsigned role){Image*m=&images[role];int fd=open_part(m->part,0);unsigned char h[32];if(fd<0)return -1;int rc=fd_hash(fd,m->size,h)||memcmp(h,m->full,32);close(fd);return rc?-1:0;}
static int prerequisite(Image*m){
if(m->role==4)return verify_image(2);
if(m->part!=9)return 0;
if(verify_image(m->role-1))return -1;
return m->role==3&&image_count==5?verify_image(4):0;
}
static int send_status(int c){char msg[512],id[65];for(int i=0;i<32;i++)snprintf(id+i*2,3,"%02x",manifest_id[i]);int n=snprintf(msg,sizeof(msg),"state=%s armed=%u writer=idle uncertain_image=%d enforcing=%d protocol=1 max_chunk=%u no_reboot=1 peer_uid=2000 peer_sec=u:r:shell:s0 daemon_pid=%d manifest=%s\n",frozen?"FROZEN":"IDLE",image_count,uncertain_image,enforcing(),CHUNK,getpid(),id);return frame_out(c,0x81,msg,n);}
static int error_reply(int c,const char*s){(void)frame_out(c,0xff,s,strlen(s));return -1;}
static int session(int c){
uint32_t op,n;int fd=-1;unsigned char token[32],h[32],same[MAX_CHUNKS];int index=-1;uint32_t next=0;enum{IDLE,RECONCILED,WRITING,VERIFIED}state=IDLE;int rc=-1;
while(!frame_in(c,&op,wire,&n)){
if(op==1&&n==0&&state==IDLE){if(send_status(c))break;continue;}
if(((op==2&&n==68)||(op==8&&n==104))&&state==IDLE){
index=(int)u32(wire+64);if(!image_count||memcmp(wire,manifest_id,32)||index<0||(uint32_t)index>=image_count||(uncertain_image>=0&&memcmp(wire+32,recovery_pin,32))||(op==2&&uncertain_image>=0&&index!=uncertain_image)||(op==8&&(uncertain_image<0||u32(wire+68)!=(uint32_t)uncertain_image||index>1||memcmp(wire+72,images[index].full,32)))){error_reply(c,"manifest/image mismatch; deliberate same-image reconciliation required");break;}
memcpy(recovery_pin,wire+32,32);Image*m=&images[index];
if(identity()||recovery_ok()||prerequisite(m)){error_reply(c,"identity/recovery/system prerequisite failed");break;}
fd=open_part(m->part,0);if(fd<0){error_reply(c,"node guard failed");break;}
for(uint32_t j=0;j<m->count;j++){uint64_t off=(uint64_t)j*CHUNK;size_t count=m->size-off>CHUNK?CHUNK:(size_t)(m->size-off);if(readat(fd,io_buf,count,off))goto done;hash(io_buf,count,h);same[j]=!memcmp(h,m->chunks+j*32,32);}
close(fd);fd=-1;
if(identity()||recovery_ok()||clear_pending()||new_token(token))break;
memcpy(wire,token,32);memcpy(wire+32,same,m->count);
if(frame_out(c,0x82,wire,32+m->count))break;state=RECONCILED;continue;}
if(op==3&&n==32&&state==RECONCILED&&!memcmp(wire,token,32)){
Image*m=&images[index];if(identity()||recovery_ok()||prerequisite(m))break;
frozen=1;uncertain_image=index;
if(journal(index,"UNCERTAIN"))break;
fd=open_part(m->part,1);if(fd<0)break;state=WRITING;next=0;
if(frame_out(c,0x83,NULL,0))break;continue;}
if((op==4||op==7)&&state==WRITING){Image*m=&images[index];if(next>=m->count)break;uint64_t off=(uint64_t)next*CHUNK;uint32_t count=m->size-off>CHUNK?CHUNK:(uint32_t)(m->size-off);
if(op==4){if(n!=count)break;hash(wire,n,h);if(memcmp(h,m->chunks+next*32,32)){error_reply(c,"chunk digest mismatch");break;}}else if(n!=0)break;
n=count;
/* Short I/O is uncertain; never retry it. Re-read the current chunk even after reconciliation. */
if(identity()||validate_fd(fd,geom(m->part))||recovery_ok()||readat(fd,io_buf,n,off))break;
hash(io_buf,n,h);int skipped=!memcmp(h,m->chunks+next*32,32);
if(op==7&&!skipped)break;
if(!skipped){if(writeat(fd,wire,n,off)||flush(fd)||readat(fd,io_buf,n,off))break;hash(io_buf,n,h);if(memcmp(h,m->chunks+next*32,32))break;}
unsigned char ack[8];put32(ack,next++);put32(ack+4,skipped);
if(injected("ack")||frame_out(c,0x84,ack,8))break;continue;}
if(op==5&&n==0&&state==WRITING){Image*m=&images[index];if(next!=m->count||flush(fd)||fd_hash(fd,m->size,h)||memcmp(h,m->full,32)||identity()||recovery_ok()||validate_fd(fd,geom(m->part)))break;
if(close(fd)){fd=-1;break;}fd=-1;if(journal(index,"VERIFIED"))break;
/* Even a lost final acknowledgement leaves mutation frozen until a new reconciliation. */
if(frame_out(c,0x85,h,32))break;state=VERIFIED;continue;}
if(op==9&&n==32&&state==VERIFIED&&!memcmp(wire,images[index].full,32)){
if(identity()||recovery_ok()||frame_out(c,0x89,wire,32))break;frozen=0;uncertain_image=-1;rc=0;goto done;}
if(op==6&&n==8&&state==IDLE){int part=(int)u32(wire);uint32_t chunk=u32(wire+4);const Geometry*g=geom(part);
if(!image_count||!g||!part||(part==26&&image_count!=5)||(uint64_t)chunk*CHUNK>=g->size||identity()){error_reply(c,"readback guard failed");break;}
fd=open_part(part,0);if(fd<0)break;uint64_t off=(uint64_t)chunk*CHUNK;uint32_t count=g->size-off>CHUNK?CHUNK:(uint32_t)(g->size-off);
if(readat(fd,io_buf,count,off))break;close(fd);fd=-1;hash(io_buf,count,h);
if(frame_out(c,0x86,h,32)||frame_out(c,0x87,io_buf,count))break;continue;}
error_reply(c,"invalid state/opcode/length");break;
}
done:if(fd>=0)close(fd);if((state==WRITING||state==VERIFIED)&&rc!=0)frozen=1;return rc;
}
static int serve(void){
if(getuid()!=0)return 81; if(!context_is("u:r:os_rescue:s0"))return 82; if(!enforcing())return 83; if(load_manifest())return 84;
/* An exclusive abstract Unix bind is the lifetime writer lock. It also works
   on kernels without CONFIG_FILE_LOCKING, and cannot outlive its process. */
int lock=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);
struct sockaddr_un lockaddr={.sun_family=AF_UNIX};
memcpy(lockaddr.sun_path+1,"asus-rescue-writer-v1",21);
if(lock<0||bind(lock,(void*)&lockaddr,offsetof(struct sockaddr_un,sun_path)+22))return 73;
/* A stale publication file is removed only while holding the lifetime writer lock. */
if(clear_pending())return 74;
const char*env=getenv("ANDROID_SOCKET_os_rescue");if(!env)return 78;char*end;long sock=strtol(env,&end,10);if(*end||sock<3||sock>1024)return 78;
struct sockaddr_un address; socklen_t address_size=sizeof(address); int socket_type=0; socklen_t type_size=sizeof(socket_type);
if(getsockname((int)sock,(void*)&address,&address_size)||address.sun_family!=AF_UNIX||address_size<offsetof(struct sockaddr_un,sun_path)+22||address_size>sizeof(address)||memcmp(address.sun_path,"/dev/socket/os_rescue",22)||getsockopt((int)sock,SOL_SOCKET,SO_TYPE,&socket_type,&type_size)||socket_type!=SOCK_STREAM)return 74;
if(listen((int)sock,1))return 74;signal(SIGPIPE,SIG_IGN);
for(;;){int c=accept4((int)sock,NULL,NULL,SOCK_CLOEXEC);if(c<0){if(errno==EINTR)continue;return 74;}
struct timeval tv={15,0};if(setsockopt(c,SOL_SOCKET,SO_RCVTIMEO,&tv,sizeof(tv))||setsockopt(c,SOL_SOCKET,SO_SNDTIMEO,&tv,sizeof(tv))||!peer_ok(c)){close(c);continue;}
(void)session(c);shutdown(c,SHUT_RDWR);close(c);}
}
#ifndef RESCUE_LIBRARY
int main(int argc,char**argv){return argc==2&&!strcmp(argv[1],"--serve")?serve():64;}
#endif
