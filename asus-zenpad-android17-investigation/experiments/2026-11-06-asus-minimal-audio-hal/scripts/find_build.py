from pathlib import Path
p=Path('/srv/android/lineage24')
for d in ['out','out/soong','out/soong/.intermediates/hardware/libhardware/modules/audio','out/soong/.intermediates/external/tinyalsa/libtinyalsa','out/target/product']:
 q=p/d;print(d, [x.name for x in q.glob('*')][:60])
for x in (p/'out').glob('*.ninja'):print('NINJA',x)
for x in (p/'out/soong').glob('*.ninja'):print('NINJA',x)
