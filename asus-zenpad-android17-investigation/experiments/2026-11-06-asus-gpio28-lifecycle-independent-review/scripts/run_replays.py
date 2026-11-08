from bounded import ROOT,run
run(['python3',ROOT/'scripts/prepare_tests.py'],'prepare-tests.log')
flags=['/usr/bin/clang','-std=gnu89','-O0','-g','-fsanitize=undefined','-fno-sanitize-recover=all']
for name,expected in [('lifetime-null',-6),('lifetime-routing-pm',-6),('lifetime-stale-suspend',0)]:
    exe=ROOT/'work'/name
    run(flags+['-Wno-implicit-function-declaration',ROOT/'work/old/tests'/f'{name}.c','-o',exe],name+'-compile.log')
    text=run([exe],name+'-run.log',expected)
    assert ('runtime error: member access within null pointer' if expected else 'On accepted') in text
run(flags+['-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-Wno-declaration-after-statement','-pthread',ROOT/'tests/contract.c','-o',ROOT/'work/inherited-lifecycle'],'inherited-compile.log')
text=run([ROOT/'work/inherited-lifecycle'],'inherited-run.log')
assert 'PASS 38 cases' in text and 'PASS lifecycle regressions: 12 scenarios' in text
