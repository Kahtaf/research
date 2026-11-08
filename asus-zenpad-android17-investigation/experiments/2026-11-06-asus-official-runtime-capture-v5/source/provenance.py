"""Exact ordinary-copy and reviewed aggregate semantics. No shell execution."""
import hashlib
import os
import shlex
from safeio import need, permitted, fingerprint

AGGREGATE='out/target/product/p00a/obj/PACKAGING/apexkeys_intermediates/apexkeys.txt'

def digest(text):return hashlib.sha256(text.encode()).hexdigest()

def shell_tokens(command):
    need(isinstance(command,str) and bool(command),'PRODUCER_COMMAND','missing command')
    outer=shlex.split(command)
    if outer[:2]==['/bin/bash','-c']:
        need(len(outer)==3,'PRODUCER_COMMAND','shell arguments');command=outer[2]
    lex=shlex.shlex(command,posix=True,punctuation_chars='();&<>');lex.whitespace_split=True;lex.commenters=''
    return list(lex)

def copy_source(edge, expected=None):
    real=[d['path'] for d in edge['dependencies'] if d['kind']=='explicit']
    need(len(real)==1 and '/' in real[0],'INSTALL_SOURCE',edge['output'])
    source=permitted(real[0]);target=edge['output']
    need(not source.startswith('-') and not target.startswith('-'),'PRODUCER_COMMAND','option-shaped path')
    need(edge['outputs']==[target],'INSTALL_SOURCE','copy output group')
    if expected is not None:need(source==expected,'INSTALL_SOURCE','wrong reviewed install source: '+target)
    tokens=shell_tokens(edge.get('command'))
    if tokens[:4]==['rm','-f',target,'&&']:tokens=tokens[4:]
    allowed=[['cp',source,target],['cp','-f',source,target],['cp','-f','-d',source,target]]
    need(tokens in allowed,'PRODUCER_COMMAND','unknown ordinary install producer: '+target)
    return source

def install_kind(edge, contract):
    if contract and edge['output']==contract['aggregate']['target']:
        need(edge['output']==AGGREGATE,'GENERATION_CONTRACT','exact aggregate target')
        return {'kind':'reviewed-aggregate','source':None}
    expected=(contract or {}).get('ordinary_install_sources',{}).get(edge['output'])
    return {'kind':'ordinary-copy','source':copy_source(edge,expected)}

def aggregate_plan(graph, edge, contract):
    spec=contract['aggregate'];target=edge['output']
    need(target==AGGREGATE==spec['target'] and edge['outputs']==[target],'GENERATION_CONTRACT','exact output')
    need(digest(edge['raw'])==spec['edge_sha256'] and digest(edge['raw_rule'] or '')==spec['rule_sha256'],'GENERATION_PRODUCER','changed aggregate edge/rule')
    deps=[{'path':d['path'],'kind':d['kind']} for d in edge['dependencies']]
    need(deps==spec['dependencies'],'GENERATION_DEPENDENCIES','aggregate dependency list/order/categories')
    explicit=[d['path'] for d in deps if d['kind']=='explicit']
    need(len(explicit)==39 and len(set(explicit))==39,'GENERATION_DEPENDENCIES','exact 39 inputs')
    expected=['(','rm','-f',target,')','&&','(','touch',target,')']
    for path in explicit:
        permitted(path);expected+=['&&','(','cat',path,'>>',target,')']
    need(shell_tokens(edge['command'])==expected,'GENERATION_PRODUCER','not the reviewed ordered concatenation')
    plans=[]
    need(set(spec['input_producers'])==set(explicit),'GENERATION_DEPENDENCIES','input producer coverage')
    for path in explicit:
        child=graph.edge(path);pin=spec['input_producers'][path]
        need(digest(child['raw'])==pin['edge_sha256'] and digest(child['raw_rule'] or '')==pin['rule_sha256'],'GENERATION_PRODUCER','changed input producer: '+path)
        child_deps=[{'path':d['path'],'kind':d['kind']} for d in child['dependencies']]
        need(child_deps==pin['dependencies'],'GENERATION_DEPENDENCIES','input dependency list: '+path)
        inputs=[d['path'] for d in child_deps if d['kind']=='explicit']
        need(inputs==[pin['source']] and child['outputs']==[path],'GENERATION_DEPENDENCIES',path)
        source=permitted(pin['source']);cmp='prebuilts/build-tools/path/linux-x86/cmp';cp='prebuilts/build-tools/path/linux-x86/cp'
        expected_copy=['if','!',cmp,'-s',source,path,';','then',cp,source,path,';','fi']
        need(shell_tokens(child['command'])==expected_copy,'GENERATION_PRODUCER','not the reviewed raw metadata copy: '+path)
        # Phony tool tokens must resolve to the exact public executable paths.
        for token,tool in (('Cmp-deps',cmp),('Cp-deps',cp)):
            need(any(d['path']==token and d['kind']=='implicit' for d in child_deps),'GENERATION_TOOL',token)
            pseudo=graph.edge(token)
            need(pseudo['rule']=='phony' and any(d['path']==tool for d in pseudo['dependencies']),'GENERATION_TOOL',tool)
        plans.append({'output':path,'source':source,'dependencies':child_deps,'rule':child['rule']})
    need({s['path'] for s in spec['generator_sources']}=={'build/make/core/Makefile','build/soong/apex/key.go','build/soong/android/raw_files.go'} and len(spec['generator_sources'])==3 and set(spec['generator_tools'])=={'prebuilts/build-tools/path/linux-x86/cmp','prebuilts/build-tools/path/linux-x86/cp'},'GENERATION_SOURCE','source/tool coverage')
    return {'kind':'reviewed-ordered-concatenation','inputs':explicit,'input_producers':plans,'generator_sources':spec['generator_sources'],'generator_tools':spec['generator_tools'],'shell_interpreter_reference':'/bin/bash','host_interpreter_bytes_qualified':False}

def bind_aggregate(state, edge, plan):
    """Future capture only: hash all sources/tools and verify actual concat bytes."""
    for source in plan['generator_sources']:
        permitted(source['path']);row=state.add('aosp',source['path'],'aggregate-generator-source',True)
        need(row['kind']=='file' and row['sha256']==source['sha256'],'GENERATION_SOURCE',source['path'])
    for tool in plan['generator_tools']:state.add('aosp',permitted(tool),'aggregate-generator-tool',True)
    for producer in plan['input_producers']:
        row=state.add('aosp',producer['output'],'aggregate-input',True)
        raw=state.add('aosp',producer['source'],'aggregate-raw-metadata-source',True)
        need(row['kind']==raw['kind']=='file' and row['sha256']==raw['sha256'],'GENERATION_INPUT_BYTES',producer['output'])
    total=0;h=hashlib.sha256();tree=state.trees['aosp']
    for path in plan['inputs']:
        pinned=state.rows['aosp:'+path];own=hashlib.sha256()
        with tree.open(path) as f:
            before=fingerprint(os.fstat(f.fileno()));need(before==pinned['identity'],'DRIFT',path)
            for chunk in iter(lambda:f.read(1024**2),b''):
                total+=len(chunk);need(total<=state.profile['limits']['file_bytes'],'SIZE',edge['output']);h.update(chunk);own.update(chunk)
            need(before==fingerprint(os.fstat(f.fileno()))==fingerprint(tree.stat(path)) and own.hexdigest()==pinned['sha256'],'DRIFT',path)
    selected=state.rows['aosp:'+edge['output']]
    need(selected['kind']=='file' and selected['bytes']==total and selected['sha256']==h.hexdigest(),'GENERATION_BYTES',edge['output'])
