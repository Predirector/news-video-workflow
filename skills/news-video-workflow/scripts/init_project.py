#!/usr/bin/env python3
"""Copy the bundled runtime into a new independent project; never overwrite."""
from pathlib import Path
import argparse,shutil,json
p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination');p.add_argument('--media-root',help='Optional existing/writable media destination; code stays in destination');a=p.parse_args();dst=Path(a.destination).expanduser().resolve();src=Path(__file__).resolve().parents[1]/'assets/starter'
if dst.exists():p.error('Destination exists. Choose a new folder; existing projects are not overwritten.')
shutil.copytree(src,dst,ignore=shutil.ignore_patterns("node_modules",".venv","__pycache__","*.pyc","runtime.local.json",".env",".env.*","output","reports","episode.compiled.json"))
refs=Path(__file__).resolve().parents[1]/'references'
for source,target in [('editorial-rules.md','PRODUCTION_RULES.md'),('implementation-matrix.md','IMPLEMENTATION_MATRIX.md')]:
 text=(refs/source).read_text().replace('](implementation-matrix.md)','](IMPLEMENTATION_MATRIX.md)').replace('](editorial-rules.md)','](PRODUCTION_RULES.md)')
 (dst/target).write_text(text)
if a.media_root:(dst/'runtime.local.json').write_text(json.dumps({'mediaRoot':str(Path(a.media_root).expanduser().resolve())},ensure_ascii=False,indent=2))
print(json.dumps({'project':str(dst),'next':'Run python3 scripts/bootstrap.py inside this project; then edit episode.json and add real media.'},ensure_ascii=False))
