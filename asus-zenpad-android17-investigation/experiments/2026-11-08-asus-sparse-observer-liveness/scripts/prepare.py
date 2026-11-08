"""Prepare exactly two recorder/tag edits from the pinned local f3da mirror."""
from pathlib import Path
import difflib
import hashlib
import json
import sys
import uuid

sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[1]
B = R.parent / '2026-11-08-asus-arm64-delay-loop-observation'
sha = lambda b: hashlib.sha256(b).hexdigest()
identity = R / 'evidence/identity.json'
assert not identity.exists(), 'Prepare once; preserve this run identity'
run = str(uuid.uuid4())
mode = ('ASUS49-MODE run=' + run +
        ' profile=sparse-v1 hot=disabled ordinary_printk=filtered delay=original-virtual')
pins = json.loads((B / 'evidence/source-pins.json').read_text())
names = ['arch/arm64/kernel/asus_retained_trace.c', 'arch/arm64/kernel/asus_entry_tag.h']
source = {n: (B / 'source' / n).read_text() for n in names}
for n in names:
    assert sha(source[n].encode()) == pins[n]['after']
tag = names[1]
source[tag] = source[tag].replace('f3da846c-cbd9-4623-adc2-5e54d097dfdc', run)
source[tag] += '\n#define ASUS_SPARSE_PROFILE 1\n#define ASUS_SPARSE_MODE "' + mode + '"\n'

# These are prefixes of complete, actual helper event() messages, after /dev/kmsg
# strips <6>. Each includes phase/stage/op/path; no generic helper-prefix admit.
events = [
    ('setup', 'actual', 'getpid', '-'),
    ('setup', 'actual', 'uname.release', '-'),
    ('observe', 'actual', 'clock.path', 'CLOCK_MONOTONIC'),
    ('observe', 'begin', 'clock_gettime', 'loop.initial'),
    ('observe', 'end', 'clock_gettime', 'loop.initial'),
    ('observe', 'begin', 'alarm.nominal1s.timer-dependent', '-'),
    ('observe', 'end', 'alarm.nominal1s.timer-dependent', '-'),
    ('observe', 'actual', 'clock_gettime.final', 'CLOCK_MONOTONIC'),
    ('observe', 'complete', 'runnable.loop', 'CLOCK_MONOTONIC'),
]
for phase in ['before', 'after']:
    events += [(phase, 'actual', 'interrupts.arch_timer', '/proc/interrupts'),
               (phase, 'complete', 'interrupts.snapshot', '/proc/interrupts')]
events += [('finish', 'actual', 'alarm.final-flag', 'SIGALRM'),
           ('finish', 'complete', 'observation', '-'),
           ('finish', 'actual', 'sink.write.error', '-'),
           ('finish', 'begin', 'reboot', '-'), ('finish', 'end', 'reboot', '-')]
prefix = 'ASUS49-SYSCLOCK run=f0c3c82c-d639-4d8a-90f2-155fd4224ceb'
suffixes = [f' phase={p} stage={s} op={o} path={a} rc=' for p, s, o, a in events]
alarm = ' stage=alarm op=SIGALRM.fired nominal_seconds=1 timer_dependent=1'
markers = [
    'ASUS-e9-retained-v2 00 arm64_memblock_init returned; before paging_init',
    'ASUS-e9-retained-v2 01 paging_init returned; trace ready',
    '02 setup_arch returned', '03 before init_IRQ', '04 init_IRQ returned',
    '05 before time_init', '06 time_init returned',
]
filter_code = r'''/* Sparse admission only; accepted writes retain the original publication path. */
static bool sparse_prefix(const char *p, unsigned int n,
                          const char *s, unsigned int k)
{
 return n >= k && !memcmp(p, s, k);
}

static bool sparse_equal(const char *p, unsigned int n,
                         const char *s, unsigned int k)
{
 return n == k && !memcmp(p, s, k);
}

static bool sparse_admit(const char *text, unsigned int len)
{
 unsigned int i;
 static const char helper[] = "HELPER";
 if (!len || len > 767)
  return false;
 if (text[len - 1] == '\n')
  --len;
 for (i = 0; i < len; ++i)
  if ((unsigned char)text[i] < 32 || (unsigned char)text[i] > 126)
   return false;
#define SAME(s) sparse_equal(text, len, s, sizeof(s) - 1)
 if (SAME(ASUS_SPARSE_MODE) || MARKERS)
  return true;
#undef SAME
 if (!sparse_prefix(text, len, helper, sizeof(helper) - 1))
  return false;
 text += sizeof(helper) - 1;
 len -= sizeof(helper) - 1;
#define PREFIX(s) sparse_prefix(text, len, s, sizeof(s) - 1)
 return PREFIXES ||
        sparse_equal(text, len, "ALARM", sizeof("ALARM") - 1);
#undef PREFIX
}

'''.replace('HELPER', prefix).replace('MARKERS', ' ||\n     '.join('SAME("' + s + '")' for s in markers)).replace('PREFIXES', ' ||\n        '.join('PREFIX("' + s + '")' for s in suffixes)).replace('ALARM', alarm)
n = names[0]
s = source[n]
needle = ' BUILD_BUG_ON(CAP_SIZE > 8192);'
assert s.count(needle) == 1
s = s.replace(needle, ' /* Keep all six ready pointers at their zero-initialized not-ready state. */\n if (ASUS_SPARSE_PROFILE)\n  return;\n' + needle)
needle = '/* Keep the first text; a full buffer freezes instead of losing entry markers. */'
assert s.count(needle) == 1
s = s.replace(needle, filter_code + needle)
needle = '\tif (!h || !len || !raw_spin_trylock_irqsave(&trace_lock, flags))'
assert s.count(needle) == 1
s = s.replace(needle, '\tif (ASUS_SPARSE_PROFILE && !sparse_admit(text, len))\n\t\treturn;\n' + needle)
needle = '\t\tcap_init(h);'
assert s.count(needle) == 1
s = s.replace(needle, '\t\tasus_retained_trace_mark(ASUS_SPARSE_MODE);\n' + needle)
source[n] = s
patch = []
outpins = {}
for n in names:
    old = (B / 'source' / n).read_bytes()
    target = R / 'source' / n
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source[n])
    outpins[n] = dict(before=sha(old), after=sha(target.read_bytes()))
    patch += difflib.unified_diff(old.decode().splitlines(True), source[n].splitlines(True),
                                 fromfile='base/' + n, tofile='candidate/' + n)
(R / 'source/changes.patch').write_text(''.join(patch))
(R / 'source/sparse-filter.inc').write_text(filter_code)
(R / 'evidence/source-pins.json').write_text(json.dumps(outpins, indent=2) + '\n')
identity.write_text(json.dumps(dict(run_uuid=run, mode=mode,
    base_remote='/srv/android/asus-arm64-delay-loop-observation-20261108-f3da846c',
    remote_root='/srv/android/asus-sparse-observer-liveness-20261108-' + run[:8],
    helper_prefix=prefix, helper_event_suffixes=suffixes, helper_alarm_suffix=alarm,
    direct_markers=markers, fresh_entry_same_run_uuid=True,
    state='SOURCE_PREPARED_CLOUD_AUTH_BLOCKED_NOT_BUILT'), indent=2) + '\n')
print(run)
