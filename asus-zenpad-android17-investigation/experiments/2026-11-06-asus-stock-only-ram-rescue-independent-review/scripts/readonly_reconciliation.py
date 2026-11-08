"""Existing opcode2 only: ordinary-file RSC model, no opcode3 or target edits."""
from pathlib import Path
import sys,json,struct,socket,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tests'));sys.path.insert(0,str(R/'source'))
from test_adapters import Adapter,h
import client
rows=[]
for case in ['original_boot_reconciliation','wrong_current_recovery_pin','changed_system_prerequisite','one_changed_boot_chunk','opcode6_without_recovery_pin','status_without_identity_qualification']:
    a=Adapter();a.setUp()
    try:
        m=a.manifest;off=112
        for _ in range(2):off+=52+32*struct.unpack_from('<I',m,off+48)[0]
        a.manifest=m[:12]+struct.pack('<I',2)+m[16:off];(a.root/'rescue.manifest').write_bytes(a.manifest)
        if case=='changed_system_prerequisite':
            p=a.root/'dev/block/mmcblk0p25';b=p.read_bytes();p.write_bytes(b'X'+b[1:])
        if case=='one_changed_boot_chunk':
            p=a.root/'dev/block/mmcblk0p9';b=p.read_bytes();p.write_bytes(b'X'+b[1:])
        if case=='opcode6_without_recovery_pin':
            p=a.root/'dev/block/mmcblk0p10';b=p.read_bytes();p.write_bytes(b'X'+b[1:])
        if case=='status_without_identity_qualification':(a.root/'sys/class/block/mmcblk0/device/cid').write_text('1'*32+'\n')
        before={str(p.relative_to(a.root)):h(p.read_bytes()).hex() for p in (a.root/'dev/block').glob('mmcblk*')}
        pending=a.root/'dev/rescue-state/journal.new';pending.write_text('test-only stale RAM journal')
        a.start();s=a.connect();sent=[]
        real_send=client.send
        def send(fd,op,b=b''):
            assert op!=3;sent.append(op);return real_send(fd,op,b)
        from unittest.mock import patch
        token_issued=False;matching=None;refused=False
        with patch.object(client,'send',side_effect=send):
            if case=='opcode6_without_recovery_pin':
                client.send(s.fileno(),6,struct.pack('<II',9,0));client.receive(s.fileno(),0x86);client.receive(s.fileno(),0x87)
            elif case=='status_without_identity_qualification':assert 'armed=2' in client.status(s.fileno())
            else:
                pin=bytes(32) if case=='wrong_current_recovery_pin' else h(a.recovery)
                try:
                    token,same,row=client.reconcile(s.fileno(),a.manifest,pin,1);token_issued=True;matching=list(same)
                    if case=='one_changed_boot_chunk':assert matching==[0,1,1]
                    else:assert all(same)
                    # Per-connection RECONCILED prevents another IDLE-only opcode2.
                    client.send(s.fileno(),2,h(a.manifest)+pin+struct.pack('<I',1))
                    try:client.receive(s.fileno(),0x82);raise AssertionError('second reconciliation accepted')
                    except RuntimeError:pass
                except RuntimeError:
                    refused=True
        s.close()
        assert refused==(case in ['wrong_current_recovery_pin','changed_system_prerequisite'])
        assert pending.exists()==(not token_issued)
        assert not (a.root/'dev/rescue-state/journal').exists()
        after={str(p.relative_to(a.root)):h(p.read_bytes()).hex() for p in (a.root/'dev/block').glob('mmcblk*')};assert before==after
        with a.connect() as s:status=client.status(s.fileno());assert 'uncertain_image=-1' in status and 'state=FROZEN' in status
        rows.append(dict(case=case,passed=True,sent=sent,token_issued=token_issued,matching_chunks=matching,refused=refused,pending_removed=not pending.exists(),journal_created=False,block_fixture_bytes_unchanged=True,status_after_disconnect=status,modeled_authority=True,small_geometry=True))
    finally:a.tearDown()
(R/'evidence/readonly-reconciliation.json').write_text(json.dumps(dict(passed=True,no_opcode3=True,cases=rows),indent=2)+'\n')
print('READONLY_RECONCILIATION_REVIEW_PASS',len(rows))
