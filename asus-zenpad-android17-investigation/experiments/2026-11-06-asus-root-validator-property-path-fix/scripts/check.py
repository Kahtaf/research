"""Run actual root validator functions on tiny non-executable fixture files."""
import ast
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import xml.etree.ElementTree as ET

SCRIPTS = Path(__file__).resolve().parents[2] / '2026-11-06-asus-r8-continuation-kit/scripts'
namespace = dict(Path=Path, struct=struct, ET=ET, hashlib=hashlib)
def functions(path, names):
    tree = ast.parse(path.read_text())
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in nodes} == set(names)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(path), 'exec'), namespace)
class Refusal(RuntimeError): pass
namespace['Refusal'] = Refusal
functions(SCRIPTS/'integrate.py', {'need', 'sha'})
functions(SCRIPTS/'verify_google_payload.py', {'digest'})
functions(Path(sys.argv[1]), {'elf64', 'verify'})
rows = []
with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'evidence') as tmp:
    root = Path(tmp); product=root/'product'; apex=root/'apex'
    def put(base, rel, data):
        p=base/rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data); return p
    header=bytearray(20);header[:6]=b'\x7fELF\x02\x01';struct.pack_into('<H',header,18,183)
    put(product,'system/system_ext/bin/adb_root',header)
    init=put(product,'system/system_ext/etc/init/adb_root.rc',b'fixture-not-executable\n')
    put(product,'system/apex/adbd.capex',b'fixture-not-an-apex')
    put(apex,'com.android.adbd/bin/adbd',header)
    put(apex,'apex-info-list.xml',b'<apex-info-list><apex-info moduleName="com.android.adbd" isActive="true" modulePath="/system/apex/adbd.capex"/></apex-info-list>')
    put(product,'system/build.prop',b'ro.secure=1\nro.debuggable=1\nro.adb.secure=1\n')
    for rel in ('system/system_ext/etc/build.prop','system/product/etc/build.prop'):
        put(product,rel,b'ro.adb.secure=1\n')
    expected_paths={'system/system_ext/etc/build.prop','system/product/etc/build.prop'}
    receipt=namespace['verify'](product,apex,namespace['sha'](init))
    rows.append({'case':'current SDK37 partition properties included','pass':expected_paths <= receipt['installed_files'].keys()})
    for rel in sorted(expected_paths):
        put(product,rel,b'ro.adb.secure=0\n')
        try:
            namespace['verify'](product,apex,namespace['sha'](init)); rejected=False
        except Refusal as error:
            rejected='Generated secure userdebug property mismatch' in str(error)
        rows.append({'case':'conflicting current property rejected: '+rel,'pass':rejected})
        put(product,rel,b'ro.adb.secure=1\n')
print(json.dumps({'cases':rows,'all_pass':all(row['pass'] for row in rows),'scope':'actual validator function behavior on tiny fixtures; no ELF/APEX authenticity or real product claim'},indent=2))
raise SystemExit(0 if all(row['pass'] for row in rows) else 1)
