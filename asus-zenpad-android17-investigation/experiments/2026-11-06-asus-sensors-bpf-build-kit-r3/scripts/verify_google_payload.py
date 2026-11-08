#!/usr/bin/env python3
"""Verify signed Google bytes against the release, in staging and final ext4."""
import argparse, hashlib, json, pathlib, subprocess


def digest(stream):
    total = 0
    h = hashlib.sha256()
    for data in iter(lambda: stream.read(1024 * 1024), b''):
        h.update(data)
        total += len(data)
    return {'size': total, 'sha256': h.hexdigest()}


def verify(manifest, product_out, raw_image=None, debugfs=None):
    if not __debug__: raise RuntimeError('Optimized Python forbidden')
    payload = manifest['payload_members']
    checks = []
    excluded = []
    before = raw_image.stat() if raw_image else None
    for relative, expected in sorted(payload.items()):
        suffix = pathlib.PurePosixPath(relative).suffix
        if suffix in ('.so', '.jar'):
            excluded.append({'path': relative, 'reason': 'Compiler stripping/dex packaging may transform this unsigned input; checked separately by the product build.'})
            continue
        assert suffix in ('.apk', '.apex', '.xml', '.der', '.rc'), relative
        parts = pathlib.PurePosixPath(relative).parts
        assert parts[0] == 'system' and '..' not in parts and not relative.startswith('/')
        staged = product_out / relative
        assert staged.is_file() and not staged.is_symlink(), staged
        first = staged.stat()
        with staged.open('rb') as stream:
            actual = digest(stream)
        last = staged.stat()
        assert (first.st_size, first.st_mtime_ns) == (last.st_size, last.st_mtime_ns), staged
        assert actual == expected, (relative, actual, expected)
        check = {'path': relative, **actual, 'staged_bytes_match_release': True}
        if raw_image:
            # SDK37 build_image.SetUpInDirAndFsConfig always constructs a
            # system-as-root filesystem containing the /system directory.
            image_path = '/' + '/'.join(parts)
            process = subprocess.Popen([str(debugfs), '-R', 'cat ' + image_path, str(raw_image)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            archived = digest(process.stdout)
            stderr = process.stderr.read().decode(errors='replace')
            assert process.wait() == 0 and archived == expected, (image_path, archived, expected, stderr)
            check.update(image_path=image_path, final_ext4_bytes_match_release=True)
        checks.append(check)
    assert any(x['path'].endswith('/Phonesky.apk') for x in checks)
    assert any(x['path'].endswith('/GoogleServicesFramework.apk') for x in checks)
    assert any(x['path'].endswith('/com.google.android.gmssystem.prodvic.apex') for x in checks)
    assert any(x['path'].endswith('/SetupWizard.apk') for x in checks)
    if raw_image:
        after = raw_image.stat()
        assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    return {'release_zip': manifest['zip'], 'checked': checks, 'unsigned_build_transformed_inputs': excluded, 'image_layout': 'SDK37 system-as-root', 'final_ext4_checked': raw_image is not None, 'runtime_google_services_validated': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', type=pathlib.Path, required=True)
    p.add_argument('--product-out', type=pathlib.Path, required=True)
    p.add_argument('--raw-system', type=pathlib.Path)
    p.add_argument('--debugfs', type=pathlib.Path)
    p.add_argument('--report', type=pathlib.Path, required=True)
    a = p.parse_args()
    assert bool(a.raw_system) == bool(a.debugfs)
    result = verify(json.loads(a.manifest.read_text()), a.product_out, a.raw_system, a.debugfs)
    with a.report.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(len(result['checked']), 'signed payload/metadata files match; final ext4:', result['final_ext4_checked'])
