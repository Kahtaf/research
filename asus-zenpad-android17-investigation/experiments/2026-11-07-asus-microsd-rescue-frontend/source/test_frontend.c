#define RESCUE_TEST
#define SD_FRONTEND_TEST
#define SD_FRONTEND_LIBRARY
#include "sd_frontend.c"
#include <assert.h>
#include <sys/wait.h>
const char *test_root="artifacts/fixture-sys";
static void manifest_fixture(unsigned count){
 memset(manifest,0,sizeof(manifest));memcpy(manifest,"ASUSR002",8);put32(manifest+8,2);put32(manifest+12,count);size_t off=112;
 for(unsigned i=0;i<count;i++){
  unsigned part=i==4?26:i%2?9:25;uint64_t size=size_for(part);unsigned n=(size+CHUNK-1)/CHUNK;put32(manifest+off,i);put32(manifest+off+4,part);
  put32(manifest+off+8,(unsigned)size);put32(manifest+off+12,(unsigned)(size>>32));put32(manifest+off+48,n);
  SHA s;sha_init(&s);for(unsigned j=0;j<n;j++){unsigned len=size-(uint64_t)j*CHUNK>CHUNK?CHUNK:(unsigned)(size-(uint64_t)j*CHUNK);memset(data,0,len);sha_add(&s,data,len);hash(data,len,manifest+off+52+j*32);}sha_end(&s,manifest+off+16);off+=52+32*n;
 }manifest_len=off;
}
static void server(int fd,int lose_ack){
 unsigned op,n;assert(!frame_in(fd,&op,data,&n)&&op==2&&n==68&&u32(data+64)==4);
 unsigned char rec[32+MAX_CHUNKS]={0};assert(!frame_out(fd,0x82,rec,32+rows[4].count));
 assert(!frame_in(fd,&op,data,&n)&&op==3&&n==32);assert(!frame_out(fd,0x83,NULL,0));
 for(unsigned i=0;i<rows[4].count;i++){
  assert(!frame_in(fd,&op,data,&n)&&op==4&&n==(i?355840:CHUNK));
  unsigned char h[32];hash(data,n,h);assert(!memcmp(h,rows[4].chunks+i*32,32));unsigned char ack[8];put32(ack,i);put32(ack+4,0);assert(!frame_out(fd,0x84,ack,8));
 }
 assert(!frame_in(fd,&op,data,&n)&&op==5&&n==0);assert(!frame_out(fd,0x85,rows[4].full,32));
 assert(!frame_in(fd,&op,data,&n)&&op==9&&n==32&&!memcmp(data,rows[4].full,32));
 if(!lose_ack)assert(!frame_out(fd,0x89,data,32));close(fd);_exit(0);
}
static void exchange_case(int lose_ack){
 int pair[2];assert(!socketpair(AF_UNIX,SOCK_STREAM,0,pair));pid_t pid=fork();assert(pid>=0);
 if(!pid){close(pair[0]);server(pair[1],lose_ack);}close(pair[1]);
 roles[0]=4;role_fds[0]=open("artifacts/chunks",O_RDONLY|O_DIRECTORY);assert(role_fds[0]>=0);
 char reportname[128];snprintf(reportname,sizeof(reportname),"artifacts/report-%d.txt",lose_ack);attempt=open(reportname,O_CREAT|O_EXCL|O_WRONLY,0600);assert(attempt>=0);
 completed=0;mutation_possible=0;int rc=write_role(pair[0],0);assert((rc<0)==lose_ack);assert(completed==(lose_ack?0U:1U));assert(mutation_possible==lose_ack);
 close(pair[0]);close(attempt);attempt=-1;close(role_fds[0]);int status;assert(waitpid(pid,&status,0)==pid&&WIFEXITED(status)&&WEXITSTATUS(status)==0);
}
int main(void){
 signal(SIGPIPE,SIG_IGN);
 manifest_fixture(2);assert(parse_manifest()<0);manifest_fixture(5);assert(!parse_manifest());assert(role_count==3&&roles[0]==2&&roles[1]==4&&roles[2]==3);
 int d=open("artifacts/chunks",O_RDONLY|O_DIRECTORY);assert(d>=0);
 assert(chunk_read(d,&rows[4],1,data)==355840); /* omitted exact final zero chunk */
 unsigned char *digest=(unsigned char*)rows[4].chunks;digest[32]^=1;assert(chunk_read(d,&rows[4],1,data)<0);digest[32]^=1;
 assert(!symlink("missing","artifacts/chunks/000001.raw"));assert(chunk_read(d,&rows[4],1,data)<0);assert(!unlink("artifacts/chunks/000001.raw"));
 int f=openat(d,"000001.raw",O_CREAT|O_EXCL|O_WRONLY,0600);assert(f>=0);assert(!ftruncate(f,355839));close(f);assert(chunk_read(d,&rows[4],1,data)<0);assert(!unlink("artifacts/chunks/000001.raw"));close(d);
 puts("PASS fixed role admission/order and exact-tail omitted-zero/nonzero/symlink/short cases");
 assert(sd_identified());assert(sd_mounts_safe(1));
 const char *line="1 0 179:0 / /bad rw - ext4 /dev/block/mmcblk0 rw\n";
 FILE *m=fopen("artifacts/fixture-sys/proc/self/mountinfo","ae");assert(m);fputs(line,m);fclose(m);assert(!sd_mounts_safe(0));
 puts("PASS independently identified removable SD permitted; mounted internal eMMC rejected");
 exchange_case(0);exchange_case(1);puts("PASS full readback + final acknowledgment accepted; lost final ack stays UNKNOWN with no completion");return 0;
}
