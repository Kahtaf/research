#!/usr/bin/env python3
"""Optional state for the single marked ASUS Alpine SD directory."""
from pathlib import Path
import argparse, ctypes, hashlib, os, shutil, socket, stat, subprocess, time

MOUNT=Path('/mnt/alpine-sd')
DEVICE=Path('/dev/asus-alpine-sd')
STATE=MOUNT/'2026-11-08-asus-alpine'
PRIVATE=STATE/'private'
DATA=STATE/'service-data'
TARGET=Path('/var/lib/asus-dashboard')
RUN=Path('/run/asus-alpine')
RAM_KEY=Path('/etc/ssh/ssh_host_ed25519_key')
KEY_NAME=RAM_KEY.name
DASHBOARD=Path('/usr/local/bin/asus-dashboard.py')
MOUNT_DATA=b'uid=0,gid=0,fmask=0177,dmask=0077'
MOUNT_FLAGS=2|4|8  # nosuid,nodev,noexec; state is data, not a program source.

def require(condition,message):
    if not condition:raise SystemExit('SD_STATE_REFUSED '+message)

def regular(path):
    require(stat.S_ISREG(path.lstat().st_mode),str(path)+' is not a regular file')

def directory(path):
    require(stat.S_ISDIR(path.lstat().st_mode),str(path)+' is not a directory')

def markers():
    directory(STATE)
    for name,value in [('ALPINE.ID',b'asus-alpine-stock-kernel-v1\n'),('PERSISTENCE.ENABLE',b'asus-alpine-state-v1\n')]:
        path=STATE/name;regular(path)
        require(path.read_bytes()==value,'wrong '+name)

def sd_mount():
    require(os.geteuid()==0,'root required')
    require(Path('/sys/class/block/mmcblk1/device/type').read_text().strip()=='SD','mmcblk1 is not SD')
    major,minor=map(int,Path('/sys/class/block/mmcblk1p1/dev').read_text().strip().split(':'))
    dev=DEVICE.stat()
    require(stat.S_ISBLK(dev.st_mode) and dev.st_rdev==os.makedev(major,minor),'wrong SD block node')
    mounts=[line.split() for line in Path('/proc/mounts').read_text().splitlines()]
    entries=[entry for entry in mounts if entry[1]==str(MOUNT)]
    require(len(entries)==1,'SD mount count differs')
    entry=entries[0]
    require(entry[0]==str(DEVICE) and entry[2]=='vfat','wrong mounted SD source/type')
    mounted=MOUNT.stat()
    require(mounted.st_dev==dev.st_rdev,'mounted SD device differs')
    require(mounted.st_uid==0 and mounted.st_gid==0,'SD mount owner is not root:root')
    markers()
    return set(entry[3].split(','))

def correct_rw(options):
    return {'rw','nosuid','nodev','noexec','fmask=0177','dmask=0077'}<=options

def reopen_rw():
    options=sd_mount()
    if correct_rw(options):return
    require(not os.path.ismount(TARGET),'existing dashboard bind needs the same protected SD options')
    libc=ctypes.CDLL(None,use_errno=True)
    libc.umount2.argtypes=[ctypes.c_char_p,ctypes.c_int]
    libc.mount.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_ulong,ctypes.c_void_p]
    require(libc.umount2(os.fsencode(MOUNT),0)==0,'cannot unmount SD before protected reopen')
    rc=libc.mount(os.fsencode(DEVICE),os.fsencode(MOUNT),b'vfat',MOUNT_FLAGS,MOUNT_DATA)
    if rc:
        saved=ctypes.get_errno()
        libc.mount(os.fsencode(DEVICE),os.fsencode(MOUNT),b'vfat',MOUNT_FLAGS|1,MOUNT_DATA)
        raise SystemExit('SD_STATE_REFUSED rw mount failed errno='+str(saved)+'; attempted read-only restoration')
    require(correct_rw(sd_mount()),'protected writable SD options not applied')

def bind_data():
    DATA.mkdir(mode=0o700,exist_ok=True);directory(DATA)
    TARGET.mkdir(parents=True,mode=0o700,exist_ok=True);directory(TARGET)
    if os.path.ismount(TARGET):
        require(os.path.samefile(DATA,TARGET),'unexpected dashboard bind target')
        return
    libc=ctypes.CDLL(None,use_errno=True)
    libc.mount.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_ulong,ctypes.c_void_p]
    require(libc.mount(os.fsencode(DATA),os.fsencode(TARGET),None,4096,None)==0,'dashboard bind failed')
    require(os.path.samefile(DATA,TARGET),'dashboard bind is not the selected state directory')

def key_pair(private):
    public=private.with_name(private.name+'.pub')
    regular(private);regular(public)
    key=subprocess.check_output(['/usr/bin/ssh-keygen','-y','-P','','-f',str(private)],stdin=subprocess.DEVNULL,text=True,timeout=5).split()[:2]
    require(len(key)==2 and key[0]=='ssh-ed25519','unexpected SSH host key type')
    require(public.read_text().split()[:2]==key,'SSH host public/private mismatch')
    return public

def hydrate_key():
    PRIVATE.mkdir(mode=0o700,exist_ok=True);directory(PRIVATE)
    stored=PRIVATE/KEY_NAME;public=stored.with_name(stored.name+'.pub')
    require(stored.exists()==public.exists(),'partial stored SSH host key pair')
    if not stored.exists():
        print('SD_SSH_HOST_KEY_NOT_YET_SAVED')
        return
    key_pair(stored)
    RAM_KEY.parent.mkdir(parents=True,exist_ok=True)
    for source,destination,mode in [(stored,RAM_KEY,0o600),(public,RAM_KEY.with_name(KEY_NAME+'.pub'),0o644)]:
        if destination.exists():
            regular(destination)
            require(destination.read_bytes()==source.read_bytes(),'RAM/stored SSH host key mismatch')
        else:shutil.copyfile(source,destination)
        os.chmod(destination,mode)
    print('SD_SSH_HOST_KEY_RESTORED')

def prepare():
    require(Path('/etc/asus-alpine/enable-persistence').is_file(),'RAM persistence gate absent')
    reopen_rw();bind_data();hydrate_key()
    RUN.mkdir(parents=True,exist_ok=True)
    (RUN/'state.ready').write_text('asus-alpine-state-v1\n')
    print('SD_STATE_PREPARED')

def prepared():
    require(correct_rw(sd_mount()),'SD state is not protected and writable')
    require((RUN/'state.ready').read_text()=='asus-alpine-state-v1\n','state preparation absent')
    require(os.path.ismount(TARGET) and os.path.samefile(DATA,TARGET),'dashboard state bind absent')

def save_host_key():
    prepared();key_pair(RAM_KEY)
    for source in [RAM_KEY,RAM_KEY.with_name(KEY_NAME+'.pub')]:
        destination=PRIVATE/source.name
        if destination.exists():
            regular(destination)
            require(destination.read_bytes()==source.read_bytes(),'refuse to overwrite stored SSH host key')
        else:
            fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            with os.fdopen(fd,'wb') as output:
                output.write(source.read_bytes());output.flush();os.fsync(output.fileno())
        require(hashlib.sha256(destination.read_bytes()).digest()==hashlib.sha256(source.read_bytes()).digest(),'stored SSH host key hash differs')
    os.sync()
    print('SD_SSH_HOST_KEY_SAVED_VERIFIED')

def owned_dashboard(pid):
    try:
        args=Path('/proc',str(pid),'cmdline').read_bytes().split(b'\0')
        return args[:2]==[b'/usr/bin/python3',os.fsencode(DASHBOARD)] and Path('/proc',str(pid),'exe').resolve()==Path('/usr/bin/python3').resolve()
    except FileNotFoundError:return False

def wait_dashboard(pid):
    for attempt in range(50):
        require(owned_dashboard(pid),'dashboard exited; inspect RAM log')
        try:
            with socket.create_connection(('127.0.0.1',8080),timeout=.2):return
        except OSError:time.sleep(.1)
    raise SystemExit('SD_STATE_REFUSED dashboard did not listen within five seconds')

def start_dashboard():
    prepared();regular(DASHBOARD)
    pidfile=RUN/'dashboard.pid'
    if pidfile.exists():
        pid=int(pidfile.read_text().strip())
        if Path('/proc',str(pid)).exists():
            require(owned_dashboard(pid),'dashboard PID belongs to another process')
            wait_dashboard(pid);print('SD_DASHBOARD_ALREADY_RUNNING');return
    with (RUN/'dashboard.log').open('ab') as log:
        process=subprocess.Popen(['/usr/bin/python3',str(DASHBOARD)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    pidfile.write_text(str(process.pid)+'\n')
    wait_dashboard(process.pid)
    print('SD_DASHBOARD_STARTED loopback=127.0.0.1:8080')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['prepare','save-host-key','start-dashboard'])
    action=parser.parse_args().operation
    {'prepare':prepare,'save-host-key':save_host_key,'start-dashboard':start_dashboard}[action]()
if __name__=='__main__':main()
