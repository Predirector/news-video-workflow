"""Exercise acquisition behavior, including a fake CLI process with real files."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];SCRIPTS=ROOT/'skills/news-video-workflow/scripts';sys.path.insert(0,str(SCRIPTS))
import intake,materials,toolchain

def text(bid,value,kind=2):return {'block_id':bid,'block_type':kind,'paragraph':{'elements':[{'text_run':{'content':value}}]}}
def table():
 return [{'block_id':'page','block_type':1,'children':['table']},{'block_id':'table','table':{'property':{'column_size':2},'cells':['h1','h2','a','b','c','d']}},*({'block_id':cell,'children':[cell+'t']} for cell in ['h1','h2','a','b','c','d']),text('h1t','编号'),text('h2t','文稿'),text('at','2.1'),text('bt','正文 https://example.com/article'),text('ct','2.10'),text('dt','另一条')]
class Acquisition(unittest.TestCase):
 def test_exact_number_not_prefix_or_substring(self):
  self.assertTrue(intake.starts_item('02.1 标题','2.1'))
  for value in ['12.1 标题','2.10 标题','数据达到2.1']:
   self.assertFalse(intake.starts_item(value,'2.1'))
 def test_docx_table_retains_headers_and_only_selected_row(self):
  rows=intake.select_doc(table(),'2.1');self.assertEqual(len(rows),1);self.assertEqual(rows[0]['headers'],['编号','文稿']);self.assertEqual(rows[0]['cells'][0],'2.1');self.assertNotIn('另一条',json.dumps(rows,ensure_ascii=False))
 def test_repeated_numbers_remain_ambiguous(self):
  blocks=table();blocks.append({'block_id':'table2','table':{'property':{'column_size':2},'cells':['a','b']}})
  self.assertEqual(len(intake.select_doc(blocks,'2.1')),2)
 def test_section_keeps_subheadings_stops_at_next_peer(self):
  blocks=[{'block_id':'p','block_type':1,'children':['a','b','c','d','e']},text('a','2.1 标题',3),text('b','2.1.1 子标题',4),text('c','需要保留'),text('d','2.2 下一条',3),text('e','不该保留')]
  rows=intake.select_doc(blocks,'2.1');self.assertIn('需要保留',rows[0]['text']);self.assertNotIn('不该保留',rows[0]['text'])
 def test_sheet_selects_exact_number(self):
  data={'sheets':[{'data':{'valueRanges':[{'range':'s!A1:C8','values':[['编号','稿件'],['2.1','正文'],['2.10','另一条']]}]}}]};self.assertEqual(intake.select_sheet(data,'2.1')[0]['cells'],['2.1','正文'])
 def test_sheet_rich_hyperlink_number_is_readable(self):
  data={'sheets':[{'data':{'valueRanges':[{'values':[[[{'type':'url','text':'2.1','link':'https://example.com'}],'脚本']]}]}}]}
  self.assertEqual(len(intake.select_sheet(data,'2.1')),1)
 def test_links_include_hyperlink_targets_and_deduplicate(self):
  data={'content':'正文 https://example.com/a。','link':{'url':'https://example.com/b'},'repeat':'https://example.com/a'};self.assertEqual(intake.links_in(data),['https://example.com/a','https://example.com/b'])
 def test_private_network_and_non_https_refused(self):
  for url in ['http://example.org','https://127.0.0.1','https://user:pass@example.org','https://[::1]']:
   with self.assertRaises(ValueError):materials.public_url(url)
 def test_source_records_strip_auth_values(self):
  u=materials.safe_url('https://example.org/file?access_token=private&X-Amz-Signature=private&id=2#private');self.assertEqual(u,'https://example.org/file?id=2')
 def test_local_import_deduplicates_and_preserves_original(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);src=root/'photo.png';src.write_bytes(b'fixture-data');one=materials.import_file(root,src);two=materials.import_file(root,src)
   self.assertEqual(one['asset'],two['asset']);self.assertEqual(src.read_bytes(),b'fixture-data');self.assertEqual(hashlib.sha256((root/'public'/one['asset']).read_bytes()).hexdigest(),one['sha256'])
 def test_cli_process_intake_downloads_selected_attachment(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);project=root/'project';project.mkdir();fixture=table();fixture.append({'block_id':'image','image':{'token':'fixture-image'}});next(b for b in fixture if b['block_id']=='b')['children']=['bt','image']
   fake=root/'fake-lark';fake.write_text('#!'+sys.executable+'\n'+'''import sys,json,pathlib
args=sys.argv[1:]
assert args[:2]==['api','GET']
assert '?' not in args[2]
assert args[args.index('--as')+1]=='user'
if '--output' in args:
 p=pathlib.Path(args[args.index('--output')+1]);assert not p.is_absolute();p.write_bytes(b'fixture-image-content');print(json.dumps({'ok':True,'data':{}}))
elif args[2].endswith('/blocks'):
 print(json.dumps({'ok':True,'data':{'items':BLOCKS,'has_more':False}}))
else:raise SystemExit(3)
'''.replace('BLOCKS',repr(fixture)));fake.chmod(0o755)
   with patch.dict(os.environ,{'NEWS_LARK_CLI':str(fake)}):
    result=intake.intake(project,'https://example.feishu.cn/docx/fixture','2.1',True)
   report=json.loads(Path(result['report']).read_text());self.assertEqual(result['downloaded'],1);self.assertEqual(report['selection']['cells'][0],'2.1');asset=project/'public'/report['downloads'][0]['asset'];self.assertEqual(asset.read_bytes(),b'fixture-image-content');self.assertEqual(list((Path(result['report']).parent/'attachments').iterdir()),[])
 def test_cli_expired_auth_is_not_empty_success(self):
  response=subprocess.CompletedProcess([],1,'',json.dumps({'ok':False,'error':{'type':'auth','code':99991663,'hint':'Please login again'}}))
  with patch('toolchain.subprocess.run',return_value=response):
   with self.assertRaisesRegex(RuntimeError,'auth/99991663'):toolchain.cli_get(['fixture'],'/docx/v1/documents/a/blocks')
if __name__=='__main__':unittest.main()
