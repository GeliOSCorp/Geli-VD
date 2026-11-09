import unittest
from unittest.mock import patch,MagicMock
from core import engine_manager as em
from pathlib import Path

class WorkerEncodingTests(unittest.TestCase):
    def test_worker_utf8_env(self):
        with patch.dict(em.os.environ, {'PYTHONIOENCODING':'cp1252'}, clear=False):
            env=em._child_utf8_env()
        self.assertEqual(env['PYTHONIOENCODING'],'utf-8:replace')
        self.assertEqual(env['PYTHONUTF8'],'1')

    def test_replacement_warning_is_json_serializable(self):
        import json
        payload=json.dumps({'type':'log','message':'⚠ No se pudo analizar'},ensure_ascii=False)
        self.assertEqual(json.loads(payload.encode('utf-8').decode('utf-8'))['message'][0],'⚠')

if __name__=='__main__':unittest.main()
