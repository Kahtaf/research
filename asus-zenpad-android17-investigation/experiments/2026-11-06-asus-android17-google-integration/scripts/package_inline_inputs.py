#!/usr/bin/env python3
"""Package only the small, verified builder inputs; never include the release ZIP."""

import gzip
import hashlib
import io
from pathlib import Path
import tarfile

import stage_inline as stager


def main():
    blobs = stager.read_tree()
    original = stager.metadata(blobs)
    adapted = stager.adapted_metadata(original)
    groups, excluded = stager.payload_groups(blobs)
    plan = stager.plan(blobs, original, adapted, groups, excluded)
    stager.read_verified_manifest(stager.ROOT / "evidence/inline-source-manifest.json", plan)
    files = ["scripts/stage_inline.py", "scripts/test_stage_inline.py", "scripts/package_inline_inputs.py",
             "evidence/upstream-tree.json", "evidence/inline-source-manifest.json",
             "evidence/platform-inline-source.json", "evidence/inline-jni-elf.json",
             "evidence/inline-build-findings.md", "evidence/stager-tests.txt", "google-astra-report.md"]
    files += ["evidence/upstream-source/" + p for p in original]
    target = stager.ROOT / "staged-inputs/google-inline-inputs.tar.gz"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as f, gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
            for name in sorted(files):
                b = (stager.ROOT / name).read_bytes()
                stager.require(len(b) < 1024 * 1024, f"unexpected large handoff file: {name}")
                info = tarfile.TarInfo(name)
                info.mode = 0o644
                info.size = len(b)
                info.mtime = 0
                tar.addfile(info, io.BytesIO(b))
    sha = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix(target.suffix + ".sha256").write_text(f"{sha}  {target.name}\n")
    print(f"{len(files)} files, {target.stat().st_size} bytes, SHA256 {sha}")


if __name__ == "__main__":
    main()
