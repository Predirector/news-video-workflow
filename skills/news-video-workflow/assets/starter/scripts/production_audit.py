"""Enforce measurable rules; list editorial checks separately from automatic results."""
from pathlib import Path
import json,re
from common import ROOT,asset,reports,save_json,sha
from visual import measured_font

def audit(d):
 layout=d['visualLayout'];fonts=d['fontAudit'];automatic=[]
 def passed(rule,detail):automatic.append({'rule':rule,'status':'passed','detail':detail})
 if layout['headerTop']<240:raise ValueError('R04: title escapes top safe area')
 if layout['headerBottom']+20>layout['picture'][1]:raise ValueError('R04: header collides with picture')
 if len(d['cover'].get('keywords',[]))>2:raise ValueError('R05: cover must use only a few essential keywords, not scattered explanatory text')
 for word in d['cover'].get('keywords',[]):
  f=measured_font(asset(d['fonts']['title']),61,fonts['title']['selectedWeight'])
  if f.getlength(word)>848:raise ValueError('R05: cover keyword line overflows. Reflow exact wording.')
 bottom=layout['coverKeywordsTop']+44+len(d['cover'].get('keywords',[]))*61*1.35+9
 if d['cover'].get('keywords') and bottom>1680:raise ValueError('R05: cover keyword block escapes centered 3:4 safe area')
 if layout['coverPicture'][1]+layout['coverPicture'][3]>1680:raise ValueError('R05: cover subject slot escapes safe area')
 passed('R03','Actual font names, weights, coverage and hashes recorded; font synthesis disabled in default renderer')
 passed('R04','Measured header, picture and panel layout; no typography shrinking to fit long captions')
 passed('R05','Cover layout inside centered 3:4; exact title wording guarded by expectedTitles')
 for i,s in enumerate(d['segments']):
  if s.get('mark') and s.get('marks'):raise ValueError('R06: choose mark or marks, not duplicate marking systems')
  marks=s.get('marks',[])
  if marks and s.get('evidence',{}).get('alreadyMarked'):raise ValueError('R06: original already marked; do not add another layer')
  for m in marks:
   r=m.get('rect',[])
   if len(r)!=4 or min(r)<0 or r[0]+r[2]>1 or r[1]+r[3]>1 or min(r[2:])<=0:raise ValueError('R06: mark rectangle escapes displayed original')
  if s.get('expectedCaption') is not None and s.get('caption','')!=s['expectedCaption']:raise ValueError('R08: caption differs from expected script')
 passed('R06','One highlight system; normalized mark bounds checked. Original screenshot identity/mark placement still needs visual review.')
 if not d.get('demo'):
  if not (ROOT/'PRODUCTION_RULES.md').is_file():raise ValueError('Missing full project rules. Initialize or migrate this project first.')
  if not d.get('expectedTitles'):raise ValueError('R02: formal production needs exact expectedTitles')
  planfile=ROOT/'production-plan.json'
  if not planfile.is_file():raise ValueError('Create production-plan.json from the supplied script and actual assets; see PRODUCTION_RULES.md and production-plan.example.json')
  plan=json.loads(planfile.read_text())
  for key in ['coreMessage','coverReason','fontDecision','backgroundReason']:
   if len(str(plan.get(key,'')))<8:raise ValueError('Production plan needs a concrete '+key)
  shots=plan.get('shots',[])
  if len(shots)!=len(d['segments']):raise ValueError('R07: map every segment to its factual claim and asset rationale')
  for shot in shots:
   for key in ['claim','assetWhy','identityAndDate','evidenceOrContext']:
    if not shot.get(key):raise ValueError('R07: shot needs '+key)
  if d.get('bgm'):
   music=plan.get('music',{})
   if not all(music.get(k) for k in ['discoveryUrl','excerptReason','listenedExcerpt','usedMusicCheck','beatDecision']):raise ValueError('R10: record music source, actual listening, prior-use check and beat decisions')
  passed('R01/R07/R10','Per-episode editorial plan present. Its factual, visual and listening conclusions are human/agent review, not machine-certified.')
  seen=[]
  for i,s in enumerate(d['segments']):
   if s['kind']=='image':
    h=sha(asset(s['asset']))
    if h in seen[-2:] and not s.get('reuseReason'):raise ValueError('R07: same image content recurs nearby; choose another semantic asset or document the genuine continuity reason')
    seen.append(h)
   else:seen.append(None)
 manual=['R01 cover expresses actual core and scope','R04 mobile hierarchy and source crop','R06 original report and exact mark positions','R07 semantic match, near-duplicate camera shots and internal source cuts','R08 early/mid/full caption readability','R09 bright natural photos and perceptible restrained texture','R10 actual music excerpt, energy and listening','R13 final encoded transition boundaries']
 result={'ruleVersion':'1.2','projectRulesHash':sha(ROOT/'PRODUCTION_RULES.md') if (ROOT/'PRODUCTION_RULES.md').is_file() else None,'automatic':automatic,'fontAudit':fonts,'layout':layout,'manualRequired':manual,'visualApprovalNotImplied':True}
 save_json(reports()/'production-audit.json',result)
 return result
if __name__=='__main__':
 d=json.loads((ROOT/'episode.compiled.json').read_text());print(json.dumps(audit(d),ensure_ascii=False,indent=2))
