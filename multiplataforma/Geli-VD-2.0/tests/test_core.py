import unittest
from unittest.mock import patch
from core.storage import platform,valid_domain
from core import downloader

class Tests(unittest.TestCase):
    def test_domains(self):
        self.assertEqual(platform('https://m.facebook.com/watch/'),'Facebook')
        self.assertEqual(platform('https://tiktok.com/video/1'),'TikTok')
        self.assertEqual(platform('https://youtu.be/abc'),'YouTube')
        self.assertEqual(platform('https://media.cursos.ejemplo.com/video',['cursos.ejemplo.com']),'cursos.ejemplo.com')
        self.assertEqual(platform('https://notfacebook.com/'),'notfacebook.com')
        with self.assertRaises(ValueError):valid_domain('https://localhost/')
    def test_auth_retry(self):
        class FakeYdl:
            calls=[]
            def __init__(self,op):self.op=op;FakeYdl.calls.append(op)
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def extract_info(self,url,download=False):
                if 'cookiefile' not in self.op:raise ValueError('HTTP Error 403 forbidden')
                return {'title':'ok'}
            def prepare_filename(self,info):return 'ok.mp4'
        class Stub:YoutubeDL=FakeYdl
        FakeYdl.calls.clear()
        with patch.object(downloader,'yt_dlp',Stub),patch.object(downloader,'active',lambda n:True),patch.object(downloader,'session_file',lambda n:'cookies.txt'):
            info,_=downloader.execute('https://www.tiktok.com/video/1',[],lambda:{},lambda msg:None,download=True)
        self.assertEqual(info['title'],'ok');self.assertEqual(len(FakeYdl.calls),2)
        self.assertNotIn('cookiefile',FakeYdl.calls[0]);self.assertEqual(FakeYdl.calls[1]['cookiefile'],'cookies.txt')
    def test_no_credentials_for_unrelated_failure(self):
        class FakeYdl:
            def __init__(self,o):pass
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def extract_info(self,*a,**kw):raise RuntimeError('Network timeout')
        class Stub:YoutubeDL=FakeYdl
        with patch.object(downloader,'yt_dlp',Stub):
            with self.assertRaisesRegex(RuntimeError,'Network timeout'):
                downloader.execute('https://www.youtube.com/watch?v=1',[],lambda:{},lambda msg:None)
if __name__=='__main__':unittest.main()
