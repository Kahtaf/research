"""Small offline checks; synthetic controls are never trial evidence."""
from pathlib import Path
import ctypes
import hashlib
import importlib.util
import json
import subprocess
import sys

sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[1]
B = R.parent / '2026-11-08-asus-arm64-delay-loop-observation'
sys.path.insert(0, str(B / 'source'))
import bootformat as b
from decode_sparse import decode, IDENTITY as ident, RELEASE

sha = lambda d: hashlib.sha256(d).hexdigest()
old = (B / 'artifacts/candidate.img').read_bytes()
assert sha(old) == 'f7687610c88afc296a6140bd98501b5f0f0e90f150503b0107a3044719c4175c'
_, _, ram, tail = b.parse_image(old)
assert not tail and sha(ram) == 'df6406bd884126190ce05c26f097f9d84a36c64e332286fa5aee6225670857d3'
cpio, extra = b.ungzip(ram[512:])
assert not extra
helper = b.parse_cpio(cpio)['init'][3]
assert sha(helper) == '1c9b6f23ed080be753b27ea49158564010a60cf2747e5964f07a2705e3745d1b'
reference = R.parent / '2026-11-07-asus-linux49-direct-clock-syscall-control'
_, _, reference_ram, _ = b.parse_image((reference / 'artifacts/candidate.img').read_bytes())
assert reference_ram == ram
helper_source = (reference / 'source/init.c').read_text()
for suffix in ident['helper_event_suffixes']:
    op = suffix.split(' op=')[1].split(' ')[0]
    assert '"' + op + '"' in helper_source
assert ident['helper_alarm_suffix'] in helper_source

tag = R / 'source/arch/arm64/kernel/asus_entry_tag.h'
cfile = R / 'evidence/filter-control.c'
cfile.write_text('#include <stdbool.h>\n#include <string.h>\n#include "' + str(tag) + '"\n' +
                 (R / 'source/sparse-filter.inc').read_text() +
                 '\nint accept(const char *p, unsigned int n) { return sparse_admit(p,n); }\n')
lib = R / 'evidence/filter-control.dylib'
cmd = ['cc', '-O2', '-Wall', '-Wextra', '-Werror', '-dynamiclib', str(cfile), '-o', str(lib)]
subprocess.run(cmd, check=True)
accept = ctypes.CDLL(str(lib)).accept
accept.argtypes = [ctypes.c_char_p, ctypes.c_uint]
accept.restype = ctypes.c_int
def admitted(s):
    data = s.encode()
    return bool(accept(data, len(data)))
accepted = ident['direct_markers'] + [ident['mode']]
accepted += [ident['helper_prefix'] + s + '0 errno=0 value=-' for s in ident['helper_event_suffixes']]
accepted += [ident['helper_prefix'] + ident['helper_alarm_suffix']]
for line in accepted:
    assert admitted(line) and admitted(line + '\n')
rejected = ['', 'Linux version ' + RELEASE, '02 setup_arch returned junk',
    ident['helper_prefix'], ident['helper_prefix'] + ' phase=before stage=end op=read.once.max128 path=/sys/class/block/mmcblk0/size rc=1 errno=0 value=1',
    ident['helper_prefix'] + ' phase=observe stage=actual op=clock_gettime.final path=WRONG rc=0 errno=0 value=0.0',
    accepted[-1][1:], accepted[-1] + '\nextra', accepted[-1] + '\x00', 'x' * 768,
    accepted[-1].replace('f0c3c82c', '00000000')]
for line in rejected:
    assert not admitted(line), repr(line)
# The input-length contract is authoritative; a truncated prefix never reads tail.
for count in range(len(ident['helper_prefix'])):
    assert not accept(accepted[-1].encode(), count)

def ev(p, s, o, a, rc=0, v='-', err=0):
    return ident['helper_prefix'] + f' phase={p} stage={s} op={o} path={a} rc={rc} errno={err} value={v}'
def irq(p, count):
    return [ev(p, 'actual', 'interrupts.arch_timer', '/proc/interrupts', v=f'irq=30 counts={count} cpus=1 controller=GIC-0 hwirq=30 trigger=Level name=arch_timer'),
            ev(p, 'complete', 'interrupts.snapshot', '/proc/interrupts', rc=1, v='bytes=100 read_calls=2 lines=3 arch_found=1 emitted=1 parse_or_read_errors=0 eof=1')]
start = ['ASUS49-ENTRY run=' + ident['run_uuid'] + ' stage=stext-preargs release=' + RELEASE, ident['mode'],
    ev('setup', 'actual', 'getpid', '-', rc=1, v='PID1-required'), ev('setup', 'actual', 'uname.release', '-', v=RELEASE)] + irq('before', 30) + [
    ev('observe', 'begin', 'alarm.nominal1s.timer-dependent', '-'), ev('observe', 'end', 'alarm.nominal1s.timer-dependent', '-'),
    ev('observe', 'actual', 'clock.path', 'CLOCK_MONOTONIC', v='kernel-syscall:syscall(SYS_clock_gettime);vDSO-bypassed'),
    ev('observe', 'begin', 'clock_gettime', 'loop.initial'), ev('observe', 'end', 'clock_gettime', 'loop.initial', v='0.650000000')]
def completed(delta, reason, flag, final, iterations):
    return start + [ev('observe', 'actual', 'clock_gettime.final', 'CLOCK_MONOTONIC', v=final + ' sample-valid=1'),
        ev('observe', 'complete', 'runnable.loop', 'CLOCK_MONOTONIC', v=f'delta_ns={delta} iterations={iterations} reason={reason} alarm_flag={flag} clock_error=0 counter_interval_not_wallclock=1')] + irq('after', 400)
full = completed(1500000000, 'counter-target', 1, '2.150000000', 1000000)
cap = completed(500000000, 'iteration-cap', 0, '1.150000000', 2000000)
controls = {
    'full_real_fields_GIC_0': (full, 'OBSERVED_BOUNDED_LIVENESS'),
    'partial_initial_only': (start, 'UNKNOWN_STOP'),
    'early_iteration_cap': (cap, 'VALID_PROGRESS_ITERATION_CAP_NOT_FULL_PASS'),
    'target_no_alarm': (completed(1500000000, 'counter-target', 0, '2.150000000', 1000000), 'VALID_LOOP_TARGET_INCOMPLETE_ALARM_OR_IRQ_EVIDENCE'),
    'missing_after': (full[:-2], 'VALID_LOOP_TARGET_INCOMPLETE_ALARM_OR_IRQ_EVIDENCE'),
    'wrong_uuid': ([s.replace(ident['run_uuid'], '00000000-0000-0000-0000-000000000000') for s in full], 'UNKNOWN_STOP'),
    'stale_old_area': (full + ['A49CAP1 uuid=old'], 'UNKNOWN_STOP'),
    'inconsistent_cap': (completed(1500000000, 'iteration-cap', 0, '2.150000000', 2000000), 'UNKNOWN_STOP'),
    'wrong_delta': (completed(1500000001, 'counter-target', 1, '2.150000000', 1000000), 'UNKNOWN_STOP'),
}
results = {}
for name, (lines, expected) in controls.items():
    assert all(admitted(line) for line in lines[1:] if not line.startswith('ASUS49-MODE run=0000') and not line.startswith('A49CAP1')) or name == 'wrong_uuid'
    actual = decode('\n'.join(lines))['status']
    assert actual == expected, (name, actual, expected)
    results[name] = actual

source = (R / 'source/arch/arm64/kernel/asus_retained_trace.c').read_text()
base = (B / 'source/arch/arm64/kernel/asus_retained_trace.c').read_text()
def function(text, signature, next_signature):
    return text[text.index(signature):text.index(next_signature, text.index(signature))]
writer = 'void asus_retained_trace_write('
nextfn = 'static void __init trace_init('
admission = '\tif (ASUS_SPARSE_PROFILE && !sparse_admit(text, len))\n\t\treturn;\n'
assert function(source, writer, nextfn).replace(admission, '') == function(base, writer, nextfn)
assert source.index(admission, source.index(writer)) < source.index('raw_spin_trylock_irqsave', source.index(writer))
init = function(source, 'static void __init cap_init(', 'static bool cap_lock(')
assert init.index('if (ASUS_SPARSE_PROFILE)') < init.index('raw_spin_trylock_irqsave') < init.index('memset(') < init.index('smp_store_release')
# All other function bytes, guards/mapping and entry writer are untouched by diff.
receipt = dict(status='LOCAL_SOURCE_AND_HOST_CONTROLS_ONLY', filter_accept_cases=len(accepted)*2,
    filter_reject_cases=len(rejected)+len(ident['helper_prefix']), parser_synthetic_controls=results,
    source_before_lock_filter=True, accepted_writer_body_byte_identical=True,
    cap_init_unconditional_compiled_profile_return_before_all_reservation_or_publication=True,
    baseline_package_ramdisk_sha256=sha(ram), baseline_package_helper_sha256=sha(helper),
    reference_package_entire_ramdisk_identical=True, reference_init_c_sha256=sha(helper_source.encode()),
    current_candidate_packaged_helper_verified=False, current_kernel_ELF_verified=False,
    actual_trial_data_used=False, no_device_contact=True,
    remaining='VM baseline/caller verification, one -j8 build, ELF proof, package, System.map pin, isolated PLAN and final VM state all blocked by cloud auth.')
(R / 'evidence/local-checks.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
