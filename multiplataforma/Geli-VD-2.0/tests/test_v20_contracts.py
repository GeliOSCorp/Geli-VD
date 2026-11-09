"""Source contracts for Geli-VD 2.0 RC1: no Qt display required."""
import unittest
from pathlib import Path
from core import storage

SRC=Path(__file__).resolve().parents[1]/'ui'/'main_window.py'
class V20Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.source=SRC.read_text(encoding='utf8')
    def test_session_reconnect_prompt(self):
        self.assertIn('def auth_required(self,name,reason):',self.source)
        self.assertIn('def session_saved(self,name):',self.source)
        self.assertIn('self.account_dialog.login_integrated()',self.source)
        self.assertIn('Reintentando con la sesión de ',self.source)
    def test_retry_once(self):
        self.assertIn('self._auth_retry_urls.add(key)',self.source)
        self.assertIn('automatic_retry=True',self.source)
        self.assertIn('if key in self._auth_retry_urls:',self.source)
    def test_menu_mp3_and_old_action(self):
        self.assertIn("('🎵 Convertir video a MP3',self.convert_mp3)",self.source)
        self.assertIn('def convert_mp3(self):',self.source)
    def test_legacy_storage_preserved(self):
        self.assertTrue('Geli-VD-1.8' in str(storage.DATA) or '.geli-vd-1.8' in str(storage.DATA))
    def test_queue_is_not_activated(self):
        self.assertIn('self.queue_timer=None',self.source)
        self.assertNotIn('self.queue_timer.start(',self.source)
if __name__=='__main__':unittest.main()
