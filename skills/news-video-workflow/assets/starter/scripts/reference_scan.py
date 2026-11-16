#!/usr/bin/env python3
"""Extract an inspectable local reference sheet; never invent its font or music identity."""
from common import *
import argparse,av
from PIL import Image,ImageDraw
p=argparse.ArgumentParser(description=__doc__);p.add_argument('file');p.add_argument('--source-url',default='provided-local-reference');a=p.parse_args();src=Path(a.file).expanduser().resolve()
if not src.is_file():p.error('Reference file absent')
c=av.open(str(src));s=c.streams.video[0];duration=float(s.duration*s.time_base) if s.duration is not None else c.duration/av.time_base;fps=float(s.average_rate or 30);job=reports()/'reference-library'/sha(src)[:16];job.mkdir(parents=True,exist_ok=True);targets=[0]+[duration*f for f in [.02,.10,.25,.4,.55,.7,.85,.97]];images=[]
for i,t in enumerate(targets):
 c.seek(max(0,int(t/s.time_base)),stream=s,backward=True)
 chosen=None
 for frame in c.decode(video=0):
  chosen=frame
  if frame.time is not None and frame.time>=t:break
 if chosen is None:raise RuntimeError('Could not decode reference sample')
 im=chosen.to_image();path=job/f'frame-{i:02}.jpg';im.save(path,quality=93);images.append((im,float(chosen.time or t),path.name))
c.close();sheet=Image.new('RGB',(810,1500),'#eee');draw=ImageDraw.Draw(sheet)
for i,(im,t,_) in enumerate(images):
 im.thumbnail((270,480));sheet.paste(im,(i%3*270,i//3*500));draw.text((i%3*270+8,i//3*500+482),f'{t:.2f}s',fill='black')
sheet.save(job/'contact.jpg',quality=93)
card={'sourceFile':str(src),'sourceUrl':a.source_url,'sha256':sha(src),'duration':duration,'fps':fps,'dimensions':[s.width,s.height],'samples':[{'file':n,'seconds':t} for _,t,n in images],'analysisStatus':'needs actual frame/audio review','templateStatus':'reference only, not yet a reusable verified renderer','coreExpression':'','titleFont':{'name':None,'confidence':'unknown until evidence is available','strokeAndEffects':''},'subtitleFont':'','bodyFont':'','layoutAndSafeArea':'','backgroundAndTexture':'','realImageAndReportTreatment':'','captionMode':'','transitionAndRhythm':'','music':{'identity':None,'channelVerified':False,'listeningNotes':''},'suitableTopics':[],'reproductionAssetsAndPermissions':[],'differencesFromExistingTemplates':''}
save_json(job/'style-card.json',card);print(json.dumps({'contact':str(job/'contact.jpg'),'styleCard':str(job/'style-card.json'),'note':'Inspect actual samples and listen to the original before filling this card. Names/popularity are not inferred.'},ensure_ascii=False))
