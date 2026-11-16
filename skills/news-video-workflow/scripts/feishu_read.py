#!/usr/bin/env python3
"""Read Feishu/Lark Wiki, Docx, Sheets and authorized media using the caller's token."""
from pathlib import Path,PurePosixPath
import argparse,os,json,re,urllib.request,urllib.parse,urllib.error,hashlib,mimetypes
class NoCredentialRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  if urllib.parse.urlparse(newurl).scheme!='https':raise ValueError('Refuse non-HTTPS media redirect')
  new=super().redirect_request(req,fp,code,msg,headers,newurl)
  if urllib.parse.urlparse(req.full_url).hostname!=urllib.parse.urlparse(newurl).hostname:new.remove_header('Authorization')
  return new
class Client:
 def __init__(self,token,base):self.token=token;self.base=base;self.opener=urllib.request.build_opener(NoCredentialRedirect())
 def request(self,path):return self.opener.open(urllib.request.Request(self.base+path,headers={'Authorization':'Bearer '+self.token,'User-Agent':'news-video-workflow/1.0'}),timeout=60)
 def get(self,path):
  with self.request(path) as r:j=json.load(r)
  if j.get('code',0)!=0:raise RuntimeError(f'Feishu API code {j.get("code")}: {j.get("msg","request failed")}')
  return j.get('data',j)
 def docx(self,doc):
  blocks=[];page='';seen=set()
  while True:
   q=urllib.parse.urlencode({'page_size':200,**({'page_token':page} if page else {})});d=self.get('/docx/v1/documents/'+urllib.parse.quote(doc,safe='')+'/blocks?'+q);blocks+=d.get('items',[])
   if not d.get('has_more'):break
   page=d.get('page_token','')
   if not page or page in seen:raise RuntimeError('Invalid repeated pagination token')
   seen.add(page)
  return blocks
 def download(self,token,dest,limit,route=None):
  q='?'+urllib.parse.urlencode({'extra':json.dumps({'drive_route_token':route})}) if route else ''
  with self.request('/drive/v1/medias/'+urllib.parse.quote(token,safe='')+'/download'+q) as r:
   if 'json' in r.headers.get('Content-Type',''):raise RuntimeError('Media API returned JSON instead of an authorized media file')
   if int(r.headers.get('Content-Length','0'))>limit:raise ValueError('Media exceeds configured maximum size')
   h=hashlib.sha256();size=0;tmp=dest.with_suffix(dest.suffix+'.'+__import__('uuid').uuid4().hex+'.part');owned=False
   if dest.exists():raise FileExistsError('Destination exists')
   try:
    with tmp.open('xb') as f:
     owned=True
     while True:
      b=r.read(1024*1024)
      if not b:break
      size+=len(b)
      if size>limit:raise ValueError('Media exceeds configured maximum size')
      f.write(b);h.update(b)
    if dest.exists():raise FileExistsError('Destination exists')
    tmp.replace(dest)
   except Exception:
    if owned and tmp.exists():tmp.unlink()
    raise
  return {'file':str(dest),'bytes':size,'sha256':h.hexdigest()}
def text_in(obj):
 if isinstance(obj,dict):
  if isinstance(obj.get('text_run'),dict):yield obj['text_run'].get('content','')
  else:
   for v in obj.values():yield from text_in(v)
 elif isinstance(obj,list):
  for v in obj:yield from text_in(v)
class CLIClient(Client):
 def __init__(self,command,base,workspace=None):self.command=command;self.base=base;self.token='';self.workspace=workspace
 def get(self,path):
  from toolchain import cli_get
  return cli_get(self.command,path,workspace=self.workspace)
 def download(self,token,dest,limit,route=None):
  from toolchain import cli_get
  import uuid
  if dest.exists():raise FileExistsError('Destination exists')
  tmp=dest.with_name(dest.name+'.'+uuid.uuid4().hex+'.part')
  q='?'+urllib.parse.urlencode({'extra':json.dumps({'drive_route_token':route})}) if route else ''
  try:
   cli_get(self.command,'/drive/v1/medias/'+urllib.parse.quote(token,safe='')+'/download'+q,tmp)
   if not tmp.is_file() or tmp.stat().st_size==0:raise RuntimeError('CLI returned no media')
   if tmp.stat().st_size>limit:raise ValueError('Media exceeds configured maximum size')
   with tmp.open('rb') as f:
    if f.read(100).lstrip().startswith(b'{'):raise RuntimeError('Media download returned JSON; inspect permissions')
   digest=hashlib.sha256(tmp.read_bytes()).hexdigest()
   if dest.exists():raise FileExistsError('Destination exists')
   tmp.replace(dest)
   return {'file':str(dest),'bytes':dest.stat().st_size,'sha256':digest}
  finally:
   if tmp.exists():tmp.unlink()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',required=True);p.add_argument('--output',required=True);p.add_argument('--project',help='Use this project official CLI and its managed login');p.add_argument('--sheet');p.add_argument('--range',default='A1:Z200');p.add_argument('--download-media');p.add_argument('--max-size-mb',type=int,default=500);a=p.parse_args();out=Path(a.output).expanduser()
 if out.exists():p.error('Output exists; choose a new output path')
 u=urllib.parse.urlparse(a.url);host=(u.hostname or '').lower();is_lark=host=='larksuite.com' or host.endswith('.larksuite.com')
 if u.scheme!='https' or not(is_lark or host=='feishu.cn' or host.endswith('.feishu.cn')):p.error('Use an HTTPS Feishu/Lark document URL')
 m=re.match(r'^/(wiki|docx|sheets)/([A-Za-z0-9_-]+)',u.path)
 if not m:p.error('Supported URL types: wiki, docx, sheets')
 token=os.environ.get('FEISHU_USER_ACCESS_TOKEN','').strip()
 if not token and os.environ.get('FEISHU_TOKEN_FILE'):token=Path(os.environ['FEISHU_TOKEN_FILE']).expanduser().read_text().strip()
 if not token and not a.project:p.error('Set FEISHU_USER_ACCESS_TOKEN or FEISHU_TOKEN_FILE using your own authorization; do not paste tokens into chat')
 base='https://open.larksuite.com/open-apis' if is_lark else 'https://open.feishu.cn/open-apis'
 if a.project:
  from toolchain import lark
  c=CLIClient(lark(a.project),base,a.project)
 else:c=Client(token,base)
 kind,obj=m.groups();result={'url':urllib.parse.urlunparse(u._replace(query='',fragment='')),'downloads':[]};media=[]
 try:
  if kind=='wiki':
   node=c.get('/wiki/v2/spaces/get_node?'+urllib.parse.urlencode({'token':obj}))['node'];obj=node['obj_token'];kind=node['obj_type'];result['title']=node.get('title','')
  result['type']=kind;result['objectToken']=obj
  if kind=='docx':
   blocks=c.docx(obj);result['blocks']=blocks;result['text']='\n'.join(''.join(text_in(b)) for b in blocks);result['embeddedSheetRefs']=[b['sheet'].get('token') for b in blocks if isinstance(b.get('sheet'),dict)]
   for b in blocks:
    for key in ['image','file']:
     v=b.get(key)
     if isinstance(v,dict) and v.get('token'):media.append({'token':v['token'],'name':v.get('name') or b.get('block_id','asset')+('.jpg' if key=='image' else '.bin'),'blockId':b.get('block_id'),'kind':key})
  elif kind in ['sheet','sheets']:
   if not re.fullmatch(r'[A-Z]{1,3}[1-9][0-9]*:[A-Z]{1,3}[1-9][0-9]*',a.range):p.error('Use a bounded range, for example A1:Z200')
   sheets=c.get('/sheets/v3/spreadsheets/'+obj+'/sheets/query').get('sheets',[]);selected=[s for s in sheets if not a.sheet or s['sheet_id']==a.sheet];result['sheets']=[]
   if a.sheet and not selected:raise ValueError('Specified sheet ID was not found')
   result['sheetsTruncated']=len(selected)>10
   for s in selected[:10]:
    d=c.get('/sheets/v2/spreadsheets/'+obj+'/values_batch_get?'+urllib.parse.urlencode({'ranges':s['sheet_id']+'!'+a.range,'valueRenderOption':'UnformattedValue'}));result['sheets'].append({'sheet':s,'data':d})
    def attachments(x):
     if isinstance(x,dict):
      if x.get('type')=='attachment' and x.get('fileToken'):media.append({'token':x['fileToken'],'name':x.get('name','attachment.bin'),'kind':'attachment','route':obj})
      for v in x.values():attachments(v)
     elif isinstance(x,list):
      for v in x:attachments(v)
    attachments(d)
  else:raise ValueError('Unsupported Wiki object type: '+kind)
  result['media']=media
  if a.download_media:
   dest=Path(a.download_media).expanduser();dest.mkdir(parents=True,exist_ok=True)
   for i,item in enumerate(media):
    name=PurePosixPath(str(item['name']).replace('\\','/')).name or 'attachment.bin'
    try:r=c.download(item['token'],dest/f'{i+1:03}-{name}',a.max_size_mb*1024*1024,item.get('route'));r['ok']=True
    except Exception as e:r={'ok':False,'name':name,'error':(str(e).replace(token,'[redacted]') if token else str(e))}
    result['downloads'].append(r)
  out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'output':str(out),'type':kind,'mediaCount':len(media),'downloaded':sum(bool(r.get('ok')) for r in result['downloads']),'failed':sum(not r.get('ok') for r in result['downloads'])},ensure_ascii=False))
 except urllib.error.HTTPError as e:raise SystemExit(f'Feishu HTTP {e.code}. Check your token expiry and target document/media read permissions; no credentials were printed.')
 except Exception as e:raise SystemExit((str(e).replace(token,'[redacted]') if token else str(e)))
if __name__=='__main__':main()
