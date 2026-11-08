"""Validate final boot payload extents against the ARM64 header and DT reservations."""
import struct
from fdt import parse


def check_memory(raw_image, dt, ramdisk_length):
    assert len(raw_image) >= 64 and raw_image[56:60] == b'ARMd'
    text_offset, image_size, flags = struct.unpack_from('<3Q', raw_image, 8)
    assert text_offset == 0x80000 and image_size >= len(raw_image), 'Invalid ARM64 memory extent'
    assert 0 < ramdisk_length < 0x4e000000 - 0x44000200
    h, nodes, _ = parse(dt)
    reservations = []
    dynamic = []
    position = h[4]
    while True:
        assert position + 16 <= h[2], 'Unterminated FDT memory reservation table'
        start, length = struct.unpack_from('>QQ', dt, position)
        position += 16
        if not start and not length:
            break
        assert length and start + length <= 2**64
        reservations.append({'source': 'FDT memreserve', 'start': start, 'end': start + length})
    root = nodes.get('/reserved-memory', {})
    if root:
        assert root.get('ranges', b'') == b'', 'Reserved-memory address translation requires explicit handling'
        address_cells = struct.unpack('>I', root.get('#address-cells', nodes['']['#address-cells']))[0]
        size_cells = struct.unpack('>I', root.get('#size-cells', nodes['']['#size-cells']))[0]
        assert address_cells in (1, 2) and size_cells in (1, 2)
        stride = 4 * (address_cells + size_cells)
        for node, properties in nodes.items():
            if not node.startswith('/reserved-memory/'):
                continue
            if 'size' in properties and 'reg' not in properties:
                assert node == '/reserved-memory/consys-reserve-memory', 'Unreviewed dynamic reservation'
                assert properties == {'compatible': b'mediatek,consys-reserve-memory\0', 'no-map': b'', 'size': struct.pack('>Q', 0x200000), 'alignment': struct.pack('>Q', 0x200000)}, 'Changed dynamic reservation'
                # This pinned board node is allocated by memblock after ARM64
                # reserves Image and initrd; it does not specify a fixed range.
                dynamic.append({'source': node, 'size': 0x200000, 'alignment': 0x200000, 'placement': 'kernel memblock allocation after Image/initrd reservation', 'runtime_address_verified': False})
                continue
            data = properties.get('reg', b'')
            assert len(data) % stride == 0
            for offset in range(0, len(data), stride):
                start = int.from_bytes(data[offset:offset + 4 * address_cells], 'big')
                length = int.from_bytes(data[offset + 4 * address_cells:offset + stride], 'big')
                assert length and start + length <= 2**64
                reservations.append({'source': node, 'start': start, 'end': start + length})
    payloads = [
        {'source': 'ARM64 allocated Image', 'start': 0x40080000, 'end': 0x40080000 + image_size},
        {'source': 'MTK wrapped ramdisk', 'start': 0x44000000, 'end': 0x44000200 + ramdisk_length},
        {'source': 'DTB', 'start': 0x4e000000, 'end': 0x4e000000 + len(dt)},
    ]
    for index, payload in enumerate(payloads):
        for other in reservations + payloads[index + 1:]:
            assert payload['end'] <= other['start'] or other['end'] <= payload['start'], ('Overlapping boot memory', payload, other)
    return {'text_offset': text_offset, 'image_size': image_size, 'image_file_bytes': len(raw_image), 'image_flags': flags, 'payloads': payloads, 'reservations': reservations, 'dynamic_reservations': dynamic, 'overlaps': False}
