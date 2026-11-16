#!/usr/bin/env python3
from common import *
import math,wave
import numpy as np,av
from PIL import Image,ImageFont
D=json.loads((ROOT/'episode.json').read_text());PUB=public();PUB.mkdir(parents=True,exist_ok=True);TMP=PUB/'processed';TMP.mkdir(exist_ok=True);SR=48000;FPS=30
# Demo-only generated music. No generated editorial assets enter a real episode.
if D.get('demo'):
 dest=asset('demo/rhythm.wav');dest.parent.mkdir(exist_ok=True);t=np.arange(SR*30)/SR;y=np.zeros_like(t)
 for beat in np.arange(0,30,.46875):
  q=t-beat;z=np.maximum(q,0);y+=np.where((q>=0)&(q<.19),.25*np.sin(2*np.pi*(58*z+8*(1-np.exp(-20*z))))*np.exp(-24*z),0)
 y+=.025*np.sin(2*np.pi*220*t)*(.5+.5*np.cos(2*np.pi*t/3.75))
 with wave.open(str(dest),'w') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((np.repeat(y[:,None],2,axis=1)*32767).astype('<i2').tobytes())
N=validate(D);RATE=float(D.get('speechRate',1)) if D['mode']=='speech' else 1
from visual import audit_fonts,layout
catalog=json.loads((ROOT/'font-catalog.json').read_text())
font_audit=audit_fonts(D,asset,catalog)
visual_layout=layout(D,asset,font_audit)
header_sizes=visual_layout['mainSizes']
save_json(reports()/'font-audit.json',font_audit)
ff=ffmpeg();compiled=dict(D);compiled['headerFonts']=header_sizes;compiled['fontAudit']=font_audit;compiled['visualLayout']=visual_layout;compiled.update(fps=FPS,frames=N,coverFrames=3,segments=[],subtitles=[]);voices=[];offset=3;raw_offset=0;timemap=[];cleanup=[]
def read_wav(file):
 with wave.open(str(file)) as w:return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2).astype(float)/32768
for i,s0 in enumerate(D['segments']):
 s=dict(s0);raw=float(s['duration']);base=round(raw*FPS);n=math.ceil(base/RATE);s.update(startFrame=offset,frames=n,rate=RATE);src=asset(s['asset'])
 if s['kind']=='video':
  c=av.open(str(src));st=c.streams.video[0];s.update(sourceWidth=st.width,sourceHeight=st.height);actual=float(st.duration*st.time_base) if st.duration is not None else c.duration/av.time_base if c.duration else None
  if actual is not None and float(s.get('sourceStart',0))+base/FPS>actual+.1:raise ValueError(f'Segment {i}: source interval exceeds original video duration')
  c.close();rel=f'processed/clip-{i:03}.mp4';out=asset(rel)
  run([ff,'-v','error','-ss',s.get('sourceStart',0),'-i',src,'-t',base/FPS,'-an','-r',FPS,'-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-y',out]);s['asset']=rel
 if s['kind']=='image' and s.get('crop'):
  im=Image.open(src);s.update(sourceWidth=im.width,sourceHeight=im.height)
 if s.get('crop'):
  x0,y0,cw,ch=map(float,s['crop'])
  if min(x0,y0)<0 or min(cw,ch)<=0 or x0+cw>s['sourceWidth'] or y0+ch>s['sourceHeight']:raise ValueError('Crop escapes source bounds; do not expose empty edges')
 x=np.zeros((n*1600,2))
 if D['mode']=='speech' and s.get('voice'):
  tmp=TMP/f'voice-part-{i:03}.wav';run([ff,'-v','error','-ss',s.get('sourceStart',0),'-t',base/FPS,'-i',src,'-vn','-af',f'atempo={RATE}','-ar',SR,'-ac','2','-y',tmp]);z=read_wav(tmp);x[:min(len(x),len(z))]=z[:len(x)];cleanup.append(str(tmp.relative_to(PUB)))
 if len(x)>192:x[:96]*=np.linspace(0,1,96)[:,None];x[-96:]*=np.linspace(1,0,96)[:,None]
 voices.append(x);compiled['segments'].append(s);timemap.append((raw_offset,raw_offset+base/FPS,offset,n));raw_offset+=base/FPS;offset+=n
v=np.vstack([np.zeros((4800,2)),*voices]);assert len(v)==N*1600
if D['mode']=='speech' and D.get('speechAsset'):
 tmp=TMP/'voice-separate.wav';run([ff,'-v','error','-i',asset(D['speechAsset']),'-vn','-af',f'atempo={RATE}','-ar',SR,'-ac','2','-y',tmp]);z=read_wav(tmp);v[4800:4800+min(len(z),len(v)-4800)]=z[:len(v)-4800];cleanup.append(str(tmp.relative_to(PUB)))
if D['mode']=='speech' and np.max(abs(v))<1e-6:raise ValueError('Speech mode has no audible speech source')
if np.max(abs(v))>0:v*=.82/(np.max(abs(v))+1e-12)
def mapped(t):
 for a,b,o,n in timemap:
  if a<=t<=b:return min(o+n,o+round((t-a)/RATE*FPS))
 return N
if D['mode']=='speech':
 if D.get('subtitles'):
  compiled['subtitles']=[{'a':mapped(float(s['start'])),'b':min(N,mapped(float(s['end']))),'text':s['text'],'keywords':s.get('keywords',[])} for s in D['subtitles']]
 else:compiled['subtitles']=[{'a':s['startFrame'],'b':s['startFrame']+s['frames'],'text':s.get('caption',''),'keywords':s.get('keywords',[])} for s in compiled['segments'] if s.get('caption')]
 for s in compiled['subtitles']:
  from visual import wrap,measured_font
  s['lines']=wrap(s['text'],measured_font(asset(D['fonts']['body']),54,font_audit['body']['selectedWeight']),924)
  if len(s['lines'])>2:raise ValueError('Speech subtitle needs a shorter complete phrase, not smaller text')
  if not 3<=s['a']<s['b']<=N:raise ValueError('Invalid subtitle interval')
m=np.zeros_like(v)
if D.get('bgm'):
 bg=D['bgm'];temp=TMP/'music-part.wav';run([ff,'-v','error','-ss',bg.get('start',0),'-i',asset(bg['asset']),'-vn','-t',N/FPS,'-ar',SR,'-ac','2','-y',temp]);z=read_wav(temp)
 if len(z)<len(m)-2400:raise ValueError('Music excerpt is too short; use one longer continuous excerpt, do not loop/stitch it silently.')
 m[:min(len(z),len(m))]=z[:len(m)]
 from music_analysis import analyze
 save_json(reports()/'music-analysis.json',analyze(m,SR,compiled['segments']))
 cleanup.append(str(temp.relative_to(PUB)));m*=.075/(np.sqrt(np.mean(m*m))+1e-12)
 if D['mode']=='speech':
  gain=np.full(N,.85)
  for s in compiled['subtitles']:gain[max(0,s['a']-4):min(N,s['b']+5)]=.38
  g=np.interp(np.arange(len(v))/1600,np.arange(N),gain);m*=g[:,None];mask=np.repeat(gain<.5,1600)
  if mask.any():m*=np.sqrt(np.mean(v[mask]**2))/10**(float(D.get('speechMusicGapDB',24))/20)/(np.sqrt(np.mean(m[mask]**2))+1e-12)
 m[:4800]*=np.linspace(0,1,4800)[:,None];m[-14400:]*=np.linspace(1,0,min(14400,len(m)))[:,None]
x=v+m
if abs(x).max()>.94:x*=.94/abs(x).max()
def save_wav(dest,x):
 with wave.open(str(dest),'w') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype('<i2').tobytes())
save_wav(asset('voice.wav'),v);save_wav(asset('mix.wav'),x)
from production_audit import audit
audit(compiled)
compiled['audioPeak']=float(abs(x).max());compiled['captionMode']='normal phrase' if D['mode']=='speech' else 'fixed-layout progressive';save_json(ROOT/'episode.compiled.json',compiled)
save_json(reports()/'prepared.json',{'frames':N,'seconds':N/FPS,'speechRate':RATE,'pitchPreserved':True,'musicRate':1,'audioPeak':compiled['audioPeak'],'episodeHash':sha(ROOT/'episode.json'),'media':[{'asset':str(p.relative_to(PUB)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in PUB.rglob('*') if p.is_file() and p.suffix!='.part']})
save_json(reports()/'process-files.json',cleanup);print(json.dumps({'prepared':True,'frames':N,'seconds':N/FPS,'mode':D['mode'],'rate':RATE},ensure_ascii=False))
