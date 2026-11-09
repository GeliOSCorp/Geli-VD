"""Worker interno de un motor aislado. No es una aplicación de usuario."""
import json,sys,os
# Print JSON diagnostics in UTF-8 even when the Windows console uses cp1252.
for stream in (sys.stdout,sys.stderr):
    if stream is not None and hasattr(stream,'reconfigure'):
        stream.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path

def emit(kind,**kw):
    print(json.dumps({'type':kind,**kw},ensure_ascii=False,default=str),flush=True)

def _select_engine(package):
    # El proceso worker es nuevo; no debe cargar el yt-dlp incluido antes del alternativo.
    import importlib
    for key in list(sys.modules):
        if key=='yt_dlp' or key.startswith('yt_dlp.'):
            del sys.modules[key]
    sys.path.insert(0,str(package))
    importlib.invalidate_caches()

def check_engine(package):
    from pathlib import Path
    path=Path(package).resolve()
    if not (path/'yt_dlp'/'__init__.py').is_file():return 2
    _select_engine(path)
    import yt_dlp
    print(yt_dlp.version.__version__)
    return 0

def main():
    package=Path(sys.argv[1]).resolve()
    if not (package/'yt_dlp'/'__init__.py').exists():
        emit('error',message='Motor instalado incompleto');return 1
    _select_engine(package)
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from core.downloader import options,execute,AuthenticationNeeded
    request=json.loads(sys.stdin.readline())
    def log(x):emit('log',message=str(x))
    o=options(log,not request['options'].get('noplaylist',True))
    o.update(request['options'])
    def hook(d):
        if d.get('status')=='downloading':
            total=d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            if total:emit('progress',percent=min(100,int(d.get('downloaded_bytes',0)*100/total)))
            emit('status',message='Descargando…')
        elif d.get('status')=='finished':emit('status',message='Procesando el archivo…')
    if request['download']:o['progress_hooks']=[hook]
    try:
        info,target=execute(request['url'],request['custom'],lambda:dict(o),log,download=request['download'])
        if info and info.get('_type')=='playlist':
            info={'title':info.get('title','Lista'),'_type':'playlist','entries':len(info.get('entries') or [])}
        else:
            info={key:info.get(key) for key in ('id','title','uploader','channel','duration','extractor_key','thumbnail','webpage_url') if info and info.get(key) is not None}
        emit('result',info=info,target=target)
        return 0
    except AuthenticationNeeded as e:
        emit('error',message=str(e),auth=True);return 2
    except Exception as e:
        emit('error',message=str(e));return 1
if __name__=='__main__':sys.exit(main())
