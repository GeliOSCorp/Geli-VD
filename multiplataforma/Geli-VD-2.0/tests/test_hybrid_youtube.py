import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class HybridYoutubeTests(unittest.TestCase):
    def test_native_firefox_route(self):
        src=(ROOT/'ui'/'main_window.py').read_text(encoding='utf8')
        self.assertIn("self.youtube_wizard();return",src)
        self.assertIn("def youtube_wizard(self):",src)
        self.assertIn("launch_firefox(firefox)",src)
        self.assertIn("import_youtube_from_profile()",src)
        self.assertIn("'🔑 Conectar cuenta'",src)
    def test_browser_is_not_automated(self):
        s=(ROOT/'core'/'firefox_native.py').read_text(encoding='utf8')
        self.assertIn('def launch_firefox',s)
        self.assertNotIn('from playwright',s.lower())
        self.assertIn('S(A)PISID',s)
if __name__=='__main__':unittest.main()
