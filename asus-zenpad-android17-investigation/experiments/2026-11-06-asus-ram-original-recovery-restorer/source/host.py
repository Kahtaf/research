"""Fixed P10R1 exchange over a parent-established authenticated rescue stream.
No CLI, subprocess, discovery, ADB, network connection, retry or source override.
The delivered unarmed profile is refused by restore(); tests call the exact
exchange implementation directly against the injected storage server.
"""
from pathlib import Path
import hashlib,json,os,stat,struct,time
from generated_host_binding import PRIOR_SHA,HELPER_SHA,ARMED
SIZE=16740352
CHUNK=1048576
STOCK_SHA='902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20'
ROOT=Path(__file__).resolve().parents[1]
class UnknownOutcome(RuntimeError):pass

def _receipt(directory,name,value,exclusive=False):
    directory=Path(directory)
    dfd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        data=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
        flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW
        temp=name if exclusive else name+'.new'
        fd=os.open(temp,flags,0o600,dir_fd=dfd)
        try:
            with os.fdopen(fd,'wb',closefd=False) as f:
                f.write(data);f.flush();os.fsync(fd)
        finally:os.close(fd)
        if not exclusive:os.rename(temp,name,src_dir_fd=dfd,dst_dir_fd=dfd)
        os.fsync(dfd)
    finally:os.close(dfd)

def _payload():
    fd=os.open(ROOT/'artifacts/original-recovery.payload',os.O_RDONLY|os.O_NOFOLLOW)
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size!=SIZE:raise ValueError('fixed payload geometry')
        with os.fdopen(fd,'rb',closefd=False) as f:data=f.read(SIZE+1)
        if len(data)!=SIZE or hashlib.sha256(data).hexdigest()!=STOCK_SHA:raise ValueError('fixed payload integrity')
        return data
    finally:os.close(fd)

class Frames:
    def __init__(self,stream):self.stream=stream;self.deadline=time.monotonic()+300
    def _limit(self):
        remaining=self.deadline-time.monotonic()
        if remaining<=0:raise TimeoutError('operation deadline; outcome unknown')
        self.stream.settimeout(min(15,remaining))
    def send(self,op,data=b''):
        self._limit();self.stream.sendall(struct.pack('<4sII',b'RSC1',op,len(data))+data)
    def read(self,n):
        out=bytearray()
        while len(out)<n:
            self._limit();b=self.stream.recv(n-len(out))
            if not b:raise EOFError('lost acknowledgement; outcome unknown')
            out.extend(b)
        return bytes(out)
    def receive(self,expected,length):
        magic,op,n=struct.unpack('<4sII',self.read(12))
        if magic!=b'RSC1' or op!=expected or n!=length:raise ValueError('invalid fixed response')
        return self.read(n)

def _exchange(stream,receipt_directory):
    payload=_payload()  # complete held-memory host preflight before protocol
    record=dict(protocol='P10R1',outcome='UNKNOWN',prior_sha256=PRIOR_SHA,
                original_sha256=STOCK_SHA,helper_sha256=HELPER_SHA,bytes=SIZE,
                retry=False,reboot=False,started_utc=time.time())
    # An attempt is consumed before the first request. Never replace it.
    _receipt(receipt_directory,'attempt.json',record,exclusive=True)
    f=Frames(stream)
    try:
        f.send(0x30);f.receive(0xb0,0)
        for off in range(0,SIZE,CHUNK):
            f.send(0x31,payload[off:off+CHUNK]);f.receive(0xb1,0)
        f.send(0x32);ready=f.receive(0xb2,36)
        skipped=struct.unpack_from('<I',ready)[0];prior=ready[4:].hex()
        if skipped not in (0,1) or prior!=(STOCK_SHA if skipped else PRIOR_SHA):
            raise ValueError('actual full prior readback is not the fixed reviewed profile')
        if not skipped:f.send(0x33)
        full=f.receive(0xb4,32).hex()
        if full!=STOCK_SHA:raise ValueError('full actual final readback mismatch')
        record.update(outcome='SKIPPED' if skipped else 'DONE',actual_prior_sha256=prior,
                      full_readback_sha256=full,completed_utc=time.time())
        _receipt(receipt_directory,'receipt.json',record)
        return record
    except Exception as exc:
        # attempt.json remains durable UNKNOWN even if a final disk write fails.
        record.update(outcome='UNKNOWN',error=type(exc).__name__+': '+str(exc))
        try:_receipt(receipt_directory,'receipt.json',record)
        except OSError:pass
        raise UnknownOutcome(record['error']) from exc
    finally:stream.close()

def restore(stream,receipt_directory):
    if not ARMED:raise RuntimeError('Unarmed artifact; parent review and separate bound build required')
    return _exchange(stream,receipt_directory)
