"""Read-only comparison of the complete fixed policy's avtab ordering.
The selected offset/count is independently checked by libsepol policydb_read.
No policy output is generated, loaded or modified.
"""
from collections import Counter
from pathlib import Path
import hashlib,json,struct
OFFSET=101268
COUNT=17746
def parts(data):
    count=struct.unpack_from('<I',data,OFFSET)[0]
    if count!=COUNT:raise ValueError('fixed avtab count mismatch')
    records=[];pos=OFFSET+4
    for _ in range(count):
        start=pos
        src,dst,cl,spec=struct.unpack_from('<4H',data,pos);pos+=8
        if not src or not dst or not cl:raise ValueError('invalid key')
        choices=[x for x in [1,2,4,0x10,0x20,0x40,0x100,0x200,0x400] if spec&x]
        if len(choices)!=1 or spec&~0x8777:raise ValueError('specifier shape')
        pos+=34 if spec&0x700 else 4
        if pos>len(data):raise ValueError('truncated record')
        records.append(data[start:pos])
    avend=pos
    # Exact policy30 following sections: zero conditional nodes, zero role
    # transitions and zero role allows; then six filename transitions.
    if struct.unpack_from('<4I',data,pos)!=(0,0,0,6):
        raise ValueError('fixed intervening section counts')
    pos+=16;filenames=[]
    for _ in range(6):
        start=pos;length=struct.unpack_from('<I',data,pos)[0];pos+=4
        if not 0<length<256:raise ValueError('filename length')
        pos+=length+16
        if pos>len(data):raise ValueError('truncated filename transition')
        filenames.append(data[start:pos])
    # No conflicting filename keys whose order could change their meaning.
    if len({v[:-4] for v in filenames})!=6:raise ValueError('duplicate filename key')
    return data[:OFFSET+4],records,data[pos:],avend,filenames,pos
def compare(saved,live):
    a,ar,z,end,af,tail=parts(saved);b,br,y,bend,bf,btail=parts(live)
    if a!=b or z!=y or end!=bend or tail!=btail or Counter(ar)!=Counter(br) or Counter(af)!=Counter(bf):
        raise ValueError('policy difference extends beyond ordering')
    return dict(equivalent_record_multiset=True,records=COUNT,avtab_start=OFFSET,
                avtab_end=end,filename_transition_records=6,identical_suffix_start=tail,
                identical_prefix_bytes=len(a),identical_suffix_bytes=len(z),
                duplicate_records=COUNT-len(set(ar)),
                only_difference='serialization order of complete avtab and filename-transition records')
def main():
    r=Path(__file__).resolve().parents[1];w=r.parent
    saved=(w/'2026-11-06-asus-framework-clear-bcb-api/inputs/stock-boot.sepolicy').read_bytes()
    live=next((r/'inputs').glob('*/policy')).read_bytes()
    assert hashlib.sha256(saved).hexdigest()=='873141c3874066341dcb4e2c7be4eb3f664686635ee3f84d2c4100f557ae740f'
    result=compare(saved,live)
    prefix,records,suffix,end,filenames,tail=parts(live)
    following=live[end:]
    negatives=[]
    changed=bytearray(live);changed[OFFSET+4+8]^=1
    changed_filename=bytearray(live);changed_filename[tail-1]^=1
    candidates={'changed_permission':bytes(changed),'omitted_record':prefix+b''.join(records[:-1])+following,
                'duplicated_record':prefix+records[0]+b''.join(records[1:-1])+records[0]+following,
                'changed_filename_transition':bytes(changed_filename),
                'changed_suffix':live[:-1]+bytes([live[-1]^1])}
    for name,data in candidates.items():
        try:compare(saved,data)
        except (ValueError,struct.error):negatives.append(name)
        else:raise AssertionError(name)
    result.update(saved_sha256=hashlib.sha256(saved).hexdigest(),live_sha256=hashlib.sha256(live).hexdigest(),negative_cases_refused=negatives,device_operation=False)
    (r/'evidence/policy-order-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
