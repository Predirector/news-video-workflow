"""Behavior checks for the handoff contract; no live accounts or media required."""
from pathlib import Path
import unittest,json,copy,sys,importlib.util,urllib.request
ROOT=Path(__file__).resolve().parents[1];SKILL=ROOT/'skills/news-video-workflow';START=SKILL/'assets/starter';sys.path.insert(0,str(START/'scripts'));import common
spec=importlib.util.spec_from_file_location('feishu_read',SKILL/'scripts/feishu_read.py');feishu=importlib.util.module_from_spec(spec);spec.loader.exec_module(feishu)
class Contract(unittest.TestCase):
 def setUp(self):self.d=json.loads((START/'episode.json').read_text())
 def test_fixed_title_mismatch_stops(self):
  self.d['mainTitle'][0]+='改写'
  with self.assertRaisesRegex(ValueError,'script wording'):common.validate(self.d,False)
 def test_redrawn_report_rejected(self):
  self.d['segments'][0]['evidence']={'original':False}
  with self.assertRaisesRegex(ValueError,'original layout'):common.validate(self.d,False)
 def test_demo_assets_cannot_masquerade_as_news(self):
  self.d['demo']=False
  with self.assertRaisesRegex(ValueError,'Demo graphics'):common.validate(self.d,False)
 def test_flash_segment_rejected(self):
  self.d['segments'][0]['duration']=.1
  with self.assertRaisesRegex(ValueError,'flash'):common.validate(self.d,False)
 def test_caption_reading_time_protected(self):
  self.d['segments'][0]['duration']=1.1
  with self.assertRaisesRegex(ValueError,'reading time'):common.validate(self.d,False)
 def test_asset_escape_rejected(self):
  with self.assertRaises(ValueError):common.asset('../../outside.txt')
 def test_speech_retime_keeps_cover_and_complete_tail(self):
  self.d.update(mode='speech',speechRate=1.1);self.d['segments']=[{'asset':'provided.mp4','kind':'video','duration':7.8,'voice':True,'caption':'完整一句话'}]
  self.assertEqual(common.validate(self.d,False),216)
 def test_docx_pagination(self):
  c=feishu.Client('fixture-only','https://open.feishu.cn/open-apis');calls=[]
  def get(path):
   calls.append(path)
   return {'items':[{'block_id':'one'}],'has_more':True,'page_token':'next'} if len(calls)==1 else {'items':[{'block_id':'two'}],'has_more':False}
  c.get=get;self.assertEqual([b['block_id'] for b in c.docx('fixture-doc')],['one','two']);self.assertIn('page_token=next',calls[1])
 def test_no_bearer_forward_to_media_cdn(self):
  req=urllib.request.Request('https://open.feishu.cn/open-apis/drive/v1/medias/fixture/download',headers={'Authorization':'Bearer fixture-only'})
  new=feishu.NoCredentialRedirect().redirect_request(req,None,302,'Found',{},'https://cdn.example.org/file')
  self.assertIsNone(new.get_header('Authorization'))
 def test_http_redirect_rejected(self):
  req=urllib.request.Request('https://open.feishu.cn/a')
  with self.assertRaises(ValueError):feishu.NoCredentialRedirect().redirect_request(req,None,302,'Found',{},'http://example.org/file')
if __name__=='__main__':unittest.main()
