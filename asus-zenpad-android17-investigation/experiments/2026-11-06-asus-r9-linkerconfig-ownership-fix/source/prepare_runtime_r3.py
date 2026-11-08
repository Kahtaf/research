from pathlib import Path
import os
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');os.environ['TMPDIR']=str(R/'tmp');src=(R/'source/prepare_runtime_r2_resumed.py').read_text().replace('runtime-r2','runtime-r3').replace('runtime_patcher_r2.c','runtime_patcher_r2.c');needle="(I/'init.rc').write_text(core.replace(needle,needle+line));";replacement="""adapted=core.replace(needle,needle+line)
pos=adapted.index('    wait_for_prop keystore.module_hash.sent true\\n')
at=adapted.index('    perform_apex_config\\n',pos)
adapted=adapted[:at]+line+adapted[at:]
assert adapted.count(line)==2
(I/'init.rc').write_text(adapted);""";assert needle in src;src=src.replace(needle,replacement).replace('for(int i=0;i<18;i++)','for(int i=0;i<36;i++)');(R/'source/prepare_runtime_r3_actual.py').write_text(src);exec(compile(src,str(R/'source/prepare_runtime_r3_actual.py'),'exec'))
d=__import__('json').loads((R/'evidence/runtime-r2-adaptations.json').read_text());d['core_init_added_lines']=[d.pop('core_init_added_line')]*2;d['second_bind_location']='after original keystore.module_hash.sent wait, before original post-data perform_apex_config';d['wall_seconds']=180;d['extension_reason']='r2 genuine post-data APEX activation took 72.221s, leaving under 1s after the original module-hash wait before 90s bound; fresh r3 verifies final namespace generation without readiness changes';(R/'evidence/runtime-r3-adaptations.json').write_text(__import__('json').dumps(d,indent=2))
s=(R/'source/execute_runtime_r2.py').read_text().replace('runtime-r2','runtime-r3').replace("+'-r2'","+'-r3'").replace('run-patch-r2','run-patch-r3').replace('runtime-r2-cow-verification','runtime-r3-cow-verification').replace("seconds=45 if phase=='patch' else 90","seconds=45 if phase=='patch' else 180");(R/'source/execute_runtime_r3.py').write_text(s)
