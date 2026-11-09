"""Verificaciones estructurales del flujo de instalación; sin navegador ni red."""
from pathlib import Path
import ast
import unittest

ROOT=Path(__file__).resolve().parents[1]

class BrowserInstallerContract(unittest.TestCase):
    def test_python_parses(self):
        ast.parse((ROOT/'ui/main_window.py').read_text(encoding='utf-8'))
    def test_chromium_uses_same_interpreter_and_requires_consent(self):
        src=(ROOT/'ui/main_window.py').read_text(encoding='utf-8')
        self.assertIn("cmd=[sys.executable,'-m','playwright','install','chromium']",src)
        self.assertIn("QMessageBox.question(self,'Instalar navegador de Geli-VD'",src)
        self.assertIn("'INSTALLING'",src)
        self.assertIn("proc.terminate()",src)
    def test_browser_not_saved_before_open(self):
        src=(ROOT/'ui/main_window.py').read_text(encoding='utf-8')
        self.assertIn("save.setEnabled(False)",src)
        self.assertIn("self.main.events.browser_saved.emit(name,'READY')",src)
        self.assertIn("self.main.events.browser_saved.emit(name,'SAVED')",src)
        self.assertNotIn('Abrir en mi navegador habitual',src)
    def test_launchers_include_playwright(self):
        for f in ('iniciar_windows.bat','iniciar_mac.command','iniciar_linux.sh'):
            self.assertIn('playwright.sync_api',(ROOT/f).read_text(encoding='utf-8'))

if __name__=='__main__':unittest.main()
