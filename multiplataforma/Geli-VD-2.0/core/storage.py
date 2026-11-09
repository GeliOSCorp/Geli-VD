"""Geli-VD 1.8.4: sesiones segregadas y datos locales no destructivos."""
import json, os, re, shutil
from pathlib import Path
from urllib.parse import urlparse

VERSION='2.0'
DATA=Path(os.environ.get('APPDATA',str(Path.home()))) / 'Geli-VD-1.8' if os.name=='nt' else Path.home()/'.geli-vd-1.8'
SESSIONS=DATA/'sessions'
SETTINGS=DATA/'settings.json'
HISTORY=DATA/'history.json'
SITES={'YouTube':('youtube.com','youtu.be'),'TikTok':('tiktok.com',),'Instagram':('instagram.com',),'Facebook':('facebook.com','fb.watch'),'Dailymotion':('dailymotion.com','dai.ly'),'Vimeo':('vimeo.com',),'X':('x.com','twitter.com')}
LOGIN={'YouTube':'https://www.youtube.com/','TikTok':'https://www.tiktok.com/login','Instagram':'https://www.instagram.com/accounts/login/','Facebook':'https://www.facebook.com/login/','Dailymotion':'https://www.dailymotion.com/signin','Vimeo':'https://vimeo.com/log_in','X':'https://x.com/i/flow/login'}

def read(path, default):
    try:return json.loads(Path(path).read_text(encoding='utf8'))
    except (OSError, ValueError):return default

def write(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8');temp.replace(path)

def hostname(url):return (urlparse(url).hostname or '').lower().rstrip('.')
def valid_domain(domain):
    d=hostname(domain) if '://' in domain else domain.lower().strip('. ')
    if not (3<len(d)<=253 and '.' in d) or not all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',s) for s in d.split('.')):
        raise ValueError('Introduce un dominio válido, por ejemplo cursos.ejemplo.com')
    if d=='localhost' or all(p.isdigit() for p in d.split('.')):raise ValueError('No se admiten IP o localhost')
    return d

def match(host,domain):return bool(host and (host==domain or host.endswith('.'+domain)))
def platform(url,custom=None):
    h=hostname(url)
    for d in (custom or []):
        if match(h,d):return d
    for name,domains in SITES.items():
        if any(match(h,d) for d in domains):return name
    return h or 'Desconocido'

def session_file(name):
    SESSIONS.mkdir(parents=True,exist_ok=True)
    return SESSIONS/(re.sub(r'[^a-z0-9.-]','_',name.lower())+'.txt')

def active(name):
    f=session_file(name)
    try:return f.is_file() and f.stat().st_size>40
    except OSError:return False

def clear_session(name):session_file(name).unlink(missing_ok=True)

def init_clean():
    """Ensure current app directories exist without touching older installations.

    A beta/test release must never silently delete saved sessions from 1.5.
    """
    DATA.mkdir(parents=True,exist_ok=True)
    SESSIONS.mkdir(parents=True,exist_ok=True)
