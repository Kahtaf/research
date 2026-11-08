#!/usr/bin/env python3
"""Bounded Linux-container source probes; never communicate with the tablet."""
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path('/audit')
SOURCE = ROOT / 'sources/asus-original/kernel-3.18'
OUT = ROOT / 'build/asus-original'
LOGS = ROOT / 'evidence/build'
OUT.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)
results = []

def probe(name, command, timeout=90):
    try:
        r = subprocess.run(command, cwd=SOURCE, text=True, errors='replace',
                           capture_output=True, timeout=timeout)
        text = r.stdout + r.stderr
        status = r.returncode
    except subprocess.TimeoutExpired as error:
        text = str(error)
        status = 'timeout'
    (LOGS / (name + '.log')).write_text(text)
    results.append({'name': name, 'command': command, 'exit_code': status})
    (LOGS / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    print(name, status, text[-1800:], flush=True)
    return status

base = ['make', 'O=' + str(OUT), 'ARCH=arm64', 'CROSS_COMPILE=aarch64-linux-gnu-',
        'ROOTDIR=' + str(ROOT / 'sources/asus-original')]
if probe('defconfig', base + ['asus8163_tb_380_m_defconfig']) == 0:
    probe('prepare-gcc13', base + ['-j4', 'prepare'])
else:
    # ASUS's custom target references an absent product diffconfig. Probe the
    # supplied base configuration independently without altering the source.
    shutil.copyfile(SOURCE / 'arch/arm64/configs/asus8163_tb_380_m_defconfig', OUT / '.config')
    if probe('base-olddefconfig', base + ['olddefconfig']) == 0:
        probe('base-prepare-gcc13', base + ['-j4', 'prepare'])

dts = SOURCE / 'arch/arm64/boot/dts/asus8163_tb_380_m-Z380M.dts'
if probe('dts-preprocess', ['aarch64-linux-gnu-cpp', '-nostdinc', '-undef', '-D__DTS__',
          '-x', 'assembler-with-cpp', '-I' + str(SOURCE / 'include'),
          '-I' + str(dts.parent), str(dts), '-o', str(OUT / 'Z380M.dts')]) == 0:
    probe('dtb-compile', ['dtc', '-I', 'dts', '-O', 'dtb', '-o', str(OUT / 'Z380M.dtb'),
                         str(OUT / 'Z380M.dts')])
