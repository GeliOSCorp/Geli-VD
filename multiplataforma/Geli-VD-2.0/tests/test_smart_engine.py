import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from core import engine_manager as m

class SmartEngineTests(unittest.TestCase):
    def test_fallback_errors(self):
        self.assertTrue(m.compatible_failure(RuntimeError('Requested format is not available')))
        self.assertTrue(m.compatible_failure(RuntimeError('challenge solving failed')))
        self.assertFalse(m.compatible_failure(RuntimeError('HTTP Error 403: Forbidden')))
        self.assertFalse(m.compatible_failure(RuntimeError('Video is private')))
        self.assertFalse(m.compatible_failure(RuntimeError('Network timeout')))
        self.assertFalse(m.compatible_failure(RuntimeError('Cancelado por el usuario')))
    def test_fallback_to_isolated(self):
        logs=[]
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'nightly-1'/'yt_dlp').mkdir(parents=True)
            (root/'nightly-1'/'yt_dlp'/'__init__.py').write_text('')
            with patch.object(m,'ROOT',root),patch.object(m,'REGISTRY',root/'registry.json'), \
                 patch.object(m,'embedded_execute',side_effect=RuntimeError('Requested format is not available')), \
                 patch.object(m,'_run_isolated',return_value=({'title':'ok'},'video.mp4')) as alternate:
                m._save({'engines':[{'folder':'nightly-1','channel':'nightly','version':'1','installed_at':1}],'preferred':{}})
                info,path=m.smart_execute('https://www.youtube.com/watch?v=abc',[],lambda:{},logs.append,download=True)
                self.assertEqual(info['title'],'ok');self.assertEqual(path,'video.mp4')
                self.assertEqual(alternate.call_count,1)
                self.assertEqual(m._read()['preferred']['YouTube'],'nightly-1')
    def test_auth_failure_never_switches_engine(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'nightly-1'/'yt_dlp').mkdir(parents=True)
            (root/'nightly-1'/'yt_dlp'/'__init__.py').write_text('')
            with patch.object(m,'ROOT',root),patch.object(m,'REGISTRY',root/'registry.json'), \
                 patch.object(m,'embedded_execute',side_effect=RuntimeError('HTTP Error 403: forbidden')), \
                 patch.object(m,'_run_isolated') as alternate:
                m._save({'engines':[{'folder':'nightly-1','channel':'nightly','version':'1'}],'preferred':{}})
                with self.assertRaisesRegex(RuntimeError,'403'):
                    m.smart_execute('https://www.youtube.com/watch?v=abc',[],lambda:{},lambda v:None)
                alternate.assert_not_called()
if __name__=='__main__':unittest.main()
