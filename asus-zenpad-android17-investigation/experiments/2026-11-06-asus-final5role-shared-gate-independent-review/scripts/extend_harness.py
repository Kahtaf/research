"""Generate only a host syscall-model extension. Never edit production C/H."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
T=R/'NONDEPLOYABLE/tests'
s=(T/'integration.c').read_text()
def edit(old,new):
 global s
 assert s.count(old)==1,old
 s=s.replace(old,new)
edit('static int self_opens,p10_stops,identity_entries;', 'static int self_opens,p10_stops,identity_entries;\nstatic int self_maps, manifest_reads;')
edit('if(!strcmp(p,"/rescue.manifest"))event("manifest");', 'if(!strcmp(p,"/rescue.manifest")){manifest_reads++;event("manifest");}')
# Every injection is in a syscall model or caller fixture setup, never in the
# production parser/session/gates/identity/proof implementations.
edit('int host_fstat(int fd,struct stat *st){int rc=fstat(fd,st);if(!rc&&fd==self_fd){st->st_uid=st->st_gid=0;st->st_mode=(st->st_mode&~0777)|0700;}return rc;}', '''int host_fstat(int fd,struct stat *st){int rc=fstat(fd,st);if(!rc&&fd==self_fd){
 st->st_uid=st->st_gid=0;st->st_mode=(st->st_mode&~0777)|0700;
 if(is("h_self_fstat")){errno=EIO;return -1;}
 if(is("h_self_uid"))st->st_uid=1;
 if(is("h_self_gid"))st->st_gid=1;
 if(is("h_self_mode"))st->st_mode=(st->st_mode&~0777)|0755;
 if(is("h_self_type"))st->st_mode=(st->st_mode&~S_IFMT)|S_IFDIR;
 if(is("h_self_links"))st->st_nlink=2;
 if(is("h_self_zero"))st->st_size=0;
 if(is("h_self_oversize"))st->st_size=2*1024*1024+1;
 }return rc;}
void *host_mmap(void *a,size_t n,int prot,int flags,int fd,off_t off){
 assert(phase=='H'&&fd==self_fd&&prot==PROT_READ&&flags==MAP_PRIVATE&&off==0);
 self_maps++;event("self-map");if(is("h_self_mmap")){errno=ENOMEM;return MAP_FAILED;}
 return mmap(a,n,prot,flags,fd,off);
}''')
edit('if(fd==self_fd)self_fd=-1;', 'if(fd==self_fd){self_fd=-1;if(is("h_self_close")){int rc=close(fd);assert(!rc);errno=EIO;return -1;}}')
edit('if(opt==SO_PEERCRED){event("peeruid");', '''if(opt==SO_PEERCRED){event("peeruid");
 if(is("h_peercred_error")){errno=EIO;return -1;}
 if(is("h_peercred_short")){*n=sizeof(struct ucred)-1;return 0;}''')
edit('assert(opt==SO_PEERSEC);event("peersec");', '''assert(opt==SO_PEERSEC);event("peersec");
 if(is("h_peersec_error")){errno=EIO;return -1;}
 if(is("h_peersec_zero")){*n=0;return 0;}
 if(is("h_peersec_long")){*n=128;return 0;}''')
edit('memcpy(p,&a,sizeof(a));*n=offsetof(struct sockaddr_un,sun_path)+22;return 0;', '''if(is("h_lock_family"))a.sun_family=AF_INET;
 if(is("h_lock_named"))a.sun_path[0]='x';
 if(is("h_lock_name"))a.sun_path[4]^=1;
 memcpy(p,&a,sizeof(a));*n=offsetof(struct sockaddr_un,sun_path)+22;
 if(is("h_lock_short"))(*n)--;
 if(is("h_lock_long"))(*n)++;
 return 0;''')
edit('reset_manifest();phase=\'H\';helper_rc=main_restore();', '''/* New boundary cases alter owned fixture files only after complete daemon
  * proofs/descriptor handoff, then let production helper startup re-parse. */
 if(!strncmp(mode,"x_manifest_",11)){
  char q[4096];mapped(q,sizeof(q),"/rescue.manifest");
  int fd=open(q,O_RDWR);assert(fd>=0);struct stat st;assert(!fstat(fd,&st));
  unsigned char b[MAX_MANIFEST];assert(read(fd,b,(size_t)st.st_size)==st.st_size);
  size_t n=(size_t)st.st_size,offs[5],off=112;
  for(int i=0;i<5;i++){offs[i]=off;off+=52+(size_t)u32(b+off+48)*32;}assert(off==n);
  if(is("x_manifest_zero")){put32(b+12,0);n=112;}
  else if(is("x_manifest_two")){put32(b+12,2);n=offs[2];}
  else if(is("x_manifest_four")){put32(b+12,4);n=offs[4];}
  else if(is("x_manifest_six"))put32(b+12,6);
  else if(is("x_manifest_magic"))b[0]^=1;
  else if(is("x_manifest_truncated"))n--;
  else if(is("x_manifest_trailing"))b[n++]='x';
  else if(is("x_manifest_cid"))b[16]^=1;
  else if(is("x_manifest_system_full"))b[offs[0]+16]^=1;
  else if(is("x_manifest_system_table"))b[offs[0]+52]^=1;
  else if(is("x_manifest_boot_full"))b[offs[1]+16]^=1;
  else if(is("x_manifest_boot_table"))b[offs[1]+52]^=1;
  else if(is("x_manifest_install_full"))b[offs[2]+16]^=1;
  else if(is("x_manifest_install_table"))b[offs[3]+52]^=1;
  else if(is("x_manifest_data_full"))b[offs[4]+16]^=1;
  else if(is("x_manifest_data_table"))b[offs[4]+52]^=1;
  else abort();
  assert(pwrite(fd,b,n,0)==(ssize_t)n&&!ftruncate(fd,(off_t)n)&&!close(fd));
 }
 if(is("h_system_head"))change("/dev/block/mmcblk0p25",0);
 if(is("h_boot_head"))change("/dev/block/mmcblk0p9",0);
 if(is("h_backup_gpt"))change("/dev/block/mmcblk0",(off_t)geom(0)->size-1);
 if(is("h_self_missing")){char q[4096];mapped(q,sizeof(q),"/sbin/p10-restore");assert(!unlink(q));}
 if(is("h_swap_missing")){char q[4096];mapped(q,sizeof(q),"/proc/swaps");assert(!unlink(q));}
 if(is("h_swap_header"))replace_text("/proc/swaps","INVALID\\n");
 if(is("h_swap_partial"))replace_text("/proc/swaps","Filename");
 if(is("h_system_mount"))replace_text("/proc/self/mountinfo","1 0 179:25 / / rw - ext4 fixture rw\\n");
 if(is("h_mount_malformed"))replace_text("/proc/self/mountinfo","invalid\\n");
 if(is("h_system_sys_start"))replace_text("/sys/dev/block/179:25/start","1072425\\n");
 if(is("h_boot_sys_size"))replace_text("/sys/dev/block/179:9/size","1\\n");
 if(is("h_system_holder")){char q[4096];mapped(q,sizeof(q),"/sys/dev/block/179:25/holders/fixture");int fd=open(q,O_CREAT|O_WRONLY,0600);assert(fd>=0&&!close(fd));}
 if(is("h_boot_alias")){char q[4096];mapped(q,sizeof(q),"/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/boot");assert(!unlink(q)&&!symlink("system",q));}
 reset_manifest();phase='H';helper_rc=main_restore();''')
edit('if(is("uncertain0"))uncertain_image=0;', '''if(is("uncertain_min"))uncertain_image=INT32_MIN;
  if(is("uncertain_max"))uncertain_image=INT32_MAX;
  if(is("uncertain0"))uncertain_image=0;''')
# Report supplemental counters without modifying the preexisting JSON layout.
edit('printf("{\\"parser\\":%d,', 'printf("{\\"manifest_loads\\":%d,\\"self_maps\\":%d,\\"parser\\":%d,')
edit(' parser_rc,daemon_rc,helper_rc,execs,exit_code,', ' manifest_reads,self_maps,parser_rc,daemon_rc,helper_rc,execs,exit_code,')
s=s.replace('#undef fgetxattr','#undef fgetxattr\n#undef mmap')
(T/'adversarial.c').write_text(s)
p=(T/'platform.h').read_text()
assert p.endswith('#endif\n')
p=p[:-7]+'''/* Independent extension: only the read-only self mmap syscall is modeled. */
void *host_mmap(void *,size_t,int,int,int,off_t);
#define mmap host_mmap
#endif
'''
(T/'adversarial-platform.h').write_text(p)
# Use a distinct include, leaving the original harness/platform byte-exact.
s=s.replace('#include "platform.h"','#include "adversarial-platform.h"')
(T/'adversarial.c').write_text(s)
print('Generated syscall-model extension; production source unchanged')
