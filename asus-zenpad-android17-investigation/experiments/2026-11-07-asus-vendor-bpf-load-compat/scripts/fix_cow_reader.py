from pathlib import Path
import json,subprocess as s
R=Path('/srv/android/asus-vendor-bpf-load-compat-20261107');p=R/'source/cow.py';old=p.read_text();(R/'source/cow-before-extent1.py').write_text(old)
start=old.index('def extentblocks(ib):');stop=old.index('def contents(n):',start)
new='''def extentblocks(ib):
 assert u32(ib,32)&0x80000
 def walk(ex,depth):
  assert u16(ex,0)==0xf30a and u16(ex,6)==depth and depth<=1
  assert 12+12*u16(ex,2)<=len(ex)
  out=[]
  for i in range(u16(ex,2)):
   if depth:
    logical,lo,hi,unused=struct.unpack_from('<IIHH',ex,12+12*i)
    out.extend(walk(C.read(((hi<<32)|lo)*bs,bs),depth-1))
   else:
    logical,count,hi,lo=struct.unpack_from('<IHHI',ex,12+12*i);assert 0<count<0x8000
    out.extend((logical+k,((hi<<32)|lo)+k) for k in range(count))
  return out
 return sorted(walk(ib[40:100],u16(ib,46)))
'''
p.write_text(old[:start]+new+old[stop:]);(R/'evidence/startup-pipeline-initial-result.json').write_bytes((R/'evidence/startup-pipeline-result.json').read_bytes())
# Continue from verification only: no new patch helper, fresh data or Android invocation.
cmd=['python3','-B',str(R/'scripts/verify_cow.py')];x=s.run(cmd,capture_output=True,text=True);(R/'evidence/cow-verifier-resume.txt').write_text(x.stdout+x.stderr);print(x.stdout+x.stderr);assert x.returncode==0
assert not (R/'evidence/actual-os-once.json').exists()
f=(R/'evidence/runtime-resume.log').open('xb')
script='from pathlib import Path\nimport subprocess as s,json,datetime\nR=Path("'+str(R)+'")\nstatus={"actual_os_boots":1,"candidate_runtime":True}\ntry:\n for stage,args in [("execute",["runtime"]),("extract",[])]:\n  p=s.run(["python3","-B",str(R/"scripts"/(stage+".py"))]+args,stdin=s.DEVNULL);assert p.returncode==0\n status["completed"]=True\nfinally:\n status["finished_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat();(R/"evidence/runtime-resume-result.json").write_text(json.dumps(status,indent=2))\n'
(R/'scripts/runtime_resume.py').write_text(script);p=s.Popen(['python3','-B',str(R/'scripts/runtime_resume.py')],stdin=s.DEVNULL,stdout=f,stderr=s.STDOUT,start_new_session=True);print('owned_resume_pid',p.pid)
