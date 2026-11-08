"""R3 mutation, new-source, failure and provenance fixtures; no install outputs."""
import gzip
import json
import hashlib
import shutil
import struct
import sys
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'tests'))
import integrate as i
import r3_inputs as r
import verify_product_r3 as p
from test_kit import KitTests,put,jsonput

class R3Tests(KitTests):
    # Reuse setup/helpers, not the inherited test suite.
    def test_unsealed_extra_guard_script_is_rejected(self):
        put(self.root/'scripts/unused_guard.py','TEST_ONLY extra module')
        with self.assertRaisesRegex(i.Refusal,'Kit file set changed'):i.verify_pins(self.root)

    def test_exact_sensor_suffix_rejects_rebound_manifest(self):
        rel='BoardConfig.mk';candidate=Path(self.p['staging'])/'product-device'/rel
        candidate.write_bytes(candidate.read_bytes()+b'TARGET_ARCH := arm\n')
        receipt=i.read(self.p['sensor_receipt']);receipt['after_sha256'][rel]=i.sha(candidate)
        jsonput(self.p['sensor_receipt'],receipt)
        staged=self.f.receipts['staged'];staged['product_after'][rel]=i.item(candidate);jsonput(self.p['staged_receipt'],staged)
        with self.assertRaisesRegex(i.Refusal,'Exact r2'):self.audit()

    def test_sensor_arm32_or_shim_cannot_replace_genuine_64bit_selection(self):
        base=Path(self.p['staging'])/'product-device/sensors'
        put(base/'sensors.mk',(base/'sensors.mk').read_bytes().replace(b':64',b':32'))
        with self.assertRaisesRegex(i.Refusal,'ARM64'):r.sensor_selection(self.p,self.f.receipts['staged'])
        shutil.copyfile(ROOT/'inputs/sensor-source/sensors.mk',base/'sensors.mk')
        put(base/'Android.bp','cc_binary { name: "fake-wrapper" }')
        with self.assertRaisesRegex(i.Refusal,'ARM64'):r.sensor_selection(self.p,self.f.receipts['staged'])

    def test_new_source_preexists_is_refused(self):
        new=self.f.k/'src/268'
        put(new,'unexpected preexisting source')
        with self.assertRaisesRegex(i.Refusal,'Kernel preimage'):self.audit()

    def test_overlap_delta_cannot_change_original_preimage(self):
        data=i.read(self.p['kernel_delta']);data['src/267']['before']='0'*64;jsonput(self.p['kernel_delta'],data)
        with self.assertRaisesRegex(i.Refusal,'BMC r5-relative preimage'):self.audit()

    def test_platform_before_after_and_preserved_backups(self):
        for name,pin in r.PLATFORM.items():
            path=Path(self.p[name])/pin['relative'];old=path.read_bytes();put(path,'wrong preimage')
            with self.assertRaisesRegex(i.Refusal,'active beforeimage'):self.audit()
            path.write_bytes(old)
        self.execute(True)
        for name,pin in r.PLATFORM.items():
            active=Path(self.p[name])/pin['relative']
            self.assertEqual(i.sha(active),pin['after'])
            self.assertEqual(i.sha(self.root/'attempt/before'/name/pin['relative']),pin['before'])
            put(active,'mutated postimage')
            with self.assertRaisesRegex(i.Refusal,'active afterimage'):i.verify_integrated(self.p)
            shutil.copyfile(Path(self.p[name+'_staged'])/pin['relative'],active)
        self.assertEqual((self.f.k/'src/268').read_text(),'after-268')
        self.assertIsNone(i.read(self.root/'attempt/preservation.json')[str(self.f.k/'src/268')])

    def test_partial_platform_apply_never_launches_or_retries(self):
        real=i.copy_exact
        def fail(src,dst,expected):
            if str(dst).endswith('model/PublicVolume.cpp'):raise OSError('TEST_ONLY vold write failure')
            return real(src,dst,expected)
        with patch.object(i,'copy_exact',side_effect=fail):
            with self.assertRaisesRegex(OSError,'vold write failure'):self.execute(True)
        self.assertEqual(i.sha(Path(self.p['platform_bpf'])/'loader/bpfloader.rs'),r.PLATFORM['platform_bpf']['after'])
        self.assertFalse((self.root/'attempt/launch.json').exists())
        self.assertTrue((self.root/'attempt/FAILED.json').is_file())
        with self.assertRaisesRegex(i.Refusal,'Previous attempt'):self.execute(True)

    def test_bundle_missing_member_cannot_be_accepted(self):
        data=i.read(self.p['bpf_supplement_manifest']);data['files'].pop(next(iter(data['files'])))
        self.p['bpf_supplement_manifest']=str(jsonput(self.root/'bad-manifest.json',data))
        with self.assertRaisesRegex(i.Refusal,'Unexpected supplement files'):r.verify_bundle(self.p)

    def test_failed_result_review_rejects_changed_image(self):
        put(Path(self.p['logs'])/'full-build-r5.exit-code','1\n');(Path(self.p['logs'])/'full-build-r5.complete').unlink()
        template=i.terminal(self.p,describe=True)['review_template'];template.update(reviewed_by_parent=True,reason='TEST_ONLY')
        review=jsonput(self.root/'parent-review/failed.json',template)
        put(Path(self.p['product_out'])/'system.img','changed failed-result image')
        with self.assertRaisesRegex(i.Refusal,'changed since parent review'):i.terminal(self.p,(review,i.sha(review)))

    def test_compiled_manifest_checks_unselected_files_too(self):
        compiled=Path(self.p['compiled_fixture']);expected={str(f.relative_to(compiled)):i.sha(f) for f in compiled.rglob('*') if f.is_file()}
        self.p['complete_kernel_manifest']=str(put(self.root/'complete.json.gz',gzip.compress(json.dumps(expected).encode())))
        self.assertEqual(r.complete_kernel(self.p),276)
        put(compiled/'unreviewed-source.c','extra')
        with self.assertRaisesRegex(i.Refusal,'Complete compiled source mismatch'):r.complete_kernel(self.p)

# Avoid rerunning all inherited cases under the R3 class.
for name in list(KitTests.__dict__):
    if name.startswith('test_') and name not in R3Tests.__dict__:setattr(R3Tests,name,None)

class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='TEST_ONLY-',dir=ROOT/'tests');self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    @unittest.skipUnless(sys.platform=='linux' and shutil.which('strip') and shutil.which('objcopy'), 'requires existing ELF binutils')
    def test_google_jni_allocated_code_survives_strip_but_detects_mutation(self):
        from verify_google_transformed import allocated_sections
        original=Path('/usr/bin/true')
        output=self.root/'TEST_ONLY-native-elf';shutil.copyfile(original,output)
        expected=allocated_sections(original)
        subprocess.run(['strip','--strip-debug',str(output)],check=True,capture_output=True)
        self.assertEqual(allocated_sections(output),expected)
        text=self.root/'text.bin'
        subprocess.run(['objcopy','--dump-section','.text='+str(text),str(output)],check=True,capture_output=True)
        data=bytearray(text.read_bytes());data[0]^=1;text.write_bytes(data)
        subprocess.run(['objcopy','--update-section','.text='+str(text),str(output)],check=True,capture_output=True)
        self.assertNotEqual(allocated_sections(output),expected)

    def test_elf_arm32_and_fixture_text_rejected(self):
        path=put(self.root/'not-shipping','TEST_ONLY text')
        with self.assertRaisesRegex(i.Refusal,'Wrong ELF'):p.elf(path)
        data=bytearray(64);data[:6]=b'\x7fELF\x01\x01';struct.pack_into('<H',data,18,40);path.write_bytes(data)
        with self.assertRaisesRegex(i.Refusal,'Wrong ELF'):p.elf(path)
    def test_graph_include_and_real_source_chain_no_engine(self):
        install='out/target/product/p00a/system/bin/vold'
        link='out/soong/.intermediates/system/vold/vold/android_arm64/unstripped/vold'
        obj='out/soong/.intermediates/system/vold/libvold/android_arm64/obj/system/vold/model/PublicVolume.o'
        put(self.root/'out/combined-lineage_p00a.ninja','subninja out/sub.ninja\n')
        put(self.root/'out/sub.ninja',f'rule cc\n  command = clang -c $in -o $out\nrule ld\n  command = clang++ $in -o $out\nbuild {obj}: cc system/vold/model/PublicVolume.cpp\nbuild {link}: ld {obj}\nbuild {install}: phony {link}\n')
        edges,receipt=p.selected_graph(self.root,{'system/bin/vold'})
        self.assertEqual(p.chain(edges,install),{install,link,obj})
        self.assertIn('clang',receipt['rules']['cc'])
        put(self.root/'out/combined-lineage_p00a.ninja','subninja ../outside.ninja\n')
        with self.assertRaisesRegex(i.Refusal,'Unsafe relative'):list(p.graph_files(self.root))
    def test_fresh_compiler_output_requires_log_and_real_source_command(self):
        out=put(self.root/'obj','TEST_ONLY compiler output')
        timestamp=out.stat().st_mtime
        entries={'obj':{'command_hash':'abc','mtime_ns':out.stat().st_mtime_ns}}
        with self.assertRaisesRegex(i.Refusal,'Missing actual r6'):p.execution_record(self.root,'obj',entries,{},timestamp-1,True,'source.c')
        commands={'obj':['clang -c source.c -o obj']}
        self.assertEqual(p.execution_record(self.root,'obj',entries,commands,timestamp-1,True,'source.c')['sha256'],i.sha(out))
        with self.assertRaisesRegex(i.Refusal,'Stale r6'):p.execution_record(self.root,'obj',entries,commands,timestamp+1,True,'source.c')
        with self.assertRaisesRegex(i.Refusal,'Missing actual r6'):p.execution_record(self.root,'obj',entries,commands,timestamp-1,True,'unreviewed.c')
    def test_ninja_log_retains_latest_actual_command_record(self):
        log=put(self.root/'.ninja_log','# ninja log v5\n1\t2\t100\tobj\tabcd\n3\t4\t200\tobj\tdef0\n')
        self.assertEqual(p.log_entries(log,{'obj'})['obj']['command_hash'],'def0')
        log.write_text('# ninja log v4\n')
        with self.assertRaisesRegex(i.Refusal,'Unsupported actual'):p.log_entries(log,{'obj'})

del KitTests

if __name__=='__main__':unittest.main()
