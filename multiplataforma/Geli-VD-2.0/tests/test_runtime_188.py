import unittest
import zipfile
from unittest.mock import patch
from core import runtime_manager as r
from core import downloader as d

class RuntimeTests(unittest.TestCase):
    def test_large_official_deno_binary_is_not_rejected(self):
        entry=zipfile.ZipInfo('deno.exe')
        entry.file_size=140*1024*1024
        class FakeZip:
            def infolist(self):return [entry]
        self.assertIs(r._select_deno_entry(FakeZip(),'deno.exe'),entry)

    def test_deno_zip_rejects_multiple_executable_entries(self):
        a=zipfile.ZipInfo('deno.exe');a.file_size=140*1024*1024
        class FakeZip:
            def infolist(self):return [a,a]
        with self.assertRaises(RuntimeError):
            r._select_deno_entry(FakeZip(),'deno.exe')

    def test_deno_zip_rejects_excessive_size(self):
        a=zipfile.ZipInfo('deno.exe');a.file_size=r.MAX_EXE_BYTES+1
        class FakeZip:
            def infolist(self):return [a]
        with self.assertRaises(RuntimeError):
            r._select_deno_entry(FakeZip(),'deno.exe')

    def test_deno_version(self):
        self.assertEqual(r.version_tuple('deno 2.4.5\nv8 13.1'),(2,4,5))
        self.assertLess(r.version_tuple('deno 2.2.9'),r.MIN_VERSION)
    def test_no_deno_fallback(self):
        with patch.object(d,'find_deno',return_value=None),patch.object(d.shutil,'which',return_value=None):
            opts=d.options(lambda s:None)
            self.assertNotIn('js_runtimes',opts)
    def test_deno_preference(self):
        with patch.object(d,'find_deno',return_value='C:/geli/deno.exe'):
            opts=d.options(lambda s:None)
            self.assertEqual(opts['js_runtimes']['deno']['path'],'C:/geli/deno.exe')
            self.assertIn('ejs:npm',opts['remote_components'])
if __name__=='__main__':unittest.main()
