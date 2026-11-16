"""Acquire public assets, preserve originals, and record provenance without cookies."""
from pathlib import Path
from html.parser import HTMLParser
import hashlib,ipaddress,json,mimetypes,os,re,shutil,socket,subprocess,tempfile,urllib.parse,urllib.request,uuid
from toolchain import yt

def safe_url(url):
 u=urllib.parse.urlsplit(url)
 private={'token','access_token','refresh_token','auth','authorization','key','signature','cookie','code','ticket'}
 q=[(k,v) for k,v in urllib.parse.parse_qsl(u.query) if k.lower() not in private and not any(x in k.lower() for x in ['token','secret','signature','credential'])]
 return urllib.parse.urlunsplit((u.scheme,u.netloc,u.path,urllib.parse.urlencode(q),''))
def public_url(url):
 u=urllib.parse.urlsplit(url)
 if u.scheme!='https' or not u.hostname or u.username or u.password:raise ValueError('Only public HTTPS URLs without embedded credentials are supported')
 addresses=socket.getaddrinfo(u.hostname,u.port or 443,type=socket.SOCK_STREAM)
 if any(not ipaddress.ip_address(x[4][0]).is_global for x in addresses):raise ValueError('Private/local network URLs are not supported')
 return url
class PublicRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  public_url(newurl)
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def open_public(url):
 public_url(url)
 return urllib.request.build_opener(PublicRedirect()).open(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 news-video-workflow/1.1'}),timeout=40)
def paths(project):
 root=Path(project).resolve();cfg=root/'runtime.local.json';d=json.loads(cfg.read_text()) if cfg.exists() else {}
 media=Path(os.environ.get('NEWS_MEDIA_ROOT',d.get('mediaRoot',str(root)))).expanduser().resolve()
 if not media.is_dir():raise RuntimeError('Configured media root is absent')
 public=media/'public';assets=public/'media';assets.mkdir(parents=True,exist_ok=True)
 reports=root/'reports';reports.mkdir(exist_ok=True)
 return root,public,assets,reports
def digest(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def record(project,row):
 _,_,_,reports=paths(project);p=reports/'materials.json';rows=json.loads(p.read_text()) if p.exists() else [];rows.append(row)
 tmp=p.with_suffix('.'+uuid.uuid4().hex+'.tmp');tmp.write_text(json.dumps(rows,ensure_ascii=False,indent=2));tmp.replace(p);return row
def import_file(project,source,source_url='provided-local',purpose='context',original=False,metadata=None):
 _,public,assets,_=paths(project);src=Path(source).expanduser().resolve()
 if not src.is_file():raise ValueError('Provided local material is not a file')
 h=digest(src);name=re.sub(r'[^\w.\-\u4e00-\u9fff]','_',src.name)[:120];dst=assets/(h[:16]+'-'+name)
 if not dst.exists():shutil.copyfile(src,dst)
 if src.stat().st_size!=dst.stat().st_size or digest(dst)!=h:raise RuntimeError('Material copy verification failed')
 return record(project,{'ok':True,'asset':dst.relative_to(public).as_posix(),'sourceUrl':safe_url(source_url),'purpose':purpose,'originalLayout':original,'bytes':dst.stat().st_size,'sha256':h,**(metadata or {})})
def direct(project,url,max_mb=500,purpose='context'):
 _,_,_,reports=paths(project)
 with tempfile.TemporaryDirectory(prefix='fetch-',dir=reports) as tmp:
  with open_public(url) as r:
   limit=max_mb*1024*1024;kind=r.headers.get_content_type()
   if int(r.headers.get('Content-Length','0'))>limit:raise ValueError('Remote file exceeds maximum size')
   ext=mimetypes.guess_extension(kind) or Path(urllib.parse.urlsplit(url).path).suffix or '.bin'
   path=Path(tmp)/('original'+ext);size=0
   with path.open('xb') as f:
    while chunk:=r.read(1024*1024):
     size+=len(chunk)
     if size>limit:raise ValueError('Remote file exceeds maximum size')
     f.write(chunk)
   if not size:raise ValueError('Remote file is empty')
   return import_file(project,path,url,purpose,kind=='text/html',{'contentType':kind})
class PageAssets(HTMLParser):
 def __init__(self,base):super().__init__();self.base=base;self.images=[];self.videos=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs);value=None
  if tag=='meta' and a.get('property') in ['og:image','twitter:image']:value=a.get('content')
  if tag=='img':value=a.get('data-src') or a.get('data-original') or a.get('src')
  if tag=='a' and re.search(r'\.(?:jpe?g|png|webp|gif|bmp)(?:[?#]|$)',a.get('href',''),re.I):value=a['href']
  if value:
   u=urllib.parse.urljoin(self.base,value)
   if u.startswith('https://') and u not in self.images:self.images.append(u)
  if tag in ['video','source'] and a.get('src'):
   u=urllib.parse.urljoin(self.base,a['src'])
   if u.startswith('https://') and u not in self.videos:self.videos.append(u)
def page(project,url,max_images=6,purpose='context'):
 row=direct(project,url,20,purpose);_,public,_,reports=paths(project);p=public/row['asset']
 parser=PageAssets(url);parser.feed(p.read_text(errors='replace'));results=[]
 for image in parser.images[:max_images]:
  try:results.append(direct(project,image,30,purpose))
  except Exception as e:results.append(record(project,{'ok':False,'sourceUrl':safe_url(image),'error':type(e).__name__,'action':'Check access or select another original asset'}))
 return {'originalPage':row,'images':results,'videoCandidates':[safe_url(x) for x in parser.videos],'note':'Review candidates for exact event/identity. A saved HTML file is not a report screenshot.'}
def ffmpeg_config(project):
 import importlib.util
 p=Path(project)/'scripts/common.py'
 if not p.exists():return [],os.environ.copy()
 spec=importlib.util.spec_from_file_location('_news_common',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 try:exe=m.ffmpeg();return ['--ffmpeg-location',str(Path(exe).parent)],m.tool_env(exe)
 except RuntimeError:return [],os.environ.copy()
def video(project,url,height=1080,browser=None,purpose='context',max_mb=500):
 public_url(url);_,_,_,reports=paths(project);ff,env=ffmpeg_config(project)
 with tempfile.TemporaryDirectory(prefix='video-',dir=reports) as tmp:
  template=str(Path(tmp)/'%(id)s.%(ext)s')
  args=yt(project)+['--ignore-config','--no-playlist','--no-progress','--no-warnings','--socket-timeout','25','--retries','2','--max-filesize',str(max_mb)+'M','--format',f'bv*[height<=?{height}]+ba/b[height<=?{height}]','--merge-output-format','mp4','--print-json','--output',template]+ff
  if browser:args+=['--cookies-from-browser',browser]
  r=subprocess.run(args+['--',url],capture_output=True,text=True,env=env,timeout=900)
  if r.returncode:
   text=r.stderr.lower();reason='login_or_platform_restriction' if any(x in text for x in ['login','cookie','403','412','premium','sign in']) else 'extractor_or_network_error'
   raise RuntimeError(reason+': use your own authorized browser login, inspect available formats, or provide an original file. No lower-resolution success is implied.')
  info=json.loads(r.stdout.strip().splitlines()[-1]);file=Path(info.get('_filename',''))
  # After merging, yt-dlp may change the extension.
  if not file.is_file():
   files=[p for p in Path(tmp).iterdir() if p.suffix in ['.mp4','.webm','.mkv','.mov']]
   if len(files)!=1:raise RuntimeError('Cannot uniquely locate downloaded video')
   file=files[0]
  if file.stat().st_size>max_mb*1024*1024:raise ValueError('Downloaded video exceeds maximum size')
  actual=info.get('height')
  if actual is None:
   python=Path(project)/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
   if python.exists():
    probe=subprocess.run([str(python),'-c','import av,json,sys;c=av.open(sys.argv[1]);s=c.streams.video[0];print(json.dumps({"height":s.height,"duration":float(c.duration/1000000) if c.duration else None}))',str(file)],capture_output=True,text=True,timeout=30)
    if probe.returncode==0:
     details=json.loads(probe.stdout);actual=details['height'];info['duration']=details['duration']
  return import_file(project,file,url,purpose,metadata={'title':info.get('title'),'requestedMaxHeight':height,'actualHeight':actual,'belowRequested':isinstance(actual,int) and actual<height,'duration':info.get('duration')})
def search(project,query,provider='commons',limit=6):
 limit=max(1,min(limit,20));results=[]
 if provider=='commons':
  q=urllib.parse.urlencode({'action':'query','format':'json','generator':'search','gsrsearch':query,'gsrnamespace':6,'gsrlimit':limit,'prop':'imageinfo','iiprop':'url|extmetadata'})
  with open_public('https://commons.wikimedia.org/w/api.php?'+q) as f:data=json.load(f)
  for item in data.get('query',{}).get('pages',{}).values():
   for image in item.get('imageinfo',[]):
    results.append({'title':item['title'],'url':image.get('descriptionurl'),'downloadUrl':image.get('url'),'license':image.get('extmetadata',{}).get('LicenseShortName',{}).get('value'),'purpose':'candidate-context-not-verified-event'})
 elif provider=='youtube':
  r=subprocess.run(yt(project)+['--ignore-config','--flat-playlist','--dump-single-json','--socket-timeout','25','--',f'ytsearch{limit}:{query}'],capture_output=True,text=True,timeout=120)
  if r.returncode:raise RuntimeError('Video search failed; use Codex web search or another provider')
  for x in json.loads(r.stdout).get('entries',[]):results.append({'title':x.get('title'),'url':x.get('url'),'purpose':'candidate-not-verified-event'})
 elif provider=='brave':
  key=os.environ.get('BRAVE_SEARCH_API_KEY')
  if not key:raise RuntimeError('Set your own BRAVE_SEARCH_API_KEY, or use Codex web search / commons')
  req=urllib.request.Request('https://api.search.brave.com/res/v1/web/search?'+urllib.parse.urlencode({'q':query,'count':limit}),headers={'X-Subscription-Token':key,'Accept':'application/json'})
  with urllib.request.urlopen(req,timeout=40) as f:data=json.load(f)
  results=[{'title':x.get('title'),'url':x.get('url'),'description':x.get('description')} for x in data.get('web',{}).get('results',[])]
 _,_,_,reports=paths(project);p=reports/('search-'+uuid.uuid4().hex[:8]+'.json');p.write_text(json.dumps({'query':query,'provider':provider,'results':results},ensure_ascii=False,indent=2));return {'results':results,'report':str(p)}
