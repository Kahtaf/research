#!/usr/bin/env python3
"""Serial, bounded compiler/executor. Outputs stay inside this spike."""
import json
import os
import platform
import resource
import shutil
import subprocess
import sys
from pathlib import Path
from extract import SPIKE, SCENARIOS, dump, main as extract, sha


def limits():
    if sys.platform != 'darwin':
        resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def bounded(command, receipt_name):
    env = dict(os.environ, OMP_NUM_THREADS='1', LLVM_PARALLEL_COMPILE_JOBS='1')
    # Darwin rejects RLIMIT_AS/RSS/DATA with EINVAL in this host. time -l records
    # the actual peak; this tiny serial unit must stay below 1 GiB to pass.
    measured_command = ['/usr/bin/time', '-l', *command] if sys.platform == 'darwin' else command
    result = subprocess.run(measured_command, cwd=SPIKE, env=env, preexec_fn=limits,
                            capture_output=True, text=True, timeout=60)
    import re
    match = re.search(r'(\d+)\s+maximum resident set size', result.stderr)
    peak = int(match[1]) if match else None
    record = {'command': measured_command, 'returncode': result.returncode,
              'stdout': result.stdout, 'stderr': result.stderr,
              'limits': {'memory_budget_bytes': 1024**3, 'peak_rss_bytes': peak,
                         'hard_address_space_limit': sys.platform != 'darwin',
                         'memory_enforcement': 'post-run observed RSS gate on Darwin; no hard RSS cap claimed',
                         'cpu_seconds': 30, 'serial': True,
                         'frontend_threads': 1, 'linker_threads': 1}}
    receipt = SPIKE / 'evidence' / receipt_name
    if receipt.exists():
        previous = json.loads(receipt.read_text())
        if previous['returncode']:
            receipt.rename(receipt.with_name(receipt.stem + '-failure-' + sha(receipt.read_bytes())[:8] + '.json'))
    dump(receipt, record)
    if result.returncode:
        raise RuntimeError(f'{receipt_name}: exit {result.returncode}; see retained receipt')
    if sys.platform == 'darwin':
        assert peak is not None and peak < 1024**3, 'Measured memory budget failed'
    return result.stdout


def generate_main(sensor):
    out = [f'#define HOST_SENSOR_TYPES_PATH "../generated/{sensor}-types.inc"\n',
           '#include "../tests/host-fixtures.h"\n', f'#include "{sensor}-production.inc"\n',
           '#line 1 "host-main-fixture"\nint main(void) {\nunsigned result;\n']
    def case(label, fps, code):
        out.append(f'begin_case("{label}", {fps});\n{code}\nfinish_case(result);\n')
    n = 6 if sensor == 'ov5670' else 5
    for scenario in SCENARIOS[:n]:
        fps = 150 if scenario == 'CAMERA_CAPTURE_JPEG' and sensor == 'ov5670' else 300
        case(f'control/{scenario}/{fps}', fps, f'result = control(MSDK_SCENARIO_ID_{scenario}, NULL, NULL);')
    # Every real capture predicate side, declared cap/cap1, and representative fallbacks.
    for fps in [0, 149, 150, 151, 239, 240, 241, 300, 65535]:
        case(f'capture/{fps}', fps, 'result = control(MSDK_SCENARIO_ID_CAMERA_CAPTURE_JPEG, NULL, NULL);')
    for fps in [0, 150, 240, 65535]:
        case(f'video/{fps}', fps, 'result = control(MSDK_SCENARIO_ID_VIDEO_PREVIEW, NULL, NULL);')
    case('invalid-scenario', 300, 'result = control((MSDK_SCENARIO_ID_ENUM)999, NULL, NULL);')
    for first, second in [('CAMERA_PREVIEW', 'HIGH_SPEED_VIDEO'), ('HIGH_SPEED_VIDEO', 'CAMERA_PREVIEW')]:
        case(f'sequence/{first}/{second}', 300,
             f'control(MSDK_SCENARIO_ID_{first}, NULL, NULL); stage_boundary = write_count;\n'
             f'result = control(MSDK_SCENARIO_ID_{second}, NULL, NULL);')
    for fps in [150, 240, 300]:
        case(f'capture-then-scenario-rate/{fps}', fps,
             'control(MSDK_SCENARIO_ID_CAMERA_CAPTURE_JPEG, NULL, NULL); stage_boundary = write_count;\n'
             f'result = set_max_framerate_by_scenario(MSDK_SCENARIO_ID_CAMERA_CAPTURE_JPEG, {fps});')
        case(f'capture-then-video-rate/{fps}', fps,
             'control(MSDK_SCENARIO_ID_CAMERA_CAPTURE_JPEG, NULL, NULL); stage_boundary = write_count;\n'
             f'result = set_video_mode({fps});')
    for scenario in SCENARIOS[:n]:
        case(f'scenario-rate/{scenario}/240', 300,
             f'control(MSDK_SCENARIO_ID_{scenario}, NULL, NULL); stage_boundary = write_count;\n'
             f'result = set_max_framerate_by_scenario(MSDK_SCENARIO_ID_{scenario}, 240);')
        # Sentinel distinguishes missing default-frame-rate branches (not a real default).
        case(f'default-rate/{scenario}', 300,
             f'result = get_default_framerate_by_scenario(MSDK_SCENARIO_ID_{scenario}, &query_result);')
    for fps in [0, 150, 300, 240]:
        case(f'flicker-video-rate/{fps}', 300,
             'control(MSDK_SCENARIO_ID_CAMERA_PREVIEW, NULL, NULL); imgsensor.autoflicker_en = KAL_TRUE; stage_boundary = write_count;\n'
             f'result = set_video_mode({fps});')
    case('video-scenario-rate-zero', 300,
         'control(MSDK_SCENARIO_ID_VIDEO_PREVIEW, NULL, NULL); stage_boundary = write_count;\n'
         'result = set_max_framerate_by_scenario(MSDK_SCENARIO_ID_VIDEO_PREVIEW, 0);')
    # Direct set_max_framerate clamp branches; positive frame rate avoids known division precondition.
    for fps, minimum_en in [(1, 0), (1, 1), (65535, 0)]:
        case(f'direct-rate/{fps}/{minimum_en}', 300,
             'control(MSDK_SCENARIO_ID_CAMERA_PREVIEW, NULL, NULL); stage_boundary = write_count;\n'
             f'set_max_framerate({fps}, {minimum_en}); result = 0;')
    out.append('return 0;\n}\n')
    path = SPIKE / 'generated' / f'{sensor}-host.c'
    path.write_text(''.join(out))
    return path


def main():
    extract()
    compiler = shutil.which('clang')
    assert compiler, 'Local clang required; no download is attempted'
    dump(SPIKE / 'evidence/toolchain.json', {'platform': platform.platform(),
         'compiler': compiler, 'version': subprocess.check_output([compiler, '--version'], text=True),
         'sanitizers': 'undefined (no recovery)', 'asan': 'not used: shadow reservation conflicts with 1 GiB address-space bound'})
    for sensor in ['ov5670', 'ov2680']:
        path = generate_main(sensor)
        obj = SPIKE / 'generated' / f'{sensor}-host.o'
        exe = SPIKE / 'generated' / f'{sensor}-host'
        flags = ['-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter',
                 '-fsanitize=undefined', '-fno-sanitize-recover=all', '-fno-lto']
        bounded([compiler, *flags, '-c', str(path), '-o', str(obj)], f'{sensor}-compile.json')
        # Apple's classic linker is serial; modern ld has concurrent passes and
        # does not accept an explicit thread count on this installed version.
        link_threads = ['-Wl,-ld_classic'] if sys.platform == 'darwin' else ['-fuse-ld=lld', '-Wl,--threads=1']
        bounded([compiler, '-fsanitize=undefined', *link_threads, str(obj), '-o', str(exe)], f'{sensor}-link.json')
        stdout = bounded([str(exe)], f'{sensor}-run.json')
        traces = [json.loads(line) for line in stdout.splitlines()]
        dump(SPIKE / 'evidence' / f'{sensor}-traces.json', traces)
        undefined = subprocess.check_output(['nm', '-u', str(exe)], text=True)
        imports = [line.strip().split()[-1] for line in undefined.splitlines() if line.strip()]
        allowed_imports = {'_abort', '_printf', '_puts', '_memset',
            '___ubsan_handle_divrem_overflow_abort', '___ubsan_handle_out_of_bounds_abort',
            '___ubsan_handle_pointer_overflow_abort', '___ubsan_handle_type_mismatch_v1_abort',
            '___ubsan_handle_add_overflow_abort', '___ubsan_handle_shift_out_of_bounds_abort'}
        if sys.platform == 'darwin':
            assert set(imports) <= allowed_imports, f'Unexpected host binary imports: {set(imports)-allowed_imports}'
        dump(SPIKE / 'evidence' / f'{sensor}-binary-audit.json', {'sha256': sha(exe.read_bytes()),
             'undefined_imports': imports, 'allowed_imports': sorted(allowed_imports),
             'dynamic_libraries': subprocess.check_output(['otool', '-L', str(exe)], text=True) if sys.platform == 'darwin' else None,
             'boundary': 'Programmed functions call only reviewed whitelist/fixtures; loader and stdout belong to the host runtime. No sensor transport, file-opening, socket, or vendor library import.'})
        print(f'{sensor}: {len(traces)} bounded production-body cases; compiler/runtime diagnostics retained.')
    # Independent analysis and behavioral tests run only after both production witnesses succeed.
    subprocess.run([sys.executable, 'scripts/facts.py'], cwd=SPIKE, check=True)
    test = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=SPIKE, capture_output=True, text=True)
    dump(SPIKE / 'evidence/tests.json', {'returncode': test.returncode, 'stdout': test.stdout, 'stderr': test.stderr})
    print(test.stderr)
    assert test.returncode == 0
    # Verify original pins again after all execution.
    from extract import validate_pins
    validate_pins()
    dump(SPIKE / 'evidence/artifact-pins.json', {
        str(p.relative_to(SPIKE)): sha(p.read_bytes()) for folder in ['scripts', 'tests', 'inputs', 'generated']
        for p in sorted((SPIKE / folder).rglob('*')) if p.is_file() and '__pycache__' not in p.parts})


if __name__ == '__main__':
    main()
