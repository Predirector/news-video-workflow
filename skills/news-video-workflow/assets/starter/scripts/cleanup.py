#!/usr/bin/env python3
from common import *
import argparse
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args();v=json.loads((reports()/'verification.json').read_text());F=Path(v['file']);assert sha(F)==v['sha256'];review=reports()/'review.json'
if a.apply:
 if not review.exists():raise SystemExit('Write reports/review.json from actual review; see review.example.json')
 from review_gate import validate_review
 validate_review(json.loads(review.read_text()),ROOT,media_root())
raw=json.loads((reports()/'process-files.json').read_text());candidates=[asset(rel) for rel in raw]+[p for p in (output()/'__checks').glob('frame-*.png')];rows=[]
for f in candidates:
 if not f.exists():continue
 if not (f.resolve().is_relative_to(public().resolve()) or f.resolve().is_relative_to((output()/'__checks').resolve())):raise ValueError('Refuse out-of-project cleanup')
 rows.append({'path':str(f.resolve()),'bytes':f.stat().st_size,'sha256':sha(f),'reason':'registered temporary audio or superseded frame check'})
log={'state':'listed','files':rows};save_json(reports()/'cleanup.json',log)
if not a.apply:print(json.dumps(log,ensure_ascii=False,indent=2));raise SystemExit(0)
for row in rows:Path(row['path']).unlink()
frame=min(v['frames']-1,max(3,round(v['frames']*.52)));run(['node','scripts/render.mjs','--frame',frame]);check=output()/f'__checks/frame-{frame}.png';im=Image.open(check);im.load();assert im.size==(1080,1920);log['actualPostCleanupRender']={'frame':frame,'dimensions':list(im.size),'sha256':sha(check)};check.unlink();assert sha(F)==v['sha256'];log.update(state='complete',finalHashUnchanged=True,releasedBytes=sum(row['bytes'] for row in rows));save_json(reports()/'cleanup.json',log);print(json.dumps({'state':'complete','releasedBytes':log['releasedBytes'],'actualRenderPassed':True}))
