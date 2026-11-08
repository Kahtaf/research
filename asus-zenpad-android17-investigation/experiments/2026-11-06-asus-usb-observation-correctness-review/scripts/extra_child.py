"""Tiny local negative-path fixture. Never invokes another process or network."""
import os
import sys
import time

mode = sys.argv[1]
if mode == 'stderr_eof_then_valid':
    os.close(2)
    request = b''
    while len(request) < 80:
        request += os.read(0, 80 - len(request))
    os.write(1, b'RSC1\x82\0\0\0\x30\0\0\0' + bytes(32) + bytes([1]) * 16)
    assert os.read(0, 1) == b''
elif mode == 'close_both_then_hang':
    os.close(1)
    os.close(2)
    time.sleep(5)
elif mode == 'early_stdout':
    os.write(1, b'not-a-response')
    time.sleep(5)
elif mode == 'broken_stdin':
    os.close(0)
    time.sleep(5)
elif mode == 'discovery_flood':
    os.write(1, b'x' * 100_000)
elif mode == 'stderr_flood_without_exit':
    while True:
        os.write(2, b'x' * 8192)
else:
    raise RuntimeError('Unknown fixture mode')
