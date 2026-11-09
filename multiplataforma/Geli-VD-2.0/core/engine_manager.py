"""Geli Smart Engine 1.8.7: versiones de yt-dlp aisladas y fallback limitado.

No toca el yt-dlp de la aplicación ni borra sesiones. Cada versión descargada
se instala en DATA/engines/<canal>-<versión> y se ejecuta en proceso propio.
"""
import json, os, queue, re, shutil, subprocess, sys, threading, time
from pathlib import Path
from .storage import DATA, platform, hostname
from .downloader import execute as embedded_execute, AuthenticationNeeded, clean
from .runtime_manager import find_deno

ROOT=DATA/'engines'
REGISTRY=ROOT/'registry.json'
COMPAT=re.compile(r'requested format is not available|only images are available|challenge solving failed|signature extraction failed|unable to extract|nsig extraction failed|no video formats found|unsupported url|unable to download (?:webpage|api page)|video unavailable',re.I)
NEVER=re.compile(r'drm|private video|members.only|login required|sign in|not a bot|age.restricted|http error (401|403|404)|forbidden|unauthorized|video has been removed|cancelado|cancelled|geo.restricted',re.I)

def _read():
    try:
        obj=json.loads(REGISTRY.read_text(encoding='utf-8'))
        if isinstance(obj,dict):return obj
    except (OSError,ValueError):pass
    return {'engines':[],'preferred':{}}

def _save(data):
    ROOT.mkdir(parents=True,exist_ok=True)
    tmp=REGISTRY.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    tmp.replace(REGISTRY)

def available():
    obj=_read()
    valid=[]
    for row in obj.get('engines',[]):
        path=ROOT/row.get('folder','')
        if row.get('folder') and (path/'yt_dlp'/'__init__.py').is_file():valid.append(row)
    return valid

def install(channel='nightly',log=lambda msg:None,timeout=420):
    """Instala una versión validada en una carpeta NUEVA; jamás actualiza pip global."""
    if channel not in ('stable','nightly'):raise ValueError('Canal no permitido')
    ROOT.mkdir(parents=True,exist_ok=True)
    stage=ROOT/('preparando-'+channel+'-'+str(os.getpid()))
    if stage.exists():shutil.rmtree(stage)
    stage.mkdir()
    try:
        cmd=([_worker_exe(),'--engine-pip'] if getattr(sys,'frozen',False) else [sys.executable,'-m','pip']) + ['install','--disable-pip-version-check','--target',str(stage),
             '--upgrade','--no-input']
        if channel=='nightly':cmd.append('--pre')
        cmd.append('yt-dlp[default,curl-cffi]')
        log('Preparando un motor alternativo de forma independiente…')
        r=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',env=_child_utf8_env(),timeout=timeout)
        if r.returncode:
            raise RuntimeError('No se pudo preparar el motor: '+(r.stderr or r.stdout)[-900:])
        verify=([_worker_exe(),'--engine-check',str(stage)] if getattr(sys,'frozen',False) else [sys.executable,'-c',
                'import sys;sys.path.insert(0,sys.argv[1]);import yt_dlp;'
                'from yt_dlp import YoutubeDL;from yt_dlp.version import __version__;'
                'assert callable(YoutubeDL);print(__version__)',str(stage)])
        check=subprocess.run(verify,capture_output=True,text=True,encoding='utf-8',errors='replace',env=_child_utf8_env(),timeout=45)
        if check.returncode:raise RuntimeError('Motor alternativo rechazado en autoprueba: '+check.stderr[-500:])
        version=check.stdout.strip().splitlines()[-1].strip()
        if not re.fullmatch(r'[A-Za-z0-9.+_-]{3,70}',version):raise RuntimeError('Versión devuelta no válida')
        folder=f'{channel}-{version}'
        dest=ROOT/folder
        if dest.exists():
            shutil.rmtree(stage)
        else:
            stage.rename(dest)
        registry=_read()
        registry['engines']=[x for x in registry.get('engines',[]) if x.get('folder')!=folder]
        registry['engines'].append({'channel':channel,'version':version,'folder':folder,'installed_at':int(time.time())})
        _save(registry)
        log(f'✓ Motor alternativo {channel} {version} validado y conservado.')
        return version
    finally:
        if stage.exists():shutil.rmtree(stage,ignore_errors=True)

def _worker_exe():
    if not getattr(sys,'frozen',False):return sys.executable
    worker=Path(sys.executable).with_name('Geli-VD-Worker.exe')
    if not worker.is_file():raise RuntimeError('Falta Geli-VD-Worker.exe en la instalación')
    return str(worker)

def _child_utf8_env():
    """Ensure Windows worker can print yt-dlp Unicode warnings over JSONL."""
    env=os.environ.copy()
    env['PYTHONIOENCODING']='utf-8:replace'
    env['PYTHONUTF8']='1'
    return env


def _run_isolated(row,url,custom,opts,log,cancel,download,progress=None,status=None):
    """El runner usa stdin para datos y stdout JSONL para eventos; sin shell."""
    path=ROOT/row['folder']
    worker=Path(__file__).with_name('engine_worker.py')
    safe={k:v for k,v in opts.items() if k not in ('logger','progress_hooks','postprocessor_hooks')}
    request={'url':url,'custom':custom,'options':safe,'download':download}
    p=subprocess.Popen(([_worker_exe(),'--engine-worker',str(path)] if getattr(sys,'frozen',False) else [sys.executable,'-X','utf8',str(worker),str(path)]),stdin=subprocess.PIPE,
                       stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1,
                       env=_child_utf8_env(),creationflags=(getattr(subprocess,'CREATE_NO_WINDOW',0) if os.name=='nt' else 0))
    result=None;error=None;auth=False
    try:
        p.stdin.write(json.dumps(request,ensure_ascii=False)+'\n');p.stdin.close()
        events=queue.Queue()
        def reader():
            for line in p.stdout:events.put(line)
            events.put(None)
        threading.Thread(target=reader,daemon=True).start()
        while True:
            if cancel is not None and cancel.is_set():
                p.terminate();raise RuntimeError('Cancelado por el usuario')
            try:raw=events.get(timeout=0.15)
            except queue.Empty:continue
            if raw is None:break
            try:event=json.loads(raw)
            except ValueError:continue
            kind=event.get('type')
            if kind=='log':log(event.get('message',''))
            elif kind=='progress' and progress:progress(int(event.get('percent',0)))
            elif kind=='status' and status:status(event.get('message',''))
            elif kind=='result':result=(event.get('info') or {},event.get('target'))
            elif kind=='error':error=event.get('message','Error de motor');auth=bool(event.get('auth'))
        p.wait(timeout=15)
        if result is not None and p.returncode==0:return result
        if auth:raise AuthenticationNeeded(platform(url,custom),error or 'Se requiere iniciar sesión')
        raise RuntimeError(error or ('Motor terminado con código '+str(p.returncode)))
    finally:
        if p.poll() is None:
            p.terminate()
            try:p.wait(timeout=3)
            except subprocess.TimeoutExpired:p.kill();p.wait()
        if p.stdout:p.stdout.close()

def compatible_failure(error):
    msg=str(error)
    return bool(COMPAT.search(msg)) and not bool(NEVER.search(msg))

def smart_execute(url,custom,build_options,log,cancel=None,download=False,progress=None,status=None):
    """Primero motor previamente exitoso; luego incluido y hasta 2 alternativos.
    No cambia motor ante fallos de autenticación, DRM, red o permisos.
    """
    name=platform(url,custom)
    # Los Stories no están implementados por el extractor de Facebook; no intentar motores a ciegas.
    from urllib.parse import urlparse
    fb_story=(name=='Facebook' and urlparse(url).path.lower().startswith('/stories/'))
    if name=='YouTube' and not find_deno():
        log('ℹ Compatibilidad de YouTube limitada: Deno no está disponible.')
    engines=available()
    registry=_read()
    preferred=registry.get('preferred',{}).get(name)
    alternatives=sorted(engines,key=lambda x:(x.get('folder')!=preferred,x.get('channel')!='nightly',-x.get('installed_at',0)))
    candidates=[('incluido',None)]+[(x['folder'],x) for x in alternatives]
    if preferred:
        candidates.sort(key=lambda item:item[0]!=preferred)
    candidates=candidates[:3]
    last=None
    for i,(key,engine) in enumerate(candidates):
        if cancel and cancel.is_set():raise RuntimeError('Cancelado por el usuario')
        if i:log('↻ Geli Smart Engine: probando una alternativa compatible…')
        try:
            if engine is None:
                result=embedded_execute(url,custom,build_options,log,cancel,download)
            else:
                result=_run_isolated(engine,url,custom,build_options(),log,cancel,download,progress,status)
            if registry.get('preferred',{}).get(name)!=key:
                latest=_read();latest.setdefault('preferred',{})[name]=key;_save(latest)
            log('✓ Motor compatible: '+key)
            return result
        except AuthenticationNeeded:raise
        except Exception as exc:
            last=exc;log('⚠ '+key+': '+clean(str(exc))[-600:])
            if fb_story or not compatible_failure(exc) or i==len(candidates)-1:raise
    raise last or RuntimeError('No hay un motor compatible')
