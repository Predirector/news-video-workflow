#!/usr/bin/env python3
"""Install only missing project dependencies; keep tools and media portable."""
from pathlib import Path
import sys,subprocess,shutil,urllib.request,json,argparse,os
ROOT=Path(__file__).resolve().parents[1]
if sys.version_info<(3,12):raise SystemExit('Python >=3.12 is required for the locked media dependencies.')
p=argparse.ArgumentParser();p.add_argument('--skip-fonts',action='store_true');p.add_argument('--skip-browser',action='store_true');p.add_argument('--skip-python',action='store_true');a=p.parse_args()
if not shutil.which('node') or not shutil.which('npm'):raise SystemExit('Install Node.js 20.19 (20 series) or >=22.12 and retry. No global packages will be installed by this script.')
node_version=json.loads(subprocess.check_output(['node','-p','JSON.stringify(process.versions.node.split(".").map(Number))'],text=True));major,minor=node_version[:2];assert (major==20 and minor>=19) or major>22 or (major==22 and minor>=12),'Node.js 20.19.x (20 series) or >=22.12 is required'
expected=json.loads((ROOT/'package.json').read_text())['dependencies'];node_ok=all((ROOT/'node_modules'/n/'package.json').is_file() and json.loads((ROOT/'node_modules'/n/'package.json').read_text()).get('version')==v for n,v in expected.items())
if not node_ok:
 if (ROOT/'node_modules').is_symlink():raise SystemExit('Project node_modules points elsewhere; use an independent project before installing pinned dependencies.')
 subprocess.run(['npm','ci' if (ROOT/'package-lock.json').exists() else 'install','--ignore-scripts'],cwd=ROOT,check=True)
venv=ROOT/'.venv';python=venv/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
if not a.skip_python:
 if not python.exists():subprocess.run([sys.executable,'-m','venv',str(venv)],check=True)
 requirements=dict(line.strip().split('==',1) for line in (ROOT/'requirements.txt').read_text().splitlines() if '==' in line)
 check=subprocess.run([str(python),'-c',f'import importlib.metadata as m; expected={requirements!r}; assert all(m.version(n)==v for n,v in expected.items())'],capture_output=True)
 if check.returncode:subprocess.run([str(python),'-m','pip','install','-r',str(ROOT/'requirements.txt')],check=True)
from common import public,config,ffmpeg
pub=public();pub.mkdir(parents=True,exist_ok=True)
for src in (ROOT/'public').rglob('*'):
 if src.is_file():
  dst=pub/src.relative_to(ROOT/'public')
  if src.resolve()!=dst.resolve() and not dst.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
if not a.skip_fonts:
 for name,slug in [('NotoSansSC','notosanssc'),('NotoSerifSC','notoserifsc')]:
  folder=pub/'fonts';folder.mkdir(exist_ok=True)
  for file,url in [(name+'.ttf',f'https://raw.githubusercontent.com/google/fonts/main/ofl/{slug}/{name}%5Bwght%5D.ttf'),(name+'-OFL.txt',f'https://raw.githubusercontent.com/google/fonts/main/ofl/{slug}/OFL.txt')]:
   dst=folder/file
   if not dst.exists():
    temp=dst.with_suffix(dst.suffix+'.part')
    with urllib.request.urlopen(url,timeout=60) as response,temp.open('wb') as out:shutil.copyfileobj(response,out)
    temp.replace(dst)
if not a.skip_browser:
 cmd=['node',str(ROOT/'node_modules/@remotion/cli/remotion-cli.js'),'browser','ensure'];exe=os.environ.get('REMOTION_BROWSER_EXECUTABLE') or config().get('browserExecutable')
 if exe:cmd+=['--browser-executable',exe]
 subprocess.run(cmd,cwd=ROOT,check=True)
print(json.dumps({'project':str(ROOT),'public':str(pub),'ffmpeg':ffmpeg(),'python':str(python) if python.exists() else sys.executable,'next':'Use the project Python (.venv/bin/python on macOS/Linux) for prepare.py, verify.py and cleanup.py.'},ensure_ascii=False,indent=2))
