from pathlib import Path
import struct,subprocess

def analyze(path, level):
    p=subprocess.run(['aarch64-linux-gnu-nm','-an',str(path)],capture_output=True,text=True,check=True)
    symbols={l.split()[2]:int(l.split()[0],16) for l in p.stdout.splitlines() if len(l.split())==3}
    data=path.read_bytes()
    assert data[:6]==b'\x7fELF\x02\x01'
    phoff=struct.unpack_from('<Q',data,32)[0]; ents,num=struct.unpack_from('<HH',data,54)
    loads=[struct.unpack_from('<IIQQQQQQ',data,phoff+i*ents) for i in range(num)]
    def pointer(addr):
        seg=next(x for x in loads if x[0]==1 and x[3]<=addr and addr+8<=x[3]+x[5])
        return struct.unpack_from('<Q',data,seg[2]+addr-seg[3])[0]
    rows=[]
    specs=[('mtk_wdt_driver_init',str(level),level,level+1),('of_platform_default_populate_init','3s',3,4),('watchdog_init','4s',4,5)]
    for name,suffix,lo,hi in specs:
        sym='__initcall_'+name+suffix
        addr=symbols[sym]; target=pointer(addr)
        assert target==symbols[name]
        assert symbols['__initcall'+str(lo)+'_start']<=addr<symbols['__initcall'+str(hi)+'_start']
        rows.append(dict(initcall=sym,entry=hex(addr),actual_pointer=hex(target),target=name,level=suffix))
    wdt=[s for s in symbols if s.startswith('__initcall_mtk_wdt_driver_init')]
    assert wdt==['__initcall_mtk_wdt_driver_init'+str(level)],wdt
    early=['serial8250_early_in','serial8250_early_out','early_serial8250_setup','early_serial8250_write','__earlycon_uart8250','__earlycon_uart']
    assert not any(any(n==s or n.startswith(s+'.') for s in early) for n in symbols)
    assert all(s in symbols for s in ['serial8250_register_8250_port','early_memremap','mtk_wdt_probe','mtk_wdt_stop'])
    assert any('mtk8250' in n for n in symbols)
    if level==3:assert symbols[wdt[0]]<symbols['__initcall_of_platform_default_populate_init3s']<symbols['__initcall_watchdog_init4s']
    return dict(elf=str(path),method='nm symbols plus actual little-endian 64-bit pointers read through ELF PT_LOAD mappings',entries=rows,watchdog_entries=wdt,no_late_duplicate=level==3,early_uart_absent=early,normal_uart_preserved=True,scope='Compiled registration order only; runtime probe time and reset cause unproved')
