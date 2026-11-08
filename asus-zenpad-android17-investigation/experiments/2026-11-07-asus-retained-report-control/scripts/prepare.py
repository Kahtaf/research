from pathlib import Path
import difflib,hashlib,json
R=Path(__file__).resolve().parents[1];W=R.parent
src=W/'2026-11-07-asus-sd-media-flag-probe/source/init.c'
s=src.read_text();s=s.replace('#include <sys/utsname.h>','#include <sys/utsname.h>\n#include <sys/klog.h>')
new=r'''
#define RETAINED_MARKER "ASUS-stock-retained-control-20261107-v1 1fd4c968-c0b4-49ab-851a-b0ea4c50c01d"
static struct {
 int level_rc, level_errno, node_errno, open_errno, write_errno, close_errno;
 ssize_t written;
} retained = {.level_rc=-1, .written=-1};
static void retained_marker(void){
 const char msg[]="<0>" RETAINED_MARKER " pid1 /dev/kmsg\n";
 struct stat st;
 errno=0;retained.level_rc=klogctl(8,NULL,1);retained.level_errno=errno;
 /* Only the private /dev tmpfs is changed; major 1 minor 11 is kmsg. */
 if(mknod("/dev/kmsg",S_IFCHR|0600,makedev(1,11))||
    lstat("/dev/kmsg",&st)||!S_ISCHR(st.st_mode)||st.st_rdev!=makedev(1,11)){
  retained.node_errno=errno?errno:EINVAL;return;
 }
 int fd=open("/dev/kmsg",O_WRONLY|O_CLOEXEC|O_NOFOLLOW);
 if(fd<0){retained.open_errno=errno;return;}
 if(fstat(fd,&st)||!S_ISCHR(st.st_mode)||st.st_rdev!=makedev(1,11)){
  retained.open_errno=errno?errno:EINVAL;(void)close(fd);return;
 }
 /* One bounded record; do not split it or retry an ambiguous short write. */
 errno=0;retained.written=write(fd,msg,sizeof(msg)-1);retained.write_errno=errno;
 if(close(fd))retained.close_errno=errno;
}
'''
s=s.replace('static int arm_watchdog(void);',new+'\nstatic int arm_watchdog(void);')
s=s.replace('status=pid1_uname_observed\\n",RUN_ID,u.sysname,u.release,u.version,u.machine);','status=pid1_uname_observed\\nretained_marker=%s\\nkmsg_level_rc=%d\\nkmsg_level_errno=%d\\nkmsg_node_errno=%d\\nkmsg_open_errno=%d\\nkmsg_written=%ld\\nkmsg_expected=%zu\\nkmsg_write_errno=%d\\nkmsg_close_errno=%d\\n",RUN_ID,u.sysname,u.release,u.version,u.machine,RETAINED_MARKER,retained.level_rc,retained.level_errno,retained.node_errno,retained.open_errno,(long)retained.written,sizeof("<0>" RETAINED_MARKER " pid1 /dev/kmsg\\n")-1,retained.write_errno,retained.close_errno);')
s=s.replace('char report[1024];int n=make_report(report,sizeof(report));if(n<0)return -1;','char report[1024];int n;')
s=s.replace('struct binding b;struct stat st;\n if(discover','retained_marker();\n n=make_report(report,sizeof(report));if(n<0)return -1;\n struct binding b;struct stat st;\n if(discover')
assert s.count('retained_marker();')==1 and 'kmsg_written=%ld' in s
(R/'source/init.c').write_text(s)
(R/'source/init.diff').write_text(''.join(difflib.unified_diff(src.read_text().splitlines(True),s.splitlines(True),fromfile='working-sd/init.c',tofile='retained-control/init.c')))
(R/'evidence/helper-provenance.json').write_text(json.dumps(dict(source=str(src.relative_to(W)),sha256=hashlib.sha256(src.read_bytes()).hexdigest(),new_sha256=hashlib.sha256(s.encode()).hexdigest(),marker='ASUS-stock-retained-control-20261107-v1 1fd4c968-c0b4-49ab-851a-b0ea4c50c01d',syslog_action=8,console_level=1,kmsg_priority=0),indent=2)+'\n')
