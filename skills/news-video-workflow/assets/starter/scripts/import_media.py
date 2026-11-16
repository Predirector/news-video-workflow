#!/usr/bin/env python3
from common import *
import argparse
p=argparse.ArgumentParser(description='Copy a provided media file into this project and record its source. No source deletion.');p.add_argument('file');p.add_argument('--source-url',default='provided-local');p.add_argument('--purpose',choices=['fact','context','demo'],default='fact');a=p.parse_args();src=Path(a.file).expanduser().resolve();assert src.is_file();digest=sha(src);rel='media/'+digest[:12]+'-'+src.name;dst=asset(rel);dst.parent.mkdir(parents=True,exist_ok=True)
if not dst.exists():shutil.copyfile(src,dst)
assert dst.stat().st_size==src.stat().st_size and sha(dst)==digest
file=reports()/'imported-media.json';rows=json.loads(file.read_text()) if file.exists() else [];rows.append({'asset':rel,'sourceUrl':a.source_url,'purpose':a.purpose,'bytes':dst.stat().st_size,'sha256':digest});save_json(file,rows);print(json.dumps(rows[-1],ensure_ascii=False))
