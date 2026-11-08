from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'inputs/tests/contract.c').read_text().replace('int main(void){','static int original_main(void){')
crash=s+'''
int main(void){
 CHECK(original_main()==0);
 reset();CHECK(core_probe()==0);detach();
 CHECK(!mCodec_data&&!mInitCodec);
 fprintf(stderr,"REPRO: completed codec detach; independent routing PM invokes SetAnalogSuspend(true)\\n");
 SetAnalogSuspend(true);
 fprintf(stderr,"UNEXPECTED: suspend after codec detach survived\\n");return 2;
}
'''
stale=s+'''
int main(void){
 CHECK(original_main()==0);
 reset();CHECK(core_probe()==0);SetAnalogSuspend(true);
 CHECK(mAnaSuspend&&p00a_gate_suspended);detach();
 CHECK(core_probe()==0);CHECK(mAnaSuspend&&!p00a_gate_suspended);
 SetAnalogSuspend(true);CHECK(mAnaSuspend&&!p00a_gate_suspended);
 CHECK(set(1)==1&&get()==1);
 fprintf(stderr,"REPRO: suspend->detach->full reprobe->suspend(true) leaves stale mAnaSuspend=true, gate_suspended=false; On accepted\\n");
 detach();return 0;
}
'''
(R/'inputs/tests/lifetime-null.c').write_text(crash)
(R/'inputs/tests/lifetime-stale-suspend.c').write_text(stale)
print('Generated sequential PM-after-detach null repro and stale-suspend repro')
