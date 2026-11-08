#!/usr/bin/env python3
"""Compile exact source bodies with explicit host I/O stubs, never an Android boot."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from lk_contract import LK_DEFAULT,HEADER
sources=ROOT/'source';receipts=json.loads((ROOT/'evidence/source-receipts.json').read_text())['files'];extracted=[]

def body(path,signature):
    data=(sources/path).read_bytes();assert hashlib.sha256(data).hexdigest()==receipts[path]['sha256']
    text=data.decode();start=text.index(signature);end=text.index('\n}\n',start)+3;value=text[start:end]
    extracted.append({'source':path,'source_sha256':receipts[path]['sha256'],'first_line':text[:start].count('\n')+1,'last_line':text[:end].count('\n'),'extracted_sha256':hashlib.sha256(value.encode()).hexdigest()})
    return value

boot='aosp/system/fs/fs_mgr/libfstab/boot_config.cpp';fstab='aosp/system/fs/fs_mgr/libfstab/fstab.cpp';selinux='aosp/system/core/init/selinux.cpp'
s=r'''
#include <algorithm>
#include <cassert>
#include <cerrno>
#include <cstdlib>
#include <functional>
#include <iostream>
#include <map>
#include <set>
#include <string>
#include <string_view>
#include <vector>
std::string cmdline;
std::map<std::string,std::string> properties,bootconfig,dtfiles;
std::set<std::string> files;
int mock_access(const char* p,int) {return files.count(p)?0:-1;}
#define access mock_access
#define F_OK 0
#define FSTAB_CHECK assert
namespace android { namespace base {
std::string GetProperty(const std::string& k,const std::string& d) {return properties.count(k)?properties.at(k):d;}
bool ReadFileToString(const std::string& k,std::string* out) {if(!dtfiles.count(k))return false;*out=dtfiles.at(k);return true;}
std::vector<std::string> Split(const std::string& s,const std::string& sep) {std::vector<std::string> r;size_t p=0,q;do{q=s.find(sep,p);r.push_back(s.substr(p,q-p));p=q+sep.size();}while(q!=s.npos);return r;}
bool ConsumeSuffix(std::string_view* v,std::string_view suffix) {if(v->substr(v->size()-suffix.size())!=suffix)return false;v->remove_suffix(suffix.size());return true;}
} namespace fs_mgr {
'''
s+=body(boot,'void ImportKernelCmdlineFromString(')+body(boot,'bool GetKernelCmdlineFromString(')
s+=r'''
bool GetKernelCmdline(const std::string& k,std::string* out) {return GetKernelCmdlineFromString(cmdline,k,out);}
void ImportKernelCmdline(const std::function<void(std::string,std::string)>& fn) {ImportKernelCmdlineFromString(cmdline,fn);}
bool GetBootconfig(const std::string& k,std::string* out) {if(!bootconfig.count(k))return false;*out=bootconfig.at(k);return true;}
std::string GetAndroidDtDir() {return "/proc/device-tree/firmware/android/";}
} }
bool is_dt_compatible() {return false;}
'''
s+=body(boot,'bool fs_mgr_get_boot_config(')
s+=r'''
bool InRecovery() {return false;}
std::string GetRecoveryFstabPath() {return "";}
'''
s+=body(fstab,'std::string GetFstabPath()')
s+=r'''
namespace android { namespace fs_mgr {
using base::Split;
bool ReadDtFile(const std::string& k,std::string* out) {return base::ReadFileToString(k,out);}
struct Fstab {};
bool ReadDefaultFstab(Fstab*) {return false;}
std::set<std::string> ExtraBootDevices(const Fstab&) {return {};}
'''
s+=body(fstab,'std::set<std::string> GetBootDevices()')+'\n}}\n'
s+='enum EnforcingStatus { SELINUX_PERMISSIVE, SELINUX_ENFORCING };\n'
s+=body(selinux,'EnforcingStatus StatusFromProperty()')+body(selinux,'bool IsEnforcing()')
s+=r'''
#define __init
int selinux_enforcing;
int kstrtoul(const char* v,unsigned base,unsigned long* out) {char* e;errno=0;*out=strtoul(v,&e,base);return errno||*e?-1:0;}
'''
s+=body('kernel/security/selinux/hooks.c','static int __init enforcing_setup(')
s+='\nint main() {\ncmdline='+json.dumps((LK_DEFAULT+b' '+HEADER).decode())+';\n'
s+=r'''
std::string v;
assert(fs_mgr_get_boot_config("hardware",&v) && v=="mt8163");
assert(!fs_mgr_get_boot_config("fstab_suffix",&v));
files.insert("/fstab.mt8163");assert(GetFstabPath()=="/fstab.mt8163");
files.clear();files.insert("/first_stage_ramdisk/system/etc/fstab.mt8163");assert(GetFstabPath()=="/first_stage_ramdisk/system/etc/fstab.mt8163");
assert(android::fs_mgr::GetBootDevices()==std::set<std::string>{"soc/11230000.mmc"});
assert(StatusFromProperty()==SELINUX_ENFORCING && IsEnforcing());
assert(android::fs_mgr::GetKernelCmdline("enforcing",&v) && v=="1");
selinux_enforcing=0;assert(enforcing_setup(v.data())==1 && selinux_enforcing==1);
assert(android::fs_mgr::GetKernelCmdline("bootopt",&v) && v=="64S3,32N2,64N2");
assert(android::fs_mgr::GetKernelCmdline("build_version",&v) && v=="3");
cmdline+=" androidboot.selinux=permissive";
assert(StatusFromProperty()==SELINUX_PERMISSIVE);
assert(IsEnforcing()==!ALLOW_PERMISSIVE_SELINUX);
cmdline="androidboot.hardware=wrong";assert(GetFstabPath().empty());
assert(android::fs_mgr::GetBootDevices().empty());
std::cout<<"PASS 14 source-body checks; ALLOW_PERMISSIVE_SELINUX="<<ALLOW_PERMISSIVE_SELINUX<<"; I/O and platform dependencies are host stubs\n";
}
'''
out=ROOT/'tests/generated';out.mkdir(exist_ok=True);cpp=out/'sdk37-source-bodies.cpp';cpp.write_text(s)
results=[]
for flag in (0,1):
    binary=out/('sdk37-source-test-'+str(flag))
    cmd=['/usr/bin/clang++','-std=c++17','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-omit-frame-pointer','-DALLOW_PERMISSIVE_SELINUX='+str(flag),str(cpp),'-o',str(binary)]
    p=subprocess.run(cmd,text=True,capture_output=True);assert p.returncode==0,p.stderr
    p=subprocess.run([str(binary)],text=True,capture_output=True);assert p.returncode==0,p.stderr
    print(p.stdout.strip());results.append({'allow_permissive':flag,'exit_code':p.returncode,'stdout':p.stdout,'compiler_command':cmd})
(ROOT/'evidence/source-body-tests.json').write_text(json.dumps({'method':'Exact source bodies; host filesystem/property/bootconfig/DT and platform I/O stubs; not Android runtime','extracted':extracted,'results':results},indent=2)+'\n')
