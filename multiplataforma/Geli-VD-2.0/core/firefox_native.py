"""Firefox nativo, perfil privado de Geli-VD. Sin control automatizado del login.

Nunca lee el perfil personal del usuario. Importa solo cookies necesarias para
YouTube desde el perfil dedicado, después de que Firefox se haya cerrado.
"""
import http.cookiejar
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from .storage import DATA, session_file, match

FIREFOX_DIR = DATA / "firefox-runtime"
PROFILE_DIR = DATA / "firefox-youtube-profile"
INSTALLER_URL = "https://download.mozilla.org/?product=firefox-latest&os=win64&lang=es-ES"


def find_firefox():
    candidates = [FIREFOX_DIR / "firefox.exe"]
    if os.name == 'nt':
        for env in ('PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA'):
            if os.environ.get(env):
                candidates.append(Path(os.environ[env]) / 'Mozilla Firefox' / 'firefox.exe')
    elif sys_platform() == 'darwin':
        candidates += [Path('/Applications/Firefox.app/Contents/MacOS/firefox'),
                       Path.home()/'Applications/Firefox.app/Contents/MacOS/firefox']
    for c in candidates:
        if c.is_file():return c
    found = shutil.which('firefox')
    return Path(found) if found else None


def sys_platform():
    import sys
    return sys.platform


def download_installer(cancel, progress):
    """Download only Mozilla HTTPS installer; avoid running arbitrary binaries."""
    if os.name != 'nt':
        raise RuntimeError('La instalación automática de Firefox es solo para Windows. Instala Firefox desde mozilla.org.')
    path = Path(tempfile.mkdtemp(prefix='geli-firefox-')) / 'FirefoxSetup.exe'
    try:
        request = urllib.request.Request(INSTALLER_URL,headers={'User-Agent':'Geli-VD/1.8.5'})
        with urllib.request.urlopen(request, timeout=40) as response:
            from urllib.parse import urlparse
            host=urlparse(response.geturl()).hostname or ''
            if urlparse(response.geturl()).scheme!='https' or not (host in ('mozilla.org','mozilla.net') or host.endswith(('.mozilla.org','.mozilla.net'))):
                raise RuntimeError('La descarga no procede de un dominio HTTPS de Mozilla.')
            total=int(response.headers.get('Content-Length') or 0)
            if total>150_000_000:raise RuntimeError('El instalador supera el límite de tamaño esperado.')
            n=0
            with path.open('wb') as f:
                while True:
                    if cancel.is_set():raise RuntimeError('Descarga cancelada.')
                    block=response.read(256*1024)
                    if not block:break
                    n+=len(block)
                    if n>150_000_000:raise RuntimeError('Descarga demasiado grande.')
                    f.write(block)
                    progress(n,total)
        if n < 500_000:raise RuntimeError('El archivo de instalación parece incompleto.')
        return path
    except Exception:
        shutil.rmtree(path.parent,ignore_errors=True)
        raise


def verify_signature(installer):
    """Require a valid Windows Authenticode signature from Mozilla."""
    escaped=str(installer).replace("'", "''")
    script=(f"$s=Get-AuthenticodeSignature -LiteralPath '{escaped}'; "
            "if($s.Status -ne 'Valid' -or $s.SignerCertificate.Subject -notmatch 'Mozilla') {exit 1}")
    proc=subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',script],
                        capture_output=True,text=True,timeout=60)
    if proc.returncode:
        raise RuntimeError('Windows no pudo verificar la firma digital oficial de Mozilla. No se ejecutará el instalador.')


def install_firefox(cancel, progress):
    installer=download_installer(cancel,progress)
    try:
        if cancel.is_set():raise RuntimeError('Instalación cancelada.')
        verify_signature(installer)
        FIREFOX_DIR.parent.mkdir(parents=True,exist_ok=True)
        flags=['/S', '/InstallDirectoryPath='+str(FIREFOX_DIR),
               '/DesktopShortcut=false','/StartMenuShortcuts=false',
               '/TaskbarShortcut=false','/MaintenanceService=false']
        proc=subprocess.Popen([str(installer),*flags],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        while proc.poll() is None:
            if cancel.wait(0.35):
                proc.terminate()
                raise RuntimeError('Instalación cancelada.')
        if proc.returncode != 0 or not (FIREFOX_DIR/'firefox.exe').is_file():
            raise RuntimeError('Firefox no pudo instalarse en la carpeta de Geli-VD. Puedes instalarlo normalmente desde mozilla.org.')
        return FIREFOX_DIR/'firefox.exe'
    finally:
        shutil.rmtree(installer.parent,ignore_errors=True)


def launch_firefox(executable):
    PROFILE_DIR.mkdir(parents=True,exist_ok=True)
    # Ventana normal visible; Firefox realiza su propio login sin Playwright/CDP.
    return subprocess.Popen([str(executable),'--new-instance','--no-remote',
                             '--profile',str(PROFILE_DIR),'--new-window','https://www.youtube.com/'],
                            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


def import_youtube_from_profile():
    """Read the *dedicated* browser profile using yt-dlp; save selected domains only.
    No passwords, and never a user's default Firefox profile.
    """
    if not (PROFILE_DIR/'cookies.sqlite').is_file():
        raise RuntimeError('Firefox no ha creado cookies en el perfil. Inicia sesión e inténtalo de nuevo.')
    from yt_dlp.cookies import extract_cookies_from_browser
    jar=extract_cookies_from_browser('firefox',profile=str(PROFILE_DIR))
    # YouTube auth may depend on google.com S(A)PISID and youtube.com cookies.
    allowed=('youtube.com','google.com','accounts.google.com','youtu.be')
    selected=[c for c in jar if any(match(c.domain.lstrip('.').lower(),d) for d in allowed)]
    indicators={'SID','HSID','SSID','SAPISID','__Secure-1PSID','__Secure-3PSID','LOGIN_INFO'}
    if not selected or not any(c.name in indicators for c in selected):
        raise RuntimeError('No detectamos indicios suficientes de una sesión de YouTube. Comprueba que hayas iniciado sesión en Firefox.')
    target=session_file('YouTube')
    # Escribir primero el temporal; no reemplazar una sesión anterior si falla.
    tmp=target.with_suffix('.pending')
    filtered=http.cookiejar.MozillaCookieJar(str(tmp))
    for cookie in selected:filtered.set_cookie(cookie)
    try:
        filtered.save(ignore_discard=True,ignore_expires=False)
        if os.name != 'nt':tmp.chmod(0o600)
        tmp.replace(target)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return len(selected)


def close_firefox_gracefully(proc, timeout=15):
    """Ask Windows to close only the launched Firefox window; never force-kill or alter other profiles."""
    import time
    if proc.poll() is not None:return
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        user32=ctypes.windll.user32
        CB=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
        ids=[]
        def check(hwnd, _):
            pid=wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
            if pid.value==proc.pid and user32.IsWindowVisible(hwnd):ids.append(hwnd)
            return True
        user32.EnumWindows(CB(check),0)
        for hwnd in ids:user32.PostMessageW(hwnd,0x0010,0,0)  # WM_CLOSE
    try:proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError('Cierra la ventana de Firefox de Geli-VD y pulsa «Ya inicié sesión» otra vez. No se cerrará a la fuerza.')
