"""Optional full reproduction. Writes only this spike, always sequential."""
from bounded import ROOT,run
run(['python3',ROOT/'scripts/audit.py'],'source-audit-final.log')
# This script bounds and reaps each child separately.
from run_replays import *
flags=['/usr/bin/clang','-std=gnu89','-O0','-g','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-Wno-declaration-after-statement','-fsanitize=undefined','-fno-sanitize-recover=all','-pthread']
for name in ('adversarial','controls'):
    run(['python3',ROOT/'scripts'/('prepare_'+name+'.py')],name+'-reproduce-prepare.log')
    extra=['-Wno-unused-but-set-variable'] if name=='controls' else []
    run(flags+extra+[ROOT/'tests'/(name+'-contract.c'),'-o',ROOT/'work'/name],name+'-reproduce-compile.log')
    run([ROOT/'work'/name],name+'-reproduce-run.log')
# Runs finite bounded patch/preprocessor/MTK children and rehashes original inputs.
import scope_verify
