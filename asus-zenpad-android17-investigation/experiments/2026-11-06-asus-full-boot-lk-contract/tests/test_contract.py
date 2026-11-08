import gzip
import hashlib
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from bootformat import sha, pad, boot_id, ungzip, make_cpio, parse_image, PARTITION_SIZE
from fdt import parse
from lk_contract import HEADER, LK_DEFAULT, REQUIRED_INPUT, header_limit, narrow_header, chosen_dt, kernel_config
from boot_memory import check_memory
from package_full_boot import components, package, validate_ramdisk, wrapper_templates
from build_fixtures import BASE, PINS, inputs, fixture


def edit_dt(dt, node, prop, value):
    h,nodes,tokens=parse(dt);strings=bytearray(dt[h[3]:h[3]+h[8]])
    name=prop.encode()+b'\0';off=strings.find(name)
    if off<0:off=len(strings);strings+=name
    encoded=struct.pack('>III',3,len(value),off)+value+bytes(-len(value)%4)
    stream=bytearray();done=False
    for t,n,p,v,raw in tokens:
        if n==node and t==3 and p==prop:stream+=encoded;done=True
        elif n==node and t==2 and not done:stream+=encoded+raw;done=True
        else:stream+=raw
    assert done
    head=list(h);head[1]=h[2]+len(stream)+len(strings);head[3]=h[2]+len(stream);head[8]=len(strings);head[9]=len(stream)
    return struct.pack('>10I',*head)+dt[40:h[2]]+stream+strings


def gzip_length(data, length):
    # Valid gzip optional COMMENT makes compressed byte length exact, without
    # changing decompressed cpio. This is an in-memory boundary fixture only.
    assert data[3]==0 and length>len(data)+1
    return data[:3]+b'\x10'+data[4:10]+b'x'*(length-len(data)-1)+b'\0'+data[10:]


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ram,cls.probe_ram=inputs()
        cls.kernels={n:(BASE/'artifacts'/n).read_bytes() for n in PINS}
        cls.k=cls.kernels['Image.gz-dtb-combined-r1'];cls.raw,cls.dt=ungzip(cls.k)
        cls.data=fixture(cls.k,cls.ram)
        cls.cmd=b' '.join(k+b'='+v for k,v in REQUIRED_INPUT.items())

    def run_package(self,data=None,k=None):
        data=self.data if data is None else data
        return package(data,self.k if k is None else k,{'boot':{'sha256':sha(data)}},synthetic=True)

    def test_real_r1_and_product_r3_preserved(self):
        for name,k in self.kernels.items():
            with self.subTest(kernel=name):
                self.assertEqual(sha(k),PINS[name]);data=fixture(k,self.ram)
                image,dt,r=self.run_package(data,k);h,wk,wr,cmd=components(image)
                raw,old=ungzip(k);stream=k[:-len(old)]
                self.assertEqual(wk[512:512+len(stream)],stream)
                self.assertEqual(wr[512:],self.ram)
                self.assertEqual(ungzip(wk[512:])[0],raw)
                self.assertEqual(h[576:608],boot_id(wk,wr))
                self.assertEqual(hashlib.sha256(image+bytes(PARTITION_SIZE-len(image))).hexdigest(),r['padded_partition_sha256'])
                self.assertEqual(r['status'],'NONBOOTABLE_SYNTHETIC_FIXTURE')
                self.assertNotIn('init',__import__('bootformat').parse_cpio(ungzip(wr[512:])[0]))

    def test_header_99_accepted_100_rejected(self):
        self.assertEqual(header_limit(b'a'*99),b'a'*99)
        with self.assertRaises(ValueError):header_limit(b'a'*100)
        with self.assertRaises(ValueError):header_limit(b'a\0')
        with self.assertRaises(ValueError):header_limit(b'\xff')

    def test_99th_required_character_survives_100th_would_be_lost(self):
        token=b'enforcing=1'
        good=b' '*(99-len(token))+token
        bad=b' '*(100-len(token))+token
        self.assertEqual(header_limit(good)[-len(token):],token)
        self.assertTrue(good[:99].endswith(b'enforcing=1'))
        self.assertTrue(bad[:99].endswith(b'enforcing='))
        with self.assertRaises(ValueError):header_limit(bad)

    def test_memreserve_and_one_byte_over_four_mib_rejected_by_memory(self):
        dt=chosen_dt(self.dt,0x400000,HEADER)
        check_memory(self.raw,dt,0x400000)
        bad=edit_dt(dt,'/chosen','linux,initrd-end',struct.pack('>I',0x44400001))
        with self.assertRaisesRegex(AssertionError,'Overlapping boot memory'):check_memory(self.raw,bad,0x400001)
        h,_,_=parse(dt);h=list(h)
        table=bytearray(dt[40:h[2]])
        assert table[h[4]-40:h[4]-24]==bytes(16)
        table[h[4]-40:h[4]-24]=struct.pack('>QQ',0x44000000,1)
        table+=bytes(16)
        h[1]+=16;h[2]+=16;h[3]+=16
        bad=struct.pack('>10I',*h)+table+dt[parse(dt)[0][2]:]
        with self.assertRaisesRegex(AssertionError,'Overlapping boot memory'):check_memory(self.raw,bad,0x400000)

    def test_lk_inflate_capacity(self):
        dt=chosen_dt(self.dt,len(self.ram),HEADER)
        raw=bytearray(self.raw+bytes(0x1c00001-len(self.raw)))
        struct.pack_into('<Q',raw,16,len(raw))
        with self.assertRaisesRegex(AssertionError,'inflate capacity'):check_memory(raw,dt,len(self.ram))

    def test_cli_defaults_plan_only_and_rejects_synthetic_as_full(self):
        import subprocess,tempfile
        kernel=BASE/'artifacts/Image.gz-dtb-combined-r1'
        source=ROOT/'artifacts/Image.gz-dtb-combined-r1'
        with tempfile.TemporaryDirectory(dir=ROOT/'tests') as temp:
            out=Path(temp)/'output'
            args=[sys.executable,str(ROOT/'scripts/package_full_boot.py'),'--aosp-boot',str(source/'NONBOOTABLE-SYNTHETIC-AOSP-input.img'),'--build-report',str(source/'input-report.json'),'--kernel',str(kernel),'--out',str(out)]
            for mode in ([],['--mode','PACKAGE_UNTESTED']):
                result=subprocess.run(args+mode,capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('Synthetic fixture rejected',result.stderr)
                self.assertFalse(out.exists())
            result=subprocess.run(args+['--mode','SYNTHETIC_FIXTURE'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads((out/'manifest.json').read_text())
            self.assertEqual(report['image_file'],'NONBOOTABLE-SYNTHETIC-full-BOOT.img')
            self.assertFalse(report['flashable_claim'])
            result=subprocess.run([sys.executable,'-O',str(ROOT/'scripts/package_full_boot.py'),'--help'],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Do not use optimized Python',result.stderr)

    def test_narrow_header_preserves_92_exact(self):
        self.assertGreater(len(self.cmd),99)
        self.assertEqual(narrow_header(self.cmd),HEADER);self.assertEqual(len(HEADER),92)
        self.assertIn(b'enforcing=1',HEADER.split())
        self.assertNotIn(b'initrd=',HEADER)
        self.assertEqual(narrow_header(self.cmd+b' androidboot.selinux=enforcing enforcing=1'),HEADER)

    def test_required_arguments_absent_conflicting_duplicated(self):
        for key,value in REQUIRED_INPUT.items():
            token=key+b'='+value
            with self.subTest(key=key):
                for bad in (b' '.join(t for t in self.cmd.split() if t!=token),self.cmd.replace(token,key+b'=wrong'),self.cmd+b' '+token):
                    with self.assertRaises(ValueError):narrow_header(bad)

    def test_unknown_and_enforcement_bypasses_rejected(self):
        for arg in [b'enforcing=0',b'selinux=0',b'androidboot.selinux=permissive',b'init=/bin/sh',b'rdinit=/bin/sh',b'androidboot.mode=recovery',b'random=value',b'androidboot.selinux=enforcingX']:
            with self.subTest(arg=arg),self.assertRaises(ValueError):narrow_header(self.cmd+b' '+arg)

    def test_any_initrd_override_rejected(self):
        for arg in [b'initrd=0x44000200,0x100',b'initrd=0x44000000,0x100',b'initrd=0x44000200,0x100 initrd=0x44000000,0x100']:
            with self.subTest(arg=arg),self.assertRaises(ValueError):narrow_header(self.cmd+b' '+arg)
        stale=edit_dt(self.dt,'/chosen','bootargs',b'initrd=0x44000200,0x100\0')
        with self.assertRaises(ValueError):chosen_dt(stale,len(self.ram),HEADER)

    def test_three_dt_properties_only_and_reservations_preserved(self):
        result=chosen_dt(self.dt,len(self.ram),HEADER)
        h,before,tokens=parse(self.dt);nh,after,_=parse(result)
        differences={(n,p) for n in before.keys()|after.keys() for p in before.get(n,{}).keys()|after.get(n,{}).keys() if before.get(n,{}).get(p)!=after.get(n,{}).get(p)}
        self.assertEqual(differences,{('/chosen','bootargs'),('/chosen','linux,initrd-start'),('/chosen','linux,initrd-end')})
        self.assertEqual(self.dt[40:h[2]],result[40:nh[2]])
        self.assertEqual(after['/chosen']['bootargs'],LK_DEFAULT+b' '+HEADER+b'\0')
        self.assertEqual(after['/chosen']['linux,initrd-start'],b'\x44\0\0\0')
        self.assertEqual(int.from_bytes(after['/chosen']['linux,initrd-end'],'big'),0x44000000+len(self.ram))

    def test_old_plus_512_start_and_end_rejected(self):
        dt=chosen_dt(self.dt,len(self.ram),HEADER)
        for name,value in [('linux,initrd-start',0x44000200),('linux,initrd-end',0x44000200+len(self.ram))]:
            with self.subTest(name=name),self.assertRaises(AssertionError):
                check_memory(self.raw,edit_dt(dt,'/chosen',name,struct.pack('>I',value)),len(self.ram))

    def test_actual_probe_ram_payload_copy_starts_at_gzip(self):
        # No candidate image is written with this bootable probe payload.
        _,rw,_=wrapper_templates();from bootformat import wrap
        wrapped=wrap(rw,self.probe_ram)
        recognized=struct.unpack_from('<I',wrapped,4)[0]
        relocated=wrapped[512:512+recognized]
        self.assertEqual(relocated,self.probe_ram);self.assertEqual(relocated[:2],b'\x1f\x8b')
        self.assertNotEqual(relocated[512:514],b'\x1f\x8b')
        dt=chosen_dt(self.dt,len(relocated),HEADER);memory=check_memory(self.raw,dt,len(relocated))
        self.assertEqual(memory['payloads'][1]['end'],0x44000000+len(relocated))

    def test_exact_four_mib_boundary_end_exclusive(self):
        for length in (0x3fffff,0x400000):
            with self.subTest(length=length):
                ram=gzip_length(self.ram,length);data=fixture(self.k,ram)
                image,dt,report=self.run_package(data)
                self.assertEqual(report['ramdisk_end'],hex(0x44000000+length))
                self.assertEqual(components(image)[2][512:],ram)
        with self.assertRaises(ValueError):self.run_package(fixture(self.k,gzip_length(self.ram,0x400001)))

    def test_memory_empty_huge_and_fixed_overlap(self):
        with self.assertRaises(ValueError):chosen_dt(self.dt,0,HEADER)
        dt=chosen_dt(self.dt,len(self.ram),HEADER)
        with self.assertRaises(AssertionError):check_memory(self.raw,dt,0xe000000)
        overlap=edit_dt(dt,'/reserved-memory/ram_console-reserved-memory','reg',struct.pack('>QQ',0x44000000,1))
        with self.assertRaises(AssertionError):check_memory(self.raw,overlap,len(self.ram))

    def test_image_size_not_file_length_and_atf_overlap(self):
        dt=chosen_dt(self.dt,len(self.ram),HEADER);m=check_memory(self.raw,dt,len(self.ram))
        self.assertGreater(m['image_size'],len(self.raw))
        self.assertEqual(m['payloads'][0]['end'],0x40080000+m['image_size'])
        for size in [len(self.raw)-1,0x43000001-0x40080000]:
            raw=bytearray(self.raw);struct.pack_into('<Q',raw,16,size)
            with self.subTest(size=size),self.assertRaises(AssertionError):check_memory(raw,dt,len(self.ram))
        raw=bytearray(self.raw);struct.pack_into('<Q',raw,8,0)
        with self.assertRaises(AssertionError):check_memory(raw,dt,len(self.ram))

    def test_payload_outside_static_ram(self):
        dt=chosen_dt(self.dt,len(self.ram),HEADER)
        dt=edit_dt(dt,'/memory@00000000','reg',struct.pack('>QQ',0x40000000,0x8000000))
        with self.assertRaises(AssertionError):check_memory(self.raw,dt,len(self.ram))

    def test_dynamic_consys_is_preserved_not_certified(self):
        dt=chosen_dt(self.dt,len(self.ram),HEADER);m=check_memory(self.raw,dt,len(self.ram))
        self.assertFalse(m['dynamic_reservations'][0]['runtime_address_verified'])
        changed=edit_dt(dt,'/reserved-memory/consys-reserve-memory','size',struct.pack('>Q',0x400000))
        with self.assertRaises(AssertionError):check_memory(self.raw,changed,len(self.ram))

    def test_charging_opt_in_rejected(self):
        bad=edit_dt(self.dt,'/chosen','asus,allow-battery-charging',b'')
        with self.assertRaises(ValueError):chosen_dt(bad,len(self.ram),HEADER)

    def test_android_id_padding_trailing_and_truncation(self):
        for offset in (576,len(self.data)-1):
            b=bytearray(self.data);b[offset]^=1
            with self.subTest(offset=offset),self.assertRaises(ValueError):self.run_package(bytes(b))
        for b in (self.data[:-1],self.data+b'\0'*2048):
            with self.assertRaises(ValueError):self.run_package(b)

    def test_header_geometry_version_extended_cmdline(self):
        for offset,value in [(12,0x40080200),(20,0x44000200),(24,1),(28,0x40000000),(32,0x4e000200),(36,4096),(40,1),(608,1),(1632,1)]:
            b=bytearray(self.data);struct.pack_into('<I',b,offset,value)
            with self.subTest(offset=offset),self.assertRaises(ValueError):self.run_package(bytes(b))

    def test_kernel_and_build_report_mismatch(self):
        with self.assertRaises(ValueError):package(self.data,self.k,{'boot':{'sha256':'0'*64}},synthetic=True)
        with self.assertRaises(ValueError):self.run_package(k=self.k+b'x')

    def test_gzip_extra_member_bootconfig_and_missing_fstab(self):
        with self.assertRaises(ValueError):validate_ramdisk(self.ram+gzip.compress(b'x'),True)
        with self.assertRaises(ValueError):validate_ramdisk(self.ram+b'bootconfig',True)
        ram=gzip.compress(make_cpio({'NONBOOTABLE-SYNTHETIC-FIXTURE.txt':(0o100644,0,0,b'test')}),mtime=0)
        with self.assertRaises(ValueError):validate_ramdisk(ram,True)
        with self.assertRaises(ValueError):validate_ramdisk(self.ram,False)

    def test_lk_last_magic_selection_rejected(self):
        dt=edit_dt(self.dt,'/chosen','unrelated-test-property',b'\xd0\x0d\xfe\xed')
        k=self.k[:-len(self.dt)]+dt
        with self.assertRaisesRegex(ValueError,'last DT magic'):self.run_package(fixture(k,self.ram),k)

    def test_partition_limit_including_wrappers(self):
        stream=self.k[:-len(self.dt)]
        # AOSP input itself fits exactly; adding two wrappers consumes extra pages.
        budget=PARTITION_SIZE-2048-len(pad(self.ram))
        k=gzip_length(stream,budget-len(self.dt))+self.dt
        data=fixture(k,self.ram)
        self.assertEqual(len(data),PARTITION_SIZE)
        with self.assertRaisesRegex(ValueError,'partition overflow'):self.run_package(data,k)
        with self.assertRaises(ValueError):components(data+b'\0')

    def test_embedded_kernel_config_and_initrd_required(self):
        config=kernel_config(self.raw)
        self.assertIn(b'CONFIG_SECURITY_SELINUX_DEVELOP=y',config)
        bad=self.raw.replace(b'IKCFG_ST',b'NO_CONFIG',1)
        with self.assertRaises(ValueError):kernel_config(bad)


if __name__=='__main__':unittest.main(verbosity=2)
