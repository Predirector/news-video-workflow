#!/usr/bin/env python3
"""Project setup, official Feishu login, numbered intake and material collection."""
from pathlib import Path
import argparse,json,subprocess,sys,tempfile,urllib.parse,urllib.error
import toolchain,materials,intake

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',required=True);sub=p.add_subparsers(dest='command',required=True)
 sub.add_parser('setup').add_argument('--runtime',action='store_true',help='Also install the video runtime dependencies')
 c=sub.add_parser('connect');c.add_argument('--configure',action='store_true');c.add_argument('--resume',help='Device code returned by the official CLI; not an access token')
 sub.add_parser('status')
 c=sub.add_parser('intake');c.add_argument('--url',required=True);c.add_argument('--item',required=True);c.add_argument('--download',action='store_true');c.add_argument('--sheet');c.add_argument('--section',help='Exact parent section heading when item numbers repeat');c.add_argument('--range',default='A1:Z200')
 c=sub.add_parser('search');c.add_argument('query');c.add_argument('--provider',choices=['commons','youtube','brave'],default='commons');c.add_argument('--limit',type=int,default=6)
 c=sub.add_parser('fetch');c.add_argument('url');c.add_argument('--kind',choices=['file','page','video','screenshot'],required=True);c.add_argument('--purpose',choices=['fact','context'],default='context');c.add_argument('--height',type=int,default=1080);c.add_argument('--browser',help='Explicit consent to use this browser login, e.g. chrome');c.add_argument('--selector');c.add_argument('--max-mb',type=int,default=500)
 c=sub.add_parser('import');c.add_argument('file');c.add_argument('--purpose',choices=['fact','context'],default='context')
 c=sub.add_parser('collect');c.add_argument('--input',required=True,help='Intake result JSON with selected links');c.add_argument('--browser');c.add_argument('--max-links',type=int,default=12)
 a=p.parse_args();root=Path(a.project).expanduser().resolve()
 if a.command=='setup':
  if not root.exists():subprocess.run([sys.executable,str(Path(__file__).with_name('init_project.py')),str(root)],check=True)
  if not (root/'episode.json').is_file():raise ValueError('Choose a new project folder or an existing news-video project')
  result=toolchain.setup(root)
  if a.runtime:subprocess.run([sys.executable,'scripts/bootstrap.py'],cwd=root,check=True)
 elif not root.is_dir():raise ValueError('Project directory is absent; run setup first')
 elif a.command=='connect':toolchain.connect(root,a.configure,a.resume);return
 elif a.command=='status':subprocess.run(toolchain.lark(root)+['auth','status'],check=True,cwd=root);return
 elif a.command=='intake':result=intake.intake(root,a.url,a.item,a.download,a.sheet,a.range,a.section)
 elif a.command=='search':result=materials.search(root,a.query,a.provider,a.limit)
 elif a.command=='import':result=materials.import_file(root,a.file,purpose=a.purpose)
 elif a.command=='fetch':
  if a.max_mb<1 or a.height<1:raise ValueError('Height and maximum size must be positive')
  if a.kind=='file':result=materials.direct(root,a.url,a.max_mb,a.purpose)
  elif a.kind=='page':result=materials.page(root,a.url,purpose=a.purpose)
  elif a.kind=='video':result=materials.video(root,a.url,a.height,a.browser,a.purpose,a.max_mb)
  else:
   materials.public_url(a.url);_,_,_,reports=materials.paths(root)
   with tempfile.TemporaryDirectory(prefix='screenshot-',dir=reports) as tmp:
    path=Path(tmp)/'original-page.png';subprocess.run(['node',str(Path(__file__).with_name('screenshot.mjs')),str(root),a.url,str(path)]+([a.selector] if a.selector else []),check=True,timeout=120);result=materials.import_file(root,path,a.url,a.purpose,True)
 elif a.command=='collect':
  data=json.loads(Path(a.input).read_text());rows=[]
  for url in data.get('links',[])[:max(1,min(a.max_links,30))]:
   host=urllib.parse.urlsplit(url).hostname or '';suffix=Path(urllib.parse.urlsplit(url).path).suffix.lower()
   try:
    if host.endswith(('feishu.cn','larksuite.com')):rows.append({'sourceUrl':materials.safe_url(url),'ok':False,'action':'Read this linked Feishu source with intake; do not treat a login page as material'});continue
    if host.endswith(('bilibili.com','b23.tv','youtube.com','youtu.be','douyin.com')) or suffix in ['.m3u8']:
     rows.append(materials.video(root,url,browser=a.browser))
    elif suffix in ['.jpg','.jpeg','.png','.webp','.pdf','.mp4','.mov','.webm','.zip']:
     rows.append(materials.direct(root,url))
    else:rows.append(materials.page(root,url))
   except Exception as e:rows.append(materials.record(root,{'ok':False,'sourceUrl':materials.safe_url(url),'error':type(e).__name__,'action':'Check login/platform restriction or provide another original source'}))
  result={'results':rows,'note':'Review factual identity and select usable shots; download success is not editorial verification.'}
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':
 try:main()
 except urllib.error.HTTPError as e:raise SystemExit(f'HTTP {e.code}: source unavailable or access restricted; inspect the original URL and use another original source if needed.')
 except (RuntimeError,ValueError,subprocess.SubprocessError,OSError) as e:raise SystemExit(str(e) if isinstance(e,(RuntimeError,ValueError)) else type(e).__name__+': run status or inspect the dependency/network prerequisites')
