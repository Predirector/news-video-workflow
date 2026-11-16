from pathlib import Path
import os,json,subprocess,shutil,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
def config():return json.loads((ROOT/'runtime.local.json').read_text()) if (ROOT/'runtime.local.json').exists() else {}
def media_root():
 p=Path(os.environ.get('NEWS_MEDIA_ROOT',config().get('mediaRoot',str(ROOT)))).expanduser().resolve()
 if p!=ROOT and not p.exists():raise RuntimeError('Configured media root is absent. Mount/create the intended destination; no automatic internal-disk fallback.')
 return p
def public():return media_root()/'public'
def output():return media_root()/'output'
def reports():
 p=ROOT/'reports';p.mkdir(exist_ok=True);return p
def asset(name):
 if not isinstance(name,str) or not name:raise ValueError('Asset path required')
 p=(public()/name).resolve()
 if not p.is_relative_to(public().resolve()):raise ValueError('Asset paths must stay inside this project public directory')
 return p
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest() if hasattr(hashlib,'file_digest') else _oldhash(f)
def _oldhash(f):
 h=hashlib.sha256()
 for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def tool_env(exe):
 env=os.environ.copy();parent=str(Path(exe).resolve().parent)
 if sys.platform=='darwin' and list(Path(parent).glob('libav*.dylib')):env['DYLD_LIBRARY_PATH']=parent+(':'+env['DYLD_LIBRARY_PATH'] if env.get('DYLD_LIBRARY_PATH') else '')
 elif sys.platform.startswith('linux') and list(Path(parent).glob('libav*.so*')):env['LD_LIBRARY_PATH']=parent+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
 elif os.name=='nt':env['PATH']=parent+os.pathsep+env.get('PATH','')
 return env
def checked_ffmpeg(exe):
 r=subprocess.run([str(exe),'-version'],env=tool_env(exe),capture_output=True,text=True)
 if r.returncode:raise RuntimeError('FFmpeg exists but cannot run. Check its local libraries or select a working FFMPEG_PATH.')
 return str(exe)
def ffmpeg():
 found=os.environ.get('FFMPEG_PATH') or config().get('ffmpeg') or shutil.which('ffmpeg')
 if found and Path(found).is_file():return checked_ffmpeg(Path(found).resolve())
 script="const fs=require('fs'),path=require('path');const n='@remotion/compositor-'+process.platform+'-'+process.arch+(process.platform==='linux'?'-gnu':process.platform==='win32'?'-msvc':'');const p=path.join(path.dirname(require.resolve(n+'/package.json')),'ffmpeg'+(process.platform==='win32'?'.exe':''));if(fs.existsSync(p))process.stdout.write(p);"
 r=subprocess.run(['node','-e',script],cwd=ROOT,text=True,capture_output=True)
 if r.returncode==0 and r.stdout.strip():return checked_ffmpeg(r.stdout.strip())
 raise RuntimeError('FFmpeg missing: install ffmpeg, set FFMPEG_PATH, or install the project Node dependencies first.')
def run(args):subprocess.run([str(v) for v in args],check=True,cwd=ROOT,env=tool_env(args[0]))
def save_json(p,value):Path(p).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def validate(d,check_files=True):
 from visual import resolve_fonts
 resolve_fonts(d)
 if d.get('mode') not in ['news','speech']:raise ValueError('mode must be news or speech')
 if d.get('style') not in ['paper-red','speed-yellow','berry-progress']:raise ValueError('Unknown style')
 if any(c in d.get('name','') for c in '/\\\0') or not d.get('name'):raise ValueError('Use the full numbered title without path separators')
 if not d.get('mainTitle') or not d.get('subtitle'):raise ValueError('Provide exact mainTitle and subtitle arrays')
 if len(d['mainTitle'])>2 or len(d['subtitle'])>2:raise ValueError('Starter layout supports up to two main and subtitle lines. For longer titles adapt both the renderer and layout checks, never truncate the script.')
 if d.get('expectedTitles'):
  if ''.join(d['mainTitle'])!=d['expectedTitles']['main'] or ''.join(d['subtitle'])!=d['expectedTitles']['subtitle']:raise ValueError('Main/subtitle differ from expected script wording')
 if not 0.5<=float(d.get('speechRate',1))<=2:raise ValueError('speechRate must be 0.5..2')
 rate=float(d.get('speechRate',1)) if d['mode']=='speech' else 1
 n=3
 for i,s in enumerate(d.get('segments',[])):
  if s.get('kind') not in ['image','video']:raise ValueError(f'Segment {i}: use an original image/video asset')
  dur=float(s.get('duration',0));assert dur>0,f'Segment {i}: duration must be positive'
  if dur/rate<.2:raise ValueError(f'Segment {i}: too short; would flash')
  if s.get('kind')=='image' and s.get('voice'):raise ValueError('A still image cannot supply speech')
  if not d.get('demo') and s.get('asset','').startswith('demo/'):raise ValueError('Demo graphics must not enter a real news video')
  if s.get('evidence') and s['evidence'].get('original') is not True:raise ValueError('Article evidence must be original layout, not a redrawn report')
  mark=s.get('mark')
  if mark and s['kind']!='image':raise ValueError('Mark a stable original screenshot, not a moving video')
  if mark and (len(mark)!=4 or any(not 0<=float(v)<=1 for v in mark) or mark[0]+mark[2]>1 or mark[1]+mark[3]>1):raise ValueError('mark is a normalized [x,y,width,height] inside the displayed source')
  if check_files and not asset(s['asset']).is_file():raise FileNotFoundError(f'Missing segment asset: {s["asset"]}')
  if len(s.get('caption','').replace('\n',''))>(51 if d['mode']=='news' else 34):raise ValueError('Caption too long for a readable screen; split it into complete phrases')
  if d['mode']=='news' and len(s.get('caption','').replace('\n',''))>max(0,dur-1)*18:raise ValueError(f'Segment {i}: not enough reading time after reveal')
  n+=__import__('math').ceil(round(dur*30)/rate)
 if n==3:raise ValueError('At least one segment is required')
 if n/30>20 and not d.get('durationReason') and not d.get('demo'):raise ValueError('Over 20s: provide durationReason that explains the necessary information/speech')
 if not d.get('bgm') and not d.get('allowSilent'):raise ValueError('Provide continuous music, or explicitly set allowSilent for this episode')
 for rel in [d['cover']['asset'],*d.get('fonts',{}).values(),*([d['background']['asset']] if d.get('background',{}).get('asset') else []),*([d['speechAsset']] if d.get('speechAsset') else [])]+([d['bgm']['asset']] if d.get('bgm') else []):
  if check_files and not asset(rel).is_file():raise FileNotFoundError(f'Missing asset: {rel}')
 if d.get('speechAsset') and any(s.get('voice') for s in d['segments']):raise ValueError('Choose speechAsset or per-video voice=true, not both')
 if d['mode']=='speech' and not any(s.get('voice') for s in d['segments']) and not d.get('speechAsset'):raise ValueError('Speech mode needs voice=true video segments or speechAsset')
 return n
