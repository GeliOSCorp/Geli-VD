import unittest
from pathlib import Path
from core.downloader import compatibility_message

class RC2Tests(unittest.TestCase):
 def test_facebook_story(self):
  self.assertIn('historias',compatibility_message('https://www.facebook.com/stories/1234567890123456/?source=profile_highlight','ERROR: Unsupported URL'))
 def test_facebook_reels_parser(self):
  self.assertIn('Facebook',compatibility_message('https://www.facebook.com/reel/503855738992989','Cannot parse data'))
 def test_other_platform_not_misclassified(self):
  self.assertIsNone(compatibility_message('https://www.instagram.com/reels/abc/','Unsupported URL'))
 def test_login_window_closure_instruction(self):
  src=(Path(__file__).resolve().parents[1]/'ui/main_window.py').read_text('utf8')
  self.assertIn('puedes cerrar la ventana',src)
 def test_no_story_engine_cycle(self):
  src=(Path(__file__).resolve().parents[1]/'core/engine_manager.py').read_text('utf8')
  self.assertIn('if fb_story or not compatible_failure',src)

if __name__=='__main__':unittest.main()
