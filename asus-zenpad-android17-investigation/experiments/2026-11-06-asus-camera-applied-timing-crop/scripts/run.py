"""Serial bounded host compilation, recording, assertions and provenance."""
import json
import os
import platform
import re
import resource
import shutil
import subprocess
import sys
from extract import SPIKE, ROOT, PARENT, main as extract, validate, sha, dump


def limits():
    if sys.platform!='darwin':resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
    resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))


def bounded(command,name):
    command=['/usr/bin/time','-l',*command] if sys.platform=='darwin' else command
    env=dict(os.environ,OMP_NUM_THREADS='1',LLVM_PARALLEL_COMPILE_JOBS='1',PYTHONDONTWRITEBYTECODE='1',WITNESS_BOUNDED='1')
    try:
        p=subprocess.run(command,cwd=SPIKE,env=env,preexec_fn=limits,capture_output=True,text=True,timeout=60)
        peak=re.search(r'(\d+)\s+maximum resident set size',p.stderr)
        result={'command':command,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,
                'peak_rss_bytes':int(peak[1]) if peak else None,'memory_budget_bytes':1024**3,
                'hard_address_space_limit':sys.platform!='darwin','serial':True,'cpu_seconds':30}
    except subprocess.TimeoutExpired as e:
        result={'command':command,'returncode':'timeout','stdout':str(e.stdout),'stderr':str(e.stderr)}
    target=SPIKE/'evidence'/name
    if target.exists() and json.loads(target.read_text())['returncode']!=0:
        target.rename(target.with_name(target.stem+'-failed-'+sha(target.read_bytes())[:10]+'.json'))
    dump(target,result)
    assert result['returncode']==0,f'Failed evidence preserved: {name}'
    if sys.platform=='darwin':assert result['peak_rss_bytes'] is not None and result['peak_rss_bytes']<=1024**3
    return result['stdout']


def cases(sensor):
    out=[]
    for fps in [300,240,150]:
        for shutter in [0,1,2,3,4,100,1289,1290,2041,2042,2043,65535,65536,65537,(1<<64)-1]:
            out.append({'label':f'rate-{fps}-shutter-{shutter}','seed':'capture/'+str(fps),'rate':fps,'shutter':shutter})
    for rate in [1,2,65535,(1<<32)+240,(1<<32)-1]:
        out.append({'label':f'width-rate-{rate}','seed':'capture/240','rate':rate,'shutter':65535})
    for fps in [146,147,150,151,296,297,305,306]:
        out.append({'label':f'flicker-boundary-{fps}','seed':'capture/300','flicker':True,'synthetic_state':{'pclk':fps*1000,'line_length':10,'frame_length':1000,'min_frame_length':1000},'shutter':100})
    for mode in ['CAMERA_PREVIEW','HIGH_SPEED_VIDEO']:
        for shutter in [100,4090]:
            out.append({'label':f'{mode}-flicker-{shutter}','seed':f'control/{mode}/300','flicker':True,'shutter':shutter})
    out.append({'label':'set-framerate-is-state-only','seed':'capture/300','set_fps':65536+240,'shutter':100})
    out.append({'label':'legacy-video-then-shutter','seed':'capture/240','video_rate':240,'shutter':100})
    out.append({'label':'scenario-then-legacy-clamp','seed':'capture/240','rate':1,'video_rate':240,'shutter':100})
    out.append({'label':'synthetic-margin-underflow','seed':'capture/300','synthetic_state':{'pclk':1,'line_length':1,'frame_length':2,'min_frame_length':2},'shutter':0})
    out.append({'label':'synthetic-u32-wrap','seed':'capture/300','synthetic_state':{'pclk':4294967295,'line_length':1,'frame_length':1000,'min_frame_length':1000},'video_rate':1,'flicker':True,'shutter':100})
    return out


def generate(sensor):
    inherited=json.loads((PARENT/'evidence'/f'{sensor}-traces.json').read_text());lookup={x['case']:x for x in inherited}
    specs=cases(sensor)
    code=[f'#define HOST_SENSOR_TYPES_PATH "../generated/{sensor}-types.inc"\n#include "../tests/host.h"\n#include "{sensor}-production.inc"\n#line 1 "synthetic-host-main"\nint main(void) {{\n',
          'uint16_t endian=1; if(*(uint8_t *)&endian!=1) abort();\n']
    for spec in specs:
        seed=lookup[spec['seed']];spec['inherited_seed']=seed
        code.append('memset(&imgsensor,0,sizeof(imgsensor)); write_count=0; period_query[0]=period_query[1]=0;\n')
        code.append('case_label='+json.dumps(spec['label'])+';\n')
        for k,v in seed['state'].items():code.append(f'imgsensor.{k}={v}u;\n')
        for k,v in spec.get('synthetic_state',{}).items():code.append(f'imgsensor.{k}={v}u;\n')
        code.append(f'imgsensor.autoflicker_en={int(spec.get("flicker",False))}; snapshot("seed");\n')
        if 'rate' in spec:
            code.append(f'host_feature(SENSOR_FEATURE_SET_MAX_FRAME_RATE_BY_SCENARIO,MSDK_SCENARIO_ID_CAMERA_CAPTURE_JPEG,{spec["rate"]}ull); snapshot("scenario-rate");\n')
        if 'set_fps' in spec:
            code.append(f'host_feature(SENSOR_FEATURE_SET_FRAMERATE,{spec["set_fps"]}ull,0); snapshot("set-framerate");\n')
        if 'video_rate' in spec:
            code.append(f'host_feature(SENSOR_FEATURE_SET_VIDEO_MODE,{spec["video_rate"]}ull,0); snapshot("video-rate");\n')
        code.append('host_feature(SENSOR_FEATURE_GET_PERIOD,0,0); snapshot("period-before");\n')
        code.append(f'host_feature(SENSOR_FEATURE_SET_ESHUTTER,{spec["shutter"]}ull,0); snapshot("exposure");\n')
        code.append('host_feature(SENSOR_FEATURE_GET_PERIOD,0,0); snapshot("period-after");\n')
    code.append('SENSOR_WINSIZE_INFO_STRUCT win;\n')
    for i,scenario in enumerate(['CAMERA_PREVIEW','CAMERA_CAPTURE_JPEG','VIDEO_PREVIEW','HIGH_SPEED_VIDEO','SLIM_VIDEO','CUSTOM1','INVALID']):
        n='999' if scenario=='INVALID' else 'MSDK_SCENARIO_ID_'+scenario
        code.append(f'host_crop({n},&win);host_grab((MSDK_SCENARIO_ID_ENUM){n});\n')
        code.append(f'printf("{{\\\"crop\\\":\\\"{scenario}\\\",\\\"grab\\\":[%u,%u],\\\"winsize\\\":[",grab[0],grab[1]);\n'.replace('\\\"','\\"'))
        code.append('uint16_t values'+str(i)+'[16]; memcpy(values'+str(i)+',&win,sizeof(win));\n')
        code.append(f'for(unsigned j=0;j<16;j++)printf("%s%u",j?",":"",(unsigned)values{i}[j]); puts("]}}");\n')
    code.append('return 0; }\n')
    p=SPIKE/'generated'/f'{sensor}-host.c';p.write_text(''.join(code));dump(SPIKE/'evidence'/f'{sensor}-cases.json',specs)
    return p


def main():
    extraction=extract();compiler=shutil.which('clang');assert compiler
    dump(SPIKE/'evidence/toolchain.json',{'compiler':compiler,'version':subprocess.check_output([compiler,'--version'],text=True),'platform':platform.platform(),
         'arithmetic':'32-bit unsigned/int, uint16 narrowing; little-endian feature fixture; -fno-strict-aliasing; no numeric enum or target layout ABI claim',
         'sanitizer':'UBSan no recovery, unsigned wrap/narrowing are C-defined and independently checked'})
    for sensor in ['ov5670','ov2680']:
        source=generate(sensor);obj=source.with_suffix('.o');exe=source.with_suffix('')
        bounded([compiler,'-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-fno-strict-aliasing','-fno-lto','-fsanitize=undefined','-fno-sanitize-recover=all','-c',str(source),'-o',str(obj)],f'{sensor}-compile.json')
        link=['-Wl,-ld_classic'] if sys.platform=='darwin' else ['-fuse-ld=lld','-Wl,--threads=1']
        bounded([compiler,'-fsanitize=undefined',*link,str(obj),'-o',str(exe)],f'{sensor}-link.json')
        output=bounded([str(exe)],f'{sensor}-run.json')
        traces=[json.loads(x) for x in output.splitlines()];dump(SPIKE/'evidence'/f'{sensor}-traces.json',traces)
        imports=subprocess.check_output(['nm','-u',str(exe)],text=True)
        allowed={'_abort','_printf','_puts','_memset','_memcpy','___stack_chk_guard','___stack_chk_fail','___ubsan_handle_out_of_bounds_abort','___ubsan_handle_pointer_overflow_abort',
          '___ubsan_handle_type_mismatch_v1_abort','___ubsan_handle_divrem_overflow_abort','___ubsan_handle_shift_out_of_bounds_abort','___ubsan_handle_add_overflow_abort'}
        symbols={x.strip().split()[-1] for x in imports.splitlines() if x.strip()}
        if sys.platform=='darwin':assert symbols<=allowed,symbols-allowed
        dump(SPIKE/'evidence'/f'{sensor}-binary-audit.json',{'sha256':sha(exe.read_bytes()),'imports':sorted(symbols),'allowed_imports':sorted(allowed),
          'libraries':subprocess.check_output(['otool','-L',str(exe)],text=True) if sys.platform=='darwin' else None})
    from verify import main as verify
    verify(extraction)
    from trace_sources import main as trace_sources
    trace_sources()
    from report import main as report
    report()
    validate()
    dump(SPIKE/'evidence/artifact-pins.json',{str(p.relative_to(SPIKE)):sha(p.read_bytes()) for folder in ['scripts','tests','inputs','generated'] for p in sorted((SPIKE/folder).rglob('*')) if p.is_file() and '__pycache__' not in p.parts})
    print('Both sensors: applied timing and crop fragment verification passed; source-only, no camera activation.')

if __name__=='__main__':
    try:
        if os.environ.get('WITNESS_BOUNDED')=='1':main()
        else:print(bounded([sys.executable,str(SPIKE/'scripts/run.py')],'full-run.json'),end='')
    except Exception as error:
        import traceback
        message=traceback.format_exc();failure=SPIKE/'evidence'/('failure-'+sha(message.encode())[:12]+'.json')
        dump(failure,{'error':str(error),'traceback':message});raise
