import copy
import unittest
from test_observe import observer, fixture_tree

class InterfaceNubTests(unittest.TestCase):
    def test_driver_nub_descriptor_copies_do_not_count_as_interfaces(self):
        tree = fixture_tree()
        interface = tree[0]['IORegistryEntryChildren'][0]
        media = interface['IORegistryEntryChildren']
        driver = {'IOObjectClass': 'IOUSBMassStorageDriverNub', 'bInterfaceClass': 8,
                  'bInterfaceSubClass': 6, 'bInterfaceProtocol': 80, 'IORegistryEntryChildren': media}
        nub = {'IOObjectClass': 'IOUSBMassStorageInterfaceNub', 'bInterfaceClass': 8,
               'bInterfaceSubClass': 6, 'bInterfaceProtocol': 80, 'IORegistryEntryChildren': [driver]}
        interface['IORegistryEntryChildren'] = [nub]
        self.assertEqual(observer.select_media(tree)['disk'], 'disk12')

    def test_physical_uas_descriptor_is_not_replaced_by_bulk_nub(self):
        tree = fixture_tree()
        interface = tree[0]['IORegistryEntryChildren'][0]
        interface['bInterfaceProtocol'] = 98
        interface['IORegistryEntryChildren'] = [{
            'IOObjectClass': 'IOUSBMassStorageInterfaceNub', 'bInterfaceClass': 8,
            'bInterfaceSubClass': 6, 'bInterfaceProtocol': 80,
            'IORegistryEntryChildren': interface['IORegistryEntryChildren']}]
        with self.assertRaises(observer.Refused):
            observer.select_media(tree)

    def test_driver_nub_alone_cannot_stand_in_for_physical_interface(self):
        tree = fixture_tree()
        tree[0]['IORegistryEntryChildren'][0]['IOObjectClass'] = 'IOUSBMassStorageInterfaceNub'
        with self.assertRaises(observer.Refused):
            observer.select_media(tree)
