from pathlib import Path
import base64,hashlib,json,struct,subprocess,re,zlib
R=Path('/srv/android/asus-linux49-retained-clock-capture-20261107-fef31ed4');B=Path('/srv/android/asus-linux49-calibrated-entry-build-20261107');K=R/'kernel';O=R/'out';E=R/'evidence'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((E/'build-status.json').read_text())['status']=='complete'
assert not (E/'linked-capture.json').exists(),'One scoped ELF/source/config verification'
pins=json.loads((E/'source-pins.json').read_text())
for n,v in pins.items():assert sha(K/n)==v['after'] and sha(B/'kernel'/n)==v['before']
assert (O/'.config').read_bytes()==(B/'out/.config').read_bytes()
assert (O/'source').resolve()==K
# Old output and old entry/exclusion/DT sources are read-only and selected here only.
selected=['arch/arm64/kernel/head.S','arch/arm64/kernel/asus_entry_text.S','arch/arm64/boot/dts/asus/asus-p00a.dts']
preserved={}
for n in selected:
 if (B/'kernel'/n).is_file():
  assert (K/n).read_bytes()==(B/'kernel'/n).read_bytes();preserved[n]=sha(K/n)
assert sha(B/'out/arch/arm64/boot/Image.gz-dtb')=='97b7e1199d607f852bf52ff7766e8aa079fee92986cd3d473b765a45adbf45fb'
nm=subprocess.check_output(['aarch64-linux-gnu-nm','-an',str(O/'vmlinux')],text=True)
symbols={p[2]:int(p[0],16) for l in nm.splitlines() if len(p:=l.split())==3}
size_nm=subprocess.check_output(['aarch64-linux-gnu-nm','-S','--defined-only',str(O/'vmlinux')],text=True)
sized={p[3]:(int(p[0],16),int(p[1],16)) for l in size_nm.splitlines() if len(p:=l.split())==4}
want=['ktime_get_ts64','arch_counter_read','asus_capture_mono_enter','asus_capture_mono_seq','asus_capture_counter_enter','asus_capture_event_enter','asus_capture_exit','cap_publish','cap_init']
want += [n for n in sized if n.startswith('arch_timer_handler_')]
# __init may inline cap_init; use its retained init parent in that case.
want += ['asus_retained_trace_init','trace_init','asus_entry_text_begin','asus_entry_text_end']
dis={}
for n in want:
 if n not in sized:continue
 addr,size=sized[n]
 if not size:continue
 dis[n]=subprocess.check_output(['aarch64-linux-gnu-objdump','-d','--start-address='+hex(addr),'--stop-address='+hex(addr+size),str(O/'vmlinux')],text=True)
(E/'capture-hooks.disasm').write_text('\n'.join(dis.values()))
assert '<asus_capture_mono_enter>' in dis['ktime_get_ts64'] and '<asus_capture_mono_seq>' in dis['ktime_get_ts64'] and '<asus_capture_exit>' in dis['ktime_get_ts64']
assert '<asus_capture_counter_enter>' in dis['arch_counter_read'] and '<asus_capture_exit>' in dis['arch_counter_read'] and len(re.findall(r'\bblr\b',dis['arch_counter_read']))==1
handlers={n:d for n,d in dis.items() if n.startswith('arch_timer_handler_')}
assert handlers and all('<asus_capture_event_enter>' in d and '<asus_capture_exit>' in d and len(re.findall(r'\bblr\b',d))==1 for d in handlers.values())
# Recorder's actual functions have no clock, printk, allocation or scheduling call.
rec={n:d for n,d in dis.items() if n.startswith(('asus_capture_','cap_'))}
for n,d in rec.items():
 assert not re.search(r'<(?:ktime_|printk|_printk|sched_clock|kmalloc|kzalloc|vmalloc|schedule)(?:[^>]*)>',d),n
raw=(O/'arch/arm64/boot/Image').read_bytes();text=symbols['_text'];end=symbols['_end']
identity=json.loads((R/'source/identity.json').read_text());tag=identity['tag'].encode()
a,z=symbols['asus_entry_tag'],symbols['asus_entry_tag_end'];assert raw[a-text:z-text]==tag
assert ('A49CAP1 uuid='+identity['run_uuid']).encode() in raw
image_size=struct.unpack_from('<Q',raw,16)[0];assert image_size==end-text and image_size>=len(raw)
assert raw[56:60]==b'ARM\x64'
result=dict(status='ELF_CAPTURE_HOOKS_AND_SCOPED_SOURCE_CONFIG_PASS',symbols={n:hex(symbols[n]) for n in want if n in symbols},hook_receipts=dict(monotonic='entry + seq stages + exit linked',counter='entry + exactly one indirect counter call + exit linked',timer={n:'entry + exactly one actual indirect event callback + exit linked' for n in handlers}),entry_identity=identity,Image=dict(file_bytes=len(raw),image_size=image_size,text=hex(text),end=hex(end)),preserved_sources=preserved,config_byte_identical=True,old_kernel_and_selected_sources_unchanged=True,isolated_output_source_symlink=True,physical_execution=False)
(E/'linked-capture.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
