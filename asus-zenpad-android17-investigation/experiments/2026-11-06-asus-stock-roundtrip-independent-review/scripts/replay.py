from pathlib import Path
import sys, importlib.util, unittest, json, datetime, hashlib
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[1]
W = R.parent
C = W/'2026-11-06-asus-stock-roundtrip-continuation'
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
mode = sys.argv[1]
if mode == 'faults':
    m = load('review_fault_tests', C/'tests/service/test_faults.py')
    m.S = R
    (R/'tests').mkdir(exist_ok=True)
    with (R/'evidence/fault-replay.txt').open('w') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(m))
    payload = dict(status='PASS' if result.wasSuccessful() else 'FAIL', tests=result.testsRun,
                   errors=len(result.errors), failures=len(result.failures), scenarios=m.RESULTS,
                   loss_points=m.LOSS_POINTS, device_contacted=False)
    assert result.wasSuccessful()
elif mode == 'firmware':
    m = load('review_firmware_tests', C/'tests/service/test_firmware.py')
    cases = [m.adbd(),m.adbd(connect_failure=True),m.adbd(send_short=True),m.adbd(target='sideload'),
             m.init_property(),m.init_reboot(),m.init_reboot(sysrq_denied=True)]
    assert cases[0].stop == 'adbd_waits_for_reboot_after_property_send'
    assert cases[1].stop == cases[2].stop == 'returned'
    payload = dict(status='PASS', cases=[r.summary() for r in cases], device_contacted=False,
                   limits='Saved exact ELF instructions; named libc/OS/property/shutdown stubs. No Linux or PMIC execution.')
else:
    raise ValueError(mode)
payload['utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
(R/('evidence/'+mode+'-replay.json')).write_text(json.dumps(payload, indent=2)+'\n')
print(json.dumps({k:v for k,v in payload.items() if k not in ('scenarios','cases','loss_points')}))
