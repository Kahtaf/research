"""Source-only inspection. Default PLAN_ONLY; never opens a target transport."""
import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from sources import RemoteSource, reference


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation', choices=['samples', 'preflight'])
    p.add_argument('--profile', choices=['userdata-pristine', 'stock-system'], required=True)
    p.add_argument('--output', type=Path)
    p.add_argument('--read-only-execute', action='store_true')
    a = p.parse_args()
    profile, chunks = reference(a.profile)
    if not a.read_only_execute:
        print(json.dumps({'mode': 'PLAN_ONLY', 'source': profile, 'target_authorized': False}))
        return
    if a.output is None:
        raise ValueError('new receipt path required')
    # Reserve before any source access; no overwrite of existing evidence.
    with a.output.open('x') as output:
        started = time.monotonic()
        started_utc = datetime.now(timezone.utc).isoformat()
        source = RemoteSource(a.profile)
        try:
            source.open()
            if a.operation == 'samples':
                samples = []
                for index in sorted({0, profile['count'] // 2, profile['count'] - 1}):
                    data = source.read_chunk(index, sample=True)
                    samples.append({'index': index, 'offset': index * 1048576,
                                    'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                                    'all_zero': not any(data)})
                source.check()
                result = {'format': 'SOURCE-SAMPLES1', 'mode': 'READ_ONLY_SAMPLES',
                          'profile': profile, 'stat': source.stat, 'samples': samples,
                          'full_preflight': False, 'target_authorized': False}
            else:
                source.preflight()
                result = source.receipt()
                chunk_path = a.output.with_suffix('.chunks')
                with chunk_path.open('xb') as f:
                    f.write(chunks)
                    f.flush()
                    os.fsync(f.fileno())
            result['started_utc'] = started_utc
            result['elapsed_seconds'] = time.monotonic() - started
            result['reader_sha256'] = {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                                       for name in ('sources.py', 'worker.py', 'source_cli.py')}
            json.dump(result, output, indent=2)
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
            print(json.dumps({'receipt': str(a.output), 'full_preflight': result['full_preflight'],
                              'target_authorized': False}))
        finally:
            source.close()


if __name__ == '__main__':
    main()
