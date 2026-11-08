from pathlib import Path
import json, os, subprocess, hashlib, datetime, secrets, fcntl, re, struct

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
HELPER = WORK / '2026-11-07-asus-usb-retained-log-collector/scripts/root_shell_usb.py'
assert hashlib.sha256(HELPER.read_bytes()).hexdigest() == '76b28970223c63b9cdd6774c2190051953beee2d89cde1a22b30d1eebba5c78c'
record = ROOT / 'evidence/snapshot.json'
assert not record.exists(), 'Snapshot already attempted; preserve it, no automatic retry'
nonce = secrets.token_hex(16)
begin, end = 'CHECKPOINT_'+nonce+'_BEGIN', 'CHECKPOINT_'+nonce+'_END'
script = r'''
printf 'BOOT=';cat /proc/sys/kernel/random/boot_id
printf 'KERNEL=';uname -r
printf 'CACHE_BEGIN\n'
if [ -f /proc/aed/reboot-reason ] && [ ! -L /proc/aed/reboot-reason ]; then
head -c 32768 /proc/aed/reboot-reason || printf 'CACHE_READ_ERROR\n'
else printf 'CACHE_UNAVAILABLE\n';fi
printf '\nCACHE_END\n'
printf 'DT_BEGIN\n'
for p in /proc/device-tree/compatible /proc/device-tree/memory/reg /proc/device-tree/memory@40000000/reg /proc/device-tree/reserved-memory/#address-cells /proc/device-tree/reserved-memory/#size-cells /proc/device-tree/reserved-memory/ranges; do
if [ -f "$p" ]; then printf 'FIELD=%s\n' "$p";head -c 256 "$p" | od -An -tx1 -v;printf 'FIELD_END\n';fi
done
for n in /proc/device-tree/reserved-memory/ram_console*;do
[ -d "$n" ] || continue
printf 'NODE=%s\n' "$n"
for a in reg compatible status no-map reusable;do
if [ -f "$n/$a" ];then printf 'FIELD=%s/%s\n' "$n" "$a";head -c 256 "$n/$a" | od -An -tx1 -v;printf 'FIELD_END\n';else printf 'ABSENT=%s\n' "$a";fi
done
done
printf 'DT_END\n'
printf 'HEADER_BEGIN\n'
if [ -c /dev/mem ] && [ ! -L /dev/mem ] && [ "$(stat -c '%t:%T' /dev/mem)" = 1:1 ];then
# Fixed64-byte public OEMheader only; no interface creation or memory writes.
dd if=/dev/mem bs=64 skip=17891328 count=1 2>/dev/null | od -An -tx1 -v
else printf 'HEADER_INTERFACE_UNAVAILABLE\n';fi
printf 'HEADER_END\n'
printf 'BOOT_AFTER=';cat /proc/sys/kernel/random/boot_id
'''
assert 17891328 * 64 == 0x44400000
script = 'printf "'+begin+'\\n"\n'+script+'\nprintf "'+end+'\\n"\n'
env = {k:v for k,v in os.environ.items() if not k.startswith(('ADB_', 'ANDROID_ADB_')) and k != 'ANDROID_SERIAL'}
env['PATH'] = str(WORK/'2026-11-07-asus-usb-retained-log-collector/scripts/usb-adb')+os.pathsep+env.get('PATH', '/usr/bin:/bin')
s = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), status='UNKNOWN',
         diagnostic_command_read_only=True, helper_staging=True, memory_writes=False,
         image_writes=False, reboot=False, VM_start=False,
         fixed_header_address='0x44400000', maximum_header_read=64)
record.write_text(json.dumps(s, indent=2)+'\n')
with (WORK/'2026-11-06-asus-recovery-control-transport/evidence/execute.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        q = subprocess.run(['python3', '-B', str(HELPER)], input=script.encode(),
                           capture_output=True, env=env, timeout=90)
        (ROOT/'private/helper.stdout').write_bytes(q.stdout)
        (ROOT/'private/helper.stderr').write_bytes(q.stderr)
        s['helper_exit'] = q.returncode
        raw = q.stdout.decode('utf-8').replace('\r', '')
        assert q.returncode == 0 and raw.count(begin) == 1 and raw.count(end) == 1, 'Completion not verified; stop, no retry'
        data = raw.split(begin+'\n', 1)[1].split(end, 1)[0]
        boot = re.search(r'^BOOT=([0-9a-f-]+)$', data, re.M).group(1)
        after = re.search(r'^BOOT_AFTER=([0-9a-f-]+)$', data, re.M).group(1)
        assert boot == after, 'Boot changed during read'
        s.update(status='COMPLETE', boot_id=boot,
                 kernel=re.search(r'^KERNEL=(.*)$', data, re.M).group(1),
                 enforcing_restored=True)
        cache = data.split('CACHE_BEGIN\n', 1)[1].split('CACHE_END', 1)[0]
        s['cached_diagnostic_lines'] = [line[:500] for line in cache.splitlines()
                                      if any(key in line for key in ('WDT status:', 'fiq step:', '[LAST PC]'))]
        s['cache_unavailable'] = 'CACHE_UNAVAILABLE' in cache or 'CACHE_READ_ERROR' in cache
        dt = data.split('DT_BEGIN\n', 1)[1].split('DT_END', 1)[0]
        fields = {}
        for name, val in re.findall(r'FIELD=([^\n]+)\n(.*?)FIELD_END\n', dt, re.S):
            b = bytes.fromhex(val.strip())
            fields[name] = dict(hex=b.hex(), bytes=len(b))
        s['stock_DT_fields'] = fields
        s['stock_DT_not_linux49_runtime'] = True
        head = data.split('HEADER_BEGIN\n', 1)[1].split('HEADER_END', 1)[0].strip()
        if head == 'HEADER_INTERFACE_UNAVAILABLE':
            s['header_status'] = 'INTERFACE_UNAVAILABLE'
        elif not head:
            s['header_status'] = 'READ_REFUSED_OR_EMPTY'
        else:
            b = bytes.fromhex(head)
            assert len(b) == 64, 'Unexpected fixedheader read length'
            names = ['sig', 'off_pl', 'off_lpl', 'sz_pl', 'off_lk', 'off_llk', 'sz_lk',
                     'padding0', 'padding1', 'padding2', 'sz_buffer', 'off_linux',
                     'off_console', 'log_start', 'log_size', 'sz_console']
            s['header_status'] = 'READ64'
            s['header_fields'] = {k:hex(v) for k,v in zip(names, struct.unpack('<16I', b))}
            s['header_sha256'] = hashlib.sha256(b).hexdigest()
    except Exception as e:
        s.update(status='UNKNOWN', error=type(e).__name__+': '+str(e))
s['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
record.write_text(json.dumps(s, indent=2)+'\n')
print(json.dumps(s, indent=2))
raise SystemExit(0 if s['status'] == 'COMPLETE' else 2)
