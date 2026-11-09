import unittest
from pathlib import Path
from core.downloader import is_unsupported_story
from core.engine_manager import compatible_failure

class ReleaseTests(unittest.TestCase):
    def test_story_detected(self):
        self.assertTrue(is_unsupported_story('https://www.facebook.com/stories/123/?locale=es_LA'))
    def test_reel_not_story(self):
        self.assertFalse(is_unsupported_story('https://www.facebook.com/reel/123'))
    def test_other_domain_safe(self):
        self.assertFalse(is_unsupported_story('https://myfacebook.com/stories/123'))
    def test_no_story_prompt(self):
        s=(Path(__file__).parents[1]/'ui/main_window.py').read_text(encoding='utf8')
        self.assertLess(s.index('if is_unsupported_story(url):'),s.index('if is_youtube and not find_deno()'))
    def test_worker_entry(self):
        s=(Path(__file__).parents[1]/'main.py').read_text(encoding='utf8')
        self.assertIn('--engine-worker',s)
        self.assertIn('--engine-pip',s)
