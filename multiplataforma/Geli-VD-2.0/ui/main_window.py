"""Geli-VD 2.0 — lanzamiento preparado · Python/PySide6."""
import io, os, re, sys, shutil, threading, urllib.request, webbrowser, http.cookiejar, subprocess, uuid, time
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse
from PySide6.QtCore import Qt, QObject, Signal, QTimer, QDateTime
from PySide6.QtGui import QIcon, QPixmap, QDesktopServices, QAction, QFont
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QFrame,QVBoxLayout,QHBoxLayout,QGridLayout,
    QLabel,QPushButton,QLineEdit,QComboBox,QCheckBox,QProgressBar,QTextEdit,QListWidget,QFileDialog,
    QMessageBox,QDialog,QInputDialog,QScrollArea,QSplitter,QMenu,QSizePolicy,QDateTimeEdit,QPlainTextEdit)
from core.storage import (DATA,SESSIONS,SETTINGS,HISTORY,SITES,LOGIN,read,write,platform,valid_domain,hostname,match,
                          session_file,active,clear_session)
from core.downloader import yt_dlp,options,AuthenticationNeeded,clean,compatibility_message,is_unsupported_story
from core.engine_manager import smart_execute, install as install_engine, available as available_engines
from core.runtime_manager import find_deno, install_deno
from core.firefox_native import find_firefox, install_firefox, launch_firefox, import_youtube_from_profile, close_firefox_gracefully
from ui.theme import DARK,LIGHT

class Events(QObject):
    log=Signal(str)
    status=Signal(str)
    progress=Signal(int)
    preview=Signal(object)
    completed=Signal(object)
    failed_auth=Signal(str,str)
    busy=Signal(bool)
    engine_done=Signal(str)
    queue_finished=Signal(str,bool,str)
    browser_saved=Signal(str,str)
    firefox_login_event=Signal(str)
    runtime_ready=Signal(bool,str)

def button(text,fn=None,primary=False):
    b=QPushButton(text);b.setCursor(Qt.PointingHandCursor)
    if primary:b.setObjectName('primary')
    if fn:b.clicked.connect(fn)
    return b

def label(text,section=False,muted=False):
    a=QLabel(text)
    if section:a.setObjectName('section')
    if muted:a.setObjectName('muted')
    a.setWordWrap(True)
    return a

class AccountsDialog(QDialog):
    def __init__(self,parent,selected=None):
        super().__init__(parent);self.main=parent
        self.setWindowTitle('Mis cuentas · Geli-VD');self.setMinimumSize(780,540);self.resize(890,590)
        root=QVBoxLayout(self);root.setContentsMargins(22,20,22,20);root.setSpacing(14)
        heading=QLabel('Mis cuentas');heading.setObjectName('dialogTitle');root.addWidget(heading)
        root.addWidget(label('Conecta tus plataformas y administra cada sesión desde un mismo lugar.',muted=True))
        body=QHBoxLayout();root.addLayout(body,1)
        self.list=QListWidget();self.list.setObjectName('accountNav')
        self.list.setSpacing(5);self.list.setMinimumWidth(215);self.list.setMaximumWidth(245)
        self.list.setToolTip('Selecciona una plataforma para ver o administrar su sesión')
        body.addWidget(self.list)
        detail=QFrame();detail.setObjectName('accountCard');right=QVBoxLayout(detail)
        right.setContentsMargins(21,21,21,18);right.setSpacing(11)
        self.name=QLabel('');self.name.setObjectName('accountTitle')
        right.addWidget(self.name)
        self.state=QLabel('');self.state.setObjectName('accountStatus')
        self.state.setWordWrap(True);right.addWidget(self.state)
        self.account_hint=label('',muted=True);right.addWidget(self.account_hint)
        right.addSpacing(12)
        self.login_button=button('🔑 Iniciar sesión',self.login_integrated,True)
        self.login_button.setToolTip('Abre el navegador independiente de Geli-VD; si falta, ofrece instalarlo')
        right.addWidget(self.login_button)
        self.import_button=button('📁 Importar sesión (cookies.txt)',self.import_cookies)
        right.addWidget(self.import_button)
        self.delete_button=button('🗑 Cerrar sesión guardada',self.delete_session)
        right.addWidget(self.delete_button)
        right.addStretch()
        self.privacy_note=label('Las sesiones se conservan en este equipo. Las sesiones se guardan en este equipo. Las cookies aún no tienen cifrado propio: evita compartir el perfil de Windows.',muted=True)
        right.addWidget(self.privacy_note)
        body.addWidget(detail,1)
        footer=QHBoxLayout();root.addLayout(footer)
        footer.addWidget(button('＋ Añadir sitio',self.add_site))
        footer.addStretch();footer.addWidget(button('Cerrar',self.close))
        self.list.currentRowChanged.connect(self.select)
        self.refresh(selected)

    def names(self):return list(SITES)+list(self.main.custom)
    def selected(self):
        item=self.list.currentItem();return item.data(Qt.UserRole) if item else None
    def refresh(self,selected=None):
        selected=selected or self.selected()
        self.list.clear()
        from PySide6.QtWidgets import QListWidgetItem
        for name in self.names():
            item=QListWidgetItem(('✓   ' if active(name) else '○   ')+name)
            item.setData(Qt.UserRole,name);self.list.addItem(item)
        row=self.names().index(selected) if selected in self.names() else 0
        if self.list.count():self.list.setCurrentRow(row)
        self.main.update_accounts_badge()
    def select(self,*_):
        name=self.selected()
        if not name:return
        self.name.setText(name)
        stored=active(name)
        self.state.setText('✓ Cookies guardadas  ·  pendientes de verificar' if stored else '○  Sin sesión conectada')
        self.state.setProperty('connected', bool(stored))
        self.state.style().unpolish(self.state);self.state.style().polish(self.state)
        self.delete_button.setEnabled(stored)
        if name=='YouTube':
            self.login_button.setText('🔑 Conectar con Firefox')
            self.login_button.setToolTip('Abre Firefox normal en un perfil independiente de Geli-VD')
            self.account_hint.setText('Conéctate usando Firefox normal en una ventana propia. No necesitas instalar extensiones ni compartir tu contraseña con Geli-VD.')
            self.privacy_note.setText('Puedes descargar contenido público sin cuenta. Las cookies guardadas aún no están cifradas en esta beta y se usan solo cuando una descarga necesita autenticación.')
        else:
            self.login_button.setText('🔑 Conectar cuenta')
            self.login_button.setToolTip('Abre Chromium con un perfil aislado; ofrece instalarlo si falta')
            self.account_hint.setText('Se abre una ventana exclusiva de Geli-VD para iniciar sesión. Al finalizar, podrás guardar las cookies de esta plataforma.')
            self.privacy_note.setText('Las cookies permanecen en este equipo, sin cifrar todavía en esta beta. Guardarlas no garantiza que la cuenta siga autenticada.')
        self.import_button.setText('📁 Importar sesión (alternativa)' if name=='YouTube' else '📁 Importar sesión')

    def youtube_wizard(self):
        """Firefox real with private profile; no Google login automation."""
        if getattr(self,'firefox_dialog',None) and self.firefox_dialog.isVisible():
            self.firefox_dialog.raise_();self.firefox_dialog.activateWindow();return
        dlg=QDialog(self);self.firefox_dialog=dlg
        dlg.setWindowTitle('Conectar YouTube · Firefox · Geli-VD')
        dlg.setMinimumWidth(600);dlg.resize(680,340)
        lay=QVBoxLayout(dlg);lay.setContentsMargins(24,22,24,22);lay.setSpacing(12)
        lay.addWidget(label('CONECTAR YOUTUBE',section=True))
        lay.addWidget(label('Inicia sesión normalmente en una ventana de Firefox. No utilizamos un navegador automatizado para acceder a Google.',muted=True))
        status=label('Preparando Firefox…',muted=True);lay.addWidget(status)
        progress=QProgressBar();progress.setRange(0,0);lay.addWidget(progress)
        lay.addWidget(label('Firefox utiliza un perfil exclusivo de Geli-VD. Al terminar, puedes cerrar la ventana de Firefox y pulsar «Ya inicié sesión» para guardar la conexión. No se copian contraseñas ni cookies de tu navegador personal.',muted=True))
        row=QHBoxLayout();lay.addLayout(row)
        finish=button('✔ Ya inicié sesión',None,True);finish.setEnabled(False)
        cancel=button('Cancelar',dlg.reject)
        row.addWidget(finish);row.addWidget(cancel)
        state={'proc':None,'busy':True,'cancel':threading.Event(),'opened':False}
        def apply(event):
            if not dlg.isVisible():return
            if event=='INSTALLING':status.setText('Descargando e instalando Firefox oficial…');progress.setRange(0,0)
            elif event.startswith('BYTES:'):
                _,n,total=event.split(':');n=int(n);total=int(total)
                if total:progress.setRange(0,100);progress.setValue(min(100,int(n*100/total)))
                else:progress.setRange(0,0)
            elif event=='READY':
                state['busy']=False;state['opened']=True;progress.hide();finish.setEnabled(True)
                status.setText('Firefox abierto. Inicia sesión en YouTube; puedes cerrar la ventana de Firefox manualmente y después pulsar «Ya inicié sesión».')
            elif event=='SAVING':
                finish.setEnabled(False);progress.show();progress.setRange(0,0)
                status.setText('Cerrando el Firefox de Geli-VD y leyendo las cookies autorizadas…')
            elif event.startswith('SAVED:'):
                progress.hide();self.refresh('YouTube');dlg.accept()
                self.main.log('🔐 YouTube: cookies de Firefox guardadas (validez por comprobar).')
                self.main.session_saved('YouTube')
                QMessageBox.information(self,'Sesión guardada',
                    'Se guardaron cookies de YouTube. La autenticación se comprobará cuando una descarga las necesite.\n'
                    'Tu navegador personal no fue modificado.')
            elif event.startswith('ERROR:'):
                state['busy']=False;progress.hide();finish.setEnabled(state['opened'])
                status.setText('⚠ '+event[6:][:330]);self.main.log('⚠ Firefox: '+event[6:][:400])
        self.main.events.firefox_login_event.connect(apply)
        def cleanup(_):
            state['cancel'].set()
            try:self.main.events.firefox_login_event.disconnect(apply)
            except (TypeError,RuntimeError):pass
        dlg.finished.connect(cleanup)
        def start_job():
            try:
                firefox=find_firefox()
                if not firefox:
                    if os.name!='nt':
                        raise RuntimeError('Firefox no está instalado. Instálalo desde mozilla.org y vuelve a conectar.')
                    self.main.events.firefox_login_event.emit('INSTALLING')
                    firefox=install_firefox(state['cancel'],lambda n,total:self.main.events.firefox_login_event.emit(f'BYTES:{n}:{total}'))
                if state['cancel'].is_set():return
                proc=launch_firefox(firefox)
                state['proc']=proc
                # No depender de que el proceso inicial permanezca vivo: Firefox puede usar subprocesos.
                self.main.events.firefox_login_event.emit('READY')
            except Exception as ex:
                if not state['cancel'].is_set():self.main.events.firefox_login_event.emit('ERROR:'+str(ex))
        def finish_job():
            try:
                proc=state['proc']
                if not proc:raise RuntimeError('Firefox todavía no se abrió.')
                self.main.events.firefox_login_event.emit('SAVING')
                # Only close the process we launched, never an existing personal Firefox.
                if proc.poll() is None:
                    close_firefox_gracefully(proc)
                if state['cancel'].is_set():return
                n=import_youtube_from_profile()
                self.main.events.firefox_login_event.emit('SAVED:'+str(n))
            except Exception as ex:
                if not state['cancel'].is_set():self.main.events.firefox_login_event.emit('ERROR:'+str(ex))
        def confirm_install():
            if find_firefox():return True
            if os.name!='nt':return True
            return QMessageBox.question(dlg,'Preparar Firefox',
                'Geli-VD necesita Firefox nativo para conectar YouTube.\n\n'
                '¿Autorizas descargar el instalador oficial de Mozilla e instalarlo en los datos locales de Geli-VD? '
                'La descarga requiere Internet. No se cambiará tu navegador predeterminado.',
                QMessageBox.Yes|QMessageBox.No,QMessageBox.Yes)==QMessageBox.Yes
        finish.clicked.connect(lambda: (finish.setEnabled(False), threading.Thread(target=finish_job,daemon=True,name='geli-firefox-save').start()))
        if not confirm_install():return
        dlg.show()
        threading.Thread(target=start_job,daemon=True,name='geli-firefox-login').start()

    def login_integrated(self):
        """Autoinstala Chromium con consentimiento y abre una sesión aislada.

        El instalador corre en un hilo y usa el mismo Python/Playwright de Geli.
        Nunca se extraen perfiles o contraseñas de otros navegadores.
        """
        name=self.selected()
        if not name:return
        if name=='YouTube':
            self.youtube_wizard();return
        if getattr(self,'login_dialog',None) and self.login_dialog.isVisible():
            self.login_dialog.raise_();self.login_dialog.activateWindow();return
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as api:
                chromium_path=Path(api.chromium.executable_path)
            chromium_ready=chromium_path.is_file()
        except ImportError:
            QMessageBox.warning(self,'Falta Playwright',
                'No está instalado Playwright en el Python usado por Geli-VD.\n\n'
                'Cierra la aplicación y ejecuta iniciar_windows.bat para preparar las dependencias.\n'
                'También puedes ejecutar: python -m pip install playwright')
            return
        except Exception as exc:
            QMessageBox.warning(self,'No se pudo comprobar Chromium',str(exc))
            return
        if not chromium_ready:
            answer=QMessageBox.question(self,'Instalar navegador de Geli-VD',
                'Chromium todavía no está disponible para esta instalación de Playwright.\n\n'
                '¿Deseas descargarlo ahora? Se instalará en el almacenamiento de Playwright '
                'de tu usuario, sin modificar Edge o Chrome. Requiere conexión a Internet y '
                'espacio en disco.\n\nPuedes cancelar y seguir usando descargas públicas.',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if answer!=QMessageBox.Yes:return
        self.login_dialog=QDialog(self)
        dlg=self.login_dialog
        dlg.setWindowTitle('Conectar '+name+' · Geli-VD')
        dlg.setMinimumWidth(540);dlg.resize(590,260)
        lay=QVBoxLayout(dlg);lay.setSpacing(12);lay.setContentsMargins(20,20,20,20)
        lay.addWidget(label('Conectar cuenta · '+name,section=True))
        explanation=label('Se abrirá una ventana de navegador exclusiva de Geli-VD. '
            'Inicia sesión allí. Cuando termines, vuelve aquí y pulsa «Guardar sesión». '
            'Después puedes cerrar la ventana del navegador manualmente. '
            'No introduzcas contraseñas en esta ventana de Geli-VD.',muted=True)
        lay.addWidget(explanation)
        status=label('Preparando el navegador…',muted=True)
        status.setObjectName('loginStatus');lay.addWidget(status)
        progress=QProgressBar();progress.setRange(0,0)
        progress.setVisible(not chromium_ready);lay.addWidget(progress)
        actions=QHBoxLayout();lay.addLayout(actions)
        save=button('🔐 Guardar sesión',lambda:done.set(),True);save.setEnabled(False)
        cancel=button('Cancelar',lambda:(stop.set(),dlg.reject()))
        actions.addWidget(save);actions.addWidget(cancel)
        done=threading.Event();stop=threading.Event()
        self._login_running=True
        dlg.finished.connect(lambda _:(stop.set(),setattr(self,'_login_running',False)))
        # El diálogo recibe las señales en el hilo Qt, nunca mutamos controles desde Python worker.
        def callback(n,state):
            if n!=name or not dlg.isVisible():return
            if state=='INSTALLING':
                status.setText('Descargando Chromium de Playwright… La descarga puede tomar un tiempo.')
            elif state=='INSTALLED':
                status.setText('Chromium instalado. Iniciando navegador…')
            elif state=='READY':
                progress.hide();status.setText('Navegador abierto. Inicia sesión en '+name+', pulsa «Guardar sesión» y después puedes cerrar la ventana del navegador.')
                save.setEnabled(True)
            elif state=='SAVED':
                self.main.log('🔐 Cookies de '+name+' guardadas localmente (sin verificar autenticación).')
                self.refresh(name);dlg.accept()
                self.main.session_saved(name)
                QMessageBox.information(self,'Cookies guardadas',
                    'Se guardaron cookies de '+name+' en este equipo. Su validez se comprobará al descargar. '
                    'Puedes cerrar la ventana de inicio de sesión si continúa abierta. '
                    'El resto de tus cuentas y navegadores no se modificaron.')
            elif state=='CANCELLED':
                status.setText('Instalación o acceso cancelado. No se guardó ninguna sesión.')
                save.setEnabled(False);progress.hide()
            elif state.startswith('ERROR:'):
                status.setText('No se pudo completar: '+state[6:][:260])
                save.setEnabled(False);progress.hide()
                self.main.log('⚠ Navegador de '+name+': '+state[6:][:500])
        self.main.events.browser_saved.connect(callback)
        def disconnect(_):
            try:self.main.events.browser_saved.disconnect(callback)
            except (RuntimeError,TypeError):pass
        dlg.finished.connect(disconnect)
        dlg.show()

        def job():
            try:
                from playwright.sync_api import sync_playwright
                if not chromium_ready:
                    self.main.events.browser_saved.emit(name,'INSTALLING')
                    cmd=[sys.executable,'-m','playwright','install','chromium']
                    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                        text=True,encoding='utf-8',errors='replace',creationflags=(getattr(subprocess,'CREATE_NO_WINDOW',0) if os.name=='nt' else 0))
                    try:
                        started=time.monotonic()
                        while True:
                            if stop.is_set():
                                proc.terminate()
                                try:proc.wait(timeout=4)
                                except subprocess.TimeoutExpired:proc.kill()
                                self.main.events.browser_saved.emit(name,'CANCELLED');return
                            try:
                                output,_=proc.communicate(timeout=0.5)
                                break
                            except subprocess.TimeoutExpired:
                                if time.monotonic()-started>900:
                                    proc.kill()
                                    raise RuntimeError('Se agotó el límite de instalación de Chromium. Revisa la conexión.')
                        if proc.returncode!=0:
                            raise RuntimeError('Falló la instalación de Chromium (código '+str(proc.returncode)+'). '+(output or '')[-350:])
                        with sync_playwright() as verify:
                            if not Path(verify.chromium.executable_path).is_file():
                                raise RuntimeError('La instalación terminó, pero el navegador no aparece en su ruta esperada.')
                    finally:
                        if proc.poll() is None:proc.kill()
                    self.main.events.browser_saved.emit(name,'INSTALLED')
                if stop.is_set():return
                with sync_playwright() as api:
                    browser=api.chromium.launch(headless=False)
                    try:
                        context=browser.new_context()
                        # Recuperar solo las cookies guardadas de esta plataforma, no de Edge.
                        previous=session_file(name)
                        if previous.is_file():
                            try:
                                jar=http.cookiejar.MozillaCookieJar();jar.load(str(previous),ignore_discard=True,ignore_expires=False)
                                restore=[]
                                for cookie in jar:
                                    restore.append({'name':cookie.name,'value':cookie.value,
                                       'domain':cookie.domain,'path':cookie.path,'secure':cookie.secure,
                                       **({'expires':cookie.expires} if cookie.expires else {})})
                                if restore:context.add_cookies(restore)
                            except Exception as exc:
                                self.main.events.log.emit('ℹ No se pudieron restaurar cookies anteriores: '+str(exc)[:120])
                        page=context.new_page()
                        url=LOGIN.get(name,'https://'+name+'/')
                        try:page.goto(url,wait_until='domcontentloaded',timeout=45000)
                        except Exception as exc:
                            self.main.events.log.emit('ℹ '+name+': abre la página manualmente si es necesario: '+str(exc)[:100])
                        if stop.is_set():return
                        self.main.events.browser_saved.emit(name,'READY')
                        while not done.wait(0.25):
                            if stop.is_set():return
                            if not browser.is_connected():raise RuntimeError('Chromium se cerró antes de guardar la sesión.')
                        if stop.is_set():return
                        domains=SITES.get(name,(name,))
                        valid=[c for c in context.cookies() if any(match(c.get('domain','').lstrip('.').lower(),d) for d in domains)]
                        if not valid:raise RuntimeError('No hay cookies de '+name+'. Inicia sesión e inténtalo de nuevo.')
                        # Almacén de cookies Netscape filtradas por dominio. No declarar login confirmado.
                        from http.cookiejar import Cookie
                        target=session_file(name)
                        jar=http.cookiejar.MozillaCookieJar(str(target))
                        for c in valid:
                            dom=c['domain'];exp=c.get('expires',-1)
                            expires=int(exp) if exp and exp>0 else None
                            jar.set_cookie(Cookie(version=0,name=c['name'],value=c['value'],port=None,
                                port_specified=False,domain=dom,domain_specified=True,
                                domain_initial_dot=dom.startswith('.'),path=c.get('path','/'),
                                path_specified=True,secure=bool(c.get('secure')),expires=expires,
                                discard=expires is None,comment=None,comment_url=None,
                                rest={'HttpOnly':c.get('httpOnly',False)},rfc2109=False))
                        jar.save(ignore_discard=True,ignore_expires=True)
                        if os.name!='nt':target.chmod(0o600)
                        self.main.events.browser_saved.emit(name,'SAVED')
                    finally:
                        browser.close()
            except Exception as exc:
                if not stop.is_set():self.main.events.browser_saved.emit(name,'ERROR:'+str(exc))
        threading.Thread(target=job,daemon=True,name='geli-chromium-login').start()

    def import_cookies(self):
        name=self.selected()
        if not name:return
        src,_=QFileDialog.getOpenFileName(self,'Importar cookies Netscape','','Texto (*.txt);;Todos (*.*)')
        if not src:return
        try:
            jar=http.cookiejar.MozillaCookieJar();jar.load(src,ignore_discard=True,ignore_expires=True)
            domains=SITES.get(name,(name,))
            matches=[c for c in jar if any(match(c.domain.lstrip('.').lower(),d) or match(d,c.domain.lstrip('.').lower()) for d in domains)]
            if not matches:raise ValueError('El archivo no contiene cookies correspondientes a '+name)
            if len(Path(src).read_bytes())>10_000_000:raise ValueError('Archivo de cookies demasiado grande')
            # Copiar exclusivamente cookies del dominio elegido; no guardar
            # credenciales de servicios ajenos incluidas en la exportación.
            target=session_file(name)
            filtered=http.cookiejar.MozillaCookieJar(str(target))
            for cookie in matches:filtered.set_cookie(cookie)
            filtered.save(ignore_discard=True,ignore_expires=True)
            if os.name!='nt':target.chmod(0o600)
            self.main.log(f'🔐 Sesión de {name} importada (no verificada).')
            self.refresh(name)
            self.main.session_saved(name)
            QMessageBox.information(self,'Cookies guardadas','Sesión asociada a '+name+'. Se utilizará automáticamente si una descarga pública necesita autenticación.')
        except Exception as e:QMessageBox.warning(self,'No se pudo importar',str(e))
    def delete_session(self):
        name=self.selected()
        if name and active(name):
            if QMessageBox.question(self,'Eliminar sesión','¿Eliminar las cookies de '+name+' guardadas por Geli-VD?')==QMessageBox.Yes:
                clear_session(name);self.refresh(name)
    def add_site(self):
        raw,ok=QInputDialog.getText(self,'Dominio personalizado','Dominio (ej.: cursos.ejemplo.com):')
        if not ok:return
        try:
            domain=valid_domain(raw)
            if domain not in self.main.custom and domain not in {d for a in SITES.values() for d in a}:
                self.main.custom.append(domain);self.main.save();self.refresh(domain)
        except ValueError as e:QMessageBox.warning(self,'Dominio no válido',str(e))

def url_to_qurl(url):
    from PySide6.QtCore import QUrl
    return QUrl(url)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__();self.cfg=read(SETTINGS,{})
        self.custom=self.cfg.get('custom_domains',[])
        self.history=read(HISTORY,[])
        self.events=Events();self.working=False;self.cancel=threading.Event();self.account_dialog=None
        self.preview_info=None;self.setWindowTitle('Geli-VD v2.0 · GeliCorp')
        self.jobs=read(DATA/'queue.json',[])
        for job in self.jobs:
            if job.get('state')=='Descargando':job['state']='Pendiente'
        self.queue_active=None
        screen=QApplication.primaryScreen()
        area=screen.availableGeometry() if screen else None
        w=min(1480,int(area.width()*0.92)) if area else 1380
        h=min(960,int(area.height()*0.91)) if area else 870
        self.resize(max(930,w),max(620,h));self.setMinimumSize(900,600)
        icon=Path(__file__).resolve().parents[1]/'assets/geli_vd_icon.png'
        if icon.exists():self.setWindowIcon(QIcon(str(icon)))
        self.build_menu();self.build()
        self.events.log.connect(self.log);self.events.status.connect(self.set_status)
        self.events.progress.connect(self.progress.setValue);self.events.preview.connect(self.display_preview)
        self.events.completed.connect(self.download_done);self.events.failed_auth.connect(self.auth_required)
        self.events.busy.connect(self.set_busy);self.events.engine_done.connect(self.engine_result)
        self.events.queue_finished.connect(self.queue_finished)
        self.events.runtime_ready.connect(self._runtime_ready)
        self._runtime_pending=None
        self._runtime_asked=False
        self._auth_pending=None
        self._auth_retry_urls=set()
        self.set_theme(self.cfg.get('theme','claro'))
        self.update_accounts_badge()
        self.refresh_history()
        self.log('Geli-VD 2.0 listo · Sesiones guiadas y avisos de compatibilidad.')
        self.refresh_queue()
        # V1.8.7: la cola y programación quedan reservadas para 3.0.
        # No iniciar el temporizador: nunca descargar tareas antiguas en silencio.
        self.queue_timer=None

    def build_menu(self):
        bar=self.menuBar();file=bar.addMenu('Archivo');history=bar.addMenu('Historial');tools=bar.addMenu('Herramientas');help=bar.addMenu('Ayuda')
        for menu,items in [(file,[('📋 Pegar enlace',self.paste),('📁 Abrir descargas',self.open_folder),('✖ Salir',self.close)]),
                           (history,[('🗑 Borrar historial',self.clear_history)]),
                           (tools,[('👤 Mis cuentas',self.accounts),('🎵 Convertir video a MP3',self.convert_mp3),('⚙ Motor / actualizar yt-dlp',self.engine_info),('🎨 Alternar tema',self.toggle_theme)]),
                           (help,[('ℹ Acerca de Geli-VD',self.about),('🔒 Privacidad y datos',self.privacy),('💻 GeliCorp en GitHub',lambda:QDesktopServices.openUrl(url_to_qurl('https://github.com/GeliOSCorp')))])]:
            for name,fn in items:menu.addAction(name,fn)

    def build(self):
        base=QWidget()
        self.scroller=QScrollArea();self.scroller.setWidgetResizable(True)
        self.scroller.setFrameShape(QFrame.NoFrame)
        self.scroller.setWidget(base);self.setCentralWidget(self.scroller)
        base.setMinimumHeight(760)
        page=QVBoxLayout(base);page.setContentsMargins(18,16,18,16);page.setSpacing(12)
        hero=QFrame();hero.setObjectName('hero');h=QHBoxLayout(hero)
        h.setContentsMargins(22,15,22,15);h.setSpacing(14)
        icon=Path(__file__).resolve().parents[1]/'assets/geli_vd_icon.png'
        il=QLabel();il.setObjectName('brandIcon');im=QPixmap(str(icon))
        il.setPixmap(im.scaled(60,60,Qt.KeepAspectRatio,Qt.SmoothTransformation))
        il.setFixedSize(60,60);h.addWidget(il)
        name=QVBoxLayout();name.setSpacing(3)
        name_title=QLabel('Geli-VD');name_title.setObjectName('brandTitle');name.addWidget(name_title)
        name_sub=QLabel('Video Downloader  ·  v2.0');name_sub.setObjectName('brandSubtitle');name.addWidget(name_sub)
        h.addLayout(name);h.addSpacing(14)
        h.addWidget(button('↻  Actualizar motor',self.update_engine))
        self.themebtn=button('☾  Modo oscuro',self.toggle_theme);h.addWidget(self.themebtn)
        h.addStretch()
        mark=QVBoxLayout();mark.setSpacing(2)
        brand=QLabel('GeliCorp');brand.setObjectName('brandSignature');brand.setAlignment(Qt.AlignRight)
        tagline=QLabel('Software local · Sin anuncios');tagline.setObjectName('brandSubtitle');tagline.setAlignment(Qt.AlignRight)
        mark.addWidget(brand);mark.addWidget(tagline);h.addLayout(mark)
        page.addWidget(hero)
        split=QSplitter(Qt.Horizontal);split.setChildrenCollapsible(False);page.addWidget(split,1)
        left=QWidget();l=QVBoxLayout(left);l.setSpacing(10);l.setContentsMargins(0,0,7,0)
        # Acción protagonista: enlace, pegar y analizar dentro de un panel propio.
        link_card=QFrame();link_card.setObjectName('linkCard')
        link_l=QVBoxLayout(link_card);link_l.setContentsMargins(20,18,20,20);link_l.setSpacing(12)
        lead=QHBoxLayout();lead.setSpacing(10)
        lead_title=QLabel('①  PEGA EL ENLACE DEL VIDEO');lead_title.setObjectName('heroHeading')
        lead.addWidget(lead_title);lead.addStretch()
        lead_tip=QLabel('Tu descarga comienza aquí');lead_tip.setObjectName('heroHelp')
        lead.addWidget(lead_tip)
        link_l.addLayout(lead)
        row=QHBoxLayout();row.setSpacing(9)
        self.url=QLineEdit();self.url.setObjectName('heroUrl')
        self.url.setPlaceholderText('Pega un enlace de YouTube, TikTok, Instagram, Facebook…')
        self.url.setClearButtonEnabled(True);self.url.setMinimumHeight(56)
        self.url.returnPressed.connect(self.analyze);row.addWidget(self.url,1)
        self.paste_button=button('📋  Pegar',self.paste);self.paste_button.setObjectName('pasteAction')
        self.paste_button.setMinimumHeight(56);self.paste_button.setMinimumWidth(98);row.addWidget(self.paste_button)
        self.anbtn=button('⌕  Analizar',self.analyze,True);self.anbtn.setObjectName('primary')
        self.anbtn.setMinimumHeight(56);self.anbtn.setMinimumWidth(146);row.addWidget(self.anbtn)
        link_l.addLayout(row)
        l.addWidget(link_card)
        l.addWidget(label('DESTINO DE VÍDEOS',section=True));row=QHBoxLayout()
        self.destination=QLineEdit(self.cfg.get('video_destination',self.cfg.get('destination',str(Path.home()/'Downloads'))));row.addWidget(self.destination,1)
        row.addWidget(button('📂 Elegir',self.choose_folder));l.addLayout(row)
        l.addWidget(label('DESTINO DE AUDIO',section=True));row=QHBoxLayout()
        self.audio_destination=QLineEdit(self.cfg.get('audio_destination',self.cfg.get('destination',str(Path.home()/'Downloads'))));row.addWidget(self.audio_destination,1)
        row.addWidget(button('📂 Elegir',self.choose_audio_folder));l.addLayout(row)
        row=QHBoxLayout();col=QVBoxLayout();col.addWidget(label('FORMATO',section=True));self.fmt=QComboBox();self.fmt.addItems(['Video (MP4)','Audio (MP3)','Audio (M4A)']);self.fmt.currentTextChanged.connect(self.quality_change);col.addWidget(self.fmt);row.addLayout(col)
        col=QVBoxLayout();col.addWidget(label('CALIDAD',section=True));self.quality=QComboBox();col.addWidget(self.quality);row.addLayout(col)
        row.addStretch();col=QVBoxLayout();col.addWidget(label('SESIONES INICIADAS',section=True));self.account_badge=button('👤 Mis cuentas',self.accounts);col.addWidget(self.account_badge);row.addLayout(col);l.addLayout(row)
        self.quality_change();row=QHBoxLayout();self.subtitles=QCheckBox('Subtítulos (es/en)');self.playlist=QCheckBox('Lista / carrusel completo')
        for check in (self.subtitles,self.playlist):
            check.setCursor(Qt.PointingHandCursor);check.setMinimumHeight(28)
        row.addWidget(self.subtitles);row.addSpacing(17);row.addWidget(self.playlist);row.addStretch();l.addLayout(row)
        row=QHBoxLayout();self.dlbtn=button('⬇  Descargar video',self.download,True);self.dlbtn.setMinimumSize(235,50);row.addWidget(self.dlbtn);self.cancelbtn=button('■ Cancelar',self.cancel_download);self.cancelbtn.setEnabled(False);row.addWidget(self.cancelbtn)
        row.addStretch();row.addWidget(button('♫ Video → MP3',self.convert_mp3));row.addWidget(button('📂 Abrir carpeta',self.open_folder));l.addLayout(row)
        # Cola y descargas temporizadas se reservan para Geli-VD 3.0.
        # Mantener el código interno y queue.json para futura migración, sin UI.
        self.progress=QProgressBar();self.progress.setValue(0)
        self.progress.setMinimumHeight(23);self.progress.setFormat('%p%')
        self.progress.setObjectName('downloadProgress');l.addWidget(self.progress)
        self.status=label('Listo para descargar.',muted=True);l.addWidget(self.status)
        l.addWidget(label('HISTORIAL',section=True));self.hist=QListWidget();self.hist.itemDoubleClicked.connect(self.open_history);l.addWidget(self.hist,1)
        row=QHBoxLayout();row.addWidget(label('DETALLES TÉCNICOS',section=True));row.addStretch();row.addWidget(button('🧹 Limpiar log',lambda:self.logs.clear()));l.addLayout(row)
        self.logs=QTextEdit();self.logs.setReadOnly(True);self.logs.setMaximumHeight(145);l.addWidget(self.logs)
        split.addWidget(left)
        right=QFrame();right.setObjectName('card');r=QVBoxLayout(right)
        r.setContentsMargins(18,18,18,18);r.setSpacing(11)
        r.addWidget(label('VISTA PREVIA',section=True))
        self._cover_original=None
        self.cover=QLabel('Pega un enlace para visualizar el video')
        self.cover.setObjectName('cover');self.cover.setAlignment(Qt.AlignCenter);self.cover.installEventFilter(self)
        self.cover.setMinimumHeight(220);self.cover.setMaximumHeight(430)
        self.cover.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        r.addWidget(self.cover)
        self.video_title=QLabel('Esperando un enlace');self.video_title.setObjectName('videoTitle')
        self.video_title.setWordWrap(True);r.addWidget(self.video_title)
        self.meta=label('Analiza un video para ver sus datos.',muted=True);r.addWidget(self.meta)
        r.addSpacing(7)
        # La parte inferior del panel queda ahora ocupada por información útil,
        # no por un bloque vacío que crece con la ventana.
        self.details=QFrame();self.details.setObjectName('infoPanel')
        detail_l=QVBoxLayout(self.details);detail_l.setContentsMargins(15,14,15,14);detail_l.setSpacing(9)
        self.detail_heading=QLabel('Detalles de descarga');self.detail_heading.setObjectName('infoTitle')
        detail_l.addWidget(self.detail_heading)
        self.detail_format=label('Formato  ·  Video (MP4)',muted=True);detail_l.addWidget(self.detail_format)
        self.detail_destination=label('Destino  ·  Selecciona una carpeta',muted=True)
        self.detail_destination.setTextInteractionFlags(Qt.TextSelectableByMouse)
        detail_l.addWidget(self.detail_destination)
        self.detail_engine=label('Motor  ·  yt-dlp',muted=True);detail_l.addWidget(self.detail_engine)
        r.addWidget(self.details)
        self.help_panel=QFrame();self.help_panel.setObjectName('infoPanel')
        help_l=QVBoxLayout(self.help_panel);help_l.setContentsMargins(15,13,15,13);help_l.setSpacing(6)
        help_title=QLabel('Privacidad por diseño');help_title.setObjectName('infoTitle');help_l.addWidget(help_title)
        help_l.addWidget(label('Las descargas y el historial se gestionan en tu equipo. Las sesiones se importan únicamente cuando tú lo decides.',muted=True))
        r.addWidget(self.help_panel)
        # Espacio disponible utilizado por la vista previa y detalles, no cola.
        self.fmt.currentTextChanged.connect(self.update_preview_details)
        self.quality.currentTextChanged.connect(self.update_preview_details)
        self.destination.textChanged.connect(self.update_preview_details)
        self.audio_destination.textChanged.connect(self.update_preview_details)
        split.addWidget(right)
        self.splitter=split
        split.setSizes([770,530]);self.fmt.setCurrentText(self.cfg.get('format','Video (MP4)'))
        self.quality.setCurrentText(self.cfg.get('quality','Mejor calidad'))
        self.update_preview_details()
        QTimer.singleShot(0,self.adapt_layout)

    def adapt_layout(self):
        width=self.width()
        if hasattr(self,'help_panel'):
            self.help_panel.setVisible(width>=1030)
        if hasattr(self,'details'):
            self.details.setVisible(width>=980)

    def eventFilter(self,obj,event):
        from PySide6.QtCore import QEvent
        if obj is getattr(self,'cover',None) and event.type()==QEvent.Resize and self._cover_original is not None:
            QTimer.singleShot(0,self._resize_cover_image)
        return super().eventFilter(obj,event)

    def _resize_cover_image(self):
        pix=self._cover_original
        if pix is not None and not pix.isNull() and self.cover.width()>0 and self.cover.height()>0:
            self.cover.setPixmap(pix.scaled(self.cover.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))

    def resizeEvent(self,event):
        super().resizeEvent(event)
        QTimer.singleShot(0,self.adapt_layout)

    def save_queue(self):
        write(DATA/'queue.json',self.jobs)

    def refresh_queue(self):
        if not hasattr(self,'queue_list'):return
        selected=self.queue_list.currentRow()
        self.queue_list.clear()
        for j in self.jobs:
            when=j.get('at')
            stamp=(' · '+when.replace('T',' ')[:16]) if when else ''
            self.queue_list.addItem(f"{j.get('state','Pendiente')}{stamp} · {j['url'][:58]}")
            self.queue_list.item(self.queue_list.count()-1).setToolTip(j['url'])
        if 0<=selected<self.queue_list.count():self.queue_list.setCurrentRow(selected)

    def enqueue(self,scheduled=False):
        """Always ask for NEW URLs; never silently reuse the previous download."""
        dlg=QDialog(self);dlg.setWindowTitle('Programar descargas' if scheduled else 'Añadir descargas a cola')
        dlg.resize(570,400)
        lay=QVBoxLayout(dlg);lay.setSpacing(10)
        lay.addWidget(label('Enlaces nuevos para la cola',section=True))
        lay.addWidget(label('Pega uno o varios enlaces (uno por línea). El enlace que aparece en la pantalla principal NO se añadirá automáticamente.',muted=True))
        edit=QPlainTextEdit();edit.setPlaceholderText('https://www.youtube.com/watch?v=...\nhttps://www.instagram.com/reel/...')
        lay.addWidget(edit,1)
        buttons=QHBoxLayout();lay.addLayout(buttons)
        buttons.addWidget(button('📋 Pegar',lambda:edit.insertPlainText(QApplication.clipboard().text())))
        buttons.addWidget(button('Usar enlace actual',lambda:edit.setPlainText(self.url.text().strip())))
        buttons.addStretch()
        buttons.addWidget(button('Cancelar',dlg.reject))
        buttons.addWidget(button('🕒 Programar' if scheduled else '＋ Añadir a cola',dlg.accept,True))
        if dlg.exec()!=QDialog.Accepted:return
        urls=[x.strip() for x in edit.toPlainText().splitlines() if x.strip()]
        unique=list(dict.fromkeys(urls))
        if not unique or any(not x.startswith(('https://','http://')) or not urlparse(x).hostname for x in unique):
            QMessageBox.warning(self,'Enlace inválido','Introduce al menos un enlace HTTP(S) válido por línea.');return
        dest=self.active_destination().strip()
        if not dest:
            QMessageBox.warning(self,'Destino inválido','Selecciona una carpeta de destino.');return
        at=None
        if scheduled:
            dt=self.schedule.dateTime().toPython()
            if dt<=datetime.now():
                QMessageBox.warning(self,'Horario','Elige una fecha y hora futuras.');return
            at=dt.isoformat(timespec='seconds')
        existing={j['url'] for j in self.jobs if j.get('state') in ('Pendiente','Programado','Descargando')}
        added=0
        for url in unique:
            if url in existing:continue
            job=dict(id=uuid.uuid4().hex,url=url,at=at,state='Programado' if at else 'Pendiente',
                     fmt=self.fmt.currentText(),quality=self.quality.currentText(),
                     dest=str(Path(dest).expanduser()),subtitles=self.subtitles.isChecked(),
                     playlist=self.playlist.isChecked())
            self.jobs.append(job);added+=1
        self.save_queue();self.refresh_queue()
        self.set_status(f'✓ {added} enlace(s) añadido(s) a la cola')
        self.log(f'Cola: {added} tarea(s) añadidas; {len(unique)-added} omitida(s) por duplicado.')

    def remove_selected_job(self):
        idx=self.queue_list.currentRow()
        if idx<0 or idx>=len(self.jobs):return
        if self.jobs[idx]['id']==self.queue_active:
            QMessageBox.information(self,'Descarga activa','Cancela primero la descarga en curso.')
            return
        self.jobs.pop(idx);self.save_queue();self.refresh_queue()

    def run_selected_now(self):
        idx=self.queue_list.currentRow()
        if 0<=idx<len(self.jobs) and self.jobs[idx]['state'] in ('Pendiente','Programado','Error','Cancelado'):
            self.jobs[idx]['state']='Pendiente';self.jobs[idx]['at']=None
            self.save_queue();self.refresh_queue();self.dispatch_queue()

    def queue_options(self,job):
        op=options(self.log_from_worker,job.get('playlist',False))
        op['outtmpl']=str(Path(job['dest'])/'%(title).150B [%(id)s].%(ext)s')
        op['progress_hooks']=[self.hook]
        if job['fmt']=='Video (MP4)':
            op['format']='bv*+ba/b/bv*/best';op['merge_output_format']='mp4'
            q=job['quality']
            if q.endswith('p') and q[:-1].isdigit():op['format_sort']=['res:'+q[:-1],'tbr','vcodec:h264','acodec:aac']
            if job.get('subtitles'):
                op.update(writesubtitles=True,writeautomaticsub=True,subtitleslangs=['es.*','en.*'],
                          postprocessors=[{'key':'FFmpegEmbedSubtitle'}])
        else:
            codec='mp3' if job['fmt']=='Audio (MP3)' else 'm4a'
            op['format']='ba/b'
            op['postprocessors']=[dict(key='FFmpegExtractAudio',preferredcodec=codec,
                         preferredquality=job['quality'].split()[0] if codec=='mp3' else '192')]
        return op

    def dispatch_queue(self):
        if self.working or self.queue_active:return
        now=datetime.now().isoformat(timespec='seconds')
        job=next((x for x in self.jobs if x['state'] in ('Pendiente','Programado') and
                 (not x.get('at') or x['at']<=now)),None)
        if job is None:return
        try:Path(job['dest']).mkdir(parents=True,exist_ok=True)
        except OSError as exc:
            job['state']='Error';self.log(str(exc));self.save_queue();self.refresh_queue();return
        self.queue_active=job['id'];job['state']='Descargando';self.save_queue();self.refresh_queue()
        self.cancel.clear();self.set_busy(True);self.progress.setValue(0)
        self.set_status('Descargando desde la cola…')
        opts=self.queue_options(job);custom=self.custom[:]
        def worker():
            try:
                info,target=smart_execute(job['url'],custom,lambda:dict(opts),self.log_from_worker,
                                    self.cancel,download=True)
                record=dict(url=job['url'],title=info.get('title',job['url']) if info else job['url'],
                            date=datetime.now().strftime('%Y-%m-%d %H:%M'),file=target)
                self.events.completed.emit(record)
                self.events.progress.emit(100)
                self.events.queue_finished.emit(job['id'],True,'✓ Descarga de cola completa')
            except AuthenticationNeeded as exc:
                self.events.failed_auth.emit(exc.platform_name,str(exc))
                self.events.queue_finished.emit(job['id'],False,'Se requiere iniciar sesión')
            except Exception as exc:
                msg='Cancelado' if self.cancel.is_set() else clean(exc)
                self.events.log.emit('✖ '+msg)
                self.events.queue_finished.emit(job['id'],False,(compatibility_message(job['url'],exc) or msg)[:180])
        threading.Thread(target=worker,daemon=True).start()

    def queue_finished(self,id,success,msg):
        for job in self.jobs:
            if job['id']==id:
                job['state']='Completado' if success else ('Cancelado' if self.cancel.is_set() else 'Error')
                break
        self.queue_active=None;self.set_busy(False);self.save_queue();self.refresh_queue()
        self.set_status(msg)

    def update_preview_details(self,*_):
        if not hasattr(self,'detail_format'):return
        self.detail_format.setText('Formato  ·  '+self.fmt.currentText()+'   |   '+self.quality.currentText())
        target=self.destination.text() if self.fmt.currentText()=='Video (MP4)' else self.audio_destination.text()
        self.detail_destination.setText('Destino  ·  '+(target or 'Sin seleccionar'))
        version=getattr(getattr(yt_dlp,'version',None),'__version__','No instalado') if yt_dlp else 'No instalado'
        self.detail_engine.setText('Motor  ·  yt-dlp '+version)

    def quality_change(self,*_):
        items=['Mejor calidad','1080p','720p','480p','360p'] if self.fmt.currentText()=='Video (MP4)' else (['320 kbps','192 kbps','128 kbps'] if self.fmt.currentText()=='Audio (MP3)' else ['Original'])
        old=self.quality.currentText();self.quality.clear();self.quality.addItems(items)
        if old in items:self.quality.setCurrentText(old)
    def set_theme(self,theme):
        self.theme=theme
        style=DARK if theme=='oscuro' else LIGHT
        check_icon=(Path(__file__).resolve().parents[1]/'assets/check_on.png').as_posix()
        style=style.replace(':/qt-project.org/styles/commonstyle/images/checkbox_checked.png',check_icon)
        self.setStyleSheet(style)
        self.themebtn.setText('☀  Modo claro' if theme=='oscuro' else '☾  Modo oscuro')
        self.save()
    def toggle_theme(self):self.set_theme('claro' if self.theme=='oscuro' else 'oscuro')
    def save(self):write(SETTINGS,dict(theme=getattr(self,'theme','oscuro'),destination=self.destination.text(),video_destination=self.destination.text(),audio_destination=self.audio_destination.text(),custom_domains=self.custom,format=self.fmt.currentText(),quality=self.quality.currentText()))
    def update_accounts_badge(self):
        n=sum(active(name) for name in list(SITES)+self.custom)
        self.account_badge.setText(f'♙ Mis cuentas · {n} sesiones')
    def accounts(self,selected=None):
        if self.account_dialog is not None and self.account_dialog.isVisible():
            self.account_dialog.raise_();self.account_dialog.activateWindow()
            if selected:self.account_dialog.refresh(selected)
            return
        self.account_dialog=AccountsDialog(self,selected);self.account_dialog.show()
    def log(self,text):
        self.logs.append(clean(text))
        sb=self.logs.verticalScrollBar();sb.setValue(sb.maximum())
    def set_status(self,text):self.status.setText(clean(text))
    def set_busy(self,busy):
        self.working=busy
        self.dlbtn.setEnabled(not busy);self.anbtn.setEnabled(not busy);self.cancelbtn.setEnabled(busy)
    def paste(self):self.url.setText(QApplication.clipboard().text().strip())
    def choose_folder(self):
        folder=QFileDialog.getExistingDirectory(self,'Carpeta de descargas',self.destination.text())
        if folder:self.destination.setText(folder);self.save()
    def choose_audio_folder(self):
        folder=QFileDialog.getExistingDirectory(self,'Carpeta de audios',self.audio_destination.text())
        if folder:self.audio_destination.setText(folder);self.save()
    def active_destination(self):
        return self.destination.text() if self.fmt.currentText()=='Video (MP4)' else self.audio_destination.text()
    def open_folder(self):
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.active_destination()))
    def set_preview(self,info):
        self.preview_info=info;self.video_title.setText(info.get('title','Sin título'))
        self.meta.setText(' · '.join(str(v) for v in [info.get('uploader') or info.get('channel'),info.get('duration') and f"{int(info['duration'])//60} min",info.get('extractor_key')] if v))
        url=info.get('thumbnail')
        if not url:return
        def bg():
            try:
                req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
                with urllib.request.urlopen(req,timeout=12) as response:blob=response.read(4_000_000)
                self.events.preview.emit(('image',blob))
            except Exception:pass
        threading.Thread(target=bg,daemon=True).start()
    def display_preview(self,payload):
        if isinstance(payload,tuple) and payload[0]=='image':
            pix=QPixmap();pix.loadFromData(payload[1]);self._cover_original=pix;self._resize_cover_image();return
        self.set_preview(payload)
    def build_options(self,progress=False):
        op=options(self.log_from_worker,self.playlist.isChecked())
        if progress:
            dest=self.active_destination().strip();op['outtmpl']=str(Path(dest)/'%(title).150B [%(id)s].%(ext)s')
            op['progress_hooks']=[self.hook]
            if self.fmt.currentText()=='Video (MP4)':
                op['format']='bv*+ba/b/bv*/best';op['merge_output_format']='mp4'
                q=self.quality.currentText()
                if q.endswith('p') and q[:-1].isdigit():op['format_sort']=['res:'+q[:-1],'tbr','vcodec:h264','acodec:aac']
                if self.subtitles.isChecked():op.update(writesubtitles=True,writeautomaticsub=True,subtitleslangs=['es.*','en.*'],postprocessors=[{'key':'FFmpegEmbedSubtitle'}])
            else:
                codec='mp3' if self.fmt.currentText()=='Audio (MP3)' else 'm4a'
                op['format']='ba/b';op['postprocessors']=[dict(key='FFmpegExtractAudio',preferredcodec=codec,preferredquality=self.quality.currentText().split()[0] if codec=='mp3' else '192')]
        else:op['skip_download']=True;op['extract_flat']='in_playlist'
        return op
    def log_from_worker(self,s):self.events.log.emit(str(s))
    def hook(self,d):
        if self.cancel.is_set():raise RuntimeError('Cancelado por el usuario')
        if d.get('status')=='downloading':
            size=d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            if size:self.events.progress.emit(min(100,int(d.get('downloaded_bytes',0)*100/size)))
            self.events.status.emit('Descargando '+clean(d.get('_percent_str',''))+' · '+clean(d.get('_speed_str',''))+' · ETA '+clean(d.get('_eta_str','')))
        elif d.get('status')=='finished':self.events.status.emit('Procesando y uniendo audio/video…')
    def _runtime_ready(self,ok,message):
        pending=self._runtime_pending
        self._runtime_pending=None
        self.set_busy(False)
        self.log(message)
        if ok:
            self.set_status('✓ Componentes preparados. Continuando…')
            if pending and self.url.text().strip()==pending[0]:
                QTimer.singleShot(60,lambda:self.start(pending[1]))
        else:
            self.set_status('No se pudo preparar la compatibilidad de YouTube.')
            QMessageBox.warning(self,'Compatibilidad de YouTube',
                'No se pudo preparar Deno automáticamente.\n\n'
                'Puedes seguir usando Geli-VD con otros videos o plataformas. '
                'El detalle está en el registro técnico.')

    def _prepare_runtime(self,url,is_download):
        self._runtime_pending=(url,is_download)
        self.set_busy(True)
        self.set_status('Preparando compatibilidad de YouTube…')
        def background():
            try:
                path=install_deno(self.log_from_worker)
                self.events.runtime_ready.emit(True,'✓ Deno disponible: '+path)
            except Exception as exc:
                self.events.runtime_ready.emit(False,'✖ No se pudo preparar Deno: '+str(exc))
        threading.Thread(target=background,daemon=True).start()

    def start(self,is_download,automatic_retry=False):
        url=self.url.text().strip()
        if not url.startswith(('https://','http://')):QMessageBox.warning(self,'Enlace inválido','Pega un enlace http o https válido.');return
        if self.working:return
        # Historias de Facebook: identificar antes de lanzar extractores, cookies o Deno.
        if is_unsupported_story(url):
            self.set_status('Esta historia de Facebook todavía no es compatible.')
            self.log('ℹ Facebook Stories no es compatible en Geli-VD 2.0; no se intentaron motores ni autenticación.')
            QMessageBox.information(self,'Contenido no compatible',
                'Las historias de Facebook todavía no se pueden descargar con Geli-VD 2.0.\n\n'
                'Puedes seguir descargando videos y Reels compatibles. No necesitas volver a iniciar sesión.')
            return
        if not automatic_retry:
            self._auth_retry_urls.discard((url,is_download))
            self._auth_pending=None
        self._last_action_download=is_download
        # Si falta el runtime de YouTube, instalarlo una vez con autorización.
        # Nunca borrar ni modificar las cookies o los motores existentes.
        is_youtube=platform(url,self.custom)=='YouTube'
        if is_youtube and not find_deno() and not self._runtime_asked:
            self._runtime_asked=True
            answer=QMessageBox.question(self,'Mejorar compatibilidad de YouTube',
                'Para algunos videos Geli-VD necesita un componente gratuito de Deno.\n\n'
                '¿Quieres que lo prepare automáticamente? Solo se instalará en la carpeta\n'
                'privada de Geli-VD y no se modificarán tus sesiones ni tus navegadores.',
                QMessageBox.Yes|QMessageBox.No,QMessageBox.Yes)
            if answer==QMessageBox.Yes:
                self._prepare_runtime(url,is_download)
                return
            self.log('ℹ Se omitió la instalación opcional de Deno a petición del usuario.')
        if is_download:
            try:Path(self.active_destination()).mkdir(parents=True,exist_ok=True)
            except OSError as e:QMessageBox.warning(self,'Carpeta',str(e));return
        self.save();self.cancel.clear();self.set_busy(True);self.progress.setValue(0)
        self.set_status('Descargando…' if is_download else 'Analizando…')
        # Todas las opciones Qt se capturan aquí en el hilo gráfico.
        opts=self.build_options(is_download);custom=self.custom[:]
        def build():return dict(opts)
        def worker():
            try:
                info,target=smart_execute(url,custom,build,self.log_from_worker,self.cancel,download=is_download,
                    progress=self.events.progress.emit,status=self.events.status.emit)
                if is_download:
                    record=dict(url=url,title=info.get('title',url) if info else url,date=datetime.now().strftime('%Y-%m-%d %H:%M'),file=target)
                    self.events.completed.emit(record);self.events.progress.emit(100)
                    self.events.status.emit('✓ Descarga completa')
                else:
                    self.events.preview.emit(info or {});self.events.status.emit('✓ Listo para descargar')
            except AuthenticationNeeded as e:
                self.events.log.emit('🔐 Se requiere sesión en '+e.platform_name+': '+clean(e))
                self.events.status.emit('🔐 '+e.platform_name+' requiere iniciar sesión')
                self.events.failed_auth.emit(e.platform_name,str(e))
            except Exception as e:
                self.events.log.emit('✖ '+clean(e))
                self.events.status.emit('■ Cancelado' if self.cancel.is_set() else (compatibility_message(url,e) or ('⚠ Este video requiere verificar tu cuenta de YouTube' if 'confirm your age' in str(e).lower() else '⚠ No se pudo procesar este enlace')))
            finally:self.events.busy.emit(False)
        threading.Thread(target=worker,daemon=True).start()
    def analyze(self):self.start(False)
    def download(self):self.start(True)
    def cancel_download(self):self.cancel.set();self.set_status('Cancelando…')
    def download_done(self,record):
        self.history.insert(0,record);self.history=self.history[:300];write(HISTORY,self.history);self.refresh_history()
    def refresh_history(self):
        self.hist.clear()
        for r in self.history:self.hist.addItem('✓ '+r.get('title','')+' · '+r.get('date',''))
    def open_history(self,item):
        n=self.hist.row(item)
        if n<len(self.history):
            f=self.history[n].get('file')
            if f and Path(f).exists():QDesktopServices.openUrl(url_to_qurl(Path(f).as_uri()))
            else:self.url.setText(self.history[n].get('url',''))
    def clear_history(self):
        if QMessageBox.question(self,'Historial','¿Borrar el historial local?')==QMessageBox.Yes:
            self.history=[];write(HISTORY,[]);self.refresh_history()
    def auth_required(self,name,reason):
        """Offer a useful single action, not a technical error dialog.

        The retry stays bound to the exact URL/action and is attempted once only.
        Cookies are treated as *saved*, never as proof of valid authentication.
        """
        current=self.url.text().strip()
        is_download=getattr(self,'_last_action_download',False)
        key=(current,is_download)
        if key in self._auth_retry_urls:
            self._auth_pending=None
            self.log('ℹ La sesión de '+name+' no permitió acceder al contenido tras reintentar.')
            QMessageBox.information(self,'No se pudo acceder',
                'No pudimos acceder al contenido con la sesión guardada de '+name+'.\n\n'
                'Comprueba que tu cuenta tenga permiso para ver ese contenido. '
                'Si corresponde, renueva la sesión en Mis cuentas.\n\n'
                'El registro técnico contiene más información.')
            return
        if not current or platform(current,self.custom)!=name:
            return
        self._auth_pending=(name,current,is_download)
        has_cookies=active(name)
        dlg=QMessageBox(self)
        dlg.setWindowTitle('Conectar '+name)
        dlg.setIcon(QMessageBox.Information)
        dlg.setText(('Necesitamos renovar tu sesión de '+name+'.' if has_cookies else
                     'Este contenido podría necesitar una cuenta de '+name+'.'))
        dlg.setInformativeText(
            'Geli-VD abrirá la opción de conexión para esta plataforma.\n'
            'Cuando guardes la sesión, intentaremos de nuevo el mismo enlace.\n\n'
            'No todos los errores de acceso se resuelven iniciando sesión.')
        connect=dlg.addButton('Conectar cuenta' if not has_cookies else 'Renovar sesión',QMessageBox.AcceptRole)
        dlg.addButton('Ahora no',QMessageBox.RejectRole)
        dlg.exec()
        if dlg.clickedButton()==connect:
            self.accounts(name)
            if self.account_dialog and self.account_dialog.isVisible():
                self.account_dialog.login_integrated()
        else:
            self._auth_pending=None

    def session_saved(self,name):
        """Continue the pending operation once, only after a user saved cookies."""
        pending=self._auth_pending
        if not pending or pending[0]!=name:return
        _,url,is_download=pending
        self._auth_pending=None
        if self.url.text().strip()!=url or not active(name):return
        key=(url,is_download)
        if key in self._auth_retry_urls:return
        self._auth_retry_urls.add(key)
        self.log('ℹ '+name+': sesión guardada. Reintentando enlace solicitado una sola vez…')
        self.set_status('Reintentando con la sesión de '+name+'…')
        if self.account_dialog and self.account_dialog.isVisible():
            self.account_dialog.close()
        attempts={'count':0}
        def resume():
            attempts['count']+=1
            if self.url.text().strip()!=url or attempts['count']>30:return
            if not self.working:
                self.start(is_download,automatic_retry=True)
            else:
                QTimer.singleShot(350,resume)
        QTimer.singleShot(450,resume)

    def convert_mp3(self):
        path,_=QFileDialog.getOpenFileName(self,'Convertir a MP3','','Videos (*.mp4 *.mkv *.webm *.mov *.avi)')
        if not path:return
        if not shutil.which('ffmpeg'):QMessageBox.warning(self,'FFmpeg','Para convertir necesitas FFmpeg.');return
        dst=str(Path(self.audio_destination.text())/(Path(path).stem+'.mp3'))
        def worker():
            proc=__import__('subprocess').run(['ffmpeg','-y','-i',path,'-vn','-codec:a','libmp3lame','-qscale:a','2',dst],capture_output=True,text=True)
            self.events.status.emit('✓ MP3 creado: '+dst if proc.returncode==0 else '✖ Conversión fallida: '+proc.stderr[-200:])
            self.events.busy.emit(False)
        self.set_busy(True);threading.Thread(target=worker,daemon=True).start()
    def engine_info(self):
        version=yt_dlp.version.__version__ if yt_dlp else 'No instalado'
        engines=available_engines()
        text='Motor incluido: '+version+'\nMotores alternativos: '+str(len(engines))
        text+='\n\n'+'\n'.join(f"{x['channel']}: {x['version']}" for x in engines)
        dlg=QMessageBox(self);dlg.setWindowTitle('Geli Smart Engine');dlg.setText(text)
        dlg.setInformativeText('Los motores adicionales se conservan y no sustituyen al incluido. Geli-VD cambia automáticamente cuando un error de compatibilidad lo requiere. Los detalles aparecen en el registro técnico.')
        update=dlg.addButton('Buscar motor nuevo',QMessageBox.AcceptRole)
        dlg.addButton('Cerrar',QMessageBox.RejectRole);dlg.exec()
        if dlg.clickedButton()==update:self.update_engine()

    def update_engine(self):
        if self.working:
            QMessageBox.information(self,'Descarga activa','Finaliza la operación antes de actualizar.')
            return
        answer=QMessageBox.question(self,'Preparar motor alternativo',
            '¿Descargar y validar una versión alternativa de yt-dlp?\n\n'
            'El motor que ya utilizas se conservará. Necesitas conexión a Internet.\n'
            'Geli-VD probará este motor automáticamente cuando corresponda.')
        if answer!=QMessageBox.Yes:return
        self.set_busy(True);self.set_status('Preparando un motor alternativo…')
        def worker():
            try:
                ver=install_engine('nightly',self.log_from_worker)
                self.events.engine_done.emit('✓ Motor alternativo '+ver+' validado. El anterior sigue disponible.')
            except Exception as exc:
                self.events.engine_done.emit('✖ No se pudo instalar un motor alternativo: '+str(exc))
            finally:self.events.busy.emit(False)
        threading.Thread(target=worker,daemon=True).start()

    def engine_result(self,msg):
        self.set_status('✓ Motor preparado' if msg.startswith('✓') else 'No se pudo preparar el motor')
        self.log(msg)
        QMessageBox.information(self,'Geli Smart Engine',msg[:1100])
    def about(self):
        dlg=QDialog(self);dlg.setWindowTitle('Acerca de Geli-VD');dlg.setMinimumWidth(560)
        dlg.setObjectName('aboutDialog');layout=QVBoxLayout(dlg)
        layout.setContentsMargins(26,24,26,22);layout.setSpacing(13)
        top=QHBoxLayout();top.setSpacing(15)
        icon=Path(__file__).resolve().parents[1]/'assets/geli_vd_icon.png'
        image=QLabel();pix=QPixmap(str(icon));image.setPixmap(pix.scaled(68,68,Qt.KeepAspectRatio,Qt.SmoothTransformation))
        top.addWidget(image)
        info=QVBoxLayout();title=QLabel('Geli-VD');title.setObjectName('brandTitle');info.addWidget(title)
        info.addWidget(label('Versión 2.0 · GeliCorp',muted=True))
        info.addWidget(label('GeliCorp · Descargador de video y audio',muted=True))
        top.addLayout(info);top.addStretch();layout.addLayout(top)
        line=QFrame();line.setFrameShape(QFrame.HLine);line.setObjectName('separator');layout.addWidget(line)
        description=label('Aplicación gratuita de escritorio para gestionar descargas de contenido permitido, con procesamiento local y sin telemetría propia.')
        layout.addWidget(description)
        for text in [
            'Desarrollador y marca: GeliCorp',
            'Copyright © 2026 GeliCorp. Derechos sobre nombre, identidad visual y recursos originales reservados.',
            'Licencia del código: consultar LICENSE del paquete o repositorio. Los componentes de terceros conservan sus respectivas licencias.',
            'Tecnologías: Python, PySide6 (Qt), yt-dlp y FFmpeg (cuando está disponible).',
            'Privacidad: las preferencias y cookies importadas se almacenan localmente. Las cookies son credenciales sensibles.',
            'Uso responsable: descarga únicamente contenido que tengas autorización para utilizar. No se admite eludir DRM.'
        ]:
            lab=label(text,muted=True);lab.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(lab)
        links=QHBoxLayout()
        links.addWidget(button('GitHub de GeliCorp',lambda:QDesktopServices.openUrl(url_to_qurl('https://github.com/GeliOSCorp'))))
        links.addStretch();links.addWidget(button('Cerrar',dlg.accept,True));layout.addLayout(links)
        dlg.exec()
    def privacy(self):QMessageBox.information(self,'Privacidad','Las cookies importadas se guardan únicamente en este equipo y se asocian al dominio.\nNo se capturan contraseñas ni sesiones de otros navegadores.\n\nGeli-VD no elimina las cookies de versiones anteriores.\n\nDatos de la v1.8: '+str(DATA))
    def closeEvent(self,event):self.save();event.accept()
