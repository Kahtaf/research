#!/usr/bin/env python3
import io,pathlib,subprocess,tarfile,sys
from remote import SSH
r=pathlib.Path(__file__).resolve().parents[1]
b=io.BytesIO()
with tarfile.open(fileobj=b,mode='w',format=tarfile.GNU_FORMAT) as t:
 for p in sorted((r/'stagedpatches/kernel-input').rglob('*')):
  if p.is_file(): t.add(p,arcname=p.relative_to(r/'stagedpatches/kernel-input'),recursive=False)
subprocess.run(SSH+['tar -x -C /srv/android/asus-radio-kernel-port/kernel'],input=b.getvalue(),check=True)
rev=sys.argv[1]; assert rev.isalnum()
cmd=f'cd /srv/android/asus-radio-kernel-port/kernel && make -j2 O=../build ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- drivers/misc/mediatek/connectivity/ > ../logs/radio-{rev}.log 2>&1; result=$?; echo $result > ../logs/radio-{rev}.exit; grep "error:" ../logs/radio-{rev}.log | sort -u; tail -5 ../logs/radio-{rev}.log; exit $result'
sys.exit(subprocess.call(SSH+[cmd]))
