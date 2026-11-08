from pathlib import Path
R=Path(__file__).resolve().parents[1]/'fixture'
p=R/'tests/session.c';s=p.read_text();s=s.replace('if(getenv("SHORT_RECOVERY"))return pread(fd,b,n-1,off);','''if(getenv("SHORT_RECOVERY"))return pread(fd,b,n-1,off);
  const char *nth=getenv("REVIEW_MUTATE_AFTER_P10_READ");
  if(nth&&recovery_hashes==(unsigned)atoi(nth)){
   ssize_t z=pread(fd,b,n,off);int w=open(recovery_name,O_WRONLY);
   assert(w>=0);assert(pwrite(w,"Z",1,0)==1);close(w);return z;
  }
  const char *shortnth=getenv("REVIEW_SHORT_P10_HASH");
  if(shortnth&&recovery_hashes==(unsigned)atoi(shortnth))return pread(fd,b,n-1,off);''');p.write_text(s)
(R/'tests/review_guard.c').write_text(r'''
#define main fixture_main
#include "session.c"
#undef main
int main(int argc,char **argv){
 assert(argc==3);test_root=argv[1];assert(!load_manifest());
 int f=open_part(10,0);assert(f>=0);assert(!fd_hash(f,geom(10)->size,recovery_pin));close(f);
 struct recovery_phase g={.fd=-1};unsigned char token[32]={1};assert(!recovery_phase_open(&g));
 assert((fcntl(g.fd,F_GETFL)&O_ACCMODE)==O_RDONLY);assert(fcntl(g.fd,F_GETFD)&FD_CLOEXEC);
 assert(!recovery_phase_activate(&g,0,token));
 if(!strcmp(argv[2],"same_node_rw")){
  char p[512];path(p,sizeof(p),"/dev/block/mmcblk0p10");int w=open(p,O_RDWR);assert(w>=0&&w!=g.fd);
  assert(dup2(w,g.fd)==g.fd);close(w);assert(!recovery_phase_chunk(&g,0,token));
  assert((fcntl(g.fd,F_GETFL)&O_ACCMODE)==O_RDWR);assert(!(fcntl(g.fd,F_GETFD)&FD_CLOEXEC));
  puts("same-node writable replacement accepted; outside production flow");
 }else if(!strcmp(argv[2],"full_failure_no_reopen")){
  fault="shortread";assert(recovery_phase_full(&g)==-1);fault=NULL;
  assert(g.fd==-1);assert(recovery_phase_chunk(&g,0,token)==-1);assert(g.fd==-1);
  puts("failed proof invalidates; no reopen");
 }else assert(0);
 recovery_phase_close(&g);assert(g.fd==-1);return 0;
}
''')
(R/'tests/review_boundaries.py').write_text(r'''
import test_sessions as base
from test_sessions import *
class Boundaries(Sessions):
 def test_independent_guard_boundaries(self):
  for mode in ['same_node_rw','full_failure_no_reopen']:
   p=subprocess.run([str(R/'tests/review_guard'),str(self.root),mode],capture_output=True,text=True,preexec_fn=limits)
   self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(p.stderr,'');print(p.stdout.strip())
 def test_short_each_phase(self):
  for phase in range(1,6):
   self.tearDown();self.setUp();s=self.start(env={'REVIEW_SHORT_P10_HASH':str(phase)})
   try:
    self.complete(s)
    self.fail('phase short read accepted')
   except (EOFError,ValueError,ConnectionResetError):pass
   r=self.finish();self.assertEqual(r['rc'],-1);self.assertEqual(r['frozen'],1)
   self.assertEqual(r['uncertain'],0 if phase>=4 else -1)
 def test_persistent_mutation_after_each_proof_read(self):
  for phase in range(1,6):
   self.tearDown();self.setUp();s=self.start(env={'REVIEW_MUTATE_AFTER_P10_READ':str(phase)})
   if phase==5:
    self.complete(s);r=self.finish();self.assertEqual(r['rc'],0);self.assertEqual(r['frozen'],0)
    self.assertEqual(self.p('/dev/block/mmcblk0p10').read_bytes()[0:1],b'Z')
    print('post-final-read mutation: successful commit, persistent changed p10; outside writer invariant')
   else:
    try:self.complete(s);self.fail('persistent mutation missed at later boundary')
    except (EOFError,ValueError,ConnectionResetError):pass
    r=self.finish();self.assertEqual(r['rc'],-1);self.assertEqual(r['frozen'],1)
 def test_transient_midphase_restored(self):
  s=self.start();self.begin(s);self.chunk(s,0,0,True)
  self.write('/dev/block/mmcblk0p10',b'Z'*8192);self.chunk(s,0,1,True)
  self.write('/dev/block/mmcblk0p10',self.recovery)
  self.chunk(s,0,2,True);self.chunk(s,0,3,True);self.whole(s);self.commit(s)
  self.assertEqual(self.finish()['rc'],0)
 def test_partial_frame_closes_and_preserves_pin(self):
  s=self.start(second=True);self.begin(s);self.chunk(s,0,0,True)
  s.sendall(b'RSC1'+struct.pack('<II',4,C)+b'partial');s.shutdown(socket.SHUT_WR)
  later=self.sockets[1];later.settimeout(5);t=self.recon(later)
  send(later,3,t);recv(later,0x83)
  for j in range(4):self.chunk(later,0,j,True)
  self.whole(later);self.commit(later);r=self.finish();self.assertEqual(r['rc'],0);self.assertEqual(r['recovery_opens'],2)
 def test_recovery_mode_binding(self):
  s=self.start();self.begin(s);self.p('/dev/block/mmcblk0p10').chmod(0o400)
  send(s,7);self.rejected(s);r=self.finish();self.assertEqual(r['uncertain'],0)
 def test_whole_verify_too_early(self):
  s=self.start();self.begin(s);send(s,5);self.rejected(s);self.assertEqual(self.finish()['uncertain'],0)
 def test_reconnect_reproof_after_changed_content(self):
  s=self.start(second=True);self.begin(s);s.shutdown(socket.SHUT_RDWR);s.close()
  self.write('/dev/block/mmcblk0p10',b'Z'*8192);later=self.sockets[1];later.settimeout(5)
  with self.assertRaises((EOFError,ValueError)):self.recon(later)
  r=self.finish();self.assertEqual(r['uncertain'],0)
if __name__=='__main__':
 names=[n for n in Boundaries.__dict__ if n.startswith('test_')]
 suite=unittest.TestSuite(Boundaries(n) for n in names)
 result=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(not result.wasSuccessful())
''')
(R/'tests/review_exec.c').write_text(r'''
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stddef.h>
#include <string.h>
#include <assert.h>
static int fail_copy,fail_exec;
static int review_fcntl(int fd,int op,...){
 if(fail_copy&&op==F_DUPFD_CLOEXEC){errno=EMFILE;return -1;}
 assert(op==F_DUPFD_CLOEXEC);return fcntl(fd,op,10);
}
static int review_exec(const char*p,char*const*a){
 assert(!strcmp(p,"/sbin/p10-restore"));(void)a;
 if(fail_exec){errno=ENOENT;return -1;}
 char *args[]={"./tests/review_exec","child",NULL};return execv(args[0],args);
}
#define execv review_exec
#define fcntl review_fcntl
#define P10_HANDOFF
#define main fixture_main
#include "session.c"
#undef main
#undef fcntl
#undef execv
static void lock_held(int f){struct sockaddr_un a;socklen_t n=sizeof(a);assert(!getsockname(f,(void*)&a,&n));
 int second=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);assert(second>=0);errno=0;
 assert(bind(second,(void*)&a,n)<0&&errno==EADDRINUSE);close(second);}
int main(int argc,char **argv){
 if(argc==2&&!strcmp(argv[1],"child")){
  lock_held(4);for(int f=3;f<=5;f++)assert(!(fcntl(f,F_GETFD)&FD_CLOEXEC));
  char b[8];assert(read(3,b,7)==7&&!memcmp(b,"EXEC_OK",7));assert(write(3,"ACK",3)==3);
  for(int f=6;f<64;f++)assert(fcntl(f,F_GETFD)==-1);return 92;
 }
 assert(argc==4);test_root=argv[1];assert(!load_manifest());image_count=2;
 int c=atoi(argv[2]);rescue_lock_fd=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);assert(rescue_lock_fd>=0);
 struct sockaddr_un a={.sun_family=AF_UNIX};memcpy(a.sun_path+1,"asus-rescue-writer-v1",21);
 assert(!bind(rescue_lock_fd,(void*)&a,offsetof(struct sockaddr_un,sun_path)+22));
 rescue_listener_fd=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);assert(rescue_listener_fd>=0);
 fail_copy=!strcmp(argv[3],"copy_fail");fail_exec=!strcmp(argv[3],"exec_fail");
 int rc=p10_handoff(c);assert(fail_copy&&rc==-1);lock_held(rescue_lock_fd);return 0;
}
''')
# errno needed before wrappers; varargs not consumed since F_DUPFD_CLOEXEC always requests 10.
p=R/'tests/review_exec.c';p.write_text('#include <errno.h>\n'+p.read_text())
(R/'tests/review_exec.py').write_text(r'''
from test_sessions import *
class Exec(Sessions):
 def test_real_exec_and_failures(self):
  for mode,code in [('ok',92),('copy_fail',0),('exec_fail',74)]:
   a,b=socket.socketpair();a.settimeout(8)
   p=subprocess.Popen([str(R/'tests/review_exec'),str(self.root),str(b.fileno()),mode],pass_fds=[b.fileno()],stdout=subprocess.PIPE,stderr=subprocess.PIPE,preexec_fn=limits);b.close()
   if mode=='ok':a.sendall(b'EXEC_OK');self.assertEqual(a.recv(3),b'ACK')
   out,err=p.communicate(timeout=8);self.assertEqual(p.returncode,code,err.decode());self.assertEqual(err,b'');a.close()
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([Exec('test_real_exec_and_failures')]));raise SystemExit(not r.wasSuccessful())
''')
(R/'tests/review_run.sh').write_text('''#!/bin/sh
set -eu
cd /work
sh tests/run_linux.sh
export SANITIZER_CGROUP=1
export ASAN_OPTIONS=detect_leaks=1:halt_on_error=1
export UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1
cc -std=c11 -D_GNU_SOURCE -O1 -g -fsanitize=address,undefined,bounds -fno-sanitize-recover=all tests/review_guard.c -o tests/review_guard
python3 -B tests/review_boundaries.py > evidence/review-boundaries.stdout 2> evidence/review-boundaries.stderr
cc -std=c11 -D_GNU_SOURCE -O1 -g -fsanitize=address,undefined,bounds -fno-sanitize-recover=all tests/review_exec.c -o tests/review_exec
python3 -B tests/review_exec.py > evidence/review-exec.stdout 2> evidence/review-exec.stderr
cat /sys/fs/cgroup/memory.peak > evidence/review-memory-peak.txt
''')
