"""Parent-only reviewed manifest build, with exact original approval schema.
source://stock-system or source://userdata-pristine replaces only the source path.
SOURCE receipts are evidence, never a reusable preflight or an arming approval.
"""
import argparse
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
from sources import RemoteSource, local_source
from source_manifest import build


def build_review(review):
    # Original build validates approval schema and ordered roles before digest callback.
    receipts = []
    with ExitStack() as stack:
        def digest(path, length):
            if path.startswith('source://'):
                key = path[len('source://'):]
                source = RemoteSource(key)
                stack.callback(source.close)
                source.open()
            else:
                source = local_source(path)
                stack.callback(source.close)
            if source.profile['size'] != length:
                raise ValueError('fixed profile length')
            # Bind source role to its schema slot; a digest alone is not a role grant.
            roles = list(review['images'])
            matched = [i for i, role in enumerate(roles) if review['images'][role]['path'] == path]
            if matched != [source.profile['role']]:
                raise ValueError('source role binding')
            full, compact = source.preflight()
            if isinstance(source, RemoteSource):
                receipts.append(source.receipt())
            return full, [compact[i:i + 32] for i in range(0, len(compact), 32)]
        binary, evidence = build(review, digest=digest)
        return binary, evidence, receipts


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--review', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--build-reviewed-manifest', action='store_true')
    a = p.parse_args()
    if not a.build_reviewed_manifest:
        print(json.dumps({'mode': 'PLAN_ONLY', 'armed': False, 'target_authorized': False,
                          'unknown_install_images': 'UNBOUND_REFUSED'}))
        return
    if not a.review or not a.output:
        raise ValueError('review and new output required')
    with a.output.open('xb') as out:
        binary, evidence, receipts = build_review(json.loads(a.review.read_text()))
        out.write(binary)
        out.flush()
        os.fsync(out.fileno())
    with a.output.with_suffix('.SOURCE.json').open('x') as f:
        json.dump({'manifest_sha256': hashlib.sha256(binary).hexdigest(), 'images': evidence,
                   'sources': receipts, 'armed': False, 'target_authorized': False}, f, indent=2)
    print(json.dumps({'manifest_sha256': hashlib.sha256(binary).hexdigest(), 'armed': False}))


if __name__ == '__main__':
    main()
