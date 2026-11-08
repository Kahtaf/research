"""Read-only strict decoder for this candidate's complete stock /proc/last_kmsg framing."""
from pathlib import Path
import argparse,hashlib,json,re,uuid
ROOT=Path(__file__).resolve().parents[1]
U64=(1<<64)-1

def unique_json(path):
    def unique(items):
        result={}
        for k,v in items:
            if k in result:raise ValueError('duplicate JSON key')
            result[k]=v
        return result
    return json.loads(path.read_text(),object_pairs_hook=unique)

def decode(raw,attestation=None):
    result=dict(status='UNKNOWN',raw_sha256=hashlib.sha256(raw).hexdigest(),raw_bytes=len(raw),raw_preserved=True,physical_calibration=False,walltime_claim=False,storage_fullOS_protection_admission=False)
    try:
        p=unique_json(ROOT/'evidence/packaging-receipt.json')
        identity=unique_json(ROOT/'evidence/identity.json')
        if not raw or len(raw)>0x80000+256:raise ValueError('empty/oversized capture')
        text=raw.decode('ascii')
        if any(ord(c)<32 and c not in '\n\t' for c in text):raise ValueError('control/torn data')
        header=re.match(r'ram console header, hw_status: (0|[1-9][0-9]*), fiq step (0|[1-9][0-9]*)\.\n',text)
        if not header or any(int(x)>0xffffffff for x in header.groups()):raise ValueError('unknown stock-proc framing; no arbitrary leading trim')
        console=text[header.end():]
        if not console.endswith('\n'):raise ValueError('truncated final line')
        entry=identity['entry_tag']
        if not console.startswith(entry) or console.count('ASUS49-ENTRY')!=1:raise ValueError('missing/stale/mixed/duplicate kernel entry')
        prefix='ASUS-MINPLAT run='+identity['run_uuid']+' '
        records=[]
        for line in console.splitlines()[1:]:
            if 'ASUS-MINPLAT' in line:
                if not line.startswith(prefix):raise ValueError('mixed/malformed helper identity')
                records.append(line[len(prefix):])
        if len(records)!=16:raise ValueError('missing/duplicate/extra helper stages')
        expected=['event=entry pid=1',p['expected_uname_record'],'event=scheduler policy=0 priority=0 nice=0','event=compute-begin iterations=2000000','event=compute-end iterations=2000000 state=2093acf8 checksum=4296231513146560']
        if records[:5]!=expected:raise ValueError('entry/uname/scheduler/compute contract mismatch')
        def mono(sec,nano):
            if len(sec)>19 or int(sec)>(1<<63)-1:raise ValueError('monotonic range')
            return int(sec)*1000000000+int(nano)
        prior_irq=prior_mono=None
        observed=[]
        for cycle in range(1,6):
            before=re.fullmatch(r'event=timer-before cycle='+str(cycle)+r' irq=(0|[1-9][0-9]*) monotonic=(0|[1-9][0-9]*)\.([0-9]{9}) requested_interval=1s',records[5+(cycle-1)*2])
            after=re.fullmatch(r'event=timer-return cycle='+str(cycle)+r' signal=SIGALRM irq=(0|[1-9][0-9]*) irq_before=(0|[1-9][0-9]*) monotonic=(0|[1-9][0-9]*)\.([0-9]{9})',records[6+(cycle-1)*2])
            if not before or not after:raise ValueError('missing/out-of-order/malformed timer pair')
            ib=int(before[1]);ia=int(after[1]);tb=mono(before[2],before[3]);ta=mono(after[3],after[4])
            if max(ib,ia)>U64 or int(after[2])!=ib or ia<=ib or ta<=tb:raise ValueError('timer IRQ/monotonic growth invalid')
            if prior_irq is not None and (ib<prior_irq or tb<prior_mono):raise ValueError('inter-cycle observations regressed')
            observed.append(dict(cycle=cycle,irq_before=ib,irq_after=ia,monotonic_before_ns=tb,monotonic_after_ns=ta))
            prior_irq,prior_mono=ia,ta
        if records[-1]!='event=success operation=five-timer-returns errno=0 next=normal-reboot':raise ValueError('success/normal reboot request missing')
        result.update(sequence_valid=True,observed_cycles=observed,normal_scheduler_record=True,one_cpu_evidence='bound unchanged helper passed proc/sysconf gate and strict CPU0 IRQ parser before these stages',compute_valid=True,normal_reboot_requested=True)
        if not isinstance(attestation,dict):raise ValueError('parent freshness/completeness/stock-return attestations absent')
        required={'installed_full_p10_sha256','raw_sha256','complete_console_reference','console_capacity','console_log_size','console_log_start','pre_trial_stock_boot_id','post_trial_stock_boot_id','stock_return_verified','stock_return_reference'}
        if set(attestation)!=required:raise ValueError('unexpected/missing parent attestation fields')
        if attestation['installed_full_p10_sha256']!=p['full_p10']['sha256'] or attestation['raw_sha256']!=result['raw_sha256']:raise ValueError('candidate/raw binding mismatch')
        size=len(console.encode('ascii'));capacity=attestation['console_capacity']
        if type(capacity) is not int or not size<capacity<=0x80000 or attestation['console_log_size']!=size or type(attestation['console_log_size']) is not int or type(attestation['console_log_start']) is not int or attestation['console_log_start']!=0:raise ValueError('saturated/wrapped/truncated console geometry')
        for k in ['complete_console_reference','stock_return_reference']:
            if type(attestation[k]) is not str or not attestation[k].strip():raise ValueError('empty external evidence reference')
        for k in ['pre_trial_stock_boot_id','post_trial_stock_boot_id']:
            if str(uuid.UUID(attestation[k]))!=attestation[k]:raise ValueError('noncanonical stock boot identity')
        if attestation['pre_trial_stock_boot_id']==attestation['post_trial_stock_boot_id'] or attestation['stock_return_verified'] is not True:raise ValueError('fresh verified stock return unproved')
        result.update(status='FUNCTIONAL_RAM_SEQUENCE_WITH_PARENT_ATTESTED_FRESH_STOCK_RETURN',parent_attestations_only=True,attestations=attestation)
    except (ValueError,KeyError,TypeError,UnicodeError,IndexError,OSError) as exc:
        result['reason']=str(exc)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw_stock_proc',type=Path)
    parser.add_argument('--parent-attestation',type=Path)
    args=parser.parse_args()
    raw=args.raw_stock_proc.read_bytes()  # Never rewrite or normalize original raw.
    att=unique_json(args.parent_attestation) if args.parent_attestation else None
    print(json.dumps(decode(raw,att),indent=2))
if __name__=='__main__':main()
