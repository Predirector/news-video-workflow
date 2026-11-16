#!/usr/bin/env python3
"""Upgrade an unmodified v1.1 starter safely. Never overwrite custom source/data."""
from pathlib import Path
import argparse,hashlib,json,shutil,sys
p=argparse.ArgumentParser(description=__doc__);p.add_argument('project');p.add_argument('--apply',action='store_true');a=p.parse_args();root=Path(a.project).expanduser().resolve();skill=Path(__file__).resolve().parents[1];starter=skill/'assets/starter'
if not root.is_dir() or not (root/'episode.json').is_file():p.error('Choose an existing news-video project')
baseline=json.loads((skill/'assets/upgrade-v110-hashes.json').read_text());updates=[];blocked=[]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
for src in starter.rglob('*'):
 if not src.is_file() or '__pycache__' in src.parts or src.suffix=='.pyc':continue
 rel=src.relative_to(starter).as_posix()
 if rel in ['episode.json','.gitignore']:continue
 dst=root/rel
 if dst.exists() and sha(dst)==sha(src):continue
 if dst.exists() and sha(dst) not in baseline.get(rel,[]):blocked.append(rel);continue
 updates.append((src,dst,rel))
for name,target in [('editorial-rules.md','PRODUCTION_RULES.md'),('implementation-matrix.md','IMPLEMENTATION_MATRIX.md')]:
 src=skill/'references'/name;dst=root/target
 if dst.exists() and sha(dst)!=sha(src):blocked.append(target)
 elif not dst.exists():updates.append((src,dst,target))
plan={'project':str(root),'updates':[x[2] for x in updates],'blockedCustomFiles':blocked,'preserved':['episode text/timings','public media','runtime.local.json','account credentials'],'apply':a.apply}
print(json.dumps(plan,ensure_ascii=False,indent=2))
if blocked:raise SystemExit('Custom files found. Compare and port changes manually; nothing was overwritten.')
if a.apply:
 for src,dst,_ in updates:dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
 d=json.loads((root/'episode.json').read_text())
 if not d.get('fontPreset'):
  known=set(d.get('fonts',{}).values())<= {'fonts/NotoSansSC.ttf','fonts/NotoSerifSC.ttf'}
  d['fontPreset']='style-default' if known else 'custom'
  if not known:d['fonts'].setdefault('subtitle',d['fonts']['body'])
 (root/'episode.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
 ignore=root/'.gitignore';existing=ignore.read_text() if ignore.exists() else ''
 for line in (starter/'.gitignore').read_text().splitlines():
  if line and line not in existing.splitlines():existing+='\n'+line
 ignore.write_text(existing.rstrip()+'\n')
 print('Upgraded. Run bootstrap.py, prepare.py and actual visual review. No existing media or finished video was deleted.')
