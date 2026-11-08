from pathlib import Path
import xml.etree.ElementTree as E,json,re,subprocess,hashlib
R=Path(__file__).resolve().parents[1]
def contracts(root):
 out=set()
 for h in root.findall('hal'):
  fmt=h.get('format','hidl');pkg=h.findtext('name');versions=[]
  for v in h.findall('version'):
   text=v.text
   if fmt=='hidl':
    a,b=text.split('.');lo,*hi=b.split('-');versions += [f'{a}.{x}' for x in range(int(lo),int(hi[0] if hi else lo)+1)]
   elif fmt=='aidl':
    lo,*hi=text.split('-');versions += [str(x) for x in range(int(lo),int(hi[0] if hi else lo)+1)]
   else:versions += [text]
  if not versions:versions=['1'] if fmt=='aidl' else ['']
  for i in h.findall('interface'):
   for kind in ['instance','regex-instance']:
    for n in i.findall(kind):
     for v in versions:out.add((fmt,pkg,v,i.findtext('name'),kind,n.text))
 return out
b=E.parse(R/'evidence/combined-baseline.xml').getroot();c=E.parse(R/'evidence/combined-candidate.xml').getroot()
bs=contracts(b);cs=contracts(c)
canonical=lambda e:(e.tag,tuple(sorted(e.attrib.items())),(e.text or '').strip(),tuple(sorted(canonical(x) for x in e)))
bkern={canonical(x) for x in b.findall('kernel')};ckern={canonical(x) for x in c.findall('kernel')}
security={t:{'before':E.tostring(b.find(t),encoding='unicode') if b.find(t) is not None else None,'after':E.tostring(c.find(t),encoding='unicode') if c.find(t) is not None else None} for t in ['sepolicy','avb','xmlfile']}
# Framework manifests use these exact filters in VintfObject.cpp.
filter_changes=[]
for p in (R/'inputs/metadata').rglob('*.xml'):
 try:root=E.parse(p).getroot()
 except E.ParseError:continue
 if root.tag!='manifest' or root.get('type')!='framework':continue
 for h in root.findall('hal'):
  minimum=h.get('min-level');maximum=h.get('max-level')
  old=minimum is None
  new=(minimum is None or int(minimum)<=3) and (maximum is None or int(maximum)>=3)
  if old!=new:filter_changes.append({'file':str(p.relative_to(R/'inputs/metadata')),'hal':h.findtext('name'),'before_included':old,'after_included':new,'attributes':h.attrib})
# Presence comparison only; never equate a declaration with functional service availability.
provided=[]
for p in (R/'inputs/metadata').rglob('*.xml'):
 try:root=E.parse(p).getroot()
 except E.ParseError:continue
 if root.tag!='manifest':continue
 for h in root.findall('hal'):
  fmt=h.get('format','hidl');pkg=h.findtext('name')
  for fq in h.findall('fqname'):
   m=re.fullmatch(r'@(\d+)\.(\d+)::([^/]+)/(.+)',fq.text or '')
   if m:provided.append({'format':fmt,'package':pkg,'version':f'{m[1]}.{m[2]}','interface':m[3],'instance':m[4],'partition':str(p.relative_to(R/'inputs/metadata'))})
   elif '/' in (fq.text or ''):provided.append({'format':fmt,'package':pkg,'version':h.findtext('version','1'),'interface':fq.text.split('/',1)[0],'instance':fq.text.split('/',1)[1],'partition':str(p.relative_to(R/'inputs/metadata'))})
historical=E.parse(R/'candidate/device/asus/p00a/vintf-legacy/compatibility_matrix.p00a-p.xml').getroot();obligations=[]
for h in historical.findall('hal'):
 if h.get('optional')!='false':continue
 lone=E.Element('compatibility-matrix');lone.append(h)
 grouped={}
 for fmt,pkg,v,interface,kind,instance in sorted(contracts(lone)):
  grouped.setdefault((fmt,pkg,interface,kind,instance),[]).append(v)
 for (fmt,pkg,interface,kind,instance),versions in grouped.items():
  same=[x for x in provided if x['format']==fmt and x['package']==pkg and x['version'] in versions and x['interface']==interface and (x['instance']==instance if kind=='instance' else re.fullmatch(instance,x['instance']) is not None)]
  obligations.append({'format':fmt,'package':pkg,'allowed_versions':versions,'interface':interface,'instance_kind':kind,'instance':instance,'exact_declarations':same,'status':'DECLARED_NOT_RUNTIME_VERIFIED' if same else 'NO_EXACT_HISTORICAL_DECLARATION','other_declared_interfaces':[x for x in provided if x['package']==pkg]})

validations=[]
for f in [R/'candidate/device/asus/p00a/vintf-legacy/compatibility_matrix.p00a-p.xml',R/'evidence/generated/work-p/kernel.xml',R/'evidence/generated/candidate-p/system/etc/vintf/compatibility_matrix.p00a-legacy.xml']:
 a=['/usr/bin/xmllint','--noout','--schema',str(R/'inputs/schema/compatibility_matrix.xsd'),str(f)]
 q=subprocess.run(a,capture_output=True,text=True,timeout=15);validations.append({'argv':a,'exit':q.returncode,'log':q.stdout+q.stderr});assert q.returncode==0
result={'baseline_effective_hal_contract_count':len(bs),'candidate_effective_hal_contract_count':len(cs),'removed_sdk37_hal_contracts':sorted(bs-cs),'added_historical_hal_contracts':sorted(cs-bs),'removed_modern_kernel_blocks':len(bkern-ckern),'added_historical_kernel_blocks':len(ckern-bkern),'security':security,'framework_manifest_filter_changes':filter_changes,'historical_required_presence_observations':obligations,'schema_validations':validations}
assert not bs-cs and not bkern-ckern and not filter_changes
for t,x in security.items():assert x['before']==x['after']
(R/'evidence/constraint-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('effective HAL contracts',len(bs),'->',len(cs),'removed',len(bs-cs),'added',len(cs-bs));print('kernel blocks retained',len(bkern),'added',len(ckern-bkern));print('schema all pass; no security/filter changes')
