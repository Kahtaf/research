#!/usr/bin/env python3
"""Bounded official-output selection/copy; default plan does not inspect AOSP/out."""
import argparse
from collections import deque
import fnmatch
import json
import os
from pathlib import Path
import posixpath
import re
import stat
import sys

from safeio import Tree, Refusal, exclusive_file, fingerprint, load_bytes, need, permitted, relative, sha, write_json
from gates import Guard, terminal
from graph import Graph
from elf import inspect as elf_inspect

HERE = Path(__file__).resolve().parent
PREFIX = Path('/srv/android/asus-official-runtime-capture')
PRODUCT = 'out/target/product/p00a/'

class Selection:
    def __init__(self, profile, selector, work, probe=None):
        self.profile, self.selector, self.work = profile, selector, Path(work)
        self.trees = {name:Tree(profile[name]) for name in ('aosp','kernel','kit','logs')}
        self.rows = {}
        self.total = 0
        self.graph = None
        self.probe = probe
        self.links = []
        self.edges = {}
        self.deps = []
        self.missing = []
        self.inventories = {}
        self.journal = (self.work/'journal.jsonl').open('x')
        self.journal_bytes=0

    def event(self, value):
        text=json.dumps(value,sort_keys=True)+'\n'
        self.journal_bytes+=len(text.encode())
        need(self.journal_bytes<=64*1024*1024,'JOURNAL_SIZE','bounded journal exhausted')
        self.journal.write(text)
        self.journal.flush()
        os.fsync(self.journal.fileno())

    def add(self, root, path, group, hash_only=False):
        permitted(path)
        key = root + ':' + path
        if key in self.rows:
            self.rows[key]['groups'] = sorted(set(self.rows[key]['groups'])|{group})
            self.rows[key]['hash_only'] &= hash_only
            return self.rows[key]
        need(len(self.rows) < self.profile['limits']['files'], 'COUNT', key)
        tree = self.trees[root]
        try:
            s = tree.stat(path)
        except FileNotFoundError:
            self.missing.append({'root':root,'path':path,'required':True})
            self.event({'status':'MISSING','root':root,'path':path})
            raise Refusal('MISSING',key)
        row = {'root':root,'path':path,'groups':[group], 'hash_only':hash_only}
        if stat.S_ISLNK(s.st_mode):
            need(root == 'aosp' and (path.startswith(PRODUCT+'system/') or any(path.startswith(prefix) for prefix in self.selector.get('relative_symlink_prefixes',[]))), 'SYMLINK_UNSUPPORTED', key)
            target = tree.link(path)
            need(len(target) <= 4096 and '\x00' not in target, 'SYMLINK_UNSUPPORTED', path)
            row.update(kind='symlink',target=target,identity=fingerprint(s),bytes=len(target.encode()),sha256=sha(target.encode()))
            if target.startswith('/apex/') and path.startswith(PRODUCT+'system/'):
                m = re.fullmatch(r'/apex/(com\.android\.[a-z0-9.]+)/([A-Za-z0-9_+.,/\-]+)',target)
                need(m is not None and m[1] in self.selector['packages'], 'SYMLINK_UNSUPPORTED', target)
                permitted(m[2])
                row['resolution'] = {'kind':'signed-package-reference','package':m[1],'member':m[2], 'extracted':False}
            else:
                need(not target.startswith('/'), 'SYMLINK_UNSUPPORTED', target)
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path),target))
                permitted(resolved)
                need(resolved.startswith(PRODUCT+'system/') if path.startswith(PRODUCT+'system/') else not resolved.startswith(PRODUCT), 'SYMLINK_ESCAPE', path)
                row['resolution'] = {'kind':'installed-relative','path':resolved}
            self.links.append(key)
        else:
            need(stat.S_ISREG(s.st_mode), 'TYPE', key)
            maximum = self.profile['limits']['log_bytes'] if group == 'terminal-log' else self.profile['limits']['file_bytes']
            row.update(kind='file',**tree.digest(path,maximum,allow_empty=hash_only or '_contexts' in Path(path).name))
        self.total += row['bytes']
        need(self.total <= self.profile['limits']['total_bytes'], 'TOTAL_SIZE', key)
        self.rows[key] = row
        self.event({'status':'SELECTED',**row})
        return row

    def scan(self, root, path):
        paths = list(self.trees[root].walk(path,self.profile['limits']['directory_entries']))
        key = root+':'+path
        if key in self.inventories:
            need(self.inventories[key]==paths,'DRIFT',key)
        self.inventories[key] = paths
        return paths

    def package_path(self, name):
        paths=self.selector['packages'][name]
        if isinstance(paths,str):
            return paths
        present=[]
        for path in paths:
            try:
                self.trees['aosp'].stat(PRODUCT+path)
            except FileNotFoundError:
                continue
            present.append(path)
        need(len(present)==1,'PACKAGE_INSTALL_SELECTION','exactly one official installed package required: '+name)
        return present[0]

    def discover(self):
        for path in self.selector['required']:
            self.add('aosp',PRODUCT+path,'official-installed')
        for part in ('system','system/system_ext','system/product'):
            path=PRODUCT+part+'/build.prop'
            if 'aosp:'+path in self.rows:
                data=self.trees['aosp'].read(path,self.profile['limits']['file_bytes'])
                need(data.endswith(b'\n') and b'\0' not in data,'PROPERTY_PARTIAL',path)
                pairs=[line.split('=',1) for line in data.decode().splitlines() if '=' in line and not line.startswith('#')]
                need(any(key.endswith('.build.version.sdk') and value=='37' for key,value in pairs),'PROPERTY_SDK',path)
        for item in self.selector['trees']:
            path = PRODUCT+item['path']
            try:
                entries = self.scan('aosp',path)
            except FileNotFoundError:
                self.missing.append({'root':'aosp','path':path,'required':item['required']})
                self.event({'status':'MISSING','root':'aosp','path':path,'required':item['required']})
                need(not item['required'],'MISSING',path)
                continue
            need(entries or not item['required'],'PARTIAL',path)
            for path in entries:
                self.add('aosp',path,item['group'])
        for pattern in self.selector['required_patterns']:
            need(any(fnmatch.fnmatch(row['path'],PRODUCT+pattern) for row in self.rows.values()),'PARTIAL',pattern)
        for path in self.selector['source_files']:
            self.add('aosp',path,'generator-source')
        self.resolve_links()
        for row in self.rows.values():
            if row['path'].endswith('/precompiled_sepolicy'):
                import struct
                data=self.trees[row['root']].read(row['path'],self.profile['limits']['file_bytes'])
                need(len(data)>=64 and data[:8]==struct.pack('<II',0xf97cff8c,8) and data[8:16]==b'SE Linux','POLICY_PARTIAL',row['path'])
                version=struct.unpack_from('<I',data,16)[0]
                need(version==self.selector.get('policy_version',30),'POLICY_VERSION',row['path'])
                row['policy_header']={'version':version,'not_recompiled_by_capture':True}

    def resolve_links(self):
        for key in self.links:
            row = self.rows[key]
            resolution = row['resolution']
            if resolution['kind'] == 'installed-relative':
                seen = {key}
                current = row
                for _ in range(8):
                    rel = current['resolution']['path']
                    nextkey = 'aosp:'+rel
                    need(nextkey not in seen,'SYMLINK_CYCLE',row['path'])
                    seen.add(nextkey)
                    current = self.add('aosp',rel,'symlink-target',row['hash_only'])
                    if current['kind'] == 'file':
                        row['resolved_file'] = rel
                        break
                    if current['resolution']['kind'] != 'installed-relative':
                        row['package_reference'] = current['resolution']
                        break
                else:
                    need(False,'SYMLINK_DEPTH',row['path'])
            else:
                package = resolution['package']
                self.add('aosp',PRODUCT+self.package_path(package),'official-signed-package')

    def graph_paths(self):
        aosp = self.trees['aosp']
        paths = []
        for parent,pattern in self.selector['graphs']:
            fd = aosp.parent(parent+'/entry')
            try:
                paths += [parent+'/'+name for name in sorted(os.listdir(fd)) if fnmatch.fnmatch(name,pattern)]
            finally:
                os.close(fd)
        need(paths and len(paths) <= 128,'GRAPH_INVENTORY','no graph or too many graphs')
        return sorted(set(paths))

    def provenance(self):
        self.graph = Graph(self.trees['aosp'],self.graph_paths(),self.work/'graph-index.sqlite',self.profile['limits'])
        # Record the actual native install edges for every installed file. A symlink
        # is never replaced with an intermediate ELF or an extracted-looking host path.
        installed = [r['path'] for r in self.rows.values() if r['root']=='aosp' and r['path'].startswith(PRODUCT) and r['kind']=='file']
        installed_links = [r['path'] for r in self.rows.values() if r['root']=='aosp' and r['path'].startswith(PRODUCT) and r['kind']=='symlink']
        queue = deque((p,0) for p in installed+installed_links)
        while queue:
            path,depth = queue.popleft()
            if path in self.edges:
                continue
            need(depth < 30 and len(self.edges) < self.profile['limits']['edges'],'GRAPH_DEPTH',path)
            edge = self.graph.edge(path)
            need(edge['rule'] != 'phony','UNKNOWN_SELECTED_OUTPUT',path)
            self.edges[path] = edge
            if path in installed_links:
                import shlex
                command_lines=[line.split('=',1)[1].strip() for line in edge['expanded_rule'].splitlines() if line.strip().startswith('command =')]
                target=self.rows['aosp:'+path]['target']
                need(len(command_lines)==1 and target in shlex.split(command_lines[0]),'SYMLINK_PROVENANCE',path)
                edge['selected_symlink_target']=target
            is_package = path.endswith(('.apex','.capex','.apex.unsigned'))
            is_metadata = any(token in path for token in ('/selinux/','/sepolicy/','/vintf/','/linkerconfig/','build.prop','apexkeys.txt','api_fingerprint','product_config'))
            deps = edge['dependencies']
            real = [d['path'] for d in deps if d['kind']=='explicit' and '/' in d['path']]
            # Ordinary installation must identify one exact source (generated,
            # prebuilt, or selected signed package); equality is checked below.
            if path in installed:
                need(len(real)==1,'INSTALL_SOURCE',path)
                source = permitted(real[0])
                row = self.add('aosp',source,'installed-source',True)
                need(row['kind']=='file' and row['sha256']==self.rows['aosp:'+path]['sha256'],'INSTALL_BYTES',path)
                if self.graph.has_edge(source):
                    queue.append((source,depth+1))
                else:
                    edge['source_leaf'] = source
            for dep in deps:
                name = dep['path']
                if dep['kind'] in {'order_only','validation'}:
                    dep['disposition'] = 'ordering-only-not-payload'
                    continue
                if '/' not in name:
                    need(self.graph.has_edge(name),'GRAPH_PSEUDO_UNKNOWN',name)
                    pseudo = self.graph.edge(name)
                    need(pseudo['rule']=='phony','GRAPH_PSEUDO_UNKNOWN',name)
                    dep['disposition'] = 'phony-graph-token'
                    # Host tool phony edges may select a real built executable.
                    for tool in pseudo['dependencies']:
                        if tool['path'].startswith('out/host/'):
                            self.add('aosp',tool['path'],'generator-tool',True)
                    continue
                try:
                    permitted(name)
                except Refusal:
                    dep['disposition'] = 'excluded-private-or-image-path-never-opened'
                    continue
                if is_metadata or is_package:
                    row = self.add('aosp',name,'compiled-generation-dependency',not name.endswith(('.cil','.prop','.json','.txt','.xml','.pb','_contexts','.avbpubkey','.x509.pem','.py','.go','.bp','.mk','.rc','.te')))
                    dep['disposition'] = 'hash-bound-file'
                    if self.graph.has_edge(name) and (is_metadata or name.endswith(('.apex','.capex','.apex.unsigned'))):
                        queue.append((name,depth+1))
                else:
                    # Native compiler dependency closure is outside this capture;
                    # keep exact command/input paths and capture installed ELF deps.
                    dep['disposition'] = 'native-build-evidence-only'
                    if name in real and '/unstripped/' in name and self.graph.has_edge(name):
                        self.add('aosp',name,'native-selected-compile-evidence',True)
                        queue.append((name,depth+1))
        for path,origin in self.selector.get('source_side_effects',{}).items():
            data=self.trees['aosp'].read(origin['source'],self.profile['limits']['file_bytes'])
            need(origin['literal'].encode() in data and 'aosp:'+origin['source'] in self.rows,'SOURCE_GENERATION',path)
        for label,path in self.selector.get('generation_files',{}).items():
            need('aosp:'+path in self.rows,'GENERATION_BOUNDARY',label+': '+path)
        for label,path in self.selector['generation_outputs'].items():
            need(path in self.edges,'GENERATION_BOUNDARY',label+': '+path)
        runtime = self.edges[PRODUCT+'system/apex/com.android.runtime.apex']
        selected = [d['path'] for d in runtime['dependencies'] if d['kind']=='explicit']
        need(selected == [self.selector['runtime_signed_source']], 'RUNTIME_SOURCE_EDGE', 'selected signed package edge changed; separately review exact future source')
        # A variant label is recorded verbatim; no sanitizer configuration inferred.
        self.resolve_links()
        for row in self.rows.values():
            if row['root']=='aosp' and row['path'].startswith(PRODUCT+'system/apex/') and row['path'].endswith(('.apex','.capex')):
                from packages import inspect_package
                row['package_structure']=inspect_package(self.trees['aosp'],row['path'],self.profile['limits'])

    def elf_dependencies(self):
        candidates = {}
        for directory in self.selector['library_dirs']:
            try:
                paths = self.scan('aosp',PRODUCT+directory)
            except FileNotFoundError:
                self.missing.append({'root':'aosp','path':PRODUCT+directory,'required':False})
                continue
            for path in paths:
                if path.endswith('.so'):
                    candidates.setdefault(Path(path).name,[]).append(path)
        queue = deque(PRODUCT+path for path in self.selector['elf_roots'])
        seen = set()
        def parse(path):
            row = self.add('aosp',path,'elf-dependency')
            if row['kind']=='symlink':
                self.resolve_links()
                if 'resolved_file' not in row:
                    return None,row
                path = row['resolved_file']
                row = self.rows['aosp:'+path]
            data = self.trees['aosp'].read(path,self.profile['limits']['file_bytes'])
            need(sha(data)==row['sha256'],'DRIFT',path)
            row['elf'] = elf_inspect(data)
            return row['elf'],row
        while queue:
            path = queue.popleft()
            if path in seen:
                continue
            seen.add(path)
            info,row = parse(path)
            if info is None:
                need(path.removeprefix(PRODUCT) not in self.selector['elf_bits'],'ELF_ARCH','mandatory architecture cannot be supplied by an unextracted package link')
                continue
            expected = self.selector['elf_bits'].get(path.removeprefix(PRODUCT))
            need(expected is None or info['bits']==expected,'ELF_ARCH',path)
            for needed in info['dt_needed']:
                matches = []
                for candidate in sorted(candidates.get(needed,[])):
                    parsed,item = parse(candidate)
                    if parsed is None:
                        matches.append({'path':candidate,'bits':None,'required_bits':info['bits'],'package_reference':item.get('package_reference',item['resolution']),'payload_verified':False})
                    elif parsed['bits']==info['bits']:
                        matches.append({'path':candidate,'bits':parsed['bits'],'machine':parsed['machine'],'sha256':item['sha256']})
                        queue.append(candidate)
                if not matches:
                    package = self.selector['package_libraries'].get(needed)
                    need(package is not None and package in self.selector['packages'],'MISSING_ELF_DEPENDENCY',path+':'+needed)
                    self.add('aosp',PRODUCT+self.package_path(package),'dependency-signed-package')
                    matches = [{'package':package,'bits':None,'required_bits':info['bits'],'payload_verified':False,'path':None}]
                self.deps.append({'consumer':path,'bits':info['bits'],'dt_needed':needed,'candidates':matches,'loader_resolution_claimed':False})
        self.resolve_links()

    def recheck(self):
        # Full final source recheck, including metadata, receipts, symlinks,
        # graph inventory, every installed and generation dependency, and logs.
        for tree in self.trees.values():
            tree.check_root()
        for key,row in self.rows.items():
            tree = self.trees[row['root']]
            if row['kind']=='symlink':
                need(row['identity']==fingerprint(tree.stat(row['path'])) and row['target']==tree.link(row['path']),'DRIFT',key)
            else:
                maximum = self.profile['limits']['log_bytes'] if 'terminal-log' in row['groups'] else self.profile['limits']['file_bytes']
                now = tree.digest(row['path'],maximum,allow_empty=row['hash_only'] or '_contexts' in Path(row['path']).name)
                need(all(now[k]==row[k] for k in now),'DRIFT',key)
        for key,paths in self.inventories.items():
            root,path=key.split(':',1)
            need(list(self.trees[root].walk(path,self.profile['limits']['directory_entries']))==paths,'DRIFT',key)
        for missing in self.missing:
            try:
                self.trees[missing['root']].stat(missing['path'])
            except FileNotFoundError:
                pass
            else:
                need(False,'DRIFT','previously missing optional path appeared: '+missing['path'])
        need(self.graph_paths()==self.graph.paths,'DRIFT','native graph inventory')
        self.graph.recheck()

    def selected(self):
        return {'schema':1,'kind':'exact-official-runtime-selection','profile_sha256':sha(json.dumps(self.profile,sort_keys=True).encode()),
                'selector_sha256':sha(json.dumps(self.selector,sort_keys=True).encode()),
                'binding':self.binding,'files':sorted(self.rows.values(),key=lambda r:(r['root'],r['path'])),
                'missing':self.missing,'directory_inventories':self.inventories,'graph_pins':self.graph.pins,'edges':self.edges,
                'graph_evidence':self.graph.records,'elf_dependencies':self.deps,
                'selected_bytes':self.total,'apex_payloads_extracted':False,'runtime_ready':False,'physical_GO':False}

    def copy(self, selected, destination, after_copy=None):
        dst = Tree(destination)
        receipts = []
        try:
            for row in selected['files']:
                if row['kind']=='symlink':
                    # Metadata only: never create absolute /apex or dangling host
                    # symlinks in a snapshot. Future worker must extract packages.
                    target=self.trees[row['root']].link(row['path'])
                    need(target==row['target'],'DRIFT',row['path'])
                    receipts.append({'root':row['root'],'path':row['path'],'kind':'symlink-metadata-only','target':target,'before':row['sha256'],'copy':sha(target.encode()),'after':sha(self.trees[row['root']].link(row['path']).encode())})
                    continue
                if row['hash_only']:
                    continue
                src = self.trees[row['root']]
                before = src.digest(row['path'],self.profile['limits']['file_bytes'],allow_empty='_contexts' in Path(row['path']).name)
                need(all(before[k]==row[k] for k in before),'DRIFT',row['path'])
                outpath = 'files/'+row['root']+'/'+row['path']
                h, count = __import__('hashlib').sha256(), 0
                with src.open(row['path']) as inf, exclusive_file(dst,outpath) as outf:
                    need(fingerprint(os.fstat(inf.fileno()))==row['identity'],'DRIFT',row['path'])
                    for block in iter(lambda:inf.read(1024*1024),b''):
                        count += len(block)
                        need(count<=row['bytes'],'COPY_SIZE',row['path'])
                        outf.write(block)
                        h.update(block)
                    outf.flush()
                    os.fsync(outf.fileno())
                copied = dst.digest(outpath,self.profile['limits']['file_bytes'],allow_empty='_contexts' in Path(row['path']).name)
                after = src.digest(row['path'],self.profile['limits']['file_bytes'],allow_empty='_contexts' in Path(row['path']).name)
                need(before==after and copied['sha256']==before['sha256']==h.hexdigest() and copied['bytes']==count==before['bytes'],'COPY_DRIFT',row['path'])
                receipt = {'root':row['root'],'path':row['path'],'bytes':count,'before':before['sha256'],'copy':copied['sha256'],'after':after['sha256']}
                receipts.append(receipt)
                self.event({'status':'COPIED',**receipt})
                if after_copy:
                    after_copy(row)
            self.recheck()
            return receipts
        finally:
            dst.close()

    def close(self):
        if self.graph:
            self.graph.close()
        self.journal.close()
        for tree in self.trees.values():
            tree.close()

def validate_contract(profile, selector):
    need(profile['schema']==1 and selector['schema']==1,'SCHEMA','unsupported profile/selector')
    need(profile['lock']=='/srv/android/asus-device-product/logs/full-product-build.lock','LOCK_PATH','must use original shared lock')
    need(profile['aosp']=='/srv/android/lineage24' and profile['product_out']==profile['aosp']+'/'+PRODUCT.rstrip('/'),'AOSP_ROOT','unexpected official output root')
    need(re.fullmatch('r[0-9]+',profile['revision']) is not None and re.fullmatch('[0-9a-f]{64}',profile['kit_seal']) is not None,'PROFILE','exact revision/seal required')
    need(len(profile['pids'])==2 and all(type(x) is int and x>1 for x in profile['pids']),'PROFILE','exact supervisor/build PIDs required')
    need(set(profile['configuration']) >= {'PLATFORM_SDK_VERSION','TARGET_DEVICE','TARGET_BUILD_VARIANT','TARGET_ARCH'},'CONFIGURATION','identity fields absent')
    for key,value in profile['limits'].items():
        need(type(value) is int and value>0,'LIMIT',key)
    need(profile['limits']['file_bytes']<=256*1024**2 and profile['limits']['total_bytes']<=3*1024**3 and profile['limits']['files']<=8192,'LIMIT','hard ceiling exceeded')
    for path in selector['required']+selector['elf_roots']+selector['source_files']:
        permitted(path)
    need(all(p in selector['required'] for p in (
        'system/bin/boringssl_self_test32','system/bin/boringssl_self_test64','system/apex/com.android.runtime.apex','system/apex/com.android.adbd.capex',
        'system/build.prop','system/system_ext/build.prop','system/product/build.prop','obj/PACKAGING/apexkeys_intermediates/apexkeys.txt',
        'system/system_ext/bin/hwservicemanager','system/bin/init','system/bin/apexd','system/bin/keystore2','system/bin/servicemanager','system/bin/linkerconfig','system/bin/toybox','system/bin/sh','system/vendor/bin/hw/android.hardware.keymaster@4.0-service')),'SELECTOR','mandatory official boundary removed')

def run(action, profile, selector, destination, selection=None, probe=None, after_copy=None):
    destination = Path(destination)
    destination.mkdir(mode=0o700)  # Exclusive forever, including failure.
    write_json(destination/'STARTED.json',{'action':action,'schema':1,'no_retry_or_resume':True})
    state = None
    try:
        with Guard(profile,**({'probe':probe} if probe else {})) as guard:
            state = Selection(profile,selector,destination,probe)
            state.binding = terminal(profile,state.trees,state.add,state.scan)
            state.discover()
            state.elf_dependencies()
            state.provenance()
            state.recheck()
            guard.check()
            actual = state.selected()
            if selection is not None:
                need(selection==actual,'SELECTION_DRIFT','exact prior selected group no longer matches; no repair or fallback')
            write_json(destination/'selection.json',actual)
            copies = state.copy(actual,destination,after_copy) if action=='copy' else []
            state.recheck()
            guard.check()
            # Rebind terminal receipts/source integration after entire group copy.
            need(terminal(profile,state.trees,state.add,state.scan)==state.binding,'TERMINAL_DRIFT','terminal or source binding changed')
            state.recheck()
            guard.check()
            write_json(destination/'COMPLETE.json',{'schema':1,'action':action,'selection_sha256':sha((destination/'selection.json').read_bytes()),
                'copies':copies,'final_group_source_recheck':True,'runtime_ready':False,'physical_GO':False})
            return {'status':'COMPLETE','action':action,'directory':str(destination),'files':len(actual['files']),'selected_bytes':actual['selected_bytes'],
                    'selection_sha256':sha((destination/'selection.json').read_bytes()),'runtime_ready':False,'physical_GO':False}
    except BaseException as error:
        write_json(destination/'FAILED.json',{'schema':1,'code':getattr(error,'code',type(error).__name__),'error':str(error),'missing':state.missing if state else [],
            'preserved':True,'retry_or_resume_allowed':False,'runtime_ready':False,'physical_GO':False})
        raise
    finally:
        if state:
            state.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',nargs='?',choices=('plan','select','verify','copy'),default='plan')
    p.add_argument('--mode',choices=('PLAN_ONLY','PARENT_EXECUTE'),default='PLAN_ONLY')
    p.add_argument('--name',help='fresh exclusive directory name under owned VM snapshots/')
    p.add_argument('--selection',type=Path)
    p.add_argument('--selection-sha256')
    p.add_argument('--profile',type=Path,default=HERE.parent/'inputs/profile-r7.json')
    p.add_argument('--profile-sha256',help='mandatory exact hash for separately reviewed future profile')
    p.add_argument('--selector',type=Path,default=HERE.parent/'inputs/selector.json')
    p.add_argument('--selector-sha256',help='mandatory exact hash for separately reviewed future selector')
    args = p.parse_args()
    try:
        def contract(path):
            need(path.is_absolute() and path.is_relative_to(HERE.parent),'CONTRACT_PATH','contracts belong under sealed preparation (new future files require exact hash)')
            tree=Tree(HERE.parent)
            try:
                return tree.read(str(path.relative_to(HERE.parent)),4*1024*1024)
            finally:
                tree.close()
        profile_data=contract(args.profile);selector_data=contract(args.selector)
        for path,default,digest,data in ((args.profile,HERE.parent/'inputs/profile-r7.json',args.profile_sha256,profile_data),(args.selector,HERE.parent/'inputs/selector.json',args.selector_sha256,selector_data)):
            if path!=default:
                need(digest is not None and sha(data)==digest,'CONTRACT_PIN','nondefault contract needs exact external SHA256')
        profile,selector=load_bytes(profile_data),load_bytes(selector_data)
        validate_contract(profile,selector)
        if args.action=='plan':
            need(args.mode=='PLAN_ONLY','MODE','plan is read-only')
            print(json.dumps({'mode':'PLAN_ONLY','source_or_output_inspected':False,'lock_acquired':False,'profile':profile,'selector':selector,
                'runtime_ready':False,'physical_GO':False},indent=2))
            return 0
        need(sys.platform=='linux','VM_ONLY','real capture runs only on VM')
        import resource
        os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
        resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
        need(str(HERE.parent)==str(PREFIX/'preparation-v2'),'PREFIX','execute deployed sealed preparation only')
        tool_pins=load_bytes((HERE.parent/'tool-pins.json').read_bytes())
        for rel,digest in tool_pins.items():
            need(sha((HERE.parent/relative(rel)).read_bytes())==digest,'TOOL_DRIFT',rel)
        need((args.action=='copy')==(args.mode=='PARENT_EXECUTE'),'MODE','copy needs PARENT_EXECUTE; select/verify need PLAN_ONLY')
        need(args.name and re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}',args.name),'DESTINATION','fresh simple name required')
        snapshots=PREFIX/'snapshots'
        need(str(snapshots)==str(snapshots.resolve()),'DESTINATION','symlink parent')
        selection=None
        if args.action in ('verify','copy'):
            need(args.selection and re.fullmatch('[0-9a-f]{64}',args.selection_sha256 or ''),'SELECTION_PIN','exact selection path/SHA256 required')
            need(args.selection.is_relative_to(snapshots),'SELECTION_PATH','selection must remain in owned VM prefix')
            tree=Tree(snapshots)
            try:
                selected_rel=str(args.selection.relative_to(snapshots))
                need(args.selection.name=='selection.json','SELECTION_PATH','select the exact selector receipt')
                data=tree.read(selected_rel,64*1024*1024)
                complete=load_bytes(tree.read(str(args.selection.parent.relative_to(snapshots))+'/COMPLETE.json',64*1024*1024))
                need(complete.get('action')=='select' and complete.get('selection_sha256')==sha(data),'SELECTION_COMPLETION','only a completed select receipt may authorize a new snapshot')
                try:
                    tree.stat(str(args.selection.parent.relative_to(snapshots))+'/FAILED.json')
                except FileNotFoundError:
                    pass
                else:
                    need(False,'SELECTION_FAILED','failed snapshots never authorize continuation')
            finally:
                tree.close()
            need(sha(data)==args.selection_sha256,'SELECTION_PIN','selection hash mismatch')
            selection=load_bytes(data)
        else:
            need(not args.selection and not args.selection_sha256,'SELECTION','select takes no previous selection')
        print(json.dumps(run(args.action,profile,selector,snapshots/args.name,selection),indent=2))
        return 0
    except (Refusal,OSError,RuntimeError,ValueError,KeyError,TypeError,__import__('zipfile').BadZipFile,__import__('sqlite3').Error) as error:
        print(json.dumps({'status':'REFUSED','code':getattr(error,'code',type(error).__name__),'error':str(error),'runtime_ready':False,'physical_GO':False},indent=2))
        return 20

if __name__=='__main__':
    sys.exit(main())
