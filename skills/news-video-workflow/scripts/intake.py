"""Resolve a numbered item from original Docx blocks or spreadsheet rows."""
from pathlib import Path
import json,re,subprocess,sys,urllib.parse,uuid
from feishu_read import text_in,CLIClient
from toolchain import lark
from materials import paths,import_file,record,safe_url

def normalize(value):return str(value).strip().replace('．','.').replace('。','.').lstrip('0') or '0'
def starts_item(text,item):
 text=text.strip();item=normalize(item)
 if not re.fullmatch(r'\d+(?:\.\d+)*',item):return text==item
 # Match numeric identifiers, not a substring of 12.1 / 2.10 or a number inside prose.
 match=re.match(r'^(?:第\s*)?(\d+(?:[.．]\d+)*)(?=$|[\s、:：)）\]】\-]|[\u4e00-\u9fff])',text)
 return bool(match and normalize(match.group(1).replace('．','.'))==item)
def block_text(block):return ''.join(text_in(block)).strip()
def descendants(ids,by_id):
 seen=set();queue=list(ids)
 while queue:
  bid=queue.pop(0)
  if bid in seen:continue
  seen.add(bid);b=by_id.get(bid)
  if b:queue.extend(b.get('children',[]))
 return [b for b in by_id.values() if b.get('block_id') in seen]
def select_doc(blocks,item):
 by_id={b['block_id']:b for b in blocks};tables=[]
 for b in blocks:
  if not isinstance(b.get('table'),dict):continue
  table=b['table'];cols=table.get('property',{}).get('column_size',0);cells=table.get('cells',b.get('children',[]))
  if not cols:continue
  for offset in range(0,len(cells),cols):
   row=cells[offset:offset+cols];contents=['\n'.join(block_text(x) for x in descendants([cell],by_id) if block_text(x)) for cell in row]
   if contents and starts_item(contents[0],item):tables.append({'kind':'table-row','headers':['\n'.join(block_text(x) for x in descendants([cell],by_id) if block_text(x)) for cell in cells[:cols]],'cells':contents,'blocks':descendants(row,by_id)})
 if tables:return tables
 candidates=[]
 # Only top-level heading/paragraph siblings: do not mistake repeated cell labels for sections.
 page=next((b for b in blocks if b.get('block_type')==1),None)
 siblings=[by_id[x] for x in page.get('children',[]) if x in by_id] if page else [b for b in blocks if b.get('block_type') in range(2,11)]
 for i,b in enumerate(siblings):
  if not starts_item(block_text(b),item):continue
  stop=len(siblings)
  for j in range(i+1,len(siblings)):
   text=block_text(siblings[j]);other=re.match(r'^(\d+(?:[.．]\d+)*)(?=$|[\s、:：)）\-]|[\u4e00-\u9fff])',text)
   if other and other.group(1).count('.')<=normalize(item).count('.') and (siblings[j].get('block_type') in range(3,12) or re.match(r'^\d+(?:\.\d+)*\s*[、:：)]',text)):
    stop=j;break
  selected=descendants([x['block_id'] for x in siblings[i:stop]],by_id)
  candidates.append({'kind':'section','text':'\n'.join(block_text(x) for x in selected if block_text(x)),'blocks':selected})
 return candidates

def cell_text(cell):
 if isinstance(cell,str):return cell
 if isinstance(cell,(int,float)):return str(cell)
 if isinstance(cell,list):return ''.join(cell_text(x) for x in cell)
 if isinstance(cell,dict):
  if isinstance(cell.get('text'),str):return cell['text']
  if isinstance(cell.get('text_run'),dict):return cell['text_run'].get('content','')
 return ''
def select_sheet(data,item):
 result=[]
 for sheet in data.get('sheets',[]):
  ranges=sheet.get('data',{}).get('valueRanges',[])
  for values in ranges:
   for i,row in enumerate(values.get('values',[])):
    first=cell_text(row[0]) if row else ''
    if starts_item(first,item):result.append({'kind':'sheet-row','spreadsheetToken':data.get('objectToken'),'headers':values.get('values',[[]])[0],'sheet':sheet.get('sheet'),'range':values.get('range'),'rowIndexWithinRange':i,'cells':row})
 return result

def links_in(obj):
 found=[]
 def add(s):
  for u in re.findall(r'https://[^\s<>"\u3000]+',s):
   u=u.rstrip('.,;，。；）)]}')
   if u not in found:found.append(u)
 def walk(x):
  if isinstance(x,str):add(x)
  elif isinstance(x,dict):
   for v in x.values():walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 walk(obj);return found

def read(project,url,output,sheet=None,range_='A1:Z200'):
 cmd=[sys.executable,str(Path(__file__).with_name('feishu_read.py')),'--project',str(project),'--url',url,'--output',str(output),'--range',range_]
 if sheet:cmd+=['--sheet',sheet]
 subprocess.run(cmd,check=True,timeout=300)
 return json.loads(output.read_text())

def intake(project,url,item,download=False,sheet=None,range_='A1:Z200',section=None):
 root,public,assets,reports=paths(project);job=reports/('intake-'+uuid.uuid4().hex[:10]);job.mkdir()
 raw=read(root,url,job/'source.json',sheet,range_)
 blocks=raw.get('blocks',[])
 if section and raw['type']=='docx':
  by_id={b['block_id']:b for b in blocks};heads=[(i,b) for i,b in enumerate(blocks) if block_text(b)==section]
  if len(heads)!=1:raise ValueError('Section heading must match exactly once')
  i,head=heads[0];level=head.get('block_type',3);end=next((j for j in range(i+1,len(blocks)) if 3<=blocks[j].get('block_type',0)<=level),len(blocks));blocks=blocks[i:end]
 candidates=select_doc(blocks,item) if raw['type']=='docx' else select_sheet(raw,item)
 # Embedded sheets are first-class sources; refs use spreadsheetToken_sheetId.
 if not candidates:
  host=urllib.parse.urlsplit(url).netloc
  for i,ref in enumerate(raw.get('embeddedSheetRefs',[])):
   if not ref:continue
   token,_,sid=ref.partition('_');data=read(root,'https://'+host+'/sheets/'+token,job/f'embedded-{i}.json',sid or None,range_);candidates+=select_sheet(data,item)
 if len(candidates)!=1:
  report={'ok':False,'requestedItem':item,'candidateCount':len(candidates),'action':'Provide the exact section heading / sheet ID / bounded cell range to disambiguate. No row was silently chosen.'};(job/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));raise ValueError(json.dumps(report,ensure_ascii=False))
 selected=candidates[0];ids={b['block_id'] for b in selected.get('blocks',[])};media=[m for m in raw.get('media',[]) if m.get('blockId') in ids]
 if selected['kind']=='sheet-row':
  def attach(x):
   if isinstance(x,dict):
    if x.get('type')=='attachment' and x.get('fileToken'):media.append({'token':x['fileToken'],'name':x.get('name','attachment.bin'),'route':selected.get('spreadsheetToken')})
    for v in x.values():attach(v)
   elif isinstance(x,list):
    for v in x:attach(v)
  attach(selected.get('cells',[]))
 links=links_in(selected);result={'ok':True,'sourceUrl':safe_url(url),'requestedItem':item,'selection':selected,'links':links,'attachments':media,'downloads':[]}
 if download:
  c=CLIClient(lark(root),'',root);download_dir=job/'attachments';download_dir.mkdir()
  for i,m in enumerate(media):
   name=Path(str(m.get('name','attachment.bin')).replace('\\','/')).name
   try:
    path=download_dir/f'{i+1:03}-{name}';c.download(m['token'],path,500*1024*1024,m.get('route'))
    result['downloads'].append(import_file(root,path,url,'fact'));path.unlink()
   except Exception as e:result['downloads'].append(record(root,{'ok':False,'name':name,'error':type(e).__name__,'action':'Check attachment download scope and document access'}))
 output=job/'result.json';output.write_text(json.dumps(result,ensure_ascii=False,indent=2));return {'report':str(output),'requestedItem':item,'kind':selected['kind'],'links':len(links),'attachments':len(media),'downloaded':sum(x.get('ok',False) for x in result['downloads'])}
