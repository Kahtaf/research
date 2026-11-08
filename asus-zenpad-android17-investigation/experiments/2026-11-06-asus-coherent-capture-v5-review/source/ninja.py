"""Read-only Ninja bindings: eager file/build values, lazy rule values, scoped lookup."""
import re
from safeio import need
NAME = re.compile(r'[A-Za-z0-9_.-]+\Z')
SIMPLE = re.compile(r'[A-Za-z0-9_-]+')
CONTINUATION = re.compile(r'(?<!\$)((?:\$\$)*)\$\r?\n[ ]*')
MAX = 32*1024**2
RULE_FIELDS={'command','description','depfile','deps','dyndep','generator','pool','restat','rspfile','rspfile_content','msvc_deps_prefix'}

def shell_path(path):
    return path if re.fullmatch(r'[A-Za-z0-9_+./-]+',path) else "'"+path.replace("'","'\\''")+"'"

def logical(raw):
    return CONTINUATION.sub(lambda m:m[1],raw).splitlines()

def evaluate(text, lookup):
    need('\0' not in text, 'GRAPH_SYNTAX', 'NUL')
    parts=[];count=0;i=0
    while i<len(text):
        if text[i]!='$':
            j=text.find('$',i)
            if j<0:j=len(text)
            part=text[i:j];i=j
        else:
            i+=1;need(i<len(text),'GRAPH_SYNTAX','trailing $')
            c=text[i]
            if c in '$ :':part=c;i+=1
            elif c=='{':
                j=text.find('}',i+1);need(j>=0 and NAME.fullmatch(text[i+1:j]),'GRAPH_SYNTAX','malformed ${variable}')
                part=lookup(text[i+1:j]);i=j+1
            else:
                m=SIMPLE.match(text,i);need(m is not None,'GRAPH_SYNTAX','bad $ escape')
                part=lookup(m[0]);i=m.end()
        count+=len(part.encode());need(count<=MAX,'GRAPH_VARIABLE','expanded value budget')
        parts.append(part)
    return ''.join(parts)

def path_tokens(text):
    """Tokenize before expansion: variable values are never lexed a second time."""
    tokens=[];token=[];i=0
    while i<len(text):
        c=text[i]
        if c=='$':
            need(i+1<len(text),'GRAPH_SYNTAX','trailing $')
            if text[i+1]=='{':
                end=text.find('}',i+2);need(end>=0,'GRAPH_SYNTAX','missing }');token.append(text[i:end+1]);i=end+1
            else:token.append(text[i:i+2]);i+=2
        elif c.isspace() or c in ':|':
            if token:tokens.append(''.join(token));token=[]
            if c in ':|':
                if text[i:i+2] in ('||','|@'):tokens.append(text[i:i+2]);i+=2
                else:tokens.append(c);i+=1
            else:i+=1
        else:token.append(c);i+=1
    if token:tokens.append(''.join(token))
    return tokens

def bindings(lines):
    result={}
    for line in lines:
        if not line.strip() or line.lstrip().startswith('#'):continue
        need(not line.startswith('\t'),'GRAPH_SYNTAX','tab indentation')
        name,sep,value=line.lstrip(' ').partition('=')
        name=name.strip();need(sep and NAME.fullmatch(name),'GRAPH_SYNTAX','binding')
        result[name]=value.lstrip(' ')
    return result

class Scopes:
    def __init__(self, graph, paths, includes):
        self.graph=graph;self.context={};self.parents={};self.cache={};self.cache_bytes=0;self.lookups=set()
        children={p:[] for p in paths};incoming=set()
        for inc in includes:
            need(inc['graph'] in children and inc['path'] in children,'GRAPH_INCLUDE',inc['path'])
            children[inc['graph']].append(inc);incoming.add(inc['path'])
        roots=sorted(set(paths)-incoming);need(roots,'GRAPH_INCLUDE','include cycle')
        def visit(file,scope,prefix,active):
            need(file not in active and file not in self.context,'GRAPH_INCLUDE','cycle or repeated inclusion: '+file)
            self.context[file]=(scope,prefix)
            for inc in sorted(children[file],key=lambda x:x['line']):
                sub=scope
                if inc['kind']=='subninja':
                    sub=file+':'+str(inc['line']);self.parents[sub]=scope
                visit(inc['path'],sub,prefix+(inc['line'],0),active+(file,))
        for i,file in enumerate(roots):
            scope='root:'+file;self.parents[scope]=None;visit(file,scope,(i,),())
        need(set(self.context)==set(paths),'GRAPH_INCLUDE','unreachable graph')
    def key(self,file,line):return self.context[file][1]+(line,)
    def definitions(self,kind,name,scope,cutoff=None):
        rows=[]
        for file,line,raw in self.graph.rows(kind,name):
            need(file in self.context,'GRAPH_SCOPE',file)
            if self.context[file][0]==scope and (cutoff is None or self.key(file,line)<cutoff):rows.append((file,line,raw))
        return rows
    def global_value(self,name,file,cutoff=None,stack=()):
        need(len(name)<=4096,'GRAPH_VARIABLE','variable-name length')
        self.lookups.add((name,file))
        need(len(self.lookups)<=65536,'GRAPH_VARIABLE','lookup-context budget')
        scope=self.context[file][0]
        while scope is not None:
            rows=self.definitions('variable',name,scope,cutoff)
            if rows:
                record=max(rows,key=lambda r:self.key(r[0],r[1]));rf,line,raw=record;key=(rf,line)
                self.graph.record('variable',name,*record)
                if key in self.cache:return self.cache[key]
                need(len(stack)<30 and key not in stack,'GRAPH_VARIABLE','binding depth/cycle')
                value=logical(raw)[0].partition('=')[2].lstrip(' ')
                result=evaluate(value,lambda n:self.global_value(n,rf,self.key(rf,line),stack+(key,)))
                self.cache_bytes+=len(result.encode());need(self.cache_bytes<=16*1024**2,'GRAPH_VARIABLE','binding cache')
                self.cache[key]=result;return result
            scope=self.parents[scope]
        return ''
    def rule(self,name,file,line):
        scope=self.context[file][0];cutoff=self.key(file,line)
        while scope is not None:
            rows=self.definitions('rule',name,scope,cutoff)
            if rows:
                need(len(rows)==1,'GRAPH_RULE','duplicate scoped rule '+name)
                self.graph.record('rule',name,*rows[0]);return rows[0][2]
            scope=self.parents[scope]
        need(False,'GRAPH_UNKNOWN','rule '+name)
    def edge(self,target,record):
        file,line,raw=record;lines=logical(raw);tokens=path_tokens(lines[0]);need(tokens and tokens[0]=='build' and tokens.count(':')==1,'GRAPH_SYNTAX',target)
        colon=tokens.index(':');out_tokens=tokens[1:colon];rest=tokens[colon+1:]
        need(rest and NAME.fullmatch(rest[0]),'GRAPH_SYNTAX','rule name')
        rule=rest[0];raw_rule=None if rule=='phony' else self.rule(rule,file,line)
        # Ninja evaluates each build binding against the enclosing file env,
        # not the other build-local bindings, at parse time.
        local={k:evaluate(v,lambda n:self.global_value(n,file,self.key(file,line))) for k,v in bindings(lines[1:]).items()}
        def path_value(text):
            value=evaluate(text,lambda n:local[n] if n in local else self.global_value(n,file,self.key(file,line)))
            need(value and not any(c.isspace() for c in value),'GRAPH_SYNTAX','empty/whitespace path')
            return value
        outputs=[path_value(t) for t in out_tokens if t!='|'];explicit_outputs=[path_value(t) for t in out_tokens[:out_tokens.index('|') if '|' in out_tokens else len(out_tokens)]]
        need(outputs and target in outputs,'GRAPH_SYNTAX','output identity')
        deps=[];category='explicit';seen=set();order={'explicit':0,'implicit':1,'order_only':2,'validation':3}
        for token in rest[1:]:
            if token in ('|','||','|@'):
                new={'|':'implicit','||':'order_only','|@':'validation'}[token]
                need(new not in seen and order[new]>order[category],'GRAPH_SYNTAX','dependency delimiter');seen.add(new);category=new
            else:
                need(token!=':','GRAPH_SYNTAX','unexpected colon');deps.append({'path':path_value(token),'kind':category})
        rb={} if raw_rule is None else bindings(logical(raw_rule)[1:]);undefined=set()
        need(not (set(rb)-RULE_FIELDS),'GRAPH_RULE','unknown rule binding')
        need(raw_rule is None or bool(rb.get('command')),'GRAPH_RULE','missing command')
        need(('rspfile' in rb)==('rspfile_content' in rb),'GRAPH_RULE','rspfile pair')
        special={'in':' '.join(shell_path(d['path']) for d in deps if d['kind']=='explicit'),'in_newline':'\n'.join(shell_path(d['path']) for d in deps if d['kind']=='explicit'),'out':' '.join(shell_path(p) for p in explicit_outputs)}
        def lookup(name,stack=()):
            if name in special:return special[name]
            if name in local:return local[name]
            if name in rb:
                need(len(stack)<30 and name not in stack,'GRAPH_VARIABLE','rule binding cycle/depth: '+name)
                return evaluate(rb[name],lambda n:lookup(n,stack+(name,)))
            value=self.global_value(name,file)
            if not value:undefined.add(name)
            return value
        expanded={k:lookup(k) for k in rb}
        return {'output':target,'rule':rule,'outputs':outputs,'dependencies':deps,'raw':raw,'raw_rule':raw_rule,'expanded_rule':None if raw_rule is None else 'rule '+rule+'\n'+''.join('  '+k+' = '+v+'\n' for k,v in expanded.items()),'command':expanded.get('command'),'rule_bindings':expanded,'undefined_or_empty_variables':sorted(undefined),'scope':self.context[file][0]}
