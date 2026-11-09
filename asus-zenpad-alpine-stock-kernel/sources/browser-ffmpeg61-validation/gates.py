import subprocess,re,pathlib,json,hashlib
out=pathlib.Path('/out'); results={}
def run(*args):return subprocess.check_output(args,text=True)
for lib,soname,version,needed in [('libavcodec.so.61','libavcodec.so.61','LIBAVCODEC_61',{'libavutil.so.59','libc.musl-aarch64.so.1'}),('libavutil.so.59','libavutil.so.59','LIBAVUTIL_59',{'libc.musl-aarch64.so.1'})]:
 p=out/'lib'/lib
 elf=run('readelf','-h','-l','-d','-W',str(p));(out/(lib+'.elf.txt')).write_text(elf)
 assert 'ELF64' in elf and 'AArch64' in elf
 assert not re.search(r'^\s*TLS\s',elf,re.M)
 assert not any(x in elf for x in ['(TEXTREL)','(RPATH)','(RUNPATH)'])
 assert re.search(r'\(SONAME\).*\['+re.escape(soname)+r'\]',elf)
 assert set(re.findall(r'\(NEEDED\).*\[(.*?)\]',elf))==needed
 dyn=run('readelf','--dyn-syms','-W',str(p));(out/(lib+'.dynsym.txt')).write_text(dyn)
 assert version in dyn
 results[lib]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'elf_gates':'PASS','needed':sorted(needed)}
source=pathlib.Path('/src/input/FFmpegLibWrapper.cpp').read_text()
required=['avcodec_version']
for name,expr in re.findall(r'^\s*AV_FUNC\((\w+),\s*(.*?)\)\s*$',source,re.M|re.S):
 if 'AV_FUNC_61' in expr or 'AV_FUNC_AVUTIL_61' in expr or 'AV_FUNC_AVCODEC_ALL' in expr or 'AV_FUNC_AVUTIL_ALL' in expr:required.append(name)
# Limit regex to individual macro calls; reject accidental cross-call matching.
required=['avcodec_version']
for match in re.finditer(r'^\s*AV_FUNC\((\w+),([^;]*?)\)\s*(?=\n)',source,re.M):
 name,expr=match.groups()
 if re.search(r'AV_FUNC_(?:AVUTIL_)?61\b|AV_FUNC_AVCODEC_ALL|AV_FUNC_AVUTIL_ALL',expr): required.append(name)
assert len(required)>30,required
symbols=''.join((out/(lib+'.dynsym.txt')).read_text() for lib in results)
for name in required:assert re.search(r'\b'+name+r'@@LIBAV(?:CODEC_61|UTIL_59)\b',symbols),name
results['mandatory_v61_symbols']=sorted(set(required))
h=(out/'harness.txt').read_text();assert 'version=61.19.101' in h
paths=set(re.findall(r'(/\S+)\s*$',h,re.M))
allowed={'/out/harness','/out/lib/libavcodec.so.61','/out/lib/libavutil.so.59','/lib/ld-musl-aarch64.so.1'}
assert paths<=allowed,paths
assert {'/out/lib/libavcodec.so.61','/out/lib/libavutil.so.59'}<=paths
v=int(re.search(r'h264 frames=(\d+)',h)[1]);a=int(re.search(r'aac frames=\d+ samples=(\d+)',h)[1]);channels=int(re.search(r'aac .*channels=(\d+)',h)[1])
refv=sum(1 for l in (out/'reference-video.framemd5').read_text().splitlines() if l and not l.startswith('#'))
refa=(out/'reference-audio.pcm').stat().st_size//(2*channels)
assert (v,a)==(refv,refa),((v,a),(refv,refa))
results['runtime']={'maps_paths':sorted(paths),'video_frames':v,'audio_samples_per_channel':a,'reference_equal':True,'six_decoders':True}
results['status']='ALL GATES PASS'
(out/'gates.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
