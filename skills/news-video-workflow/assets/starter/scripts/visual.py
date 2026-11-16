"""Font identity, glyph coverage and measured production layout, without OS fallback."""
from pathlib import Path
import hashlib,json

STYLE_FONTS={
 'paper-red':{'title':'fonts/AlibabaPuHuiTi-2-115-Black.ttf','subtitle':'fonts/AlibabaPuHuiTi-2-105-Heavy.ttf','body':'fonts/AlibabaPuHuiTi-2-85-Bold.ttf'},
 'speed-yellow':{'title':'fonts/NotoSansSC.ttf','subtitle':'fonts/AlibabaPuHuiTi-2-105-Heavy.ttf','body':'fonts/AlibabaPuHuiTi-2-85-Bold.ttf'},
 'berry-progress':{'title':'fonts/AlibabaPuHuiTi-2-105-Heavy.ttf','subtitle':'fonts/AlibabaPuHuiTi-2-85-Bold.ttf','body':'fonts/AlibabaPuHuiTi-2-85-Bold.ttf'},
}

def resolve_fonts(d):
 preset=d.get('fontPreset')
 if preset=='style-default':d['fonts']=dict(STYLE_FONTS[d['style']])
 elif preset=='custom':
  if set(d.get('fonts',{}))!={'title','subtitle','body'}:raise ValueError('Custom fonts must explicitly bind title, subtitle and body files')
 elif not d.get('demo'):raise ValueError('Choose fontPreset=style-default or custom; old demo/system fonts must not silently enter production')
 else:d['fonts'].setdefault('subtitle',d['fonts']['body'])
 return d

def all_text(obj):
 if isinstance(obj,str):return obj
 if isinstance(obj,list):return ''.join(all_text(x) for x in obj)
 if isinstance(obj,dict):return ''.join(all_text(v) for k,v in obj.items() if k in ['lines','heading','headline','condition','label','value','text','steps','items'])
 return ''

def audit_fonts(d,asset,catalog):
 from fontTools.ttLib import TTFont
 result={}
 for role,rel in d['fonts'].items():
  path=asset(rel);font=TTFont(path);cmap=font.getBestCmap() or {};family=font['name'].getDebugName(16) or font['name'].getDebugName(1);style=font['name'].getDebugName(17) or font['name'].getDebugName(2)
  weight=font['OS/2'].usWeightClass;variable='fvar' in font
  if variable:
   axis=next((a for a in font['fvar'].axes if a.axisTag=='wght'),None)
   if axis:weight=min(axis.maxValue,900 if role=='title' else 700)
  if role=='title' and weight<800:
   exception=d.get('fontExceptions',{})
   if d.get('fontPreset')!='custom' or not exception.get('titleStrokeReviewed') or len(exception.get('titleReason',''))<12:raise ValueError('Title font needs actual Black/Heavy strokes. For a natively heavy custom face whose metadata says Regular, document fontExceptions.titleReason and review titleStrokeReviewed; never synthesize bold.')
  text=''.join(d['mainTitle'])+''.join(d['cover'].get('keywords',[]))+''.join(str(it.get('value','')) for s in d['segments'] for it in s.get('info',{}).get('items',[])) if role=='title' else ''.join(d['subtitle']) if role=='subtitle' else ''.join(s.get('caption','')+all_text(s.get('info',{})) for s in d['segments'])+''.join(s.get('text','') for s in d.get('subtitles',[]))
  missing=sorted({c for c in text if not c.isspace() and ord(c) not in cmap})
  if missing:raise ValueError(f'{role} font lacks glyphs: {"".join(missing)}. Supply an explicit compatible font; no system fallback.')
  with path.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
  expected=catalog.get(rel,{}).get('sha256')
  if expected and sha!=expected:raise ValueError(f'Font hash differs from pinned official resource: {rel}')
  result[role]={'asset':rel,'family':family,'style':style,'selectedWeight':int(weight),'variable':variable,'sha256':sha,'glyphCoveragePassed':True}
  font.close()
 return result

def measured_font(path,size,weight):
 from PIL import ImageFont
 f=ImageFont.truetype(str(path),size)
 try:f.set_variation_by_axes([weight if a['name']==b'Weight' else a['default'] for a in f.get_variation_axes()])
 except (OSError,AttributeError):pass
 return f

def wrap(text,font,width):
 rows=[]
 for raw in text.split('\n'):
  line=''
  for c in raw:
   if line and font.getlength(line+c)>width:rows.append(line);line=''
   line+=c
  rows.append(line)
 return rows

def layout(d,asset,audit):
 sizes=[];targets={'paper-red':[76,96],'speed-yellow':[72,92],'berry-progress':[74,104]}[d['style']]
 for i,text in enumerate(d['mainTitle']):
  size=targets[i]
  while measured_font(asset(d['fonts']['title']),size,audit['title']['selectedWeight']).getlength(text)>912:size-=1
  if size<56:raise ValueError('Title cannot fit at readable size. Reflow exact wording; do not shrink or truncate.')
  sizes.append(size)
 subtitle_size=42
 sub_font=measured_font(asset(d['fonts']['subtitle']),subtitle_size,audit['subtitle']['selectedWeight'])
 if any(sub_font.getlength(t)>912 for t in d['subtitle']):raise ValueError('Subtitle needs a semantic line break; retain exact words')
 main_h=sum(s*1.18 for s in sizes)+(42 if len(sizes)==2 else 30)+(12 if len(sizes)==2 else 0)
 sub_h=len(d['subtitle'])*subtitle_size*1.4+16
 header_bottom=250+main_h+18+sub_h
 picture_top=max({'paper-red':620,'speed-yellow':600,'berry-progress':610}[d['style']],round(header_bottom+26));picture_h=790 if d['mode']=='speech' else {'paper-red':710,'speed-yellow':740,'berry-progress':690}[d['style']]
 if picture_top+picture_h>1400:picture_h=1400-picture_top
 if picture_h<620:raise ValueError('Title group consumes too much space. Reflow exact wording and review layout.')
 left,width={'paper-red':(40,1000),'speed-yellow':(30,1020),'berry-progress':(50,980)}[d['style']];picture=d.get('layout',{}).get('picture',[left,picture_top,width,picture_h])
 if len(picture)!=4 or min(picture[2:])<=0 or min(picture[:2])<0 or picture[0]+picture[2]>1080 or picture[1]<header_bottom+20:raise ValueError('Custom picture slot overlaps title or escapes frame')
 board_top=picture[1]+picture[3]+30
 body_size=48 if d['mode']=='news' else 54
 body_font=measured_font(asset(d['fonts']['body']),body_size,audit['body']['selectedWeight'])
 for s in d['segments']:
  s['captionLines']=wrap(s.get('caption',''),body_font,924)
  if len(s['captionLines'])>(3 if d['mode']=='news' else 2):raise ValueError('Caption overflows readable panel; split into complete phrases')
  info=s.get('info',{})
  if info.get('type') in ['metrics','comparison']:
   items=info.get('items',[])
   if len(items) not in [2,3]:raise ValueError('Use two or three readable columns, or design a different panel')
   available=(984-12*(len(items)-1))/len(items)-44
   for item in items:
    if measured_font(asset(d['fonts']['body']),36,audit['body']['selectedWeight']).getlength(item['label'])>available:raise ValueError('Info label too long for mobile-readable column')
    value_size=96 if info['type']=='comparison' else 85
    while measured_font(asset(d['fonts']['title']),value_size,audit['title']['selectedWeight']).getlength(str(item['value']))>available:value_size-=1
    if value_size<64:raise ValueError('Info value needs another panel layout, not tiny text')
    item['valueSize']=value_size
  if info.get('type')=='text':
   info['renderLines']=[line for raw in info.get('lines',[]) for line in wrap(raw,measured_font(asset(d['fonts']['body']),48,audit['body']['selectedWeight']),900)]
   if len(info['renderLines'])>3:raise ValueError('Too many information-panel lines; split into complete units')
  s['revealFrames']=min(s.get('frames',120)-30,max(1,round(len(s.get('caption','').replace('\n',''))*1.8)))
  if d['mode']=='news' and board_top+len(s['captionLines'])*body_size*1.5+62>1760:raise ValueError('News panel escapes lower safe area; split text instead of reducing size')
 return {'headerTop':250,'headerBottom':round(header_bottom),'picture':picture,'boardTop':board_top,'subtitleSize':subtitle_size,'bodySize':body_size,'mainSizes':sizes,'coverPicture':[60,round(header_bottom+28),960,min(660,1300-round(header_bottom+28))],'coverKeywordsTop':1370,'safeCover':[0,240,1080,1440],'transitionFrames':6,'version':'2.0'}
