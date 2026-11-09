"""Deno dedicado de Geli-VD: descarga opt-in, verificación SHA-256 y sin modificar PATH global.
No se ejecuta JavaScript arbitrario de la UI. yt-dlp aplica sus propios límites a EJS.
"""
import hashlib, io, json, os, platform, re, shutil, subprocess, sys, tempfile, urllib.request, zipfile
from pathlib import Path
from .storage import DATA

TOOLS=DATA/'tools'/'deno'
MIN_VERSION=(2,3,0)
MAX_BYTES=220*1024*1024
MAX_EXE_BYTES=350*1024*1024  # Deno puede superar 80 MiB descomprimido en Windows

def version_tuple(text):
    m=re.search(r'\bdeno\s+(\d+)\.(\d+)\.(\d+)',text,re.I)
    return tuple(map(int,m.groups())) if m else (0,0,0)

def _check(path):
    if not path or not Path(path).is_file():return False
    try:
        res=subprocess.run([str(path),'--version'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=9)
        return res.returncode==0 and version_tuple(res.stdout)>=MIN_VERSION
    except (OSError,subprocess.TimeoutExpired):return False

def find_deno():
    exe='deno.exe' if os.name=='nt' else 'deno'
    for candidate in (TOOLS/exe,Path(shutil.which('deno') or '')):
        if str(candidate)!='.' and _check(candidate):return str(candidate)
    return None

def target_asset():
    machine=platform.machine().lower()
    if sys.platform=='win32' and machine in ('amd64','x86_64'):return 'deno-x86_64-pc-windows-msvc.zip'
    if sys.platform=='win32' and machine in ('arm64','aarch64'):return 'deno-aarch64-pc-windows-msvc.zip'
    if sys.platform=='darwin' and machine in ('arm64','aarch64'):return 'deno-aarch64-apple-darwin.zip'
    if sys.platform=='darwin' and machine in ('x86_64','amd64'):return 'deno-x86_64-apple-darwin.zip'
    if sys.platform.startswith('linux') and machine in ('x86_64','amd64'):return 'deno-x86_64-unknown-linux-gnu.zip'
    if sys.platform.startswith('linux') and machine in ('aarch64','arm64'):return 'deno-aarch64-unknown-linux-gnu.zip'
    raise RuntimeError('Esta arquitectura todavía no admite instalación automática de Deno.')

def fetch(url,limit=MAX_BYTES):
    req=urllib.request.Request(url,headers={'User-Agent':'Geli-VD/1.8.8','Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(req,timeout=45) as res:
        if res.status!=200:raise RuntimeError('Respuesta inesperada al descargar componentes')
        if not res.url.startswith('https://'):raise RuntimeError('Conexión no segura')
        buf=bytearray()
        while True:
            chunk=res.read(1024*1024)
            if not chunk:break
            buf.extend(chunk)
            if len(buf)>limit:raise RuntimeError('El archivo excede el tamaño esperado')
        return bytes(buf)

def _select_deno_entry(z, exe):
    """Verificar estructura del ZIP sin imponer un límite obsoleto de 80 MiB.

    El ZIP ya pasó la verificación SHA-256 oficial. Esta comprobación impide
    que una entrada inesperada o una bomba ZIP llegue a escribirse.
    """
    entries = [x for x in z.infolist() if x.filename == exe and not x.is_dir()]
    if len(entries) != 1:
        raise RuntimeError('El paquete oficial no contiene un único ejecutable Deno reconocido.')
    entry = entries[0]
    if not 1_000_000 <= entry.file_size <= MAX_EXE_BYTES:
        raise RuntimeError('El ejecutable Deno tiene un tamaño fuera del rango seguro.')
    return entry


def install_deno(log=lambda message:None):
    current=find_deno()
    if current:return current
    wanted=target_asset()
    log('Preparando el componente de compatibilidad de YouTube…')
    data=json.loads(fetch('https://api.github.com/repos/denoland/deno/releases/latest',limit=3*1024*1024))
    assets=data.get('assets',[])
    asset=next((x for x in assets if x.get('name')==wanted),None)
    if not asset:raise RuntimeError('Deno no publicó una versión para esta plataforma.')
    digest=asset.get('digest','')
    if not re.fullmatch(r'sha256:[a-fA-F0-9]{64}',digest or ''):
        # No instalar ejecutables sin integridad comprobada.
        checks=next((x for x in assets if x.get('name')==wanted+'.sha256sum'),None)
        if not checks:raise RuntimeError('No se encontró el checksum verificable de Deno.')
        checksum=fetch(checks['browser_download_url'],limit=10000).decode('utf-8')
        found=re.search(r'\b[a-fA-F0-9]{64}\b',checksum)
        if not found:raise RuntimeError('Checksum de Deno inválido')
        expected=found.group().lower()
    else:expected=digest.split(':',1)[1].lower()
    raw=fetch(asset['browser_download_url'])
    if hashlib.sha256(raw).hexdigest()!=expected:raise RuntimeError('La integridad del navegador de scripts no coincide; instalación cancelada.')
    exe='deno.exe' if os.name=='nt' else 'deno'
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entry=_select_deno_entry(z,exe)
        TOOLS.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(prefix='deno-',suffix='.exe' if os.name=='nt' else '',dir=TOOLS);os.close(fd)
        target=Path(tmp)
        try:
            with z.open(entry) as f,target.open('wb') as dest:shutil.copyfileobj(f,dest)
            if os.name!='nt':target.chmod(0o700)
            if not _check(target):raise RuntimeError('Deno descargado no pasó la prueba de versión')
            target.replace(TOOLS/exe)
        finally:target.unlink(missing_ok=True)
    log('✓ Compatibilidad JavaScript preparada sin cambiar la configuración del sistema.')
    return str(TOOLS/exe)
