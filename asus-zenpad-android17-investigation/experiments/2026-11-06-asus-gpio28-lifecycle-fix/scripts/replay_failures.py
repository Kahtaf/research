from bounded import ROOT,run
for name,expected in [('lifetime-null',-6),('lifetime-routing-pm',-6),('lifetime-stale-suspend',0)]:
 src=ROOT/'baseline/tests'/f'{name}.c';exe=ROOT/'baseline'/name
 run(['/usr/bin/clang','-std=gnu89','-Wno-implicit-function-declaration','-fsanitize=undefined','-fno-sanitize-recover=all',src,'-o',exe],f'evidence/baseline-{name}-compile.txt')
 out=run([exe],f'evidence/baseline-{name}-run.txt',expect=expected).decode()
 if expected:assert 'runtime error: member access within null pointer' in out
 else:assert 'On accepted' in out
 print(name,'preserved expected exit',expected)
