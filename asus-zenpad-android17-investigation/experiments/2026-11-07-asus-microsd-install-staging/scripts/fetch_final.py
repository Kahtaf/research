"""Fetch admitted final public build bytes, stage SD chunks, join real manifest.

No device/card operations. Run only with hashes from the completed build report.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / 'private'
SYSTEM_SIZE = 3753902080
BOOT_SIZE = 16740352


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def fetch(ssh, source, dest, size, expected):
    if not source.startswith('/srv/android/') or '\n' in source:
        raise ValueError('Expected actual builder artifact path')
    if len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
        raise ValueError('Actual build SHA256 required')
    # Held ordinary O_RDONLY file, with before/after identity; gzip only affects
    # transport. The parent hashes the actual complete uncompressed bytes.
    script = '''import gzip,os,stat,sys
p=sys.argv[1];size=int(sys.argv[2])
fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);a=os.fstat(fd)
assert stat.S_ISREG(a.st_mode) and a.st_size==size
with gzip.GzipFile(fileobj=sys.stdout.buffer,mode='wb',compresslevel=1,mtime=0) as z:
 while True:
  b=os.read(fd,1048576)
  if not b:break
  z.write(b)
b=os.fstat(fd)
assert (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns,b.st_ctime_ns)
os.close(fd)
'''
    command = 'python3 -B -c ' + shlex.quote(script) + ' ' + shlex.quote(source) + ' ' + str(size)
    proc = subprocess.Popen(ssh[:-1] + ['-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2',ssh[-1],command],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    digest = hashlib.sha256()
    total = 0
    try:
        with dest.open('xb', buffering=0) as out:
            with gzip.GzipFile(fileobj=proc.stdout) as stream:
                while chunk := stream.read(1048576):
                    total += len(chunk)
                    if total > size:
                        raise RuntimeError('Source exceeds admitted length')
                    digest.update(chunk)
                    if chunk.count(0) == len(chunk):
                        out.seek(len(chunk), os.SEEK_CUR)
                    else:
                        view = memoryview(chunk)
                        while view:
                            n = out.write(view)
                            if not n:
                                raise RuntimeError('Short download write')
                            view = view[n:]
            out.truncate(total)
            os.fsync(out.fileno())
        error = proc.stderr.read(8192)
        status = proc.wait(timeout=30)
        if status or error or total != size or digest.hexdigest() != expected:
            raise RuntimeError('Final source transport/size/hash failed')
        return digest
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        proc.stdout.close()
        proc.stderr.close()


def record(row):
    role = row['role']
    part = 26 if role == 4 else 9 if role % 2 else 25
    hashes = [bytes.fromhex(c['sha256']) for c in row['chunks']]
    assert len(hashes) == (row['bytes'] + 1048575) // 1048576
    return struct.pack('<IIQ32sI',role,part,row['bytes'],bytes.fromhex(row['sha256']),len(hashes)) + b''.join(hashes)


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('--system-path'); a.add_argument('--system-sha256')
    a.add_argument('--boot-path'); a.add_argument('--boot-sha256')
    a.add_argument('--boot-bytes',type=int); a.add_argument('--execute',action='store_true')
    args = a.parse_args()
    if not args.execute:
        print(json.dumps(dict(mode='PLAN_ONLY',needs='completed build SYSTEM/BOOT paths, sizes and SHA256',
                              device_operations=False,card_operations=False)))
        return
    if not all([args.system_path,args.system_sha256,args.boot_path,args.boot_sha256,
                args.boot_bytes and 0 < args.boot_bytes <= BOOT_SIZE]):
        raise ValueError('Actual final image identities required')
    os.umask(0o077)
    if (PRIVATE/'final-fetch-started.json').exists() or (PRIVATE/'admitted.manifest').exists():
        raise RuntimeError('Preserve previous final fetch; no automatic retry')
    original = (ROOT.parent/'2026-11-07-asus-offline-stock-fallback/inputs/original-stock.manifest').read_bytes()
    if hashlib.sha256(original).hexdigest() != '605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47':
        raise ValueError('Original-pair authority changed')
    staged = json.loads((PRIVATE/'staging.json').read_text())
    data = next(r for r in staged['roles'] if r['role']==4)
    if data['sha256'] != 'cf433efa509f09814bff0877368f0c1b811b7615eefd3cd2a02f58b57995131b':
        raise ValueError('Wrong prepared private DATA identity')
    download = PRIVATE/'final-download'
    download.mkdir(mode=0o700)
    (PRIVATE/'final-fetch-started.json').write_text(json.dumps(vars(args),indent=2)+'\n')
    remote = module('parent_remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py')
    stage = module('stage_sources',ROOT/'scripts/stage.py')
    system = download/'system.raw'
    fetch(remote.SSH,args.system_path,system,SYSTEM_SIZE,args.system_sha256)
    system.chmod(0o400)
    row2 = stage.stage(2,system,SYSTEM_SIZE,args.system_sha256,'asus-rescue',PRIVATE/'card')
    boot = download/'boot.raw'
    padded_hash = fetch(remote.SSH,args.boot_path,boot,args.boot_bytes,args.boot_sha256)
    with boot.open('r+b') as f:
        if f.read(8) != b'ANDROID!':
            raise ValueError('Expected packaged Android BOOT header')
        f.truncate(BOOT_SIZE)
        os.fsync(f.fileno())
    padded_hash.update(bytes(BOOT_SIZE-args.boot_bytes))
    boot.chmod(0o400)
    row3 = stage.stage(3,boot,BOOT_SIZE,padded_hash.hexdigest(),'asus-rescue',PRIVATE/'card')
    if row2['sha256'] == staged['roles'][0]['sha256'] or row3['sha256'] == staged['roles'][1]['sha256']:
        raise ValueError('Install images cannot be original stock pair')
    manifest = original[:8] + struct.pack('<II',2,5) + original[16:] + record(row2) + record(row3) + record(data)
    stage.write_new(PRIVATE/'admitted.manifest',manifest)
    (PRIVATE/'admitted.manifest').chmod(0o400)
    result = dict(manifest_sha256=hashlib.sha256(manifest).hexdigest(),
                  manifest_bytes=len(manifest), final_roles=[row2,row3],
                  system_source_sha256=args.system_sha256,boot_container_sha256=args.boot_sha256,
                  private_DATA_uploaded=False,device_operations=False,card_operations=False)
    stage.write_new(PRIVATE/'final-sources.json',(json.dumps(result,indent=2)+'\n').encode())
    # The actual admitted source remains on the VM; verified SD chunks are local.
    system.unlink();boot.unlink()
    print(json.dumps({k:v for k,v in result.items() if k!='final_roles'}))


if __name__=='__main__':
    main()
