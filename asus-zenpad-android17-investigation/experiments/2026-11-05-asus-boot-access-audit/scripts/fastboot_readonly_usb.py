#!/usr/bin/env python3
"""Isolated, bounded fastboot query transport; no reset/flash/download commands.

Default is descriptor inspection. --execute sends one fixed read-only query
only after matching the exact ASUS serial and fastboot interface descriptor.
The additional fixed OEM listing command was traced in the matching stock LK.
"""
import argparse,datetime,json,sys,time
from pathlib import Path
import usb.core,usb.util,usb.backend.libusb1

queries={x:('getvar:'+x).encode('ascii') for x in
    ['version','product','secure','unlocked','partition-size:boot','partition-size:recovery']}
queries['oem-show-partitions']=b'oem emmc_show_partitions'
queries['unlock-ability']=b'flashing get_unlock_ability'
p=argparse.ArgumentParser();p.add_argument('--query',choices=queries,default='version')
p.add_argument('--execute',action='store_true');p.add_argument('--log',type=Path,required=True)
a=p.parse_args();a.log.parent.mkdir(parents=True,exist_ok=True)
log=a.log.open('x',buffering=1)
def event(phase,**data):
    row=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),phase=phase,**data)
    line=json.dumps(row);log.write(line+'\n');log.flush();print(line,flush=True)

serial='DEVICE_SERIAL_REDACTED';dev=None;claimed=None
try:
    backend=usb.backend.libusb1.get_backend(find_library=lambda _: '/opt/homebrew/lib/libusb-1.0.dylib')
    if backend is None:raise RuntimeError('The existing Homebrew libusb backend is unavailable')
    event('discover',known_usb_ids=['0b05:601f (Android)', '0bb4:0c01 (observed fastboot)'],expected_serial=serial,execute=a.execute)
    for candidate in usb.core.find(find_all=True,backend=backend):
        if (candidate.idVendor,candidate.idProduct) not in {(0x0b05,0x601f),(0x0bb4,0x0c01)}:
            continue
        if candidate.serial_number==serial:
            if dev is not None:raise RuntimeError('Ambiguous serial; refusing')
            dev=candidate
    if dev is None:raise RuntimeError('Exact ASUS serial not found')
    cfg=dev.get_active_configuration()
    interfaces=[i for i in cfg if (i.bInterfaceClass,i.bInterfaceSubClass,i.bInterfaceProtocol)==(0xff,0x42,3)]
    event('descriptor',product_id=hex(dev.idProduct),interfaces=[dict(number=i.bInterfaceNumber,
          cls=i.bInterfaceClass,subclass=i.bInterfaceSubClass,protocol=i.bInterfaceProtocol) for i in cfg])
    if len(interfaces)!=1:raise RuntimeError('Exact device has no unique fastboot interface; no command sent')
    interface=interfaces[0]
    endpoints=[e for e in interface if usb.util.endpoint_type(e.bmAttributes)==usb.util.ENDPOINT_TYPE_BULK]
    ep_in=[e for e in endpoints if usb.util.endpoint_direction(e.bEndpointAddress)==usb.util.ENDPOINT_IN]
    ep_out=[e for e in endpoints if usb.util.endpoint_direction(e.bEndpointAddress)==usb.util.ENDPOINT_OUT]
    if len(ep_in)!=1 or len(ep_out)!=1:raise RuntimeError('Unexpected endpoint topology')
    if not a.execute:
        event('inspection_complete',command_sent=False);sys.exit(0)
    event('claim_start',interface=interface.bInterfaceNumber)
    usb.util.claim_interface(dev,interface.bInterfaceNumber);claimed=interface.bInterfaceNumber
    event('claim_complete')
    command=queries[a.query]
    event('query_write_start',command=command.decode())
    sent=ep_out[0].write(command,timeout=1500)
    event('query_write_complete',bytes=sent)
    if sent!=len(command):raise RuntimeError('Short USB write')
    for count in range(128 if a.query == 'oem-show-partitions' else 16):
        event('response_read_start',ordinal=count)
        response=bytes(ep_in[0].read(64,timeout=2500))
        event('response',prefix=response[:4].decode('ascii',errors='replace'),payload=response[4:].decode('utf8',errors='replace'),raw_hex=response.hex())
        if response[:4] in [b'OKAY',b'FAIL']:
            event('query_complete',success=response[:4]==b'OKAY');sys.exit(0 if response[:4]==b'OKAY' else 3)
        if response[:4]!=b'INFO':raise RuntimeError('Unexpected protocol reply; stopping without further traffic')
    raise RuntimeError('INFO reply limit reached')
except Exception as exc:
    event('error',type=type(exc).__name__,message=str(exc));sys.exit(2)
finally:
    if claimed is not None:
        try:usb.util.release_interface(dev,claimed);event('released')
        except Exception as exc:event('release_error',message=str(exc))
    if dev is not None:
        try:usb.util.dispose_resources(dev)
        except Exception as exc:event('dispose_error',message=str(exc))
    log.close()
