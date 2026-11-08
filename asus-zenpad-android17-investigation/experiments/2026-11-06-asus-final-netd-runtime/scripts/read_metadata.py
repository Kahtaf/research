from pathlib import Path
O=Path('/srv/android/asus-final-netd-runtime-20261106/run-r3-metadata-crud')
print((O/'result.json').read_text() if (O/'result.json').exists() else 'OWN RUN IN PROGRESS')
print('\n'.join(x for x in (O/'serial.log').read_text(errors='replace').splitlines() if any(k in x for k in ['MAP_INFO','MAP_CRUD','OBJECT_RESULT','EXEC_RESULT','Fatal','funcs'])))
