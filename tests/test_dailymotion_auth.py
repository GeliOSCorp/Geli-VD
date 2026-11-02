"""Run with Python + yt-dlp 2026.10.26. No account, network or media required."""
import importlib.util
from pathlib import Path
import queue
import sys
import types
import unittest
from unittest.mock import patch

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('geli_vd',(root/'escritorio/descargador_video.py' if (root/'escritorio/descargador_video.py').exists() else root/'descargador_video.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from yt_dlp.extractor import dailymotion

URL='https://www.dailymotion.com/video/x7kyjqg'
ERROR='[dailymotion] x7kyjqg: Unable to download JSON metadata: HTTP Error 401: Unauthorized'


class DailymotionAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.host=types.SimpleNamespace(cola=queue.Queue())
        self.host._extraer_simple=lambda *args:m.App._extraer_simple(self.host,*args)
        self.saved=[]
        base=dailymotion.DailymotionBaseInfoExtractor
        for cls in vars(dailymotion).values():
            if isinstance(cls,type) and issubclass(cls,base):
                self.saved.append((cls,'_HEADERS' in vars(cls),dict(getattr(cls,'_HEADERS'))))
        self.addCleanup(self.restore_headers)
    def restore_headers(self):
        for cls,own,headers in self.saved:
            if own:cls._HEADERS=headers
            elif '_HEADERS' in vars(cls):del cls._HEADERS
    def fake_engine(self,effects,seen):
        class Fake:
            def __init__(self,options):
                self.options=options;seen.append(dict(options))
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def extract_info(self,url,download=False):
                outcome=effects.pop(0)
                if isinstance(outcome,Exception):raise outcome
                if callable(outcome):return outcome(self.options,url,download)
                return outcome
        return Fake
    def extract(self,op,effects,url=URL,download=False):
        seen=[]
        with patch.object(m.yt_dlp,'YoutubeDL',self.fake_engine(effects,seen)):
            result=self.host._extraer_simple(op,url,download)
        return result,seen
    def test_first_attempt_discards_stale_class_authorization(self):
        dailymotion.DailymotionBaseInfoExtractor._HEADERS['Authorization']='Bearer stale'
        def effect(*args):
            self.assertNotIn('Authorization',dailymotion.DailymotionBaseInfoExtractor._HEADERS)
            return {'id':'ok'}
        _,seen=self.extract({},[effect]);self.assertEqual(len(seen),1)
    def test_cookie_mode_change_has_no_previous_bearer(self):
        def with_session(*args):
            dailymotion.DailymotionIE._HEADERS['Authorization']='Bearer session'
            return {'id':'first'}
        self.extract({'cookiefile':'session.txt'},[with_session])
        def anonymous(options,*args):
            self.assertNotIn('Authorization',dailymotion.DailymotionIE._HEADERS)
            self.assertNotIn('cookiefile',options)
            return {'id':'second'}
        self.extract({},[anonymous])
    def test_metadata_401_retries_once_without_session(self):
        op={'cookiefile':'session.txt','cookiesfrombrowser':('firefox',),'username':'user','password':'secret','usenetrc':True,'format':'best','progress_hooks':['existing']}
        original=dict(op)
        result,seen=self.extract(op,[RuntimeError(ERROR),{'id':'ok'}],download=True)
        self.assertEqual(result[0]['id'],'ok');self.assertEqual(len(seen),2)
        for name in ('cookiefile','cookiesfrombrowser','username','password','usenetrc'):self.assertNotIn(name,seen[1])
        self.assertEqual(seen[1]['format'],'best');self.assertEqual(seen[1]['progress_hooks'],['existing']);self.assertEqual(op,original)
        self.assertIn('una vez',self.host.cola.get()[1])
    def test_second_401_is_reported_not_looped(self):
        effects=[RuntimeError(ERROR),RuntimeError(ERROR)];seen=[]
        with patch.object(m.yt_dlp,'YoutubeDL',self.fake_engine(effects,seen)):
            with self.assertRaisesRegex(RuntimeError,'401'):self.host._extraer_simple({},URL,False)
        self.assertEqual(len(seen),2)
    def test_manifest_401_not_retried(self):
        seen=[]
        with patch.object(m.yt_dlp,'YoutubeDL',self.fake_engine([RuntimeError('HTTP Error 401: manifest')],seen)):
            with self.assertRaises(RuntimeError):self.host._extraer_simple({},URL,True)
        self.assertEqual(len(seen),1)
    def test_private_drm_and_unrelated_site_are_not_retried(self):
        for url,error in [(URL,'This video is private'),(URL,'DRM protected'),('https://youtube.com/watch?v=abc',ERROR)]:
            seen=[]
            with patch.object(m.yt_dlp,'YoutubeDL',self.fake_engine([RuntimeError(error)],seen)):
                with self.assertRaises(RuntimeError):self.host._extraer_simple({},url,False)
            self.assertEqual(len(seen),1)
    def test_browser_cookie_read_fallback_is_kept(self):
        _,seen=self.extract({'cookiesfrombrowser':('firefox',)},[RuntimeError('could not copy cookie database'),{'id':'ok'}],url='https://youtube.com/watch?v=abc')
        self.assertEqual(len(seen),2);self.assertNotIn('cookiesfrombrowser',seen[1])
    def test_other_sites_do_not_reset_dailymotion(self):
        dailymotion.DailymotionBaseInfoExtractor._HEADERS['Authorization']='Bearer keep'
        self.extract({},[{'id':'ok'}],url='https://youtube.com/watch?v=abc')
        self.assertEqual(dailymotion.DailymotionBaseInfoExtractor._HEADERS['Authorization'],'Bearer keep')
    def test_host_matching_does_not_accept_spoofed_domains(self):
        for url in (URL,'https://dai.ly/abc','https://geo.dailymotion.com/player.html?video=abc'):
            self.assertTrue(m.es_enlace_dailymotion(url))
        for url in ('https://dailymotion.com.ejemplo.org/video/abc','https://evil.test/?dailymotion.com','https://youtube.com'):
            self.assertFalse(m.es_enlace_dailymotion(url))
    def test_decrypted_session_file_is_not_deleted_or_changed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'session.txt';path.write_text('sample-session-not-real')
            self.extract({'cookiefile':str(path)},[RuntimeError(ERROR),{'id':'ok'}])
            self.assertEqual(path.read_text(),'sample-session-not-real')
    def test_version_bump_keeps_data_directory(self):
        self.assertEqual(m.APP_VERSION_NUM,'1.5.1')
        self.assertEqual(m.APP_NOMBRE,'Geli-VideoDownloader')


if __name__=='__main__':unittest.main(verbosity=2)
