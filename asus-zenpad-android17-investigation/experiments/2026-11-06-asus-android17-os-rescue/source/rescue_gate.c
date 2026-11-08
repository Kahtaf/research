/* Freestanding request gate, shared by host prototype and future root daemon.
 * No paths, shell strings, arbitrary offsets, ioctls or syscalls are accepted.
 * Operations: 1 restore boot, 2 restore system, 3 install system, 4 install boot,
 * 5 provision fresh userdata, 6 invalidate ONLY old FDE footer magic.
 * Readback: 7 boot, 8 system, 9 recovery, 10 userdata, 11 metadata.
 * Geometry comes from independently verified GPT, not firmware scatter.
 */
typedef unsigned long long u64;
typedef unsigned int u32;
struct geometry {u64 start,sectors;u32 partition,major,minor,logical_sector;};
static const struct geometry parts[]={
 {127488,32696,9,179,9,512},{1072424,7331840,25,179,25,512},
 {160184,32696,10,179,10,512},{8404264,22131383,26,179,26,512},
 {294184,65536,20,179,20,512}};
int rescue_part(unsigned op) {
 switch(op){case 1:case 4:case 7:return 0;case 2:case 3:case 8:return 1;
 case 9:return 2;case 5:case 10:return 3;case 6:case 11:return 4;default:return -1;}
}
int rescue_geometry(unsigned op,const struct geometry *observed) {
 int n=rescue_part(op);if(n<0 || !observed)return 0;
 const struct geometry *p=&parts[n];
 return p->start==observed->start && p->sectors==observed->sectors &&
 p->partition==observed->partition && p->major==observed->major &&
 p->minor==observed->minor && p->logical_sector==observed->logical_sector;
}
u64 rescue_size(unsigned op) {int n=rescue_part(op);return n<0?0:parts[n].sectors*512;}
int rescue_frame(unsigned op,u64 offset,u64 count,u64 expected_offset,unsigned phase,
 unsigned peer_uid,unsigned shell_domain,unsigned approved,unsigned migration,unsigned footer_review) {
 if(rescue_part(op)<0 || peer_uid!=2000 || shell_domain!=1 || approved!=1)return 0;
 if((op==5 || op==6 || op==10 || op==11) && migration!=1)return 0;
 if(op==6 && footer_review!=1)return 0;
 if(phase!=1 || offset!=expected_offset || !count || count>1048576)return 0;
 u64 size=op==6?4:rescue_size(op);
 if(offset>size || count>size-offset)return 0;
 if(op==6)return offset==0 && count==4;
 return offset%512==0 && count%512==0;
}
#ifdef RESCUE_UNARMED
/* Deliberately cannot serve or mutate. Manifest, Linux adapter and policy integration
 * are parent review work. This binary is NOT a rescue environment. */
void _start(void) {
 register long x8 __asm__("x8")=94;
 register long x0 __asm__("x0")=78;
 __asm__ volatile("svc 0" : : "r"(x8),"r"(x0) : "memory");
 for(;;){}
}
#endif
