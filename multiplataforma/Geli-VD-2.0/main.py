#!/usr/bin/env python3
"""Geli-VD 2.0 · GeliCorp. Entrada GUI y subprocess aislados del ejecutable Windows."""
import sys

def main():
    # En el ejecutable compilado reutilizamos el intérprete empaquetado: no requiere Python global.
    if len(sys.argv)>1 and sys.argv[1]=='--engine-check':
        from core.engine_worker import check_engine
        return check_engine(sys.argv[2])
    if len(sys.argv)>1 and sys.argv[1]=='--engine-worker':
        from core.engine_worker import main as run_worker
        sys.argv=[sys.argv[0]]+sys.argv[2:]
        return run_worker()
    if len(sys.argv)>1 and sys.argv[1]=='--engine-pip':
        from pip._internal.cli.main import main as pip_main
        return pip_main(sys.argv[2:])
    from PySide6.QtWidgets import QApplication
    from core.storage import init_clean
    from ui.main_window import MainWindow
    init_clean()
    app=QApplication(sys.argv)
    app.setApplicationName('Geli-VD')
    win=MainWindow();win.show()
    return app.exec()

if __name__=='__main__':sys.exit(main())
