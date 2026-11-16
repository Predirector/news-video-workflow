#!/usr/bin/env python3
"""Import the user's licensed files into this episode; never install system fonts."""
from common import *
import argparse
from fontTools.ttLib import TTFont
p=argparse.ArgumentParser(description=__doc__)
for role in ['title','subtitle','body']:p.add_argument('--'+role,required=True)
a=p.parse_args();d=json.loads((ROOT/'episode.json').read_text());fonts={}
for role in ['title','subtitle','body']:
 src=Path(getattr(a,role)).expanduser().resolve();f=TTFont(src);f.close();h=sha(src);rel='fonts/'+h[:16]+src.suffix.lower();dest=asset(rel);dest.parent.mkdir(exist_ok=True)
 if not dest.exists():shutil.copyfile(src,dest)
 if sha(dest)!=h:raise RuntimeError('Font copy verification failed')
 fonts[role]=rel
d['fontPreset']='custom';d['fonts']=fonts;save_json(ROOT/'episode.json',d)
print(json.dumps({'fontPreset':'custom','fonts':fonts,'note':'Source font files retained. Their own licensing continues to apply.'},ensure_ascii=False,indent=2))
