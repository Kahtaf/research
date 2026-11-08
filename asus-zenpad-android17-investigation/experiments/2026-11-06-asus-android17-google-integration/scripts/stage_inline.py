#!/usr/bin/env python3
"""Reconstruct the pinned MTG arm64 inline source without a clone or ZIP extraction.

Default: check small cached upstream sources and produce reviewable metadata.
verify: stream the existing release ZIP into hashes, never payload files.
stage: Linux builder only; reconstruct vendor/gapps atomically, refusing overwrite.
check: compare an existing stage with the verified manifest, without mutations.
"""

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parents[1]
COMMIT = "822ff6a805533792ae43a9c3f2a159222da22a6f"
TREE_SHA256 = "d0ae19c4ffac28f98358a4e2d7fd48f208b9b81c87238d08a8b1d5974f68d02b"
ZIP_NAME = "MindTheGapps-17.0.0-arm64-20261022_132445.zip"
ZIP_SIZE = 544284463
ZIP_SHA256 = "a6844eeb2613541558237e467b20feb01f8b45b2ebab0109834140ea59b6ca4d"
RAW = f"https://raw.githubusercontent.com/MindTheGapps/vendor_gapps/{COMMIT}/"
BLOCK = 1024 * 1024
TITAN = "product/priv-app/VelvetTitan/VelvetTitan.apk"
OVERLAYS = ("GmsOverlay", "GmsSettingsOverlay", "GmsSettingsProviderOverlay", "GmsSetupWizardOverlay")
INSTALLER_MEMBERS = {
    "META-INF/com/google/android/update-binary",
    "META-INF/com/google/android/updater-script",
    "META-INF/com/android/otacert", "build.prop", "toybox",
    "system/addon.d/addond_head", "system/addon.d/addond_tail",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def file_digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(BLOCK), b""):
            h.update(b)
    return h.hexdigest()


def safe_path(value):
    p = PurePosixPath(value)
    require(not p.is_absolute() and p.parts and ".." not in p.parts
            and str(p) == value and "\\" not in value, f"unsafe path: {value}")
    return value


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    fd, temp = tempfile.mkstemp(prefix=".manifest-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def read_tree():
    data = (ROOT / "evidence/upstream-tree.json").read_bytes()
    require(digest(data) == TREE_SHA256, "cached recursive tree digest changed")
    tree = json.loads(data)
    require(tree["sha"] == COMMIT and tree["truncated"] is False, "wrong or incomplete tree")
    blobs = {safe_path(x["path"]): x for x in tree["tree"] if x["type"] == "blob"}
    require(len(blobs) == 113, "unexpected upstream blob inventory")
    require(all(x["mode"] in ("100644", "100755") for x in blobs.values()), "unsupported Git file mode")
    return blobs


def metadata_entries(blobs):
    return {p: x for p, x in blobs.items() if "/proprietary/" not in p and
            (p.startswith(("arm64/", "common/", "dummy-apps/", "overlay/"))
             or p in ("README.md", "LICENSE", ".gitignore"))}


def metadata(blobs, fetch=False):
    result = {}
    for p, x in sorted(metadata_entries(blobs).items()):
        path = ROOT / "evidence/upstream-source" / p
        if not path.exists():
            require(fetch, f"missing metadata {p}; use --fetch-metadata once")
            require(x["size"] < 100000, f"metadata fetch too large: {p}")
            with urllib.request.urlopen(RAW + p, timeout=45) as response:
                data = response.read(x["size"] + 1)
            require(len(data) == x["size"] and git_blob(data) == x["sha"], f"upstream mismatch: {p}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        data = path.read_bytes()
        require(len(data) == x["size"] and git_blob(data) == x["sha"], f"cached upstream mismatch: {p}")
        result[p] = data
    return result


def replace_once(text, old, new):
    require(text.count(old) == 1, f"patch context not unique: {old!r}")
    return text.replace(old, new, 1)


def adapted_metadata(original):
    result = dict(original)
    bp = result["arm64/Android.bp"].decode()
    bp = replace_once(bp, '    name: "libjni_latinimegoogle",\n',
                      '    name: "libjni_latinimegoogle",\n    compile_multilib: "64",\n')
    # An unselected module still enters Soong's graph. Do not leave dangling
    # source references to the deliberately un-staged tangorpro-only chunks.
    start = bp.index('genrule {\n    name: "VelvetTitan.apk-genrule",')
    end = bp.index('android_app_import {\n    name: "talkback",', start)
    removed = bp[start:end]
    require(removed.count('name: "VelvetTitan') == 2, "unexpected Titan definitions")
    result["arm64/Android.bp"] = (bp[:start] + bp[end:]).encode()
    mk = result["arm64/arm64-vendor.mk"].decode()
    mk = replace_once(mk, 'ifneq ($(filter %tangorpro,$(TARGET_PRODUCT)),)\nPRODUCT_PACKAGES += \\\n    VelvetTitan\nendif\n\n', '')
    result["arm64/arm64-vendor.mk"] = mk.encode()
    result["asus-p00a-google.mk"] = b'''# Generated by the pinned ASUS Google source stager. Inline arm64 tablet profile.
# Product configuration is imported before BoardConfig defines TARGET_ARCH.
ifneq ($(TARGET_PRODUCT),lineage_p00a)
$(error ASUS Google source profile requires TARGET_PRODUCT=lineage_p00a)
endif
ifneq ($(strip $(TARGET_IS_GROUPER)),)
$(error ASUS Google source profile must retain the normal non-grouper app set)
endif
ifneq ($(filter %tangorpro,$(TARGET_PRODUCT)),)
$(error ASUS Google source profile excludes tangorpro-only VelvetTitan)
endif

# Inherit, do not plain-include: Android assigns LOCAL_PATH for each product node.
$(call inherit-product, vendor/gapps/arm64/arm64-vendor.mk)
'''
    return result


def payload_groups(blobs):
    groups = {}
    excluded = []
    for p, x in sorted(blobs.items()):
        if not p.startswith(("arm64/proprietary/", "common/proprietary/")):
            continue
        relative = p.split("/proprietary/", 1)[1]
        base = re.sub(r"\.\d{2}$", "", relative)
        if base == TITAN:
            excluded.append(p)
            continue
        groups.setdefault("system/" + base, []).append(x)
    require(len(excluded) == 4, "unexpected excluded Titan chunks")
    for member, chunks in groups.items():
        if len(chunks) > 1:
            for n, chunk in enumerate(chunks):
                require(chunk["path"].endswith(f".{n:02d}"), f"noncontiguous chunks: {member}")
        else:
            require(not re.search(r"\.\d{2}$", chunks[0]["path"]), f"incomplete chunk group: {member}")
    return groups, excluded


def output_record(data, source, mode="100644"):
    return {"size": len(data), "sha256": digest(data), "git_blob_sha1": git_blob(data),
            "mode": mode, "source": source}


def plan(blobs, original, adapted, groups, excluded):
    inputs = {}
    outputs = {}
    for p, data in original.items():
        inputs[p] = output_record(data, RAW + p, blobs[p]["mode"])
    for p, data in adapted.items():
        source = "local-profile" if p not in original else (
            "upstream" if data == original[p] else "upstream+documented-adaptation")
        outputs[p] = output_record(data, source, blobs[p]["mode"] if p in blobs else "100644")
    for member, chunks in groups.items():
        offset = 0
        for x in chunks:
            outputs[x["path"]] = {"size": x["size"], "git_blob_sha1": x["sha"],
                                  "mode": x["mode"], "source": "release-zip",
                                  "zip_member": member, "offset": offset}
            offset += x["size"]
    return {"schema": 1, "profile": "asus-p00a-arm64-normal-tablet", "commit": COMMIT,
            "tree_sha256": TREE_SHA256, "zip": {"name": ZIP_NAME, "size": ZIP_SIZE, "sha256": ZIP_SHA256},
            "metadata_inputs": inputs, "outputs": outputs, "excluded_upstream_blobs": excluded,
            "payload_bytes": sum(x["size"] for chunks in groups.values() for x in chunks),
            "adaptations": ["libjni_latinimegoogle compile_multilib=64",
                            "remove tangorpro-only VelvetTitan module/genrule/product conditional",
                            "add guarded ASUS product inheritance wrapper"],
            "verification": "metadata-only; payload not read"}


def zip_inventory(z, groups):
    infos = z.infolist()
    require(len({x.filename for x in infos}) == len(infos), "duplicate ZIP member")
    overlay_members = {f"system/product/overlay/{name}.apk" for name in OVERLAYS}
    inventory = {}
    for x in infos:
        safe_path(x.filename.rstrip("/"))
        require(not x.flag_bits & 1, "encrypted ZIP member")
        if x.is_dir():
            continue
        require((x.external_attr >> 16) & 0o170000 in (0, 0o100000), f"nonregular ZIP member: {x.filename}")
        if x.filename in groups:
            disposition = "reconstruct-upstream-blobs"
            require(x.file_size == sum(v["size"] for v in groups[x.filename]), f"ZIP/tree size mismatch: {x.filename}")
        elif x.filename in overlay_members:
            disposition = "reference-only; inline overlay rebuilt from exact upstream source"
        elif x.filename == "system/" + TITAN:
            disposition = "excluded; upstream tangorpro-only"
        else:
            require(x.filename in INSTALLER_MEMBERS, f"unclassified ZIP member: {x.filename}")
            disposition = "standalone-installer-only; not an inline build input"
        inventory[x.filename] = {"size": x.file_size, "crc32": f"{x.CRC:08x}",
                                 "compressed_size": x.compress_size, "disposition": disposition}
    require(set(inventory) == set(groups) | overlay_members | INSTALLER_MEMBERS | {"system/" + TITAN},
            "release ZIP is missing expected members")
    return inventory


def stream_payload(z, groups, outputs, destination=None):
    members = {}
    for member, chunks in sorted(groups.items()):
        total = hashlib.sha256()
        with z.open(member) as stream:
            for x in chunks:
                git = hashlib.sha1(b"blob " + str(x["size"]).encode() + b"\0")
                sha = hashlib.sha256()
                target = None
                if destination:
                    target = destination / x["path"]
                    target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") if target else contextlib.nullcontext() as out:
                    remaining = x["size"]
                    while remaining:
                        data = stream.read(min(BLOCK, remaining))
                        require(data, f"short ZIP stream: {member}")
                        remaining -= len(data)
                        git.update(data)
                        sha.update(data)
                        total.update(data)
                        if out:
                            out.write(data)
                require(git.hexdigest() == x["sha"], f"Git blob mismatch: {x['path']}")
                outputs[x["path"]]["sha256"] = sha.hexdigest()
                if target:
                    target.chmod(int(x["mode"], 8) & 0o777)
            require(stream.read(1) == b"", f"trailing bytes: {member}")
        members[member] = {"sha256": total.hexdigest(), "size": sum(x["size"] for x in chunks)}
    return members


def verify(zip_path, result, groups, destination=None):
    require(zip_path.stat().st_size == ZIP_SIZE, "wrong release ZIP size")
    require(file_digest(zip_path) == ZIP_SHA256, "wrong release ZIP SHA256")
    with zipfile.ZipFile(zip_path) as z:
        result["zip_inventory"] = zip_inventory(z, groups)
        result["payload_members"] = stream_payload(z, groups, result["outputs"], destination)
    result["verification"] = "release SHA256 + all selected upstream blob sizes/Git SHA1 + output SHA256 passed"
    return result


def read_verified_manifest(path, expected_plan):
    result = json.loads(path.read_text())
    require(result.get("verification", "").endswith("output SHA256 passed"), "manifest has no payload proof")
    for key in ("schema", "profile", "commit", "tree_sha256", "zip", "metadata_inputs", "excluded_upstream_blobs", "payload_bytes", "adaptations"):
        require(result.get(key) == expected_plan[key], f"manifest disagrees with pinned inputs: {key}")
    require(set(result["outputs"]) == set(expected_plan["outputs"]), "manifest output inventory changed")
    for p, expected in expected_plan["outputs"].items():
        actual = result["outputs"][p]
        require(all(actual.get(k) == v for k, v in expected.items()), f"manifest output changed: {p}")
        require(set(actual) == set(expected) | {"sha256"} and re.fullmatch(r"[a-f0-9]{64}", actual["sha256"]),
                f"missing or invalid SHA256: {p}")
    return result


def materialize_metadata(directory, adapted, blobs):
    for p, data in adapted.items():
        f = directory / p
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
        f.chmod(int(blobs[p]["mode"], 8) & 0o777 if p in blobs else 0o644)


def check_stage(directory, manifest):
    require(directory.is_dir() and not directory.is_symlink(), f"not a regular stage directory: {directory}")
    files = set()
    for p in directory.rglob("*"):
        require(not p.is_symlink(), f"symlink in stage: {p}")
        if p.is_file():
            files.add(p.relative_to(directory).as_posix())
        else:
            require(p.is_dir(), f"nonregular stage entry: {p}")
    require(files == set(manifest["outputs"]) | {"staging-manifest.json"}, "stage has missing or extra files")
    require(json.loads((directory / "staging-manifest.json").read_text()) == manifest, "embedded manifest mismatch")
    for p, entry in manifest["outputs"].items():
        f = directory / p
        require(f.stat().st_size == entry["size"] and file_digest(f) == entry["sha256"], f"staged bytes mismatch: {p}")
        require(f.stat().st_mode & 0o777 == int(entry["mode"], 8) & 0o777, f"staged mode mismatch: {p}")


def stage(android_root, zip_path, expected, result, adapted, blobs, groups):
    require(sys.platform.startswith("linux"), "full staging is Linux-builder-only; use verify on the Mac")
    android_root = android_root.resolve()
    require((android_root / "build/soong").is_dir(), "--android-root is not an Android source checkout")
    vendor = android_root / "vendor"
    require(vendor.is_dir() and not vendor.is_symlink(), "vendor must be an existing regular directory")
    destination = vendor / "gapps"
    require(not destination.exists() and not destination.is_symlink(), "vendor/gapps already exists; use check, never overwrite")
    require(shutil.disk_usage(vendor).free >= result["payload_bytes"] + 128 * 1024 * 1024, "insufficient builder staging space")
    temporary = Path(tempfile.mkdtemp(prefix=".gapps-stage-", dir=vendor))
    try:
        temporary.chmod(0o755)
        materialize_metadata(temporary, adapted, blobs)
        actual = verify(zip_path, result, groups, temporary)
        require(actual == expected, "reconstructed manifest differs from reviewed proof")
        write_json(temporary / "staging-manifest.json", actual)
        check_stage(temporary, expected)
        require(not destination.exists() and not destination.is_symlink(), "destination appeared during staging")
        temporary.rename(destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    print(f"Verified inline sources staged at {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("metadata", "verify", "stage", "check"), nargs="?", default="metadata")
    parser.add_argument("--zip", type=Path, default=ROOT / "downloads" / ZIP_NAME)
    parser.add_argument("--manifest", type=Path, default=ROOT / "evidence/inline-source-manifest.json")
    parser.add_argument("--android-root", type=Path)
    parser.add_argument("--fetch-metadata", action="store_true", help="fetch only missing small files from the pinned commit")
    args = parser.parse_args()
    blobs = read_tree()
    original = metadata(blobs, args.fetch_metadata)
    adapted = adapted_metadata(original)
    groups, excluded = payload_groups(blobs)
    result = plan(blobs, original, adapted, groups, excluded)
    if args.mode == "metadata":
        # This is deliberately not a vendor/gapps checkout: copying it alone
        # cannot be mistaken for a completed payload reconstruction.
        output = ROOT / "staged-inputs/inline-metadata"
        materialize_metadata(output, adapted, blobs)
        write_json(ROOT / "evidence/inline-source-plan.json", result)
        print(f"Verified {len(original)} pinned metadata files; wrote metadata-only plan and {output}")
    elif args.mode == "verify":
        result = verify(args.zip, result, groups)
        write_json(args.manifest, result)
        print(f"PASS: {len(result['payload_members'])} ZIP payload members -> "
              f"{sum(len(x) for x in groups.values())} Git blobs; {result['payload_bytes']} bytes; no payload extracted")
    else:
        require(args.android_root is not None, "stage/check require --android-root")
        expected = read_verified_manifest(args.manifest, result)
        if args.mode == "stage":
            stage(args.android_root, args.zip, expected, result, adapted, blobs, groups)
        else:
            check_stage(args.android_root / "vendor/gapps", expected)
            print("PASS: staged file inventory, embedded manifest, sizes, SHA256 and modes")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, zipfile.BadZipFile, KeyError) as error:
        sys.exit(f"ERROR: {error}")
