"""Project-local acquisition tools; credentials stay in the official CLI keychain."""
from pathlib import Path
import json,os,shutil,subprocess,sys,venv
LARK_VERSION='1.0.100'
YTDLP_VERSION='2026.10.26'
def run(args,**kw):
 return subprocess.run([str(x) for x in args],check=True,**kw)
def lark(project):
 override=os.environ.get('NEWS_LARK_CLI')
 if override:return [override]
 existing=shutil.which('lark-cli')
 if existing:return [existing]
 path=Path(project)/'.news-tools/node_modules/@larksuite/cli/scripts/run.js'
 if path.exists():return ['node',str(path)]
 raise RuntimeError('Official Lark CLI missing. Run news.py --project DIR setup first.')
def yt(project):
 p=Path(project)/'.news-tools/venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
 if p.exists():return [str(p),'-m','yt_dlp']
 if shutil.which('yt-dlp'):return ['yt-dlp']
 raise RuntimeError('yt-dlp missing. Run setup first.')
def setup(project):
 if sys.version_info<(3,12):raise RuntimeError('Python >=3.12 is required. Install it and rerun setup.')
 root=Path(project).resolve();tools=root/'.news-tools';tools.mkdir(exist_ok=True)
 if not shutil.which('node') or not shutil.which('npm'):raise RuntimeError('Install Node.js with npm first, then rerun setup.')
 try:cmd=lark(root)
 except RuntimeError:
  run(['npm','install','--prefix',tools,'--ignore-scripts','--no-audit','--no-fund','--save-exact','@larksuite/cli@'+LARK_VERSION]);cmd=lark(root)
 playwright=tools/'node_modules/playwright-core/package.json'
 if not playwright.exists() or json.loads(playwright.read_text()).get('version')!='1.65.1':
  run(['npm','install','--prefix',tools,'--ignore-scripts','--no-audit','--no-fund','--save-exact','playwright-core@1.65.1'])
 run(cmd+['--version']) # official downloader verifies its release checksum
 help_=subprocess.run(cmd+['auth','login','--help'],capture_output=True,text=True,timeout=30)
 if help_.returncode or '--device-code' not in help_.stdout or '--no-wait' not in help_.stdout:
  raise RuntimeError('Existing Lark CLI is incompatible; upgrade your own CLI or set NEWS_LARK_CLI. No configuration was overwritten.')
 p=tools/'venv';exe=p/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
 if not exe.exists():venv.EnvBuilder(with_pip=True).create(p)
 check=subprocess.run([str(exe),'-c',f'import importlib.metadata as m;assert m.version("yt-dlp")=="{YTDLP_VERSION}"'],capture_output=True)
 if check.returncode:run([exe,'-m','pip','install','yt-dlp=='+YTDLP_VERSION])
 return {'lark':cmd,'ytDlp':yt(root),'next':'connect --configure for first app setup; then connect to authorize read-only scopes'}
READ_SCOPES='docx:document:readonly docs:document.media:download drive:file:download sheets:spreadsheet:readonly wiki:wiki:readonly drive:drive:readonly offline_access'
def connect(project,configure=False,resume=None):
 cmd=lark(project)
 if configure:run(cmd+['config','init','--new'],cwd=project)
 if resume:return run(cmd+['auth','login','--device-code',resume],cwd=project)
 return run(cmd+['auth','login','--scope',READ_SCOPES,'--no-wait','--json'],cwd=project)
def cli_get(command,path,output=None,workspace=None):
 import urllib.parse
 u=urllib.parse.urlsplit(path);args=command+['api','GET','/open-apis'+u.path,'--as','user','--format','json']
 if u.query:args+=['--params',json.dumps(dict(urllib.parse.parse_qsl(u.query)))]
 cwd=Path(workspace).resolve() if workspace else None
 if output:
  target=Path(output).resolve();cwd=target.parent;args+=['--output',target.name]
 r=subprocess.run(args,capture_output=True,text=True,timeout=120,cwd=cwd)
 if r.returncode:
  # Return structured CLI errors, not raw stdout/doc bodies or credential-bearing diagnostics.
  try:
   e=json.loads(r.stderr).get('error',{});msg=f'{e.get("type","CLI")}/{e.get("code",r.returncode)}: {e.get("hint", "Check auth status, document permissions and read scopes.")}'
  except (ValueError,AttributeError):msg='CLI request failed. Run auth status; check app configuration and read scopes.'
  raise RuntimeError(msg)
 if output:return None
 j=json.loads(r.stdout)
 if j.get('ok') is False:raise RuntimeError('CLI returned unsuccessful API envelope')
 d=j.get('data',j)
 if isinstance(d,dict) and 'code' in d:
  if d['code']:raise RuntimeError(f'Feishu API code {d["code"]}')
  return d.get('data',d)
 return d
