"""Binary recovery stream framing. Use a Linux SO_PEERCRED/SO_PEERSEC checked
Unix socket behind authenticated stock adbd; never a TCP listener. No shell RPC.
This module is exercised with actual local socketpair I/O, not a device socket.
"""
import struct
from rescue import CHUNK,Refused,TransportLost,State
HEADER=struct.Struct('<4sIII') # magic, chunk index, byte count, reserved=0

def exact(sock,n):
 out=bytearray()
 while len(out)<n:
  b=sock.recv(n-len(out))
  if not b:raise TransportLost('stream EOF before exact frame length')
  out.extend(b)
 return bytes(out)

def receive_frame(session,sock):
 session.frozen()
 try:
  magic,index,count,reserved=HEADER.unpack(exact(sock,HEADER.size))
  if magic!=b'ASR1' or reserved!=0 or not 0<count<=CHUNK:raise Refused('frame header')
  session.feed(index,exact(sock,count))
 except Refused:
  session.state=State.FAILED;raise
 except Exception:
  if session.state!=State.UNCERTAIN:session.lost()
  raise

def send_frame(sock,index,data):
 if not 0<len(data)<=CHUNK:raise Refused('frame size')
 sock.sendall(HEADER.pack(b'ASR1',index,len(data),0));sock.sendall(data)
