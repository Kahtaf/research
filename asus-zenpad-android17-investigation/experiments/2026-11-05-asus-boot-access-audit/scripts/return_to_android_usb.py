#!/usr/bin/env python3
"""Send only normal reboot, to the exact confirmed ASUS fastboot interface."""
import json
import sys
import usb.backend.libusb1
import usb.core
import usb.util

backend = usb.backend.libusb1.get_backend(find_library=lambda _: '/opt/homebrew/lib/libusb-1.0.dylib')
devices = [d for d in usb.core.find(find_all=True, idVendor=0x0bb4, idProduct=0x0c01, backend=backend)
           if d.serial_number == 'DEVICE_SERIAL_REDACTED']
assert len(devices) == 1, 'Exact ASUS fastboot device required'
device = devices[0]
interfaces = [i for i in device.get_active_configuration()
              if (i.bInterfaceClass, i.bInterfaceSubClass, i.bInterfaceProtocol) == (0xff, 0x42, 3)]
assert len(interfaces) == 1
interface = interfaces[0]
endpoints = [e for e in interface if usb.util.endpoint_type(e.bmAttributes) == usb.util.ENDPOINT_TYPE_BULK]
inputs = [e for e in endpoints if usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN]
outputs = [e for e in endpoints if usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT]
assert len(inputs) == len(outputs) == 1
usb.util.claim_interface(device, interface.bInterfaceNumber)
try:
    assert outputs[0].write(b'reboot', timeout=1500) == 6
    print(json.dumps({'command': 'reboot', 'bytes_sent': 6}), flush=True)
    response = bytes(inputs[0].read(64, timeout=2500))
    print(json.dumps({'response': response.decode('ascii', errors='replace')}), flush=True)
    assert response.startswith(b'OKAY'), response
finally:
    try:
        usb.util.release_interface(device, interface.bInterfaceNumber)
        usb.util.dispose_resources(device)
    except usb.core.USBError as exc:
        print(json.dumps({'cleanup_after_reboot': str(exc)}), file=sys.stderr)
