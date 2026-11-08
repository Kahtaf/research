"""Offline bounded-buffer evidence; no subprocess, target, SSH, or full image copy."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import tracemalloc
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_remote_source import SourceThread
import sources
import worker

ROOT=Path(__file__).resolve().parents[1]
C=worker.CHUNK
with tempfile.TemporaryDirectory(dir=ROOT/'artifacts',prefix='memory-') as tmp:
    path=Path(tmp).resolve()/'sparse-small-fixture.raw'
    length=16*C+355840
    with path.open('wb') as f:
        f.write(b'A'*C)
        f.truncate(length)
    path.chmod(0o400)
    full=hashlib.sha256();compact=bytearray()
    with path.open('rb') as f:
        while block:=f.read(C):
            full.update(block);compact.extend(hashlib.sha256(block).digest())
    del block
    profile=dict(role=0,path=str(path),size=length,sha256=full.hexdigest(),
                 uid=os.getuid(),gid=os.getgid(),mode=0o400,nlink=1,chunk_bytes=C,
                 count=len(compact)//32,chunks_sha256=hashlib.sha256(compact).hexdigest())
    tracemalloc.start()
    with patch.object(sources,'reference',return_value=(profile,bytes(compact))), \
         patch.object(sources.subprocess,'Popen',side_effect=lambda *a,**kw:SourceThread(profile)):
        source=sources.RemoteSource('stock-system').open()
    try:
        source.preflight()
        received=hashlib.sha256();total=0
        for index in range(profile['count']):
            data=source.read_chunk(index);received.update(data);total+=len(data)
            del data
        source.check()
        current,peak=tracemalloc.get_traced_memory()
        assert received.hexdigest()==profile['sha256'] and total==length
        assert peak<10*C,(current,peak)
        result={'mode':'OFFLINE_SMALL_FILE_MOCK_SOURCE','target_used':False,
                'fixture_logical_bytes':length,'chunks':profile['count'],
                'final_chunk_bytes':length% C,'received_bytes':total,
                'sha256':received.hexdigest(),'tracemalloc_peak_bytes':peak,
                'tracemalloc_current_bytes':current,
                'measurement_scope':'combined host+worker Python allocations after imports; excludes interpreter baseline, OS buffers and SSH',
                'maximum_image_staging_bytes':length,'payload_files_copied':0}
        print(json.dumps(result,indent=2))
    finally:
        source.close()
        tracemalloc.stop()
