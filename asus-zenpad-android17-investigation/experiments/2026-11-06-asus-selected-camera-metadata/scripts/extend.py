from pathlib import Path
p=Path(__file__).with_name('collect.py');s=p.read_text();s=s.replace("['libcam.metadataprovider.so','libcam.halsensor.so','libcam.hal3a.v3.so','libcameracustom.so']","['libcam.hal3a.v3.dng.so']").replace("elf-pins.json","dng-pins.json");exec(compile(s,str(p),'exec'))
