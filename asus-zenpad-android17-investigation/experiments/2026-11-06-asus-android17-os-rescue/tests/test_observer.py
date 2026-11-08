import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'source'))
from observer import *
class TestObserver(unittest.TestCase):
    def setUp(self):
        self.pin=dict(stock_serial=STOCK,stock_fingerprint=FINGERPRINT,usb='1-2',stock_product='WW_P00A',stock_model='P00A_2',stock_device='P00A_2')
        self.stock=f'{STOCK} device usb:1-2 product:WW_P00A model:P00A_2 device:P00A_2 transport_id:4'
        self.diag=f'{DIAGNOSTIC} recovery usb:1-2 product:p00a_diagnostic model:P00A_RAM_diagnostic device:p00a transport_id:7'
    def test_both_modes_same_physical_port(self):
        self.assertEqual(select(parse_devices(self.stock),self.pin)['transport_id'],'4')
        self.assertEqual(select(parse_devices(self.diag),self.pin)['transport_id'],'7')
    def test_offline_emulator_ignored(self):
        self.assertEqual(select(parse_devices('emulator-5554 offline\n'+self.diag),self.pin)['serial'],DIAGNOSTIC)
    def test_ambiguous_or_unpinned_refused(self):
        cases=[self.diag+'\n'+self.diag.replace('1-2','1-3'),self.stock+'\n'+self.diag,
               self.diag.replace('usb:1-2 ',''),self.diag.replace('usb:1-2','usb:1-3'),
               self.diag.replace('p00a_diagnostic','another'),self.diag.replace('recovery','unauthorized'),
               self.diag.replace(' transport_id:7','')]
        for case in cases:
            with self.subTest(case=case),self.assertRaises(Refused):select(parse_devices(case),self.pin)
    def test_failed_report_never_success(self):
        old=b'[ /tmp/diagnostic.txt ]\nopen errno=13\n'
        self.assertFalse(validate_report(old,0))
        good=MARKER+b'\nREPORT_ENDPOINT uid=2000 context=u:r:shell:s0\nandroidboot.serialno='+STOCK.encode()+b'\nEND_DIAGNOSTIC'
        self.assertTrue(validate_report(good,0));self.assertFalse(validate_report(good,74))
        self.assertFalse(validate_report(good.replace(STOCK.encode(),b'other'),0))
if __name__=='__main__':unittest.main()
