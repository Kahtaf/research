"""Container structure only; no extraction, rewriting, signature/trust assertion."""
import zipfile
from safeio import need, relative

def inspect_package(tree, path, limits):
    with tree.open(path) as f:
        with zipfile.ZipFile(f) as archive:
            entries = archive.infolist()
            need(0 < len(entries) <= 4096,'PACKAGE_PARTIAL',path)
            names = [entry.filename for entry in entries]
            need(len(set(names))==len(names),'PACKAGE_DUPLICATE',path)
            for entry in entries:
                relative(entry.filename.rstrip('/'))
                need(not entry.flag_bits & 1 and not (entry.external_attr>>16)&0o170000==0o120000,'PACKAGE_ENTRY',entry.filename)
                need(entry.header_offset+entry.compress_size <= limits['file_bytes'],'PACKAGE_SIZE',path)
            mandatory={'apex_manifest.pb','apex_pubkey','original_apex' if path.endswith('.capex') else 'apex_payload.img'}
            need(mandatory<=set(names),'PACKAGE_PARTIAL',path)
            return {'entries':[{'path':e.filename,'stored_bytes':e.compress_size,'uncompressed_bytes':e.file_size,'crc32':e.CRC} for e in entries],
                    'extracted':False,'signature_verified':False,'trust_qualified':False}
