#!/usr/bin/env python3
"""Local two-control packaging; no hardware, network, build or execution."""
from pathlib import Path
import ast, gzip, hashlib, importlib.util, json, re, shutil, struct as S, sys, zlib
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[1]
W = R.parent
PREV = W/'2026-11-07-asus-stock-kernel-sd-control'
sys.path.insert(0, str(R/'source'))
from kallsyms import decode
sha = lambda data: hashlib.sha256(data).hexdigest()
record = lambda data: dict(bytes=len(data), sha256=sha(data))
VERSION = b'#1 SMP PREEMPT Thu Aug 9 12:33:25 CST 2018'
P10 = 16740352
pins = {}
def read(path, pin=None):
    data = path.read_bytes()
    if pin: assert sha(data) == pin, (str(path), sha(data))
    pins[str(path.relative_to(W))] = record(data)
    return data

def segment(tree, text, kind, name):
    node = next(n for n in tree.body if isinstance(n, kind) and n.name == name)
    return ast.get_source_segment(text, node)

def main():
    fmt = read(PREV/'source/bootformat.py', '3207680c9c4fdee2c2dc3704cb3564e5c3736c0eb3cae63edb17f6d5fa958017')
    (R/'source/bootformat.py').write_bytes(fmt)
    spec = importlib.util.spec_from_file_location('bootformat', R/'source/bootformat.py')
    b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
    working = read(PREV/'artifacts/candidate.img', 'eccfc87f28169bee14d0675f6ad31335f832ab25db46b013b03a06109b0df13d')
    header, kernel, ramdisk, rest = b.parse_image(working)
    assert not rest and sha(kernel) == 'b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880'
    assert sha(ramdisk) == '51a6d8deb3368c8b8a10d6d730ca21c6b157fda5f940d5ba7cdcb2d2a6788e46'
    raw, fdt = b.ungzip(kernel[512:])
    assert sha(raw) == 'db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a'
    assert len(fdt) == 62482 and sha(fdt) == '77e2d8fbeced5a827ede6c0b8589140e9211d8dc3ca77aaa31a1dd1787a9c455'
    assert S.unpack_from('>II', fdt) == (0xd00dfeed, len(fdt))
    # Retain the exact parser provenance; never import scripts with input/output side effects.
    inspector = read(W/'2026-11-07-asus-linux49-retained-boot-trace/scripts/inspect_stock.py').decode()
    parser = inspector[inspector.index('# Decode and cross-check'):inspector.index('\nmd=Cs')]
    retained = (R/'source/kallsyms.py').read_text()
    assert all('    '+line in retained for line in parser.splitlines())
    audit_path = W/'2026-11-06-asus-stock-initrd-size-premise/scripts/audit.py'
    audit = read(audit_path).decode()
    audit_tree = ast.parse(audit)
    dt_source = segment(audit_tree, audit, ast.FunctionDef, 'dt_parse')
    env = {'S': S, 'sha': sha, 'align': lambda n,a:(n+a-1)//a*a}
    exec(dt_source, env)
    dt_facts, props = env['dt_parse'](fdt)
    assert 'initrd=0x44000200,0x200000' in props['/chosen','bootargs'].decode()
    # Existing FDT initrd token is preserved, never introduced into Android bootargs.
    assert not any(t.startswith(b'initrd=') for t in header[64:576].split(b'\0')[0].split())
    symbols, sym, base, addresses = decode(raw)
    assert base == 0xffffffc000080000
    # Resolve data through a named, decoded export record (KALLSYMS_ALL is absent).
    def exported(name):
        table = sym['__ksymtab_'+name]
        ptr, nameptr = S.unpack_from('<QQ', raw, table-base)
        assert nameptr == sym['__kstrtab_'+name]
        assert raw[nameptr-base:nameptr-base+len(name)+1] == name.encode()+b'\0'
        assert 0 <= ptr-base < len(raw)
        return ptr, dict(ksymtab_address=hex(table), kstrtab_address=hex(nameptr), value_address=hex(ptr))
    uts, uts_export = exported('init_uts_ns')
    task, task_export = exported('init_task')
    no = uts-base
    assert S.unpack_from('<I', raw, no)[0] == 2
    names = [raw[no+4+65*i:no+4+65*(i+1)].split(b'\0')[0] for i in range(6)]
    assert names == [b'Linux', b'(none)', b'3.18.35', VERSION, b'arm64', b'(none)']
    # Exact sys_newuname instructions prove task->nsproxy +0x9a0, nsproxy->uts_ns +8,
    # namespace->name +4 and copy of all 390 bytes. Initial task resolves to this namespace.
    uname = sym['sys_newuname']; uo = uname-base
    expected = {0x48:('ldr','x0, [x3, #0x9a0]'), 0x4c:('ldr','x1, [x0, #8]'),
                0x50:('add','x1, x1, #4'), 0x7c:('mov','x2, #0x186')}
    insns = list(Cs(CS_ARCH_ARM64, CS_MODE_ARM).disasm(raw[uo:uo+0x88],uname))
    byoff = {i.address-uname:(i.mnemonic,i.op_str) for i in insns}
    assert all(byoff[off] == val for off,val in expected.items())
    copy_insn = byoff[0x80]
    assert copy_insn[0] == 'bl' and int(copy_insn[1][1:],16) == sym['__copy_to_user']
    nsproxy = S.unpack_from('<Q',raw,task-base+0x9a0)[0]
    assert S.unpack_from('<Q',raw,nsproxy-base+8)[0] == uts
    patch = no+4+3*65+1
    assert raw[patch-1:patch+len(VERSION)] == VERSION+b'\0'
    banner_offset = sym['linux_banner']-base
    banner = raw[banner_offset:raw.index(0,banner_offset)+1]
    assert VERSION in banner and not banner_offset <= patch < banner_offset+len(banner)
    modified = bytearray(raw); modified[patch] = ord('2')
    assert raw[:patch] == modified[:patch] and raw[patch+1:] == modified[patch+1:]
    assert modified[patch] != raw[patch] and len(modified) == len(raw)
    assert modified[banner_offset:banner_offset+len(banner)] == banner
    (R/'evidence/uts-path.disasm').write_text('\n'.join(f'{i.address:016x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in insns)+'\n')
    source_prefix = W/'2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18'
    excerpts = []
    for rel, lo, hi in [('init/version.c',25,47), ('include/linux/utsname.h',22,34),
                        ('include/linux/utsname.h',70,83), ('include/uapi/linux/utsname.h',14,31),
                        ('kernel/nsproxy.c',31,42), ('kernel/sys.c',1141,1155)]:
        path=source_prefix/rel
        data=read(path) if str(path.relative_to(W)) not in pins else path.read_bytes()
        excerpts.append('REFERENCE '+str(path.relative_to(W))+' sha256 '+sha(data))
        excerpts.extend(f'{i}: {s}' for i,s in enumerate(data.decode().splitlines(),1) if lo <= i <= hi)
    (R/'evidence/source-excerpts.txt').write_text('\n'.join(excerpts)+'\n')
    proof = dict(kallsyms_count=len(symbols), markers_tokens_and_names_validated=True, base_address=hex(base),
                 init_uts_ns_export=uts_export, init_task_export=task_export,
                 initial_task_nsproxy_address=hex(nsproxy), task_nsproxy_offset='0x9a0', nsproxy_uts_offset=8,
                 namespace_name_offset=4, field_width=65, fields=[v.decode() for v in names],
                 version_field_address=hex(base+patch-1), version_field_image_offset=patch-1,
                 patch=dict(image_offset=patch,image_offset_hex=hex(patch),virtual_address=hex(base+patch),old_ascii='1',new_ascii='2',old_hex='31',new_hex='32'),
                 pre_raw=record(raw),post_raw=record(modified),only_one_raw_byte_changed=True,
                 all_code_and_other_data_identical=True, linux_banner=dict(address=hex(sym['linux_banner']),image_offset=banner_offset,sha256=sha(banner),unchanged=True,text=banner.rstrip(b'\0').decode()),
                 runtime_expectation='If executed in the unchanged initial namespace, uname.version is #2 SMP PREEMPT Thu Aug 9 12:33:25 CST 2018; no execution claimed.')
    (R/'evidence/uts-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
    original_installer=read(PREV/'source/install.py').decode()
    original_tree=ast.parse(original_installer)
    for name in ('adb','legacy_adb.py'):
        (R/'source'/name).write_bytes(read(PREV/'source'/name))
        shutil.copymode(PREV/'source'/name,R/'source'/name)
    products={}
    for label, data in [('original',raw),('version2',modified)]:
        # Identical deterministic gzip procedure and metadata for both controls.
        compressed=gzip.compress(data,compresslevel=9,mtime=0)
        payload=compressed+fdt
        wrapped=b.wrap(kernel,payload)
        image=b.make_image(header,wrapped,ramdisk)
        full=image+bytes(P10-len(image))
        ip=R/'artifacts'/f'{label}.img'; fp=R/'artifacts'/f'{label}.p10.raw'
        ip.write_bytes(image); fp.write_bytes(full)
        actual=ip.read_bytes(); h,k,r,tail=b.parse_image(actual)
        decoded, appended=b.ungzip(k[512:])
        assert decoded == data and appended == fdt and not tail and r == ramdisk
        assert k[:4] == kernel[:4] and k[8:512] == kernel[8:512]
        assert S.unpack_from('<I',k,4)[0] == len(payload)
        assert h[:8] == header[:8] and h[12:16] == header[12:16]
        assert h[20:576] == header[20:576] and h[608:] == header[608:]
        staged=actual[2560:]
        selected=staged.rfind(bytes.fromhex('d00dfeed'),1,len(k)+4)
        assert selected == len(compressed)
        selected_dt,_=env['dt_parse'](staged[selected:])
        assert selected_dt['sha256'] == sha(fdt)
        assert fp.read_bytes() == full
        installer=original_installer
        replacements={"IMAGE=ROOT/'artifacts/candidate.img'":f"IMAGE=ROOT/'artifacts/{label}.img'",
          "IMAGE_SHA='eccfc87f28169bee14d0675f6ad31335f832ab25db46b013b03a06109b0df13d'":f"IMAGE_SHA='{sha(image)}'",
          "FULL_SHA='4b564d404bc13b20ba44790733a37010fe0677bfced235de2b334c3bff08fa19'":f"FULL_SHA='{sha(full)}'",
          'len(image)==7798784':f'len(image)=={len(image)}',
          "'7161898f7858c5eb2887a4589fce5a62d4b2d556e1413e36e4e53c3cd8431b09')":"'7161898f7858c5eb2887a4589fce5a62d4b2d556e1413e36e4e53c3cd8431b09','2bfdfb2c68c1abe97700b8c9dfb7386f32953a3de5900f08c373c51e011e30b9')",
          "profile='exact-linux49-microsd-probe'":f"profile='stock-kernel-version-{label}'"}
        for old,new in replacements.items():
            assert installer.count(old)==1
            installer=installer.replace(old,new)
        new_tree=ast.parse(installer)
        for kind,name in [(ast.FunctionDef,'execute'),(ast.ClassDef,'Transport')]:
            assert segment(original_tree,original_installer,kind,name)==segment(new_tree,installer,kind,name)
        out=R/'source'/f'install_{label}.py';out.write_text(installer)
        products[label]=dict(image=record(actual),p10=record(full),raw_image=record(data),wrapped_kernel=record(k),gzip=record(compressed),
          fdt_gzip_relative_offset=selected,fdt_android_image_offset=2560+selected,
          ramdisk_android_image_offset=2048+b.align(len(k)),android_image_id=h[576:608].hex(),installer=record(out.read_bytes()),
          checks=dict(gzip_roundtrip=True,fdt_exact_and_lk_selection=True,header_addresses_page_bootargs_preserved=True,
            mtk_wrappers_except_kernel_size_preserved=True,ramdisk_exact=True,android_lengths_id_and_padding=True,
            installer_execute_and_transport_exact=True,only_specified_installer_literals_changed=True))
    receipt=dict(status='LOCAL_PACKAGED_NO_PHYSICAL_TEST',inputs=pins,gzip_procedure=dict(api='gzip.compress',compresslevel=9,mtime=0,python=sys.version,zlib=zlib.ZLIB_VERSION),
      original_working_image=record(working),stock_wrapped_kernel=record(kernel),stock_fdt=record(fdt),wrapped_ramdisk=record(ramdisk),
      marker=dict(name='PROBE.ID',contents='dbbb6afb-dd70-4c35-961e-9c977d7164a8\n'),report='PROBE.TXT',products=products,
      added_preimage='2bfdfb2c68c1abe97700b8c9dfb7386f32953a3de5900f08c373c51e011e30b9',added_preimage_provenance='Parent explicitly supplied current verified p10 hash; not re-observed locally',
      no_new_control_hash_admitted_as_preimage=True,no_build=True,no_hardware_contact=True,no_network=True,no_execution=True,no_boot_security_change=True,no_failure_cause_claim=True)
    (R/'evidence/packaging-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file()) < 64*1024**2
    print(json.dumps(dict(products=products,patch=proof['patch'],raw_pre=proof['pre_raw'],raw_post=proof['post_raw']),indent=2))
if __name__=='__main__': main()
