"""Motor común de descargas. Nunca se extraen cookies de navegadores automáticamente."""
import re, shutil, threading
from .runtime_manager import find_deno
from pathlib import Path
from .storage import active,session_file,platform,hostname
try:import yt_dlp
except ImportError:yt_dlp=None

AUTH=re.compile(r'(sign.in|log.in|login|required.auth|not a bot|cookie.*(required|need)|private video|session expired|confirm your age|use --cookies|http error 401|forbidden|http error 403|authentication)',re.I)
ANSI=re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
def clean(s):return ANSI.sub('',str(s))

def options(log, playlist=False):
    opts=dict(quiet=True,no_warnings=False,noplaylist=not playlist,logger=YtLogger(log))
    deno=find_deno()
    if deno:
        opts['js_runtimes']={'deno':{'path':deno}}
    elif shutil.which('node'):
        opts['js_runtimes']={'node':{'path':shutil.which('node')}}
    opts['remote_components']=['ejs:npm','ejs:github'] if deno else ['ejs:github']
    return opts

class YtLogger:
    def __init__(self,log):self.log=log
    def debug(self,msg):
        if not str(msg).startswith('[debug]'):self.log(clean(msg))
    def warning(self,msg):self.log('⚠ '+clean(msg))
    def error(self,msg):self.log('✖ '+clean(msg))

class AuthenticationNeeded(Exception):
    def __init__(self,platform_name,original):
        super().__init__(str(original));self.platform_name=platform_name

def execute(url, custom, build_options, log, cancel=None, download=False):
    """Intenta público primero, reintenta una sola vez con cookies del dominio si falla.
    No asume que todas las fallas sean de inicio de sesión.
    """
    if yt_dlp is None:raise RuntimeError('Falta yt-dlp. Instálalo desde requirements.txt.')
    name=platform(url,custom)
    def one(with_auth):
        if cancel and cancel.is_set():raise RuntimeError('Cancelado por el usuario')
        op=build_options()
        if with_auth:op['cookiefile']=str(session_file(name))
        with yt_dlp.YoutubeDL(op) as ydl:
            info=ydl.extract_info(url,download=download)
            target=ydl.prepare_filename(info) if download and info and info.get('_type')!='playlist' else None
            return info,target
    try:return one(False)
    except Exception as first:
        if cancel and cancel.is_set():raise
        msg=str(first)
        if not AUTH.search(msg):raise
        if active(name):
            log(f'🔐 {name}: acceso público rechazado; reintentando con la sesión importada.')
            try:return one(True)
            except Exception as second:
                if AUTH.search(str(second)):raise AuthenticationNeeded(name,second) from second
                raise
        raise AuthenticationNeeded(name,first) from first


def compatibility_message(url, error):
    """Mensaje de usuario: compatibilidad no equivale a falta de autenticación.

    La historia de Facebook puede requerir permisos, pero un Unsupported URL
    no demuestra que iniciar sesión la haga compatible.
    """
    message=str(error).lower()
    host=hostname(url)
    if host in ('facebook.com','www.facebook.com','m.facebook.com','web.facebook.com'):
        from urllib.parse import urlparse
        path=urlparse(url).path.rstrip('/').lower()
        if path.startswith('/stories/') and 'unsupported url' in message:
            return '⚠ Las historias de Facebook todavía no son compatibles con este motor.'
        if 'cannot parse data' in message:
            return '⚠ No se pudo interpretar este video de Facebook; prueba otro enlace compatible.'
    return None


class UnsupportedContent(Exception):
    """Formato conocido pero no compatible; no es un problema de cuenta."""

def is_unsupported_story(url):
    """Reconoce únicamente historias Facebook, no Reels ni videos convencionales."""
    from urllib.parse import urlparse
    parsed=urlparse(url)
    host=(parsed.hostname or "").lower()
    return host in ("facebook.com","www.facebook.com","m.facebook.com","web.facebook.com") and parsed.path.lower().startswith("/stories/")
