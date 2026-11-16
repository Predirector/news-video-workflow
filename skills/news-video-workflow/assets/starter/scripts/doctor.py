#!/usr/bin/env python3
from common import *
import platform,importlib.util
result={'python':platform.python_version(),'node':None,'missing':[]}
try:result['node']=subprocess.check_output(['node','--version'],text=True).strip()
except Exception:result['missing'].append('Node.js >=20')
for mod in ['av','numpy','PIL']:
 if importlib.util.find_spec(mod) is None:result['missing'].append(mod)
expected=json.loads((ROOT/'package.json').read_text())['dependencies'];wrong=[]
for name,ver in expected.items():
 p=ROOT/'node_modules'/name/'package.json'
 if not p.exists():wrong.append(name+' missing')
 elif json.loads(p.read_text()).get('version')!=ver:wrong.append(name+' version differs from package.json')
result['dependencyProblems']=wrong
try:result['ffmpeg']=ffmpeg()
except Exception:result['missing'].append('FFmpeg')
try:
 result['mediaRoot']=str(media_root());result['mediaWritable']=os.access(media_root(),os.W_OK)
 if not result['mediaWritable']:result['missing'].append('writable media directory')
except Exception as e:result['missing'].append(str(e))
print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(1 if result['missing'] or wrong else 0)
