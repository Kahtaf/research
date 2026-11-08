"""Fresh host boundary reproductions against exact new C session/core binding."""
from pathlib import Path
import errno,hashlib,json,os,socket,struct,subprocess,sys,tempfile
from unittest.mock import patch
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'));import host
assert host.PRIOR_SHA=='3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a'
assert host.HELPER_SHA=='c5df268a9f0bdc31e01140a5378d404f9cb7b091b8ec50e5c2be992434089859'
rows=[]
class CountStream:
    def __init__(self,s):self.s=s;self.sent=[];self.closed=False
    def settimeout(self,v):self.s.settimeout(v)
    def sendall(self,b):self.sent.append(struct.unpack_from('<I',b,4)[0]);self.s.sendall(b)
    def recv(self,n):return self.s.recv(n)
    def close(self):self.closed=True;self.s.close()
def server():
    a,b=socket.socketpair();p=subprocess.Popen([str(R/'artifacts/session_server'),str(b.fileno()),'none'],pass_fds=[b.fileno()],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);b.close()
    return CountStream(a),p
for case in ['post_rename_directory_sync_and_storage_loss','lost_final_ack','old_external_pin_refuses_new_actual_preimage']:
    stream,p=server()
    with tempfile.TemporaryDirectory(dir=R/'artifacts') as td:
        real_fsync=os.fsync;real_open=os.open;calls=0;failed=False;BaseFrames=host.Frames
        def fsync(fd):
            global calls,failed
            calls+=1
            if calls==4:failed=True;raise OSError(errno.EIO,'review: post-rename directory sync')
            return real_fsync(fd)
        def opn(*args,**kwargs):
            if failed:raise OSError(errno.EROFS,'review: storage unavailable')
            return real_open(*args,**kwargs)
        class LostAck(BaseFrames):
            def receive(self,expected,n):
                b=super().receive(expected,n)
                if expected==0xb4:raise EOFError('review: lost live final return')
                return b
        from contextlib import ExitStack
        with ExitStack() as stack:
            if case=='post_rename_directory_sync_and_storage_loss':
                stack.enter_context(patch.object(host.os,'fsync',side_effect=fsync));stack.enter_context(patch.object(host.os,'open',side_effect=opn))
            if case=='lost_final_ack':stack.enter_context(patch.object(host,'Frames',LostAck))
            if case=='old_external_pin_refuses_new_actual_preimage':stack.enter_context(patch.object(host,'PRIOR_SHA','e3df64342477816bc9aa2c8bb44cb61adf7a0f910d2d016c339c3250ff8457e3'))
            try:host._exchange(stream,td);raise AssertionError('unexpected accepted completion')
            except host.UnknownOutcome:pass
        out,err=p.communicate(timeout=30);assert p.returncode==0,(out,err);target=json.loads(out)
        attempt=json.loads((Path(td)/'attempt.json').read_text());receipt=json.loads((Path(td)/'receipt.json').read_text())
        assert attempt['outcome']==receipt['outcome']=='UNKNOWN' and not receipt['publication_accepted']
        assert stream.closed and stream.sent.count(0x30)==1
        if case=='old_external_pin_refuses_new_actual_preimage':assert target['opens']==target['writes']==0 and 0x33 not in stream.sent
        else:assert target['state']=='DONE' and target['writes']==16
        if case=='post_rename_directory_sync_and_storage_loss':assert calls==4 and receipt['device_outcome']=='DONE'
        before=list(stream.sent)
        try:host._exchange(stream,td);raise AssertionError('replay accepted')
        except FileExistsError:pass
        assert stream.sent==before
        rows.append(dict(case=case,passed=True,target=target,sent=stream.sent,attempt=attempt,visible_receipt=receipt,replay_refused_before_transport=True,real_C_session=True))

sys.path.insert(0,str(R/'tests'));from contract_tests import Clock,ModelStream
for case,delay in [('delayed_valid_initial_reply_16s',{0x30:16}),('handoff_expiry',{0x30:181}),('stage_expiry',{0x31:16}),('prepare_expiry',{0x32:61}),('restore_expiry',{0x33:121}),('hard_expiry_after_descheduling',{0x30:179,0x31:14,0x32:59,0x33:119})]:
    clock=Clock();clock.now=1000.;stream=ModelStream(clock,delay);BaseFrames=host.Frames
    class ScheduledFrames(BaseFrames):
        def begin(self,phase):
            if case=='hard_expiry_after_descheduling' and phase=='restore':clock.now+=100
            super().begin(phase)
    with tempfile.TemporaryDirectory(dir=R/'artifacts') as td,patch.object(host.time,'monotonic',side_effect=clock.monotonic),patch.object(host,'Frames',ScheduledFrames):
        try:outcome=host._exchange(stream,td)['outcome']
        except host.UnknownOutcome:outcome='UNKNOWN'
        assert outcome==('DONE' if case=='delayed_valid_initial_reply_16s' else 'UNKNOWN')
        assert stream.closed and stream.sent.count(0x30)==1
        assert json.loads((Path(td)/'receipt.json').read_text())['outcome']=='UNKNOWN'
        if case=='hard_expiry_after_descheduling':assert clock.now==1600 and stream.sent.count(0x33)==1
        prior=list(stream.sent)
        try:host._exchange(stream,td);raise AssertionError('retry accepted')
        except FileExistsError:pass
        assert prior==stream.sent
        rows.append(dict(case=case,passed=True,host_outcome=outcome,modeled_elapsed=clock.now-1000,sent=stream.sent,no_retry=True,model_not_hardware=True))
(R/'evidence/independent-host-edges.json').write_text(json.dumps(dict(passed=True,new_binding=dict(prior=host.PRIOR_SHA,helper=host.HELPER_SHA),cases=rows),indent=2)+'\n')
print('INDEPENDENT_HOST_EDGES_PASS',len(rows))
