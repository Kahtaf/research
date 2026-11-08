"""Read accepted stock inputs and emit a non-authorizing inverse inventory.
No daemon manifest containing write records is produced. No device operations.
"""
import argparse, hashlib, json
from pathlib import Path
from manifest import digest_file, GEOMETRY
from bootformat import RECOVERY_SHA
R = Path(__file__).resolve().parents[1]
BOOT_SHA = '7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316'
SYSTEM_SHA = '4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    parent = R / 'inputs/parent'
    acceptance = json.loads((parent / 'stock-os-backup-parent-acceptance.json').read_text())
    cid = json.loads((parent / 'device-cid-parent-20261106.json').read_text())
    assert acceptance['system_sha256'] == SYSTEM_SHA
    assert acceptance['system_bytes'] == GEOMETRY[25]
    assert acceptance['backup_exit_code'] == acceptance['verify_exit_code'] == 0
    assert acceptance['whole_oem_canonical_match'] is True
    assert hashlib.sha256((parent / 'stock-system-backup.manifest.json').read_bytes()).hexdigest() == acceptance['manifest_sha256']
    assert cid['cid_encoding'] == 'lowercase32hexwithoutnewline'
    assert cid['identity_and_enforcing_verified'] is True
    assert len(bytes.fromhex(cid['cid_sha256'])) == 32
    images = {}
    for role, part, path, expected in [
        ('original_system', 25, Path(acceptance['remote_system_path']), SYSTEM_SHA),
        ('original_boot', 9, R / 'inputs/initial/boot.bin', BOOT_SHA),
        ('original_recovery', 10, R / 'inputs/initial/recovery.bin', RECOVERY_SHA),
    ]:
        size = GEOMETRY[part] if part != 10 else 16740352
        full, chunks = digest_file(path, size)
        assert full.hex() == expected
        if part in (9, 10):
            other = R / 'inputs/verify' / path.name
            second, _ = digest_file(other, size)
            assert second == full
        images[role] = dict(path=str(path), part=part, bytes=size, sha256=full.hex(),
                            chunk_bytes=1048576, chunks=[h.hex() for h in chunks])
    plan = dict(mode='PLAN_ONLY', write_authorized=False, userdata_authorized=False,
                manifest_format='ASUSR002', cid_sha256=cid['cid_sha256'],
                cid_encoding=cid['cid_encoding'],
                primary_gpt_sha256='f87e70586706b06d029a2bc8521f1b8ae9176873cba1e5b4281cbaca816742ae',
                backup_gpt_sha256='2bf991125a74bf360d0cf4eb217df369ba2f78acf3dd312f26dc7695d2f31784',
                images=images, install_images={},
                approvals=dict(durable_original_system_backup=True,
                               durable_original_boot_backup=True,
                               durable_original_recovery_backup=True,
                               independent_rescue_review=False),
                qualified_userdata=dict(bytes=11331268096,
                    sha256='1602ea3644246871468b6987bc90e9a6e0c430f6b46efb4e79cc3555b688e0c1',
                    basis='parent acceptance; pristine image not accessed by this continuation',
                    write_authorized=False),
                calibration=dict(accessed=False, uploaded=False, restoration_owner='parent',
                    future_paths=['/data/vendor/p00a/nvram/APCFG/APRDEB/BT_Addr',
                                  '/data/vendor/p00a/nvram/APCFG/APRDEB/WIFI'],
                    preserve_partition=20),
                evidence={f.name:hashlib.sha256(f.read_bytes()).hexdigest()
                          for f in sorted(parent.iterdir()) if f.is_file()})
    with a.out.open('x') as f:
        f.write(json.dumps(plan, indent=2) + '\n')
    print(json.dumps(dict(mode=plan['mode'], write_authorized=False,
        images={k:{x:v[x] for x in ['part','bytes','sha256']} for k,v in images.items()}), indent=2))

if __name__ == '__main__':
    main()
