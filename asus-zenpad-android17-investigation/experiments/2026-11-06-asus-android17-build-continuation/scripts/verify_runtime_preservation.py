#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[1]
kernel=Path('/srv/android/asus-build-continuation/kernel')
config_path=Path(sys.argv[1]);config={}
for line in config_path.read_text().splitlines():
 if line.startswith('CONFIG_') and '=' in line:
  k,v=line.split('=',1);config[k]=v
 if line.startswith('# CONFIG_') and line.endswith(' is not set'):config[line[2:-11]]='n'
baseline=json.loads((root/'evidence/runtime-config-baseline.json').read_text())
configs={k:dict(expected=v['physical'],actual=config.get(k,'n')) for k,v in baseline.items()}
source=json.loads((root/'evidence/runtime-source-baseline.json').read_text())['selected_files']
files={k:dict(expected=v['sha256'],actual=hashlib.sha256((kernel/k).read_bytes()).hexdigest()) for k,v in source.items()}
assert all(v['expected']==v['actual'] for v in configs.values()),[k for k,v in configs.items() if v['expected']!=v['actual']]
assert all(v['expected']==v['actual'] for v in files.values()),[k for k,v in files.items() if v['expected']!=v['actual']]
report=dict(config=str(config_path),configuration=configs,source_files=files,physical_hardware_verified=False)
Path(sys.argv[2]).write_text(json.dumps(report,indent=2)+'\n')
print(len(configs),'runtime prerequisite options and',len(files),'source files preserved')
