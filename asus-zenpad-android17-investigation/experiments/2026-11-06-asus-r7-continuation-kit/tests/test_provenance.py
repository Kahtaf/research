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
from test_outputs import put,jsonput

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
        with self.assertRaisesRegex(i.Refusal,'Missing actual r7'):p.execution_record(self.root,'obj',entries,{},timestamp-1,True,'source.c')
        commands={'obj':['clang -c source.c -o obj']}
        self.assertEqual(p.execution_record(self.root,'obj',entries,commands,timestamp-1,True,'source.c')['sha256'],i.sha(out))
        with self.assertRaisesRegex(i.Refusal,'Stale r7'):p.execution_record(self.root,'obj',entries,commands,timestamp+1,True,'source.c')
        with self.assertRaisesRegex(i.Refusal,'Missing actual r7'):p.execution_record(self.root,'obj',entries,commands,timestamp-1,True,'unreviewed.c')
    def test_ninja_log_retains_latest_actual_command_record(self):
        log=put(self.root/'.ninja_log','# ninja log v5\n1\t2\t100\tobj\tabcd\n3\t4\t200\tobj\tdef0\n')
        self.assertEqual(p.log_entries(log,{'obj'})['obj']['command_hash'],'def0')
        log.write_text('# ninja log v4\n')
        with self.assertRaisesRegex(i.Refusal,'Unsupported actual'):p.log_entries(log,{'obj'})
