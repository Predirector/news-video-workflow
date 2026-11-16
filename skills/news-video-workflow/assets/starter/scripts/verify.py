#!/usr/bin/env python3
from common import *
import av,numpy as np
from PIL import Image,ImageDraw
D=json.loads((ROOT/'episode.compiled.json').read_text());F=output()/(D['name']+'.mp4');N=D['frames'];c=av.open(str(F));v=c.streams.video[0];assert (v.width,v.height,v.average_rate)==(1080,1920,30)
extra=[max(3,min(N-1,s['startFrame']+offset)) for s in D['segments'] for offset in [1,round(s.get('revealFrames',30)/2),round(s.get('revealFrames',30))+4,s['frames']-1]]
points=sorted(set([0,1,2,3,N-1]+extra+[round(x) for x in np.linspace(3,N-1,8)]));samples={};prev=None;black=[];spikes=[]
for i,f in enumerate(c.decode(video=0)):
 a=f.reformat(width=108,height=192,format='gray').to_ndarray().astype(float)
 if a.mean()<20:black.append(i)
 if prev is not None:
  delta=float(abs(a-prev).mean())
  if delta>18:spikes.append([i,round(delta,2)])
 prev=a
 if i in points:samples[i]=f.to_image()
assert i+1==N,(i+1,N);assert not black,black
cover=Image.open(output()/(D['name']+'_封面.png')).convert('RGB');err=float(abs(np.asarray(cover,float)-np.asarray(samples[0],float)).mean());assert err<5
assert all(abs(np.asarray(samples[k],float)-np.asarray(samples[0],float)).mean()<3 for k in [1,2])
def read(p):
 c=av.open(str(p));r=av.AudioResampler(format='fltp',layout='stereo',rate=48000);return np.concatenate([z.to_ndarray() for f in c.decode(audio=0) for z in r.resample(f)],axis=1)
a=read(F);b=read(asset('mix.wav'));n=min(a.shape[1],b.shape[1]);assert abs(a.shape[1]/48000-N/30)<.15;assert abs(a).max()<1
corr=float(np.corrcoef(a[0,:n],b[0,:n])[0,1]) if np.std(b)>1e-8 else None
if corr is not None:assert corr>.96,corr
contact=output()/'__checks/final-contact.jpg';contact.parent.mkdir(exist_ok=True);sh=Image.new('RGB',(1080,1980),'#eee');dr=ImageDraw.Draw(sh)
for j,fr in enumerate([0]+[round(x) for x in np.linspace(3,N-1,8)]):sh.paste(samples[fr].resize((360,640)),(j%3*360,j//3*660));dr.text((j%3*360+8,j//3*660+643),f'{fr/30:.2f}s',fill='black')
sh.save(contact,quality=93)
for old in contact.parent.glob('phone-frame-*.png'):old.unlink()
phone=contact.parent/'cover-phone.png';samples[0].resize((360,640)).save(phone)
for k in extra:samples[k].resize((360,640)).save(contact.parent/f'phone-frame-{k}.png')
pairs=[[x[0],y[0]] for x,y in zip(spikes,spikes[1:]) if y[0]-x[0]<6]
report={'file':str(F),'sha256':sha(F),'frames':N,'seconds':N/30,'resolution':[1080,1920],'decodedAllFrames':True,'blackFrames':black,'firstThreeCoverFrames':True,'coverError':err,'audioPeak':float(abs(a).max()),'audioCorrelation':corr,'shortFlashCandidates':pairs,'contact':str(contact),'manualReviewRequired':True,'technicalPassDoesNotApproveVisuals':True,'fontAudit':D.get('fontAudit'),'productionAudit':str(reports()/'production-audit.json'),'phoneCover':str(phone),'speechRate':D.get('speechRate',1),'captionMode':D['captionMode']};save_json(reports()/'verification.json',report)
def ts(f):
 ms=round(f/30*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02},{ms:03}'
subs=D['subtitles'] if D['mode']=='speech' else [{'a':s['startFrame'],'b':s['startFrame']+s['frames'],'text':s.get('caption','')} for s in D['segments']]
(output()/(D['name']+'.srt')).write_text('\n\n'.join(f'{i+1}\n{ts(s["a"])} --> {ts(s["b"])}\n{s["text"]}' for i,s in enumerate(subs))+'\n',encoding='utf-8')
(output()/(D['name']+'_发布文案.txt')).write_text('\n'.join([''.join(D['mainTitle']),''.join(D['subtitle']),D.get('publishText',''),D.get('bgm',{}).get('credit','')])+'\n',encoding='utf-8');save_json(output()/(D['name']+'_来源.json'),D.get('sources',[]));print(json.dumps(report,ensure_ascii=False))
