"""Real font bytes and migration boundaries, rather than CSS string snapshots."""
from pathlib import Path
import importlib.util,json,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];SKILL=ROOT/'skills/news-video-workflow';sys.path.insert(0,str(SKILL/'assets/starter/scripts'))
import visual
from review_gate import validate_review
HAS_FONTTOOLS=bool(importlib.util.find_spec('fontTools'))

def makefont(path,weight=1000):
 from fontTools.fontBuilder import FontBuilder
 from fontTools.pens.ttGlyphPen import TTGlyphPen
 fb=FontBuilder(1000,isTTF=True);chars='标题副主正文';order=['.notdef']+['u'+format(ord(c),'04X') for c in chars];fb.setupGlyphOrder(order);fb.setupCharacterMap({ord(c):order[i+1] for i,c in enumerate(chars)})
 glyphs={}
 for glyph in order:
  pen=TTGlyphPen(None);pen.moveTo((100,0));pen.lineTo((500,0));pen.lineTo((500,700));pen.lineTo((100,700));pen.closePath();glyphs[glyph]=pen.glyph()
 fb.setupGlyf(glyphs);fb.setupHorizontalMetrics({g:(600,100) for g in order});fb.setupHorizontalHeader(ascent=800,descent=-200);fb.setupNameTable({'familyName':'Fixture','styleName':'Heavy','uniqueFontIdentifier':'Fixture'+str(weight),'fullName':'Fixture Heavy','psName':'Fixture-Heavy'});fb.setupOS2(sTypoAscender=800,sTypoDescender=-200,usWinAscent=800,usWinDescent=200,usWeightClass=weight);fb.setupPost();fb.save(path)

class VisualContract(unittest.TestCase):
 def test_legacy_demo_fonts_cannot_silently_enter_production(self):
  with self.assertRaisesRegex(ValueError,'fontPreset'):visual.resolve_fonts({'demo':False,'style':'paper-red','fonts':{'title':'fonts/old.ttf','body':'fonts/body.ttf'}})
 def test_default_font_roles_and_style_differ(self):
  paper=visual.resolve_fonts({'fontPreset':'style-default','style':'paper-red'})['fonts'];speed=visual.resolve_fonts({'fontPreset':'style-default','style':'speed-yellow'})['fonts'];self.assertNotEqual(paper['title'],paper['body']);self.assertNotEqual(paper['title'],speed['title'])
 @unittest.skipUnless(HAS_FONTTOOLS,'Use the project Python with locked fonttools installed')
 def test_missing_glyph_blocks_system_fallback(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'font.ttf';makefont(path);d={'fontPreset':'custom','fonts':{'title':'font.ttf'},'mainTitle':['标题𠮷'],'cover':{},'segments':[]}
   with self.assertRaisesRegex(ValueError,'lacks glyphs'):visual.audit_fonts(d,lambda x:Path(td)/x,{})
 @unittest.skipUnless(HAS_FONTTOOLS,'Use the project Python with locked fonttools installed')
 def test_corrupt_or_changed_font_hash_blocks_render(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'font.ttf';makefont(path);d={'fontPreset':'custom','fonts':{'title':'font.ttf'},'mainTitle':['标题'],'cover':{},'segments':[]}
   with self.assertRaisesRegex(ValueError,'hash differs'):visual.audit_fonts(d,lambda x:Path(td)/x,{'font.ttf':{'sha256':'0'*64}})
 @unittest.skipUnless(HAS_FONTTOOLS,'Use the project Python with locked fonttools installed')
 def test_regular_font_is_not_synthetically_promoted_to_heavy(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'font.ttf';makefont(path,400);d={'fontPreset':'custom','fonts':{'title':'font.ttf'},'mainTitle':['标题'],'cover':{},'segments':[]}
   with self.assertRaisesRegex(ValueError,'Black/Heavy'):visual.audit_fonts(d,lambda x:Path(td)/x,{})
 def test_init_carries_detailed_rules_into_project(self):
  with tempfile.TemporaryDirectory() as td:
   dst=Path(td)/'project';subprocess.run([sys.executable,str(SKILL/'scripts/init_project.py'),str(dst)],check=True,capture_output=True)
   self.assertEqual((dst/'PRODUCTION_RULES.md').read_bytes(),(SKILL/'references/editorial-rules.md').read_bytes());self.assertTrue((dst/'AGENTS.md').is_file());self.assertTrue((dst/'IMPLEMENTATION_MATRIX.md').is_file())
 def test_upgrade_preserves_custom_sources(self):
  with tempfile.TemporaryDirectory() as td:
   dst=Path(td);(dst/'src').mkdir();source=dst/'src/Root.tsx';source.write_text('CUSTOM USER SOURCE');(dst/'episode.json').write_text('{}')
   r=subprocess.run([sys.executable,str(SKILL/'scripts/upgrade_project.py'),str(dst),'--apply'],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0);self.assertEqual(source.read_text(),'CUSTOM USER SOURCE');self.assertFalse((dst/'font-catalog.json').exists())
 def test_upgrade_preserves_episode_and_unique_media(self):
  with tempfile.TemporaryDirectory() as td:
   dst=Path(td);(dst/'public').mkdir();(dst/'public/unique.bin').write_bytes(b'USER MEDIA');(dst/'episode.json').write_text(json.dumps({'name':'用户完整标题','mainTitle':['用户标题'],'fonts':{'title':'fonts/NotoSerifSC.ttf','body':'fonts/NotoSansSC.ttf'}}))
   r=subprocess.run([sys.executable,str(SKILL/'scripts/upgrade_project.py'),str(dst),'--apply'],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr);d=json.loads((dst/'episode.json').read_text());self.assertEqual(d['name'],'用户完整标题');self.assertEqual((dst/'public/unique.bin').read_bytes(),b'USER MEDIA');self.assertEqual(d['fontPreset'],'style-default')
 def test_bare_pass_flag_does_not_authorize_cleanup(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaisesRegex(ValueError,'checkedFiles'):validate_review({'passed':True},Path(td),Path(td))
 def test_review_cannot_claim_a_missing_file(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaisesRegex(ValueError,'absent'):validate_review({'passed':True,'checkedFiles':['output/nonexistent.png']},Path(td),Path(td))
 def test_music_candidates_find_actual_pulse_times(self):
  import numpy as np
  from music_analysis import analyze
  sr=48000;audio=np.zeros((sr*4,2));rng=np.random.default_rng(23)
  for t in [.5,1,1.5,2,2.5,3]:
   pulse=rng.normal(size=2400)*np.exp(-np.arange(2400)/400);start=int(t*sr);audio[start:start+2400]=pulse[:,None]
  result=analyze(audio,sr,[{'startFrame':3},{'startFrame':30}]);times=[v['seconds'] for v in result['candidateOnsets']]
  self.assertTrue(all(any(abs(a-b)<.06 for b in times) for a in [.5,1,1.5,2]));self.assertTrue(result['manualListeningRequired'])
if __name__=='__main__':unittest.main()
