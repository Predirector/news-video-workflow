from pathlib import Path
import unittest,tempfile,sys,os
from unittest.mock import patch
S=Path(__file__).resolve().parents[1]/'skills/news-video-workflow/scripts';sys.path.insert(0,str(S));import shared_runtime as r
class Shared(unittest.TestCase):
 def test_identity_and_version_isolation(self):
  with patch.dict(os.environ,{'NEWS_RUNTIME_ROOT':'/tmp/news-test-root'}):
   self.assertEqual(r.pool('python',{'lock':'a'}),r.pool('python',{'lock':'a'}));self.assertNotEqual(r.pool('python',{'lock':'a'}),r.pool('python',{'lock':'b'}))
 def test_projects_share_without_overwriting_local(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);shared=p/'shared';shared.mkdir();(shared/'proof').write_text('ok')
   for n in ['a','b']:r.link(shared,p/n)
   self.assertEqual((p/'a').resolve(),(p/'b').resolve());self.assertEqual((p/'b/proof').read_text(),'ok')
   local=p/'local';local.mkdir();(local/'keep').write_text('unique')
   with self.assertRaises(RuntimeError):r.link(shared,local)
   self.assertEqual((local/'keep').read_text(),'unique')
 def test_lock_released_on_error(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'pool'
   with self.assertRaises(ValueError):
    with r.locked(p):raise ValueError()
   self.assertFalse(p.with_name('pool.lock').exists())
 def test_starter_helper_identical(self):
  self.assertEqual((S/'shared_runtime.py').read_bytes(),(S.parent/'assets/starter/scripts/shared_runtime.py').read_bytes())
if __name__=='__main__':unittest.main()
