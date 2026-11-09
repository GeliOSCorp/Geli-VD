"""Static checks for the private UI beta (no graphical display required)."""
import unittest
from pathlib import Path
from unittest.mock import patch
from tempfile import TemporaryDirectory
from core import storage
from ui.theme import DARK, LIGHT

class VisualRegressionContracts(unittest.TestCase):
    def test_dark_checkboxes_have_contrast_and_visible_mark(self):
        for theme in (DARK, LIGHT):
            self.assertIn('QCheckBox::indicator:checked', theme)
            self.assertIn('checkbox_checked.png', theme)
            self.assertIn('QLabel#brandTitle',theme)
            self.assertIn('QFrame#hero',theme)
    def test_186_no_queue_background_or_visible_controls(self):
        src=(Path(__file__).resolve().parents[1]/'ui'/'main_window.py').read_text('utf8')
        self.assertNotIn('self.queue_timer.start(',src)
        self.assertNotIn("r.addWidget(label('COLA DE DESCARGAS'",src)
        self.assertNotIn("queue_actions=QHBoxLayout()",src)
        self.assertIn("def enqueue(self",src)  # preserved for a future v3, not activated
    def test_186_primary_actions_and_account_states(self):
        src=(Path(__file__).resolve().parents[1]/'ui'/'main_window.py').read_text('utf8')
        self.assertIn("setObjectName('linkCard')",src)
        self.assertIn("setObjectName('heroUrl')",src)
        self.assertIn("setObjectName('accountNav')",src)
        self.assertIn("setObjectName('accountStatus')",src)
        self.assertIn("setObjectName('downloadProgress')",src)
        self.assertIn("2.0",src)
        for theme in (DARK,LIGHT):
            self.assertIn('QProgressBar#downloadProgress',theme)
            self.assertIn('color:#ffffff;',theme)
    def test_beta_never_deletes_legacy_data(self):
        with TemporaryDirectory() as root:
            root=Path(root)
            old=root/'old';old.mkdir()
            secret=old/'sesion.dat';secret.write_text('do-not-delete')
            with patch.object(storage,'DATA',root/'new'), patch.object(storage,'SESSIONS',root/'new'/'sessions'):
                storage.init_clean()
                self.assertTrue(secret.exists())
                self.assertTrue(storage.SESSIONS.is_dir())

if __name__=='__main__':unittest.main()
