"""
Geli-VideoDownloader  (tkinter + yt-dlp)

Requisitos (ver LEEME.md; los lanzadores iniciar_* los instalan solos):
    pip install -r requirements.txt
    ffmpeg y deno en el PATH   (Mac: brew install ffmpeg deno)
Opcional (páginas que yt-dlp no reconoce):
    pip install playwright
    playwright install chromium

Datos que guarda la app (solo en este equipo):
    Mac/Linux: ~/.geli-videodownloader/      Windows: %APPDATA%\\Geli-VideoDownloader\\
        config.json      preferencias (carpeta, calidad, cookies…)
        historial.json   historial de descargas (se puede desactivar o borrar)

Novedades 1.5: la sesión «Geli (mi sesión)» se guarda cifrada (DPAPI en
Windows) y se cierra sola tras 30 días sin uso.

Novedades 1.4: botón visible "Actualizar motor" con aviso al abrir, calidades con
nombre estándar (también en videos panorámicos), tema claro/oscuro que sigue al sistema,
un solo color de acento, nombre corto Geli-VD y sin el aviso del PO Token de YouTube.
"""

APP_NOMBRE = "Geli-VideoDownloader"     # nombre interno (no cambiar: define la carpeta de datos)
APP_CORTO = "Geli-VD"                   # nombre visible
APP_VERSION_NUM = "1.5"   # py1.5 al correr con Python, win1.5 en el .exe

import importlib.machinery
import io
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import urllib.error
import urllib.request
import zipfile
from datetime import datetime
from urllib.parse import urlparse
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Al abrir con doble clic, macOS no carga el PATH de Homebrew: lo agregamos
# para que yt-dlp encuentre ffmpeg y deno (también la ruta del instalador de deno).
for _ruta in ("/opt/homebrew/bin", "/usr/local/bin",
              os.path.join(os.path.expanduser("~"), ".deno", "bin")):
    if os.path.isdir(_ruta) and _ruta not in os.environ.get("PATH", "").split(os.pathsep):
        os.environ["PATH"] = _ruta + os.pathsep + os.environ.get("PATH", "")

ES_EXE = getattr(sys, "frozen", False)          # True en la versión instalable (.exe)
APP_VERSION = ("win" if ES_EXE else "py") + APP_VERSION_NUM
# En Windows, que ffmpeg/ffprobe no abran ventanas negras de consola
SIN_VENTANA = {"creationflags": 0x08000000} if os.name == "nt" else {}

# Versión .exe: ffmpeg, ffprobe y deno vienen incluidos en la carpeta "bin"
if ES_EXE:
    _bin = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)), "bin")
    if os.path.isdir(_bin):
        os.environ["PATH"] = _bin + os.pathsep + os.environ.get("PATH", "")

# Versión Python: si deno se instaló con pip (requirements.txt), agregarlo al PATH
try:
    import deno as _deno
    _dir_deno = os.path.dirname(_deno.find_deno_bin())
    if os.path.isdir(_dir_deno):
        os.environ["PATH"] = _dir_deno + os.pathsep + os.environ.get("PATH", "")
except Exception:
    pass

# Usar los certificados del sistema operativo si está disponible "truststore".
# Así funciona también en redes con inspección SSL (firewalls corporativos).
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

# ---- Motor actualizable en la versión .exe ---------------------------------
# El .exe trae yt-dlp incluido, pero no puede usar pip. "Actualizar motor" baja la
# versión nueva a la carpeta de datos (motor/) y, al reabrir, se usa esa en lugar
# de la incluida. Si esa versión fallara, se vuelve sola a la incluida.
if os.name == "nt":
    DIR_MOTOR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                             APP_NOMBRE, "motor")
else:
    DIR_MOTOR = os.path.join(os.path.expanduser("~"), ".geli-videodownloader", "motor")


class _BuscadorMotor:
    """Hace que Python cargue yt-dlp desde la carpeta del motor actualizado."""

    def __init__(self, carpeta):
        self.carpeta = carpeta

    def find_spec(self, nombre, ruta=None, objetivo=None):
        if nombre.split(".")[0] not in ("yt_dlp", "yt_dlp_ejs"):
            return None
        return importlib.machinery.PathFinder.find_spec(
            nombre, [self.carpeta] if "." not in nombre else ruta)


def _carpeta_motor_actual():
    try:
        with open(os.path.join(DIR_MOTOR, "actual.txt"), encoding="utf-8") as f:
            carpeta = os.path.join(DIR_MOTOR, f.read().strip())
        if os.path.isfile(os.path.join(carpeta, "yt_dlp", "__init__.py")):
            return carpeta
    except OSError:
        pass
    return None


MOTOR_ACTUALIZADO = None
_buscador = None
if ES_EXE and _carpeta_motor_actual():
    MOTOR_ACTUALIZADO = _carpeta_motor_actual()
    _buscador = _BuscadorMotor(MOTOR_ACTUALIZADO)
    sys.meta_path.insert(0, _buscador)

try:
    import yt_dlp
    DescargaCancelada = getattr(yt_dlp.utils, "DownloadCancelled", None)
except Exception:
    yt_dlp = None
    DescargaCancelada = None
    if _buscador:
        # El motor descargado falló: volver al que trae el programa
        sys.meta_path.remove(_buscador)
        for _m in [m for m in sys.modules if m.split(".")[0] in ("yt_dlp", "yt_dlp_ejs")]:
            del sys.modules[_m]
        MOTOR_ACTUALIZADO = None
        try:
            import yt_dlp
            DescargaCancelada = getattr(yt_dlp.utils, "DownloadCancelled", None)
        except Exception:
            yt_dlp = None
if DescargaCancelada is None:
    class DescargaCancelada(Exception):
        pass

try:
    from PIL import Image, ImageOps, ImageTk
except ImportError:
    Image = None


# ----------------------------------------------------------------- constantes
if os.name == "nt":
    DIR_DATOS = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NOMBRE)
else:
    DIR_DATOS = os.path.join(os.path.expanduser("~"), ".geli-videodownloader")
ARCH_CONFIG = os.path.join(DIR_DATOS, "config.json")
ARCH_HISTORIAL = os.path.join(DIR_DATOS, "historial.json")
ARCH_CONFIG_VIEJO = os.path.join(os.path.expanduser("~"), ".geli-videodownloader.json")
DIR_PERFIL = os.path.join(DIR_DATOS, "navegador")             # sesión del detector
ARCH_COOKIES_DET = os.path.join(DIR_DATOS, "cookies_detector.txt")
# "Geli (mi sesión)": se guarda cifrada (Windows: DPAPI, solo tu usuario de Windows puede
# abrirla; Mac/Linux: archivo con permisos solo para tu usuario). Caduca sin uso.
ARCH_SESION = os.path.join(DIR_DATOS, "sesion.dat")
ARCH_SESION_VIEJA = os.path.join(DIR_DATOS, "cookies_sesion.txt")      # py/win 1.4 (sin cifrar)
DIAS_CADUCIDAD_SESION = 30
MAX_HISTORIAL = 300

FORMATOS = ["Video (MP4)", "Audio (MP3)", "Audio (M4A)"]
CALIDADES = {
    "Video (MP4)": {"Mejor calidad": None, "1080p": 1080, "720p": 720,
                    "480p": 480, "360p": 360},
    "Audio (MP3)": {"320 kbps": "320", "192 kbps": "192", "128 kbps": "128"},
    "Audio (M4A)": {"Original": None},
}

# Opciones de "Cookies de". En Windows, Chrome/Edge/Brave/Opera cifran sus cookies con una
# protección que ningún programa externo puede leer, así que allí no se ofrecen.
OPC_SESION = "Geli (mi sesión)"       # sesión iniciada en la ventana de Geli-VD
OPC_ARCHIVO = "archivo cookies.txt…"  # archivo exportado con una extensión del navegador
NOMBRE_NAV = {"safari": "Safari", "chrome": "Chrome", "firefox": "Firefox", "edge": "Edge",
              "brave": "Brave", "opera": "Opera", "chromium": "Chromium", "vivaldi": "Vivaldi"}


def navegadores_instalados():
    """Navegadores de los que yt-dlp puede leer la sesión, según las carpetas de perfil que
    existen en este equipo. En Windows solo Firefox: Chrome/Edge/Brave/Opera cifran sus
    cookies con una protección que ningún programa externo puede leer."""
    casa = os.path.expanduser("~")
    if os.name == "nt":
        appdata = os.environ.get("APPDATA", "")
        rutas = {"firefox": [os.path.join(appdata, "Mozilla", "Firefox", "Profiles")]}
    elif sys.platform == "darwin":
        sop = os.path.join(casa, "Library", "Application Support")
        rutas = {
            "safari": [os.path.join(casa, "Library", "Containers", "com.apple.Safari"),
                       os.path.join(casa, "Library", "Cookies")],
            "chrome": [os.path.join(sop, "Google", "Chrome")],
            "firefox": [os.path.join(sop, "Firefox", "Profiles")],
            "edge": [os.path.join(sop, "Microsoft Edge")],
            "brave": [os.path.join(sop, "BraveSoftware", "Brave-Browser")],
            "opera": [os.path.join(sop, "com.operasoftware.Opera")],
            "vivaldi": [os.path.join(sop, "Vivaldi")],
        }
    else:
        cfg = os.path.join(casa, ".config")
        rutas = {
            "firefox": [os.path.join(casa, ".mozilla", "firefox"),
                        os.path.join(casa, "snap", "firefox", "common", ".mozilla", "firefox"),
                        os.path.join(casa, ".var", "app", "org.mozilla.firefox", ".mozilla",
                                     "firefox")],
            "chrome": [os.path.join(cfg, "google-chrome")],
            "chromium": [os.path.join(cfg, "chromium"),
                         os.path.join(casa, "snap", "chromium", "common", "chromium")],
            "edge": [os.path.join(cfg, "microsoft-edge")],
            "brave": [os.path.join(cfg, "BraveSoftware", "Brave-Browser")],
            "opera": [os.path.join(cfg, "opera")],
            "vivaldi": [os.path.join(cfg, "vivaldi")],
        }
    return [n for n, rs in rutas.items() if any(os.path.isdir(r) for r in rs)]


NAVEGADORES_REALES = navegadores_instalados()
NAVEGADORES = ["(ninguno)", OPC_SESION] + NAVEGADORES_REALES + [OPC_ARCHIVO]

# Errores que se resuelven con una sesión iniciada
PATRON_PIDE_SESION = re.compile(
    r"not a bot|sign in to confirm|login required|log in|sign in|requires? authentication|"
    r"use --cookies|--cookies-from-browser|age[- ]restricted|confirm your age|"
    r"inappropriate for some users|members[- ]only|join this channel|private video|"
    r"this video is private|rate-limit reached", re.I)

PALETAS = {
    "oscuro": {
        "fondo": "#14141f", "panel": "#1f1f2e", "campo": "#2a2a3d", "borde": "#3a3a55",
        "log": "#0f0f18", "texto": "#ecebff", "tenue": "#9a98b8", "pista": "#5a5878",
        "acento": "#7c5cff", "acento_hover": "#9479ff",
        "ok": "#3ddc97", "error": "#ff6b6b", "aviso": "#ffc857",
    },
    "claro": {
        "fondo": "#f6f6fa", "panel": "#ffffff", "campo": "#ececf3", "borde": "#d8d8e4",
        "log": "#fbfbfd", "texto": "#1d1b2e", "tenue": "#6b6987", "pista": "#a3a1ba",
        "acento": "#6a4cf0", "acento_hover": "#8063ff",
        "ok": "#1b9a66", "error": "#d64545", "aviso": "#b7791f",
    },
}
TEMAS = {"Según el sistema": "sistema", "Claro": "claro", "Oscuro": "oscuro"}

# Colores activos (se llenan al abrir la app según el tema elegido).
# Un solo color de acento: "rosa" apunta al mismo acento para un look minimalista.
C = {}


def sistema_en_modo_oscuro():
    try:
        if sys.platform == "darwin":
            r = subprocess.run(["defaults", "read", "-g", "AppleInterfaceStyle"],
                               capture_output=True, text=True, timeout=3)
            return "dark" in r.stdout.lower()
        if os.name == "nt":
            import winreg
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            return winreg.QueryValueEx(k, "AppsUseLightTheme")[0] == 0
    except Exception:
        pass
    return True


def aplicar_paleta(tema):
    if tema not in PALETAS:
        tema = "oscuro" if sistema_en_modo_oscuro() else "claro"
    C.clear()
    C.update(PALETAS[tema])
    C["rosa"], C["rosa_hover"] = C["acento"], C["acento_hover"]
    return tema


# Categorías estándar de calidad (como las nombra YouTube)
CATEGORIAS = [144, 240, 360, 480, 720, 1080, 1440, 2160, 4320]


def categoria_calidad(ancho, alto):
    """Nombre estándar de la calidad. Un video panorámico de 854x366 es '480p', igual
    que en YouTube; sirve también para videos verticales y 4:3."""
    if not alto:
        return None
    if not ancho:
        return alto
    corto, largo = min(ancho, alto), max(ancho, alto)
    equivalente = max(corto, largo * 9 / 16)
    return min(CATEGORIAS, key=lambda c: abs(c - equivalente))


def version_motor_disponible():
    """Última versión de yt-dlp publicada (PyPI)."""
    return json.loads(descargar_bytes("https://pypi.org/pypi/yt-dlp/json"))["info"]["version"]


def _wheel_pypi(paquete):
    """(versión, url) del wheel universal más reciente de un paquete en PyPI."""
    datos = json.loads(descargar_bytes(f"https://pypi.org/pypi/{paquete}/json"))
    for u in datos["urls"]:
        if u["filename"].endswith("py3-none-any.whl"):
            return datos["info"]["version"], u["url"]
    raise RuntimeError(f"No se encontró un paquete descargable de {paquete}")


def instalar_motor_exe(log=print):
    """Versión .exe: baja yt-dlp (y su complemento ejs) a la carpeta del motor."""
    version, url = _wheel_pypi("yt-dlp")
    destino = os.path.join(DIR_MOTOR, version)
    tmp = destino + ".tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)
    log(f"Descargando yt-dlp {version}…")
    with zipfile.ZipFile(io.BytesIO(descargar_bytes(url))) as z:
        z.extractall(tmp)
    try:
        v_ejs, url_ejs = _wheel_pypi("yt-dlp-ejs")
        log(f"Descargando yt-dlp-ejs {v_ejs}…")
        with zipfile.ZipFile(io.BytesIO(descargar_bytes(url_ejs))) as z:
            z.extractall(tmp)
    except Exception as e:
        log(f"(sin yt-dlp-ejs nuevo: {e}; se usa el incluido)")
    if not os.path.isfile(os.path.join(tmp, "yt_dlp", "__init__.py")):
        raise RuntimeError("El paquete descargado está incompleto")
    shutil.rmtree(destino, ignore_errors=True)
    os.replace(tmp, destino)
    with open(os.path.join(DIR_MOTOR, "actual.txt"), "w", encoding="utf-8") as f:
        f.write(version)
    for nombre in os.listdir(DIR_MOTOR):          # borrar versiones viejas
        ruta = os.path.join(DIR_MOTOR, nombre)
        if os.path.isdir(ruta) and nombre != version:
            shutil.rmtree(ruta, ignore_errors=True)
    return version


def es_error_cookies(msg):
    """True si el error es por no poder leer las cookies del navegador (p. ej. Chrome
    en Windows, que cifra sus cookies con una protección que otros programas no leen)."""
    m = str(msg).lower()
    return "dpapi" in m or ("cookie" in m and any(
        p in m for p in ("decrypt", "could not copy", "database", "keyring", "app-bound")))


def version_mayor(a, b):
    def n(v):
        return tuple(int(x) for x in re.findall(r"\d+", v or ""))
    return n(a) > n(b)

FUENTE = "Helvetica"
MINI_W, MINI_H = 340, 191

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")

PATRON_MEDIA = re.compile(r"\.(m3u8|mpd|mp4)(\?|$)", re.IGNORECASE)
PATRON_ANSI = re.compile(r"\x1b\[[0-9;]*m|\[[0-9;]*m")
PATRON_LOGIN = re.compile(r"login|signin|sign-in|ingresar|iniciar.sesi|ingresa a tu cuenta|"
                          r"/auth|acceder", re.IGNORECASE)

JS_PLAY = """() => {
  document.querySelectorAll('video').forEach(v => {
    v.muted = true; const p = v.play(); if (p) p.catch(() => {});
  });
}"""

JS_META = """() => {
  const m = n => (document.querySelector(`meta[property="${n}"]`) ||
                  document.querySelector(`meta[name="${n}"]`) || {}).content || null;
  return {titulo: m('og:title') || document.title, imagen: m('og:image')};
}"""

TEXTO_PRIVACIDAD = f"""{APP_CORTO} funciona solo en este equipo:

• No envía datos a ningún servidor propio. Solo se conecta a los sitios de los videos que tú pegas.

• "Cookies de" solo LEE las cookies del navegador elegido para que el sitio te reconozca (por ejemplo, para Instagram o videos con sesión). No abre el navegador ni deja nada en su historial.

• Al usar cookies, el sitio sabe que la descarga la hace tu cuenta.

• El detector de páginas usa un navegador aparte (no tu Safari/Chrome). Si eliges "Cookies de", le pasa solo las cookies del sitio que estás abriendo. Si inicias sesión en su ventana, esa sesión queda guardada en la carpeta de datos de la app, para la próxima vez.

• «Geli (mi sesión)» (Herramientas → Iniciar sesión) se guarda protegida: en Windows, cifrada con la protección del sistema (solo tu usuario de Windows puede abrirla); en Mac/Linux, en un archivo que solo tu usuario puede leer. Se cierra sola tras 30 días sin uso. Consejo: usa una cuenta secundaria para descargar. Puedes cerrarla cuando quieras en Herramientas → Cerrar sesiones de Geli-VD.

• Guarda tus preferencias y tu historial de descargas en:
  {DIR_DATOS}

• Puedes desactivar el historial (menú Historial → Guardar historial), borrarlo, o borrar todos los datos de la app (menú Historial)."""


# ------------------------------------------------------------------ utilidades
def limpiar(texto):
    """Quita los códigos de color de terminal que yt-dlp mete en sus textos."""
    return PATRON_ANSI.sub("", str(texto)).strip()


def formatear_duracion(seg):
    if not seg:
        return ""
    seg = int(seg)
    h, r = divmod(seg, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def nombre_seguro(texto):
    return re.sub(r'[\\/:*?"<>|\n\r]+', " ", texto).strip()[:150] or "video"


def descargar_bytes(url, referer=None):
    headers = {"User-Agent": UA}
    if referer:
        headers["Referer"] = referer
    ctx = None
    try:
        import ssl
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            return r.read()
    except urllib.error.URLError as e:
        # Redes con inspección SSL (firewall corporativo): reintentar con los
        # certificados del sistema en lugar de los de certifi
        if ctx is None or "CERTIFICATE_VERIFY_FAILED" not in str(e):
            raise
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read()


def mejor_miniatura(info):
    if not info:
        return None
    if info.get("thumbnail"):
        return info["thumbnail"]
    return next((t["url"] for t in reversed(info.get("thumbnails") or []) if t.get("url")),
                None)


def es_manifiesto(url):
    return bool(re.search(r"\.(m3u8|mpd)", url, re.I))


def es_maestro(url):
    u = url.lower()
    return es_manifiesto(url) and ("master" in u or "manifest" in u)


def etiqueta_fuente(url):
    u = url.lower()
    if ".mpd" in u:
        tipo = "DASH (.mpd)"
    elif ".m3u8" in u:
        tipo = "HLS (.m3u8)"
    else:
        tipo = "MP4 directo"
    if es_maestro(url):
        tipo += " · recomendado"
    return f"{tipo}  —  {urlparse(url).netloc}"


def leer_json(ruta, defecto):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


def escribir_json(ruta, datos):
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        tmp = ruta + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        os.replace(tmp, ruta)
    except Exception:
        pass


def borrar_archivo(ruta):
    try:
        if ruta and os.path.exists(ruta):
            os.remove(ruta)
    except OSError:
        pass


# ------------------------------------------------------------ sesión protegida
def _dpapi(datos, cifrar):
    """Cifra/descifra con DPAPI de Windows (atado a tu usuario de Windows)."""
    import ctypes
    from ctypes import wintypes

    class BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    crypt32, kernel32 = ctypes.windll.crypt32, ctypes.windll.kernel32
    buf = ctypes.create_string_buffer(datos, len(datos))
    entrada = BLOB(len(datos), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    salida = BLOB()
    entropia_txt = b"Geli-VD sesion"
    ebuf = ctypes.create_string_buffer(entropia_txt, len(entropia_txt))
    entropia = BLOB(len(entropia_txt), ctypes.cast(ebuf, ctypes.POINTER(ctypes.c_char)))
    CRYPTPROTECT_UI_FORBIDDEN = 0x01
    if cifrar:
        ok = crypt32.CryptProtectData(ctypes.byref(entrada), "Geli-VD", ctypes.byref(entropia),
                                      None, None, CRYPTPROTECT_UI_FORBIDDEN,
                                      ctypes.byref(salida))
    else:
        ok = crypt32.CryptUnprotectData(ctypes.byref(entrada), None, ctypes.byref(entropia),
                                        None, None, CRYPTPROTECT_UI_FORBIDDEN,
                                        ctypes.byref(salida))
    if not ok:
        raise OSError("DPAPI no pudo procesar la sesión")
    try:
        return ctypes.string_at(salida.pbData, salida.cbData)
    finally:
        kernel32.LocalFree(salida.pbData)


def guardar_sesion(texto):
    """Guarda las cookies de la sesión (texto Netscape) protegidas."""
    datos = texto.encode("utf-8")
    try:
        protegido = None
        if os.name == "nt":
            try:
                cifrado = _dpapi(datos, True)
                if _dpapi(cifrado, False) == datos:      # comprobar que se puede abrir
                    protegido = b"GVD1" + cifrado
            except Exception:
                pass
        # Si DPAPI no está disponible, queda como en Mac/Linux: archivo solo de tu usuario
        datos = protegido or (b"GVD0" + datos)
        os.makedirs(DIR_DATOS, exist_ok=True)
        tmp = ARCH_SESION + ".tmp"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(datos)
        os.replace(tmp, ARCH_SESION)
        if os.name != "nt":
            os.chmod(ARCH_SESION, 0o600)
        return True
    except Exception:
        return False


def leer_sesion():
    """Texto Netscape de la sesión guardada, o None si no hay o no se puede abrir."""
    try:
        with open(ARCH_SESION, "rb") as f:
            datos = f.read()
        if datos.startswith(b"GVD1"):
            return _dpapi(datos[4:], False).decode("utf-8")
        if datos.startswith(b"GVD0"):
            return datos[4:].decode("utf-8")
    except Exception:
        pass
    return None


def hay_sesion():
    return os.path.isfile(ARCH_SESION)


def borrar_sesion():
    borrar_archivo(ARCH_SESION)
    borrar_archivo(ARCH_SESION_VIEJA)


def migrar_sesion_vieja():
    """La 1.4 guardaba la sesión sin cifrar: pasarla al formato protegido."""
    if os.path.isfile(ARCH_SESION_VIEJA):
        try:
            with open(ARCH_SESION_VIEJA, encoding="utf-8") as f:
                texto = f.read()
            if guardar_sesion(texto):
                borrar_archivo(ARCH_SESION_VIEJA)
        except Exception:
            pass


def sesion_caducada():
    """True si la sesión lleva más de DIAS_CADUCIDAD_SESION días sin usarse."""
    try:
        return (datetime.now().timestamp() - os.path.getmtime(ARCH_SESION)
                > DIAS_CADUCIDAD_SESION * 86400)
    except OSError:
        return False


def texto_cookies_netscape(cookies):
    """Cookies de Playwright en el formato que entiende yt-dlp (como texto)."""
    lineas = ["# Netscape HTTP Cookie File"]
    for c in cookies:
        dom = c.get("domain", "")
        exp = int(c.get("expires") or 0)
        lineas.append("\t".join([dom, "TRUE" if dom.startswith(".") else "FALSE",
                                 c.get("path", "/"), "TRUE" if c.get("secure") else "FALSE",
                                 str(max(exp, 0)), c.get("name", ""), c.get("value", "")]))
    return "\n".join(lineas) + "\n"


def abrir_con_sistema(ruta):
    if sys.platform == "darwin":
        subprocess.Popen(["open", ruta])
    elif os.name == "nt":
        os.startfile(ruta)
    else:
        subprocess.Popen(["xdg-open", ruta])


def mostrar_en_carpeta(ruta):
    if os.path.isfile(ruta):
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-R", ruta])
            return
        if os.name == "nt":
            subprocess.Popen(["explorer", "/select,", ruta])
            return
        ruta = os.path.dirname(ruta)
    if os.path.isdir(ruta):
        abrir_con_sistema(ruta)


def notificar(titulo, texto):
    """Notificación del sistema (macOS). En otros sistemas no hace nada."""
    if sys.platform != "darwin":
        return

    def q(s):
        return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'

    try:
        subprocess.Popen(["osascript", "-e",
                          f"display notification {q(texto)} with title {q(titulo)}"])
    except Exception:
        pass


def dominio_base(host):
    partes = (host or "").lower().split(".")
    if len(partes) >= 3 and len(partes[-1]) == 2 and partes[-2] in (
            "com", "net", "org", "gob", "edu", "co", "ac", "gov"):
        return ".".join(partes[-3:])          # ejemplo.com.pe
    return ".".join(partes[-2:])


def cookies_para_sitio(navegador, url):
    """Cookies del navegador elegido, solo las del sitio de `url`, en formato Playwright."""
    base = dominio_base(urlparse(url).hostname)
    with yt_dlp.YoutubeDL({"cookiesfrombrowser": (navegador,), "quiet": True,
                           "no_warnings": True}) as ydl:
        jar = list(ydl.cookiejar)
    salida = []
    for c in jar:
        dom = (c.domain or "").lstrip(".").lower()
        if not base or not (dom == base or dom.endswith("." + base)):
            continue
        ck = {"name": c.name, "value": c.value or "", "domain": c.domain,
              "path": c.path or "/", "secure": bool(c.secure)}
        if c.expires:
            ck["expires"] = float(c.expires)
        salida.append(ck)
    return salida


def escribir_cookies_netscape(cookies, ruta):
    """Guarda las cookies de Playwright en el formato que entiende yt-dlp."""
    lineas = ["# Netscape HTTP Cookie File"]
    for c in cookies:
        dom = c.get("domain", "")
        exp = int(c.get("expires") or 0)
        lineas.append("\t".join([dom, "TRUE" if dom.startswith(".") else "FALSE",
                                 c.get("path", "/"), "TRUE" if c.get("secure") else "FALSE",
                                 str(max(exp, 0)), c.get("name", ""), c.get("value", "")]))
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas) + "\n")
    except OSError:
        pass


def duracion_archivo(ruta):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", ruta],
                           capture_output=True, text=True, timeout=30, **SIN_VENTANA)
        return float(r.stdout.strip())
    except Exception:
        return None


def ruta_final(info, ydl):
    """Ruta del archivo terminado (después de unir/convertir)."""
    for d in reversed(info.get("requested_downloads") or []):
        for clave in ("filepath", "_filename", "filename"):
            if d.get(clave) and os.path.exists(d[clave]):
                return d[clave]
    try:
        base = os.path.splitext(ydl.prepare_filename(info))[0]
        for ext in (".mp4", ".mp3", ".mkv", ".webm", ".m4a"):
            if os.path.exists(base + ext):
                return base + ext
    except Exception:
        pass
    return None


# ------------------------------------------------------------------------ app
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_CORTO}  ·  {APP_VERSION}")
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        try:
            self._icono = tk.PhotoImage(file=os.path.join(base, "icono.png"))
            self.iconphoto(True, self._icono)
        except Exception:
            pass
        self.geometry("1120x720")
        self.minsize(960, 640)

        self.cola = queue.Queue()
        self.trabajando = False
        self.descargando = False
        self.cancelar = threading.Event()
        self.url_analizada = None
        self.analisis = None
        self._id_auto = None
        self._img_ref = None
        self._datos_borrados = False

        # Estado de la descarga en curso (para limpiar si se cancela)
        self._vid_actual = None
        self._parciales = []
        self._tmp_actual = None
        self._arch_actual = None

        # Datos de la fuente detectada dentro de una página (modo detector)
        self.modo_detector = False
        self.pagina_detectada = None
        self.titulo_detectado = None

        self.cfg = leer_json(ARCH_CONFIG, None) or leer_json(ARCH_CONFIG_VIEJO, {})
        self.var_tema = tk.StringVar(value=self.cfg.get("tema", "sistema"))
        aplicar_paleta(self.var_tema.get())
        self.motor_nuevo = None
        self.var_guardar_hist = tk.BooleanVar(value=self.cfg.get("guardar_historial", True))
        self.var_notificar = tk.BooleanVar(value=self.cfg.get("notificar", True))
        self.var_detalles = tk.BooleanVar(value=self.cfg.get("ver_detalles", False))
        self.historial = leer_json(ARCH_HISTORIAL, []) if self.var_guardar_hist.get() else []

        self._estilos()
        self._construir_menu()
        self._construir_ui()
        self._vista_placeholder()
        self._refrescar_historial()
        self._actualizar_cabecera()
        self.after(100, self._procesar_cola)
        self._verificar_dependencias()
        self.after(1500, self._revisar_motor_en_segundo_plano)
        self.after(800, self._revisar_sesion)
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

    # ---------------------------------------------------------------- estilo
    def _estilos(self):
        self.configure(bg=C["fondo"])
        st = ttk.Style(self)
        st.theme_use("clam")
        st.configure(".", background=C["fondo"], foreground=C["texto"],
                     fieldbackground=C["campo"], bordercolor=C["borde"],
                     lightcolor=C["borde"], darkcolor=C["borde"], font=(FUENTE, 13))
        st.configure("TFrame", background=C["fondo"])
        st.configure("Panel.TFrame", background=C["panel"])
        st.configure("TLabel", background=C["fondo"], foreground=C["texto"])
        st.configure("Tenue.TLabel", foreground=C["tenue"], font=(FUENTE, 12))
        st.configure("Privado.TLabel", foreground=C["aviso"], font=(FUENTE, 12, "bold"))
        st.configure("Campo.TLabel", foreground=C["tenue"], font=(FUENTE, 12, "bold"))
        st.configure("Pista.TLabel", foreground=C["pista"], font=(FUENTE, 11))
        st.configure("Titulo.TLabel", font=(FUENTE, 22, "bold"))
        st.configure("Version.TLabel", foreground=C["rosa"], font=(FUENTE, 12, "bold"))
        st.configure("Estado.TLabel", foreground=C["tenue"], font=(FUENTE, 12))
        st.configure("EstadoOk.TLabel", foreground=C["ok"], font=(FUENTE, 12, "bold"))
        st.configure("EstadoError.TLabel", foreground=C["error"], font=(FUENTE, 12, "bold"))
        st.configure("Panel.TLabel", background=C["panel"])
        st.configure("PanelTenue.TLabel", background=C["panel"], foreground=C["tenue"],
                     font=(FUENTE, 12))
        st.configure("PanelSeccion.TLabel", background=C["panel"], foreground=C["rosa"],
                     font=(FUENTE, 11, "bold"))
        st.configure("VideoTitulo.TLabel", background=C["panel"], foreground=C["texto"],
                     font=(FUENTE, 15, "bold"))

        st.configure("TEntry", fieldbackground=C["campo"], foreground=C["texto"],
                     insertcolor=C["texto"], padding=7)
        st.map("TEntry", bordercolor=[("focus", C["acento"])],
               lightcolor=[("focus", C["acento"])])

        st.configure("TCombobox", fieldbackground=C["campo"], background=C["campo"],
                     foreground=C["texto"], arrowcolor=C["texto"], padding=6)
        st.map("TCombobox",
               fieldbackground=[("readonly", C["campo"])],
               foreground=[("readonly", C["texto"])],
               selectbackground=[("readonly", C["campo"])],
               selectforeground=[("readonly", C["texto"])],
               bordercolor=[("focus", C["acento"])])
        self.option_add("*TCombobox*Listbox.background", C["campo"])
        self.option_add("*TCombobox*Listbox.foreground", C["texto"])
        self.option_add("*TCombobox*Listbox.selectBackground", C["acento"])
        self.option_add("*TCombobox*Listbox.selectForeground", "white")

        st.configure("TCheckbutton", background=C["fondo"], foreground=C["texto"],
                     font=(FUENTE, 12))
        st.map("TCheckbutton", background=[("active", C["fondo"])],
               indicatorcolor=[("selected", C["rosa"]), ("!selected", C["campo"])])

        def boton(nombre, fondo, hover, padding, fuente):
            st.configure(nombre, background=fondo, foreground="white", borderwidth=0,
                         focusthickness=0, padding=padding, font=fuente)
            st.map(nombre,
                   background=[("disabled", C["borde"]), ("active", hover)],
                   foreground=[("disabled", C["tenue"])])

        boton("Accion.TButton", C["acento"], C["acento_hover"], (22, 10), (FUENTE, 14, "bold"))
        boton("Rosa.TButton", C["rosa"], C["rosa_hover"], (16, 7), (FUENTE, 13, "bold"))
        st.configure("Sec.TButton", background=C["campo"], foreground=C["texto"],
                     borderwidth=0, focusthickness=0, padding=(12, 7))
        st.map("Sec.TButton", background=[("disabled", C["panel"]), ("active", C["borde"])],
               foreground=[("disabled", C["tenue"])])
        st.configure("Cancelar.TButton", background=C["campo"], foreground=C["error"],
                     borderwidth=0, focusthickness=0, padding=(14, 10),
                     font=(FUENTE, 13, "bold"))
        st.map("Cancelar.TButton", background=[("disabled", C["fondo"]),
                                               ("active", C["borde"])],
               foreground=[("disabled", C["fondo"])])
        st.configure("Link.TButton", background=C["fondo"], foreground=C["tenue"],
                     borderwidth=0, focusthickness=0, padding=(4, 2), font=(FUENTE, 12))
        st.map("Link.TButton", background=[("active", C["fondo"])],
               foreground=[("active", C["texto"])])

        st.configure("Motor.TButton", background=C["fondo"], foreground=C["tenue"],
                     borderwidth=0, focusthickness=0, padding=(8, 3), font=(FUENTE, 12))
        st.map("Motor.TButton", background=[("active", C["campo"])],
               foreground=[("active", C["texto"]), ("disabled", C["pista"])])
        st.configure("MotorNuevo.TButton", background=C["acento"], foreground="white",
                     borderwidth=0, focusthickness=0, padding=(8, 3),
                     font=(FUENTE, 12, "bold"))
        st.map("MotorNuevo.TButton", background=[("active", C["acento_hover"]),
                                                 ("disabled", C["borde"])])

        st.configure("Geli.Horizontal.TProgressbar", troughcolor=C["campo"],
                     background=C["rosa"], bordercolor=C["campo"],
                     lightcolor=C["rosa"], darkcolor=C["rosa"], thickness=10)

        st.configure("Panel.TRadiobutton", background=C["panel"], foreground=C["texto"],
                     font=(FUENTE, 12))
        st.map("Panel.TRadiobutton", background=[("active", C["panel"])],
               indicatorcolor=[("selected", C["rosa"]), ("!selected", C["campo"])])

    # ------------------------------------------------------------------ menú
    def _construir_menu(self):
        barra = tk.Menu(self)

        m = tk.Menu(barra, tearoff=0)
        m.add_command(label="Pegar enlace", command=self._pegar)
        m.add_command(label="Abrir carpeta de descargas", command=self._abrir_carpeta)
        m.add_separator()
        m.add_command(label="Salir", command=self._al_cerrar)
        barra.add_cascade(label="Archivo", menu=m)

        m = tk.Menu(barra, tearoff=0)
        m.add_checkbutton(label="Guardar historial", variable=self.var_guardar_hist,
                          command=self._cambio_guardar_historial)
        m.add_command(label="Borrar historial…", command=self._borrar_historial)
        m.add_separator()
        m.add_command(label="Borrar todos los datos de la app…",
                      command=self._borrar_todos_los_datos)
        barra.add_cascade(label="Historial", menu=m)

        m = tk.Menu(barra, tearoff=0)
        m.add_command(label="Convertir video a MP3…", command=self._convertir_local)
        m.add_command(label="Actualizar motor de descargas (yt-dlp)",
                      command=self._actualizar_motor)
        m.add_command(label="Iniciar sesión (YouTube, Instagram…)…",
                      command=lambda: self._iniciar_sesion(
                          self._url_login(self.var_url.get().strip())))
        m.add_command(label="Cerrar sesiones de Geli-VD…",
                      command=self._cerrar_sesiones_detector)
        m.add_separator()
        m.add_checkbutton(label="Notificar al terminar", variable=self.var_notificar)
        m.add_checkbutton(label="Ver detalles técnicos", variable=self.var_detalles,
                          command=lambda: self._alternar_detalles(self.var_detalles.get()))
        sub = tk.Menu(m, tearoff=0)
        for etiqueta, valor in TEMAS.items():
            sub.add_radiobutton(label=etiqueta, value=valor, variable=self.var_tema,
                                command=self._cambio_tema)
        m.add_cascade(label="Apariencia", menu=sub)
        barra.add_cascade(label="Herramientas", menu=m)

        m = tk.Menu(barra, tearoff=0)
        m.add_command(label="Privacidad y datos", command=lambda: messagebox.showinfo(
            "Privacidad y datos", TEXTO_PRIVACIDAD))
        m.add_command(label=f"Acerca de {APP_CORTO}", command=self._acerca_de)
        barra.add_cascade(label="Ayuda", menu=m)

        self.configure(menu=barra)

    # ------------------------------------------------------------------- UI
    def _construir_ui(self):
        cab = ttk.Frame(self)
        cab.pack(fill="x", padx=22, pady=(16, 8))
        ttk.Label(cab, text="🎬 " + APP_CORTO, style="Titulo.TLabel").pack(side="left")
        ttk.Label(cab, text=APP_VERSION, style="Version.TLabel").pack(
            side="left", padx=(10, 0), pady=(8, 0))
        self.btn_motor = ttk.Button(cab, text="⟳ Actualizar motor", style="Motor.TButton",
                                    command=self._actualizar_motor)
        self.btn_motor.pack(side="left", padx=(16, 0), pady=(8, 0))
        self.lbl_cabecera = ttk.Label(cab, style="Tenue.TLabel")
        self.lbl_cabecera.pack(side="right", pady=(8, 0))

        self.franja = tk.Canvas(self, height=4, highlightthickness=0, bd=0, bg=C["fondo"])
        self.franja.pack(fill="x", padx=22)
        self.franja.bind("<Configure>", self._pintar_franja)

        cuerpo = ttk.Frame(self)
        cuerpo.pack(fill="both", expand=True, padx=22, pady=16)
        # "uniform" mantiene la proporción 3:2 sin importar el contenido
        cuerpo.columnconfigure(0, weight=3, uniform="col")
        cuerpo.columnconfigure(1, weight=2, uniform="col", minsize=MINI_W + 40)
        cuerpo.rowconfigure(0, weight=1)

        self._columna_izquierda(cuerpo)
        self._columna_derecha(cuerpo)

    def _columna_izquierda(self, padre):
        izq = ttk.Frame(padre)
        izq.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        izq.columnconfigure(0, weight=1)
        self.izq = izq

        # Enlace
        ttk.Label(izq, text="ENLACE DEL VIDEO", style="Campo.TLabel").grid(
            row=0, column=0, sticky="w")
        fila = ttk.Frame(izq)
        fila.grid(row=1, column=0, sticky="ew", pady=(4, 14))
        fila.columnconfigure(0, weight=1)
        self.var_url = tk.StringVar()
        ent = ttk.Entry(fila, textvariable=self.var_url, font=(FUENTE, 13))
        ent.grid(row=0, column=0, sticky="ew")
        ent.bind("<Return>", self._iniciar_analisis)
        ent.focus_set()
        ttk.Button(fila, text="📋", style="Sec.TButton", width=3,
                   command=self._pegar).grid(row=0, column=1, padx=(8, 0))
        self.btn_analizar = ttk.Button(fila, text="🔍 Analizar", style="Rosa.TButton",
                                       command=self._iniciar_analisis)
        self.btn_analizar.grid(row=0, column=2, padx=(8, 0))
        self.var_url.trace_add("write", self._url_cambio)

        # Carpeta
        ttk.Label(izq, text="CARPETA DE DESTINO", style="Campo.TLabel").grid(
            row=2, column=0, sticky="w")
        fila = ttk.Frame(izq)
        fila.grid(row=3, column=0, sticky="ew", pady=(4, 14))
        fila.columnconfigure(0, weight=1)
        self.var_dir = tk.StringVar(value=self.cfg.get(
            "carpeta", os.path.join(os.path.expanduser("~"), "Downloads")))
        ttk.Entry(fila, textvariable=self.var_dir).grid(row=0, column=0, sticky="ew")
        ttk.Button(fila, text="Elegir…", style="Sec.TButton",
                   command=self._elegir_carpeta).grid(row=0, column=1, padx=(8, 0))

        # Formato, calidad, cookies y opciones
        fila = ttk.Frame(izq)
        fila.grid(row=4, column=0, sticky="ew", pady=(0, 16))
        formato, calidad = self._formato_guardado()
        self.var_formato = tk.StringVar(value=formato)
        self.var_cal = tk.StringVar(value=calidad)
        nav = self.cfg.get("cookies", "(ninguno)")
        if nav == OPC_ARCHIVO and not os.path.isfile(self.cfg.get("archivo_cookies") or ""):
            nav = "(ninguno)"
        self.var_nav = tk.StringVar(value=nav if nav in NAVEGADORES else "(ninguno)")
        self._nav_anterior = self.var_nav.get()

        for c, texto in enumerate(("FORMATO", "CALIDAD", "COOKIES DE")):
            ttk.Label(fila, text=texto, style="Campo.TLabel").grid(
                row=0, column=c, sticky="w", padx=(0, 14))
        cmb = ttk.Combobox(fila, textvariable=self.var_formato, values=FORMATOS,
                           state="readonly", width=13)
        cmb.grid(row=1, column=0, sticky="w", padx=(0, 14), pady=(4, 0))
        cmb.bind("<<ComboboxSelected>>", lambda e: self._cambio_formato())
        self.cmb_cal = ttk.Combobox(fila, textvariable=self.var_cal, state="readonly",
                                    width=13, values=list(CALIDADES[formato]))
        self.cmb_cal.grid(row=1, column=1, sticky="w", padx=(0, 14), pady=(4, 0))
        cmb_nav = ttk.Combobox(fila, textvariable=self.var_nav, values=NAVEGADORES,
                               state="readonly", width=17)
        cmb_nav.grid(row=1, column=2, sticky="w", pady=(4, 0))
        cmb_nav.bind("<<ComboboxSelected>>", lambda e: self._cambio_cookies())

        opc = ttk.Frame(fila)
        opc.grid(row=2, column=0, columnspan=3, sticky="w", pady=(10, 0))
        self.var_subs = tk.BooleanVar(value=self.cfg.get("subtitulos", False))
        self.chk_subs = ttk.Checkbutton(opc, text="Subtítulos (es/en)",
                                        variable=self.var_subs)
        self.chk_subs.pack(side="left", padx=(0, 18))
        self.var_lista = tk.BooleanVar(value=False)
        ttk.Checkbutton(opc, text="Lista / carrusel completo", variable=self.var_lista,
                        command=self._cambio_lista).pack(side="left")
        self._cambio_formato(inicial=True)

        # Botones principales
        fila = ttk.Frame(izq)
        fila.grid(row=5, column=0, sticky="ew", pady=(0, 14))
        self.btn_desc = ttk.Button(fila, text="⬇  Descargar", style="Accion.TButton",
                                   command=self._iniciar_descarga)
        self.btn_desc.pack(side="left")
        self.btn_cancelar = ttk.Button(fila, text="■ Cancelar", style="Cancelar.TButton",
                                       command=self._cancelar_descarga, state="disabled")
        self.btn_cancelar.pack(side="left", padx=(10, 0))
        ttk.Button(fila, text="📂 Abrir carpeta", style="Sec.TButton",
                   command=self._abrir_carpeta).pack(side="right")
        self.btn_convertir = ttk.Button(fila, text="🎵 Video → MP3 ", style="Sec.TButton",
                                        command=self._convertir_local)
        self.btn_convertir.pack(side="right", padx=(0, 8))

        # Progreso
        self.barra = ttk.Progressbar(izq, mode="determinate", maximum=100,
                                     style="Geli.Horizontal.TProgressbar")
        self.barra.grid(row=6, column=0, sticky="ew")
        self.var_estado = tk.StringVar(value="Listo.")
        self.lbl_estado = ttk.Label(izq, textvariable=self.var_estado, style="Estado.TLabel")
        self.lbl_estado.grid(row=7, column=0, sticky="w", pady=(6, 12))

        # Historial
        fila = ttk.Frame(izq)
        fila.grid(row=8, column=0, sticky="ew")
        ttk.Label(fila, text="HISTORIAL", style="Campo.TLabel").pack(side="left")
        ttk.Label(fila, text="doble clic: abrir  ·  clic derecho: más opciones",
                  style="Pista.TLabel").pack(side="right")
        self.lst_hist = tk.Listbox(
            izq, height=5, bg=C["log"], fg=C["texto"], relief="flat", activestyle="none",
            highlightthickness=1, highlightbackground=C["borde"], highlightcolor=C["borde"],
            selectbackground=C["campo"], selectforeground=C["texto"], font=(FUENTE, 12),
            borderwidth=0)
        self.lst_hist.grid(row=9, column=0, sticky="nsew", pady=(4, 6))
        self.lst_hist.bind("<Double-Button-1>", lambda e: self._hist_abrir())
        for evento in ("<Button-2>", "<Button-3>", "<Control-Button-1>"):
            self.lst_hist.bind(evento, self._hist_menu)

        self.menu_hist = tk.Menu(self, tearoff=0)
        self.menu_hist.add_command(label="▶ Abrir video", command=self._hist_abrir)
        self.menu_hist.add_command(label="📂 Mostrar en la carpeta", command=self._hist_mostrar)
        self.menu_hist.add_command(label="🔗 Copiar enlace", command=self._hist_copiar)
        self.menu_hist.add_command(label="↻ Usar este enlace otra vez", command=self._hist_reusar)
        self.menu_hist.add_separator()
        self.menu_hist.add_command(label="✖ Quitar del historial", command=self._hist_quitar)

        # Barra inferior: detalles, limpiar log, borrar historial
        fila = ttk.Frame(izq)
        fila.grid(row=10, column=0, sticky="ew")
        self.btn_detalles = ttk.Button(fila, text="▸ Ver detalles", style="Link.TButton",
                                       command=lambda: self._alternar_detalles())
        self.btn_detalles.pack(side="left")
        ttk.Button(fila, text="🗑 Borrar historial", style="Link.TButton",
                   command=self._borrar_historial).pack(side="right")
        ttk.Button(fila, text="🧹 Limpiar log", style="Link.TButton",
                   command=self._limpiar_log).pack(side="right", padx=(0, 10))

        self.log = tk.Text(izq, height=7, wrap="word", state="disabled", bg=C["log"],
                           fg=C["texto"], insertbackground=C["texto"], relief="flat",
                           highlightthickness=1, highlightbackground=C["borde"],
                           highlightcolor=C["borde"], font=("Menlo", 11), padx=10, pady=8)
        self.log.grid(row=11, column=0, sticky="nsew", pady=(4, 0))
        for tag in ("ok", "error", "aviso"):
            self.log.tag_configure(tag, foreground=C[tag])
        self.log.tag_configure("tenue", foreground=C["tenue"])

        self._alternar_detalles(self.var_detalles.get())

    def _columna_derecha(self, padre):
        der = tk.Frame(padre, bg=C["panel"], highlightthickness=1,
                       highlightbackground=C["borde"])
        der.grid(row=0, column=1, sticky="nsew")
        cont = ttk.Frame(der, style="Panel.TFrame")
        cont.pack(fill="both", expand=True, padx=18, pady=16)

        ttk.Label(cont, text="VISTA PREVIA", style="PanelSeccion.TLabel").pack(anchor="w")

        marco = tk.Frame(cont, width=MINI_W, height=MINI_H, bg=C["campo"])
        marco.pack(anchor="w", pady=(8, 12))
        marco.pack_propagate(False)
        self.lbl_mini = tk.Label(marco, bg=C["campo"], fg=C["tenue"], font=(FUENTE, 12),
                                 wraplength=MINI_W - 40, justify="center")
        self.lbl_mini.pack(fill="both", expand=True)

        self.var_titulo = tk.StringVar()
        ttk.Label(cont, textvariable=self.var_titulo, style="VideoTitulo.TLabel",
                  wraplength=MINI_W, justify="left").pack(anchor="w")
        self.var_info = tk.StringVar()
        ttk.Label(cont, textvariable=self.var_info, style="PanelTenue.TLabel",
                  wraplength=MINI_W, justify="left").pack(anchor="w", pady=(6, 0))
        self.var_calidades = tk.StringVar()
        ttk.Label(cont, textvariable=self.var_calidades, style="PanelTenue.TLabel",
                  wraplength=MINI_W, justify="left").pack(anchor="w", pady=(4, 0))

        # Lista de fuentes (solo en modo detector)
        self.frm_fuentes = ttk.Frame(cont, style="Panel.TFrame")
        self.var_fuente = tk.StringVar()

        self.btn_navegador = ttk.Button(cont, text="🌐 Abrir navegador para darle play…",
                                        style="Sec.TButton",
                                        command=self._iniciar_detector_visible)

    def _pintar_franja(self, evento):
        self.franja.delete("all")
        a = [int(C["acento"][i:i + 2], 16) for i in (1, 3, 5)]
        b = [int(C["rosa"][i:i + 2], 16) for i in (1, 3, 5)]
        ancho = max(evento.width, 1)
        for x in range(0, ancho, 2):
            t = x / ancho
            color = "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
            self.franja.create_line(x, 0, x, 4, fill=color, width=2)

    def _actualizar_cabecera(self):
        if self.var_guardar_hist.get():
            self.lbl_cabecera.configure(
                text="YouTube · Dailymotion · TikTok · Instagram · Facebook",
                style="Tenue.TLabel")
        else:
            self.lbl_cabecera.configure(text="🕶 Modo privado: el historial no se guarda",
                                        style="Privado.TLabel")

    # ------------------------------------------------------------ utilidades UI
    def _formato_guardado(self):
        formato = self.cfg.get("formato")
        calidad = self.cfg.get("calidad", "")
        if formato not in CALIDADES:                    # preferencias de versiones viejas
            if "audio" in calidad.lower():
                formato, calidad = "Audio (MP3)", "192 kbps"
            else:
                formato, calidad = "Video (MP4)", calidad.replace(" máx.", "")
        if calidad not in CALIDADES[formato]:
            calidad = next(iter(CALIDADES[formato]))
        return formato, calidad

    def _cambio_formato(self, inicial=False):
        formato = self.var_formato.get()
        opciones = list(CALIDADES[formato])
        self.cmb_cal.configure(values=opciones,
                               state="readonly" if len(opciones) > 1 else "disabled")
        if self.var_cal.get() not in opciones:
            self.var_cal.set(opciones[1] if formato == "Audio (MP3)" else opciones[0])
        # Los subtítulos solo tienen sentido en video
        self.chk_subs.configure(state="normal" if formato.startswith("Video") else "disabled")

    def _pegar(self):
        try:
            texto = self.clipboard_get().strip()
        except tk.TclError:
            return
        if texto:
            self.var_url.set(texto)

    def _elegir_carpeta(self):
        d = filedialog.askdirectory(initialdir=self.var_dir.get())
        if d:
            self.var_dir.set(d)

    def _abrir_carpeta(self):
        d = self.var_dir.get()
        if os.path.isdir(d):
            abrir_con_sistema(d)

    def _alternar_detalles(self, mostrar=None):
        if mostrar is None:
            mostrar = not self.var_detalles.get()
        self.var_detalles.set(mostrar)
        if mostrar:
            self.log.grid()
            self.izq.rowconfigure(9, weight=0)
            self.izq.rowconfigure(11, weight=1)
            self.btn_detalles.configure(text="▾ Ocultar detalles")
            self.log.see("end")
            self._ajustar_alto()
        else:
            self.log.grid_remove()
            self.izq.rowconfigure(11, weight=0)
            self.izq.rowconfigure(9, weight=1)
            self.btn_detalles.configure(text="▸ Ver detalles")

    def _ajustar_alto(self):
        """Agranda la ventana si el contenido ya no entra (p. ej. al abrir el log)."""
        self.update_idletasks()
        necesario = self.winfo_reqheight()
        if self.winfo_height() < necesario:
            self.geometry(f"{self.winfo_width()}x{necesario}")

    def _limpiar_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        if not self.trabajando:
            self.barra.configure(value=0)
            self._poner_estado("Listo.")

    def _poner_estado(self, texto, tipo=None):
        self.var_estado.set(texto)
        estilo = {"ok": "EstadoOk.TLabel", "error": "EstadoError.TLabel"}.get(
            tipo, "Estado.TLabel")
        self.lbl_estado.configure(style=estilo)

    def _escribir_log(self, texto, tag=None):
        self.log.configure(state="normal")
        self.log.insert("end", texto + "\n", tag or ())
        self.log.see("end")
        self.log.configure(state="disabled")

    def _bloquear(self, ocupado, descargando=False):
        self.trabajando = ocupado
        self.descargando = ocupado and descargando
        estado = "disabled" if ocupado else "normal"
        for b in (self.btn_desc, self.btn_analizar, self.btn_navegador, self.btn_convertir,
                  self.btn_motor):
            b.configure(state=estado)
        self.btn_cancelar.configure(state="normal" if self.descargando else "disabled")

    def _verificar_dependencias(self):
        if yt_dlp is None:
            self._escribir_log('⚠ Falta yt-dlp:  pip install "yt-dlp[default,curl-cffi]"', "aviso")
        if not shutil.which("ffmpeg"):
            self._escribir_log("⚠ No se encontró ffmpeg: sin él no se unen audio y video "
                               "en alta calidad ni se convierte a MP3.", "aviso")
        if not shutil.which("deno"):
            self._escribir_log("⚠ No se encontró deno (YouTube lo necesita). "
                               "Ver LEEME para instalarlo.", "aviso")
        if Image is None:
            self._escribir_log("⚠ Falta Pillow para mostrar miniaturas:  pip install pillow",
                               "aviso")

    def _guardar_preferencias(self):
        self._datos_borrados = False
        self.cfg.update(carpeta=self.var_dir.get(), calidad=self.var_cal.get(),
                        formato=self.var_formato.get(),
                        cookies=self.var_nav.get(),
                        archivo_cookies=self.cfg.get("archivo_cookies"),
                        subtitulos=self.var_subs.get(),
                        notificar=self.var_notificar.get(),
                        ver_detalles=self.var_detalles.get(),
                        guardar_historial=self.var_guardar_hist.get(),
                        tema=self.var_tema.get())
        escribir_json(ARCH_CONFIG, self.cfg)
        borrar_archivo(ARCH_CONFIG_VIEJO)

    def _al_cerrar(self):
        if self.descargando and not messagebox.askyesno(
                "Descarga en curso", "Hay una descarga en curso. ¿Cerrar de todas formas?"):
            return
        self.cancelar.set()
        if not self._datos_borrados:     # si acaba de borrar todo, no volver a crear datos
            self._guardar_preferencias()
        self.destroy()

    def _acerca_de(self):
        motor = getattr(getattr(yt_dlp, "version", None), "__version__", "no instalado") \
            if yt_dlp else "no instalado"
        messagebox.showinfo(
            f"Acerca de {APP_CORTO}",
            f"{APP_CORTO}  {APP_VERSION}\n"
            f"({APP_NOMBRE})\n"
            f"Parte del ecosistema Geli · GeliOS\n\n"
            f"Motor de descargas: yt-dlp {motor}"
            f"{' (actualizado)' if MOTOR_ACTUALIZADO else ''}\n"
            f"Python {sys.version.split()[0]}\n\n"
            f"Uso responsable: descarga solo contenido propio, de libre uso o "
            f"con permiso de su autor, respetando las condiciones de cada sitio.\n\n"
            f"Componentes de terceros: yt-dlp (Unlicense), FFmpeg (LGPL/GPL), "
            f"Pillow (MIT-CMU).\n\n"
            f"Datos de la app:\n{DIR_DATOS}")

    def _cambio_tema(self):
        self._guardar_preferencias()
        if messagebox.askyesno("Apariencia", "El nuevo tema se aplica al reabrir la app.\n"
                                             "¿Reabrir ahora?"):
            self._reiniciar()

    def _reiniciar(self):
        if self.descargando:
            messagebox.showinfo("Espera", "Hay una descarga en curso.")
            return
        self._guardar_preferencias()
        if getattr(sys, "frozen", False):
            args = [sys.executable] + sys.argv[1:]
        else:
            args = [sys.executable] + sys.argv
        try:
            self.destroy()
        finally:
            os.execv(args[0], args)

    # ---------------------------------------------------------------- historial
    def _refrescar_historial(self):
        self.lst_hist.delete(0, "end")
        if not self.historial:
            texto = ("  Aún no hay descargas." if self.var_guardar_hist.get()
                     else "  Modo privado: el historial solo dura esta sesión.")
            self.lst_hist.insert("end", texto)
            self.lst_hist.itemconfig(0, fg=C["tenue"])
            return
        for r in self.historial:
            try:
                fecha = datetime.fromisoformat(r.get("fecha", "")).strftime("%d/%m %H:%M")
            except ValueError:
                fecha = ""
            marca = "  ✔  " if r.get("ok") else "  ✖  "
            self.lst_hist.insert("end", f"{marca}{r.get('titulo', '')}     {fecha}")
            self.lst_hist.itemconfig("end", fg=C["ok"] if r.get("ok") else C["error"])

    def _agregar_historial(self, registro):
        self.historial.insert(0, registro)
        del self.historial[MAX_HISTORIAL:]
        if self.var_guardar_hist.get():
            escribir_json(ARCH_HISTORIAL, self.historial)
        self._refrescar_historial()

    def _guardar_historial(self):
        if self.var_guardar_hist.get():
            escribir_json(ARCH_HISTORIAL, self.historial)

    def _hist_sel(self):
        sel = self.lst_hist.curselection()
        if not sel or not self.historial or sel[0] >= len(self.historial):
            return None, None
        return sel[0], self.historial[sel[0]]

    def _hist_menu(self, evento):
        if not self.historial:
            return
        i = self.lst_hist.nearest(evento.y)
        self.lst_hist.selection_clear(0, "end")
        self.lst_hist.selection_set(i)
        _, r = self._hist_sel()
        if not r:
            return
        existe = bool(r.get("archivo")) and os.path.exists(r["archivo"])
        self.menu_hist.entryconfigure(0, state="normal" if existe and
                                      os.path.isfile(r["archivo"]) else "disabled")
        self.menu_hist.entryconfigure(1, state="normal" if existe else "disabled")
        try:
            self.menu_hist.tk_popup(evento.x_root, evento.y_root)
        finally:
            self.menu_hist.grab_release()

    def _hist_abrir(self):
        _, r = self._hist_sel()
        if not r:
            return
        ruta = r.get("archivo")
        if ruta and os.path.exists(ruta):
            abrir_con_sistema(ruta)
        else:
            messagebox.showinfo("Archivo no encontrado",
                                "El archivo ya no está en su carpeta (quizás lo moviste "
                                "o lo borraste).\n\nPuedes usar «Usar este enlace otra "
                                "vez» para descargarlo de nuevo.")

    def _hist_mostrar(self):
        _, r = self._hist_sel()
        if r and r.get("archivo"):
            mostrar_en_carpeta(r["archivo"])

    def _hist_copiar(self):
        _, r = self._hist_sel()
        if r and r.get("url"):
            self.clipboard_clear()
            self.clipboard_append(r["url"])
            self._poner_estado("🔗 Enlace copiado.", "ok")

    def _hist_reusar(self):
        _, r = self._hist_sel()
        if r and r.get("url"):
            self.var_url.set(r["url"])

    def _hist_quitar(self):
        i, r = self._hist_sel()
        if r is None:
            return
        del self.historial[i]
        self._guardar_historial()
        self._refrescar_historial()

    def _borrar_historial(self):
        if not self.historial and not os.path.exists(ARCH_HISTORIAL):
            return
        if not messagebox.askyesno("Borrar historial",
                                   "¿Borrar todo el historial de descargas?\n\n"
                                   "Los videos descargados NO se borran, solo la lista."):
            return
        self.historial = []
        borrar_archivo(ARCH_HISTORIAL)
        self._refrescar_historial()
        self._poner_estado("🗑 Historial borrado.", "ok")

    def _cambio_guardar_historial(self):
        if self.var_guardar_hist.get():
            escribir_json(ARCH_HISTORIAL, self.historial)
        elif os.path.exists(ARCH_HISTORIAL) and messagebox.askyesno(
                "Modo privado",
                "El historial ya no se guardará.\n\n"
                "¿Quieres borrar también el historial que ya estaba guardado?"):
            borrar_archivo(ARCH_HISTORIAL)
            self.historial = []
        self._guardar_preferencias()
        self._actualizar_cabecera()
        self._refrescar_historial()

    def _borrar_todos_los_datos(self):
        if not messagebox.askyesno(
                "Borrar todos los datos",
                "Se borrarán el historial, las preferencias de la app "
                "(carpeta, calidad, cookies, opciones) y las sesiones del detector.\n\n"
                "Los videos descargados NO se borran.\n\n¿Continuar?"):
            return
        self.historial = []
        for ruta in (ARCH_HISTORIAL, ARCH_CONFIG, ARCH_CONFIG_VIEJO, ARCH_COOKIES_DET):
            borrar_archivo(ruta)
        borrar_sesion()
        shutil.rmtree(DIR_PERFIL, ignore_errors=True)
        try:
            os.rmdir(DIR_DATOS)
        except OSError:
            pass
        self.cfg = {}
        self.var_dir.set(os.path.join(os.path.expanduser("~"), "Downloads"))
        self.var_formato.set("Video (MP4)")
        self.var_cal.set("Mejor calidad")
        self._cambio_formato()
        self.var_nav.set("(ninguno)")
        self.var_subs.set(False)
        self.var_notificar.set(True)
        self.var_guardar_hist.set(True)
        self._actualizar_cabecera()
        self._refrescar_historial()
        self._limpiar_log()
        self._datos_borrados = True
        messagebox.showinfo("Listo", "Se borraron todos los datos de la app.")

    # -------------------------------------------------------------- vista previa
    def _vista_placeholder(self, texto="Pega un enlace y aparecerá aquí la portada del video"):
        self._img_ref = None
        self.lbl_mini.configure(image="", text=texto)
        self.var_titulo.set("")
        self.var_info.set("")
        self.var_calidades.set("")
        self._ocultar_fuentes()
        self.btn_navegador.pack_forget()

    def _ocultar_fuentes(self):
        for w in self.frm_fuentes.winfo_children():
            w.destroy()
        self.frm_fuentes.pack_forget()
        self.modo_detector = False
        self.var_fuente.set("")

    def _poner_miniatura(self, datos_img):
        if not datos_img or Image is None:
            self.lbl_mini.configure(image="", text="(sin miniatura)")
            return
        try:
            img = Image.open(io.BytesIO(datos_img)).convert("RGB")
            img = ImageOps.fit(img, (MINI_W, MINI_H))
            self._img_ref = ImageTk.PhotoImage(img)
            self.lbl_mini.configure(image=self._img_ref, text="")
        except Exception:
            self.lbl_mini.configure(image="", text="(no se pudo mostrar la miniatura)")

    def _mostrar_vista(self, d):
        self._poner_miniatura(d.get("miniatura"))
        self.var_titulo.set(d.get("titulo") or "Sin título")
        if d.get("es_lista"):
            partes = [f"📃 Lista de {d.get('n') or '?'} videos", d.get("canal"), d.get("sitio")]
            self.var_info.set("  ·  ".join(p for p in partes if p))
            if self.var_lista.get():
                self.var_calidades.set("Se descargarán todos los videos en una carpeta "
                                       "con el nombre de la lista.")
            else:
                self.var_calidades.set("Marca «Lista / carrusel completo» para bajar todos. "
                                       "Si no, se baja solo el primero.")
            return
        partes = [d.get("canal"), formatear_duracion(d.get("duracion")), d.get("sitio")]
        self.var_info.set("  ·  ".join(p for p in partes if p))
        alturas = d.get("alturas") or []
        if alturas:
            self.var_calidades.set("Calidades: " + "  ·  ".join(f"{h}p" for h in alturas[:6]))

    def _mostrar_detectados(self, d):
        self._mostrar_vista({"titulo": d.get("titulo"), "miniatura": d.get("miniatura"),
                             "sitio": urlparse(d["pagina"]).netloc})
        if d.get("login"):
            self.var_calidades.set("⚠ La página pidió INICIAR SESIÓN: estas fuentes "
                                   "probablemente no son tu video. Usa el botón de abajo, "
                                   "inicia sesión en esa ventana y vuelve a intentar.")
        else:
            self.var_calidades.set("Video encontrado dentro de la página. Elige la fuente:")
        self.modo_detector = True
        self.pagina_detectada = d["pagina"]
        self.titulo_detectado = d.get("titulo")
        self.frm_fuentes.pack(anchor="w", fill="x", pady=(8, 0))
        for u in d["urls"][:6]:
            ttk.Radiobutton(self.frm_fuentes, text=etiqueta_fuente(u), value=u,
                            variable=self.var_fuente, style="Panel.TRadiobutton"
                            ).pack(anchor="w", pady=2)
        self.var_fuente.set(d["urls"][0])
        self.btn_navegador.pack(anchor="w", pady=(12, 0))

    def _url_cambio(self, *_):
        url = self.var_url.get().strip()
        if url == self.url_analizada:
            return
        self.url_analizada = None
        self.analisis = None
        self._vista_placeholder()
        self._programar_analisis()

    def _cambio_lista(self):
        # La opción cambia si el enlace se trata como lista o como un solo video
        if self.var_url.get().strip():
            self.url_analizada = None
            self.analisis = None
            self._programar_analisis(200)

    def _programar_analisis(self, espera=900):
        if self._id_auto:
            self.after_cancel(self._id_auto)
            self._id_auto = None
        if self.var_url.get().strip().startswith("http"):
            self._id_auto = self.after(espera, self._iniciar_analisis)

    # ------------------------------------------------- comunicación con hilos
    def _procesar_cola(self):
        try:
            while True:
                msg = self.cola.get_nowait()
                tipo = msg[0]
                if tipo == "log":
                    self._escribir_log(msg[1], msg[2] if len(msg) > 2 else None)
                elif tipo == "estado":
                    self._poner_estado(msg[1], msg[2] if len(msg) > 2 else None)
                    if len(msg) > 2 and msg[2] == "error":
                        self._alternar_detalles(True)   # ante un error, mostrar el log
                elif tipo == "progreso":
                    self.barra.configure(value=msg[1])
                elif tipo == "fin":
                    self._bloquear(False)
                elif tipo == "historial":
                    self._agregar_historial(msg[1])
                elif tipo == "dialogo":
                    messagebox.showinfo(msg[1], msg[2])
                elif tipo == "llamar":
                    msg[1]()
                elif tipo == "pedir_sesion":
                    self.after(150, lambda m=msg: self._dialogo_sesion(m[1], m[2]))
                elif tipo == "motor_nuevo":
                    self.motor_nuevo = msg[1]
                    self.btn_motor.configure(text="⟳ Motor nuevo disponible", style="MotorNuevo.TButton")
                    self._escribir_log(f"ℹ Hay una versión nueva del motor ({msg[1]}). "
                                       "Usa el botón de arriba para actualizar.", "aviso")
                elif tipo == "reiniciar":
                    if messagebox.askyesno("Motor actualizado",
                                           "Listo. Hay que reabrir la app para usar la "
                                           "nueva versión. ¿Reabrir ahora?"):
                        self._reiniciar()
                elif tipo in ("vista", "detectados", "vista_msg"):
                    url = msg[1]
                    if url != self.var_url.get().strip():
                        continue          # resultado de un enlace anterior: se descarta
                    if tipo == "vista":
                        self.analisis = msg[2]
                        self._mostrar_vista(msg[2])
                    elif tipo == "detectados":
                        self._mostrar_detectados(msg[2])
                    else:
                        self._vista_placeholder(msg[2])
                        if msg[3]:
                            self.btn_navegador.pack(anchor="w", pady=(12, 0))
        except queue.Empty:
            pass
        self.after(100, self._procesar_cola)

    def _opciones_base(self, lista=False):
        op = {
            "quiet": True,
            "no_color": True,
            "noplaylist": not lista,
            "logger": _Logger(self.cola),
            # web_creator pide un "PO Token" que no tenemos: se omite para evitar el aviso
            "extractor_args": {"youtube": {"player_client": ["default", "-web_creator"]}},
        }
        nav = self.var_nav.get()
        if nav == OPC_SESION:
            if hay_sesion():
                op["_sesion_geli"] = True      # _extraer la descifra solo mientras se usa
        elif nav == OPC_ARCHIVO:
            arch = self.cfg.get("archivo_cookies")
            if arch and os.path.isfile(arch):
                op["cookiefile"] = arch
        elif nav != "(ninguno)":
            op["cookiesfrombrowser"] = (nav,)
        return op

    # ----------------------------------------------------------------- análisis
    def _iniciar_analisis(self, *_):
        self._id_auto = None
        if self.trabajando:
            return
        url = self.var_url.get().strip()
        if not url:
            return
        if yt_dlp is None:
            self._vista_placeholder('Falta yt-dlp:\npip install "yt-dlp[default,curl-cffi]"')
            return
        self.url_analizada = url
        self.analisis = None
        self._vista_placeholder("Analizando…")
        self._bloquear(True)
        self._poner_estado("Analizando enlace…")
        threading.Thread(target=self._analizar, args=(url, self.var_lista.get()),
                         daemon=True).start()

    def _analizar(self, url, lista):
        try:
            op = self._opciones_base(lista)
            op["skip_download"] = True
            op["extract_flat"] = "in_playlist"   # las listas no se analizan video por video
            info, _ = self._extraer(op, url, download=False)
            if not info:
                raise yt_dlp.utils.DownloadError("Sin información del video")

            if info.get("_type") == "playlist":
                entradas = [e for e in list(info.get("entries") or []) if e]
                datos = {
                    "es_lista": True,
                    "n": info.get("playlist_count") or len(entradas),
                    "titulo": info.get("title") or "Lista",
                    "canal": info.get("uploader") or info.get("channel"),
                    "sitio": info.get("extractor_key"),
                }
                mini = mejor_miniatura(info) or (mejor_miniatura(entradas[0])
                                                 if entradas else None)
            else:
                datos = {
                    "es_lista": False,
                    "titulo": info.get("title"),
                    "canal": info.get("uploader") or info.get("channel"),
                    "duracion": info.get("duration"),
                    "sitio": info.get("extractor_key"),
                    "alturas": sorted({categoria_calidad(f.get("width"), f["height"])
                                       for f in info.get("formats") or []
                                       if f.get("height") and f.get("vcodec") != "none"},
                                      reverse=True),
                }
                mini = mejor_miniatura(info)
            datos["lista_marcada"] = lista
            datos["miniatura"] = None
            if mini and Image is not None:
                try:
                    datos["miniatura"] = descargar_bytes(mini)
                except Exception:
                    pass
            self.cola.put(("vista", url, datos))
            self.cola.put(("estado", "✔ Listo para descargar.", "ok"))

        except yt_dlp.utils.DownloadError as e:
            msg = limpiar(e)
            if "Unsupported URL" in msg:
                self.cola.put(("log", "ℹ yt-dlp no reconoce esta página; buscando el video "
                                      "dentro de ella…", "tenue"))
                self._detectar(url, visible=False)
            elif "DRM" in msg:
                self.cola.put(("vista_msg", url, "🔒 Este video tiene DRM; no se puede "
                                                "descargar.", False))
                self.cola.put(("estado", "🔒 Video protegido con DRM.", "error"))
            elif PATRON_PIDE_SESION.search(msg):
                self.cola.put(("log", f"✖ {msg}", "tenue"))
                self.cola.put(("vista_msg", url, "🔑 Este video pide una sesión iniciada.",
                               False))
                self.cola.put(("estado", "🔑 Este video pide iniciar sesión.", "error"))
                self.cola.put(("pedir_sesion", url, msg))
            else:
                self.cola.put(("log", f"✖ {msg}", "error"))
                self.cola.put(("vista_msg", url, "No se pudo analizar el enlace.\n"
                                                "Revisa los detalles abajo a la izquierda.",
                               False))
                self.cola.put(("estado", "✖ No se pudo analizar el enlace.", "error"))
        except Exception as e:
            self.cola.put(("log", f"✖ Error inesperado: {e}", "error"))
            self.cola.put(("estado", "✖ Error inesperado.", "error"))
        finally:
            self.cola.put(("fin",))

    # ------------------------------------------- detector de red (sin ventana)
    def _iniciar_detector_visible(self):
        if self.trabajando:
            return
        url = self.var_url.get().strip()
        if not url:
            return
        messagebox.showinfo(
            "Detector",
            "Se abrirá un navegador con la página.\n\n"
            "• Si pide iniciar sesión, hazlo ahí: quedará guardada para la próxima vez.\n"
            "• Acepta cookies si aparece el aviso y dale PLAY al video.\n"
            "• Cierra esa ventana cuando el video ya esté reproduciéndose.")
        self._bloquear(True)

        def hilo():
            try:
                self._detectar(url, visible=True)
            finally:
                self.cola.put(("fin",))

        threading.Thread(target=hilo, daemon=True).start()

    def _detectar(self, url, visible):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.cola.put(("vista_msg", url, "yt-dlp no reconoce esta página.\n\nPara buscar "
                                            "el video dentro de ella instala:\n"
                                            "pip install playwright\n"
                                            "playwright install chromium", False))
            self.cola.put(("estado", "Falta Playwright.", "error"))
            return

        encontrados = []
        meta = {}

        def al_pedir(req):
            u = req.url
            if PATRON_MEDIA.search(u) and u not in encontrados:
                encontrados.append(u)

        self.cola.put(("estado", "Buscando el video dentro de la página…"))
        navegador = self.var_nav.get()
        try:
            with sync_playwright() as p:
                os.makedirs(DIR_PERFIL, exist_ok=True)
                # Perfil propio y persistente: si inicias sesión ahí, se recuerda
                # En Windows se usa el Edge que ya trae el sistema (no hay que bajar nada)
                canal = {"channel": "msedge"} if os.name == "nt" else {}
                ctx = p.chromium.launch_persistent_context(
                    DIR_PERFIL, headless=not visible, user_agent=UA, **canal)
                if navegador in NAVEGADORES_REALES:
                    try:
                        cks = cookies_para_sitio(navegador, url)
                        puestas = 0
                        for ck in cks:
                            try:
                                ctx.add_cookies([ck])
                                puestas += 1
                            except Exception:
                                pass
                        self.cola.put(("log", f"ℹ Usando {puestas} cookie(s) de {navegador} "
                                              f"para {dominio_base(urlparse(url).hostname)}.",
                                       "tenue"))
                    except Exception as e:
                        self.cola.put(("log", f"⚠ No se pudieron leer las cookies de "
                                              f"{navegador}: {limpiar(e)}", "aviso"))
                pagina = ctx.pages[0] if ctx.pages else ctx.new_page()
                pagina.on("request", al_pedir)
                pagina.goto(url, wait_until="domcontentloaded", timeout=60000)
                try:
                    meta = pagina.evaluate(JS_META) or {}
                except Exception:
                    meta = {}
                cookies_ctx = []
                url_final = pagina.url
                if visible:
                    # Espera a que el usuario cierre la ventana (máx. 10 min), guardando
                    # las cookies por si inició sesión
                    for _ in range(400):
                        try:
                            cookies_ctx = ctx.cookies()
                            if pagina.is_closed():
                                break
                            url_final = pagina.url
                            pagina.wait_for_timeout(1500)
                        except Exception:
                            break
                else:
                    # Intenta reproducir los <video> (también dentro de iframes) y escucha
                    for _ in range(7):
                        for fr in pagina.frames:
                            try:
                                fr.evaluate(JS_PLAY)
                            except Exception:
                                pass
                        pagina.wait_for_timeout(2000)
                        if any(es_manifiesto(u) for u in encontrados):
                            pagina.wait_for_timeout(1500)
                            break
                    try:
                        cookies_ctx = ctx.cookies()
                        url_final = pagina.url
                    except Exception:
                        pass
                meta["login"] = bool(PATRON_LOGIN.search(url_final or "")) or bool(
                    PATRON_LOGIN.search(meta.get("titulo") or ""))
                if cookies_ctx:
                    escribir_cookies_netscape(cookies_ctx, ARCH_COOKIES_DET)
                try:
                    ctx.close()
                except Exception:
                    pass
        except Exception as e:
            self.cola.put(("log", f"✖ Error en el detector: {limpiar(e)}", "error"))

        if not encontrados:
            if visible:
                texto = ("No se detectó ninguna fuente de video.\n"
                         "Si el video tiene DRM tampoco se podrá descargar.")
            else:
                texto = ("No encontré el video automáticamente.\n"
                         "Puede que necesite que le des play a mano.")
            self.cola.put(("vista_msg", url, texto, not visible))
            self.cola.put(("estado", "No se encontró el video en la página.", "error"))
            return

        # Primero los manifiestos maestros, luego otros manifiestos, al final los MP4
        encontrados.sort(key=lambda u: 0 if es_maestro(u) else (1 if es_manifiesto(u) else 2))
        mini = None
        if meta.get("imagen") and Image is not None:
            try:
                mini = descargar_bytes(meta["imagen"], referer=url)
            except Exception:
                pass
        self.cola.put(("detectados", url, {"urls": encontrados, "pagina": url,
                                           "titulo": meta.get("titulo"), "miniatura": mini,
                                           "login": meta.get("login", False)}))
        self.cola.put(("log", f"✔ {len(encontrados)} fuente(s) de video encontradas en la "
                              "página.", "ok"))
        self.cola.put(("estado", "✔ Listo para descargar.", "ok"))

    # ---------------------------------------------------------------- descarga
    def _iniciar_descarga(self):
        if self.trabajando:
            return
        url = self.var_url.get().strip()
        if not url:
            messagebox.showwarning("Falta enlace", "Pega un enlace primero.")
            return
        if yt_dlp is None:
            messagebox.showerror("Falta yt-dlp", 'Instala:  pip install "yt-dlp[default,curl-cffi]"')
            return
        try:
            os.makedirs(self.var_dir.get(), exist_ok=True)
        except OSError as e:
            messagebox.showerror("Carpeta no válida", str(e))
            return

        lista = self.var_lista.get()
        es_lista = bool(self.analisis and self.analisis.get("es_lista")
                        and url == self.url_analizada)
        if self.modo_detector and self.var_fuente.get():
            obj = {"url": self.var_fuente.get(), "referer": self.pagina_detectada,
                   "titulo": self.titulo_detectado, "pagina": url}
        else:
            obj = {"url": url, "referer": None, "titulo": None, "pagina": url}
        obj.update(lista=lista, es_lista=es_lista, formato=self.var_formato.get(),
                   calidad=self.var_cal.get(), carpeta=self.var_dir.get(),
                   subs=self.var_subs.get(), detector=self.modo_detector)

        self._guardar_preferencias()
        self.cancelar.clear()
        self._vid_actual, self._parciales = None, []
        self._tmp_actual = self._arch_actual = None
        self._bloquear(True, descargando=True)
        self.barra.configure(value=0)
        self._poner_estado("Preparando descarga…")
        threading.Thread(target=self._descargar, args=(obj,), daemon=True).start()

    def _cancelar_descarga(self):
        if self.descargando:
            self.cancelar.set()
            self.btn_cancelar.configure(state="disabled")
            self._poner_estado("Cancelando…")

    def _hook_progreso(self, d):
        if self.cancelar.is_set():
            raise DescargaCancelada("Cancelado por el usuario")
        info = d.get("info_dict") or {}
        if info.get("id") != self._vid_actual:
            # Empieza otro video (en listas): lo anterior ya no es "a medio bajar"
            self._vid_actual = info.get("id")
            self._parciales = []
        if d["status"] == "downloading":
            self._tmp_actual = d.get("tmpfilename")
            self._arch_actual = d.get("filename")
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            if total:
                self.cola.put(("progreso", d.get("downloaded_bytes", 0) * 100 / total))
            pct = limpiar(d.get("_percent_str", ""))
            vel = limpiar(d.get("_speed_str", ""))
            eta = limpiar(d.get("_eta_str", ""))
            idx, n = info.get("playlist_index"), info.get("n_entries")
            pref = f"Video {idx} de {n}  ·  " if idx and n and n > 1 else ""
            self.cola.put(("estado", f"{pref}Descargando… {pct}   {vel}   ETA {eta}"))
        elif d["status"] == "finished":
            if d.get("filename"):
                self._parciales.append(d["filename"])
            self.cola.put(("progreso", 100))
            self.cola.put(("estado", "Procesando (uniendo / convirtiendo)…"))

    def _limpiar_parciales(self):
        for ruta in self._parciales + [self._tmp_actual]:
            borrar_archivo(ruta)
        if self._arch_actual:
            borrar_archivo(self._arch_actual + ".ytdl")
            borrar_archivo(self._arch_actual + ".part")

    # ------------------------------------------------------------- cookies / sesión
    def _revisar_sesion(self):
        """Al abrir: pasar la sesión de la 1.4 al formato protegido y caducar la que lleva
        mucho tiempo sin usarse."""
        migrar_sesion_vieja()
        if hay_sesion() and sesion_caducada():
            borrar_sesion()
            shutil.rmtree(DIR_PERFIL, ignore_errors=True)
            self._escribir_log(f"ℹ Tu sesión de Geli-VD se cerró sola: llevaba más de "
                               f"{DIAS_CADUCIDAD_SESION} días sin usarse. Si un video la "
                               "pide, Geli-VD te ofrecerá iniciarla de nuevo.", "tenue")

    def _cambio_cookies(self):
        nav = self.var_nav.get()
        if nav == OPC_ARCHIVO:
            ruta = filedialog.askopenfilename(
                title="Elige tu archivo cookies.txt",
                filetypes=[("Cookies (Netscape)", "*.txt"), ("Todos", "*.*")])
            if not ruta:
                self.var_nav.set(self._nav_anterior)
                return
            self.cfg["archivo_cookies"] = ruta
            self._escribir_log(f"ℹ Se usarán las cookies de {os.path.basename(ruta)}.", "tenue")
        elif nav == OPC_SESION and not hay_sesion():
            if messagebox.askyesno(
                    "Iniciar sesión",
                    "Aún no has iniciado sesión en Geli-VD.\n\n"
                    "Se abrirá una ventana del navegador: entra a tu cuenta (YouTube, "
                    "Instagram…) y luego CIERRA esa ventana. Geli-VD guardará la sesión "
                    "solo en este equipo.\n\n¿Abrir ahora?"):
                self._iniciar_sesion(self._url_login(self.var_url.get().strip()))
        self._nav_anterior = self.var_nav.get()
        self._guardar_preferencias()

    @staticmethod
    def _url_login(url_video):
        """Página de inicio de sesión del sitio del video."""
        dom = dominio_base(urlparse(url_video or "").hostname or "")
        return {
            "youtube.com": "https://accounts.google.com/ServiceLogin?"
                           "continue=https://www.youtube.com/",
            "youtu.be": "https://accounts.google.com/ServiceLogin?"
                        "continue=https://www.youtube.com/",
            "instagram.com": "https://www.instagram.com/accounts/login/",
            "facebook.com": "https://www.facebook.com/login/",
            "fb.watch": "https://www.facebook.com/login/",
            "tiktok.com": "https://www.tiktok.com/login",
            "x.com": "https://x.com/i/flow/login",
            "twitter.com": "https://x.com/i/flow/login",
            "vimeo.com": "https://vimeo.com/log_in",
        }.get(dom, url_video or "https://www.youtube.com/")

    def _dialogo_sesion(self, url, msg):
        """El video pide una sesión: ofrecer usar la de un navegador instalado o iniciar
        sesión en Geli-VD, y reintentar el análisis."""
        sitio = dominio_base(urlparse(url).hostname or "") or "este sitio"
        actual = self.var_nav.get()
        v = tk.Toplevel(self)
        v.title("Este video pide iniciar sesión")
        v.configure(bg=C["fondo"])
        v.transient(self)
        v.resizable(False, False)
        cont = ttk.Frame(v, padding=22)
        cont.pack(fill="both", expand=True)
        ttk.Label(cont, text="🔑 Este video pide una sesión iniciada",
                  font=(FUENTE, 15, "bold")).pack(anchor="w")
        if actual in (OPC_SESION, *NAVEGADORES_REALES, OPC_ARCHIVO) and actual != "(ninguno)":
            extra = (f"\nYa estabas usando «{NOMBRE_NAV.get(actual, actual)}», pero {sitio} no "
                     "la aceptó: quizás la sesión venció o no habías entrado a tu cuenta.")
        else:
            extra = ""
        ttk.Label(cont, wraplength=430, justify="left", style="Tenue.TLabel",
                  text=f"{sitio} necesita saber que eres una persona con cuenta (por ejemplo, "
                       f"YouTube pide confirmar que no eres un bot). Elige de dónde tomar "
                       f"tu sesión; solo se usa en este equipo.{extra}").pack(
            anchor="w", pady=(6, 14))

        def elegir(opcion):
            v.destroy()
            if opcion == OPC_SESION:
                self._iniciar_sesion(self._url_login(url),
                                     al_terminar=lambda: self._reintentar_analisis(url))
                return
            self.var_nav.set(opcion)
            self._nav_anterior = opcion
            self._guardar_preferencias()
            self._reintentar_analisis(url)

        nombre_sesion = ("Volver a iniciar sesión en Geli-VD"
                         if hay_sesion() else
                         "Iniciar sesión en una ventana de Geli-VD")
        ttk.Button(cont, text="🔐  " + nombre_sesion, style="Rosa.TButton",
                   command=lambda: elegir(OPC_SESION)).pack(fill="x")
        ttk.Label(cont, text="Se abre una ventana: entras a tu cuenta y la cierras. "
                             "Queda guardada para la próxima vez.",
                  style="Pista.TLabel", wraplength=430).pack(anchor="w", pady=(4, 10))
        if hay_sesion() and actual != OPC_SESION:
            ttk.Button(cont, text="Usar la sesión que ya guardé en Geli-VD",
                       style="Sec.TButton",
                       command=lambda: (v.destroy(), self.var_nav.set(OPC_SESION),
                                        setattr(self, "_nav_anterior", OPC_SESION),
                                        self._guardar_preferencias(),
                                        self._reintentar_analisis(url))).pack(
                fill="x", pady=(0, 6))
        for nav in NAVEGADORES_REALES:
            if nav == actual:
                continue
            ttk.Button(cont, text=f"Usar mi sesión de {NOMBRE_NAV.get(nav, nav)}",
                       style="Sec.TButton",
                       command=lambda n=nav: elegir(n)).pack(fill="x", pady=(0, 6))
        if NAVEGADORES_REALES:
            ttk.Label(cont, text="Usa el navegador donde ya tienes abierta tu cuenta de "
                                 f"{sitio}. Si da error, ciérralo y vuelve a intentar.",
                      style="Pista.TLabel", wraplength=430).pack(anchor="w", pady=(0, 10))
        ttk.Button(cont, text="Cancelar", style="Link.TButton",
                   command=v.destroy).pack(anchor="e", pady=(6, 0))
        v.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - v.winfo_width()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - v.winfo_height()) // 3
        v.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        v.grab_set()
        v.focus_set()

    def _reintentar_analisis(self, url):
        if self.trabajando:
            self.after(500, lambda: self._reintentar_analisis(url))
            return
        self.var_url.set(url)
        self._escribir_log(f"↻ Reintentando con «{self.var_nav.get()}»…", "tenue")
        self._iniciar_analisis()

    def _iniciar_sesion(self, url="https://accounts.google.com/ServiceLogin?"
                                  "continue=https://www.youtube.com/", al_terminar=None):
        """Abre una ventana de navegador propia de Geli-VD para iniciar sesión. Al cerrarla,
        guarda las cookies protegidas (ver guardar_sesion)."""
        if self.trabajando:
            messagebox.showinfo("Espera", "Termina la descarga o análisis en curso primero.")
            return
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            messagebox.showinfo(
                "Falta un componente",
                "Para iniciar sesión dentro de Geli-VD hace falta Playwright:\n"
                "pip install playwright\n\n"
                f"Otra opción: elige «{OPC_ARCHIVO}» con un archivo exportado desde tu "
                "navegador (extensión «Get cookies.txt LOCALLY»).")
            return
        self._bloquear(True)
        self._poner_estado("Abriendo ventana para iniciar sesión… ciérrala al terminar.")
        self._escribir_log("ℹ Inicia sesión en la ventana que se abrió y luego ciérrala.",
                           "tenue")

        def hilo():
            try:
                with sync_playwright() as p:
                    os.makedirs(DIR_PERFIL, exist_ok=True)
                    canal = {"channel": "msedge"} if os.name == "nt" else {}
                    ctx = p.chromium.launch_persistent_context(
                        DIR_PERFIL, headless=False, no_viewport=True,
                        # sin la marca de "navegador automatizado" (Google la rechaza)
                        ignore_default_args=["--enable-automation"],
                        args=["--disable-blink-features=AutomationControlled"], **canal)
                    pagina = ctx.pages[0] if ctx.pages else ctx.new_page()
                    try:
                        pagina.goto(url, wait_until="domcontentloaded", timeout=60000)
                    except Exception:
                        pass
                    cookies = []
                    # Esperar a que el usuario cierre la ventana, guardando mientras tanto
                    while ctx.pages:
                        try:
                            cookies = ctx.cookies() or cookies
                        except Exception:
                            break
                        try:
                            ctx.pages[0].wait_for_timeout(1500)
                        except Exception:
                            break
                    try:
                        ctx.close()
                    except Exception:
                        pass
                if cookies and not guardar_sesion(texto_cookies_netscape(cookies)):
                    self.cola.put(("log", "✖ No se pudo guardar la sesión.", "error"))
                    cookies = []
                if cookies:
                    sesion = any(c.get("name") in ("SAPISID", "__Secure-3PAPISID", "sessionid",
                                                   "LOGIN_INFO", "c_user")
                                 for c in cookies)
                    self.cola.put(("log", "✔ Sesión guardada." if sesion else
                                   "ℹ Se guardaron las cookies, pero no parece que hayas "
                                   "iniciado sesión.", "ok" if sesion else "aviso"))
                    self.cola.put(("llamar", lambda: (self.var_nav.set(OPC_SESION),
                                                      setattr(self, "_nav_anterior", OPC_SESION),
                                                      self._guardar_preferencias())))
                    self.cola.put(("estado", f"✔ Listo. «Cookies de» quedó en {OPC_SESION}.",
                                   "ok"))
                    if al_terminar:
                        self.cola.put(("llamar", al_terminar))
                else:
                    self.cola.put(("estado", "No se guardó ninguna sesión.", "aviso"))
            except Exception as e:
                self.cola.put(("log", f"✖ No se pudo abrir la ventana: {limpiar(e)}", "error"))
                if os.name != "nt":
                    self.cola.put(("log", "  Si falta el navegador: playwright install chromium",
                                   "tenue"))
                self.cola.put(("estado", "✖ No se pudo abrir la ventana de inicio de sesión.",
                               "error"))
            finally:
                self.cola.put(("fin",))

        threading.Thread(target=hilo, daemon=True).start()

    def _extraer(self, op, url, download):
        """extract_info. Con «Geli (mi sesión)», la sesión se descifra en un archivo temporal
        solo mientras dura la operación y luego se vuelve a guardar protegida."""
        if not op.get("_sesion_geli"):
            return self._extraer_simple(op, url, download)
        op = {k: v for k, v in op.items() if k != "_sesion_geli"}
        texto = leer_sesion()
        if texto is None:
            self.cola.put(("log", "⚠ No se pudo abrir tu sesión guardada (quizás se creó con "
                                  "otro usuario de Windows). Vuelve a iniciar sesión.", "aviso"))
            return self._extraer_simple(op, url, download)
        import tempfile
        fd, tmp = tempfile.mkstemp(prefix="gvd-", suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(texto)
            op["cookiefile"] = tmp
            return self._extraer_simple(op, url, download)
        finally:
            try:
                with open(tmp, encoding="utf-8") as f:
                    nuevo = f.read()         # yt-dlp pudo renovar cookies
                guardar_sesion(nuevo if "\t" in nuevo else texto)   # también marca el uso
            except Exception:
                pass
            borrar_archivo(tmp)

    def _extraer_simple(self, op, url, download):
        """extract_info; si fallan las cookies del navegador, sigue sin ellas y avisa."""
        try:
            with yt_dlp.YoutubeDL(op) as ydl:
                return ydl.extract_info(url, download=download), ydl
        except Exception as e:
            if "cookiesfrombrowser" not in op or not es_error_cookies(e):
                raise
            nav = op["cookiesfrombrowser"][0]
            self.cola.put(("log", f"⚠ No se pudieron leer las cookies de {nav}"
                                  f"{' (Chrome/Edge las protegen en Windows)' if os.name == 'nt' else ''}"
                                  f". Sigo sin cookies; si el sitio pide iniciar sesión, "
                                  f"elige «{OPC_SESION}» en «Cookies de».", "aviso"))
            op = {k: v for k, v in op.items() if k != "cookiesfrombrowser"}
            with yt_dlp.YoutubeDL(op) as ydl:
                return ydl.extract_info(url, download=download), ydl

    def _extraer_con_reintento(self, op, url):
        """Descarga; si el formato pedido no existe, reintenta con lo mejor disponible."""
        try:
            info, ydl = self._extraer(op, url, download=True)
        except yt_dlp.utils.DownloadError as e:
            if "format is not available" not in str(e) or self.cancelar.is_set():
                raise
            self.cola.put(("log", "⚠ Ese formato no estaba disponible; reintentando con la "
                                  "mejor opción que ofrece el sitio…", "aviso"))
            op = dict(op, format="best/bv*+ba", format_sort=["res", "tbr"])
            info, ydl = self._extraer(op, url, download=True)
        self._log_calidad(info)
        return info, ydl

    def _log_calidad(self, info):
        """Anota en el log qué resolución se bajó, para saber si salió en HD."""
        if not info or info.get("_type") == "playlist":
            return
        alto = categoria_calidad(info.get("width"), info.get("height"))
        res = info.get("resolution") or (f"{info.get('width')}x{alto}" if alto else None)
        if res and res != "audio only":
            self.cola.put(("log", f"ℹ Calidad descargada: {res}"
                                  f"{f' ({alto}p)' if alto else ''}", "tenue"))
            alturas = (self.analisis or {}).get("alturas") or []
            if alto and alturas and max(alturas) > alto and self.var_cal.get() == "Mejor calidad":
                self.cola.put(("log", f"⚠ El sitio anuncia hasta {max(alturas)}p pero entregó "
                                      f"{alto}p: puede requerir sesión (Cookies de) o ser una "
                                      "fuente de una sola calidad.", "aviso"))

    def _descargar(self, obj):
        carpeta = obj["carpeta"]
        bajar_lista = obj["lista"] and obj["es_lista"]
        if obj["titulo"]:
            plantilla = nombre_seguro(obj["titulo"]) + ".%(ext)s"
        elif bajar_lista:
            plantilla = os.path.join("%(playlist_title,playlist_id)s",
                                     "%(playlist_index)03d - %(title).120B [%(id)s].%(ext)s")
        else:
            plantilla = "%(title).150B [%(id)s].%(ext)s"

        op = self._opciones_base(obj["lista"])
        valor = CALIDADES[obj["formato"]].get(obj["calidad"])
        if obj["formato"] == "Video (MP4)":
            # Sin filtros estrictos: se elige por ORDEN de preferencia, así nunca falla
            # aunque el sitio no informe la resolución de cada formato
            formato_dl = "bv*+ba/b/bv*/best"
        elif obj["formato"] == "Audio (M4A)":
            formato_dl = "ba[ext=m4a]/ba/b"
        else:
            formato_dl = "ba/b"
        op.update({
            "format": formato_dl,
            "outtmpl": os.path.join(carpeta, plantilla),
            "progress_hooks": [self._hook_progreso],
            # Resolución (con tope si se eligió uno), luego bitrate; a igualdad,
            # H.264/AAC para que el .mp4 se abra en cualquier reproductor
            "format_sort": [f"res:{valor}" if (valor and obj["formato"] == "Video (MP4)")
                            else "res", "tbr", "vcodec:h264", "acodec:aac"],
        })
        if obj["es_lista"] and not obj["lista"]:
            op["playlist_items"] = "1"      # enlace de lista sin la opción: solo el primero
        if bajar_lista:
            op["ignoreerrors"] = "only_download"   # un video caído no frena el resto
        postprocesos = []
        if obj["formato"] == "Audio (MP3)":
            postprocesos.append({"key": "FFmpegExtractAudio",
                                 "preferredcodec": "mp3", "preferredquality": valor or "192"})
        elif obj["formato"] == "Audio (M4A)":
            # Si el audio ya es AAC/M4A solo se copia, sin perder calidad
            postprocesos.append({"key": "FFmpegExtractAudio", "preferredcodec": "m4a"})
        else:
            op["merge_output_format"] = "mp4"
            if obj["subs"]:
                op.update(writesubtitles=True, writeautomaticsub=True,
                          subtitleslangs=["es.*", "en.*", "-live_chat"])
                postprocesos.append({"key": "FFmpegEmbedSubtitle"})
        if postprocesos:
            op["postprocessors"] = postprocesos
        if obj["referer"]:
            op["http_headers"] = {"Referer": obj["referer"]}
        if obj["detector"] and os.path.exists(ARCH_COOKIES_DET):
            op["cookiefile"] = ARCH_COOKIES_DET   # la sesión que tenía el detector

        self.cola.put(("log", f"→ {obj['url']}", "tenue"))
        registro = {"url": obj["pagina"], "fecha": datetime.now().isoformat(timespec="seconds"),
                    "titulo": obj["titulo"] or obj["pagina"], "archivo": None, "ok": False}
        try:
            info, ydl = self._extraer_con_reintento(op, obj["url"])
            if info and info.get("_type") == "playlist":
                entradas = [e for e in info.get("entries") or [] if e]
                registro["titulo"] = f"📃 {info.get('title') or 'Lista'} " \
                                     f"({len(entradas)} videos)"
                rutas = [ruta_final(e, ydl) for e in entradas]
                rutas = [r for r in rutas if r]
                registro["archivo"] = os.path.dirname(rutas[0]) if rutas else carpeta
            elif info:
                registro["titulo"] = obj["titulo"] or info.get("title") or registro["titulo"]
                registro["archivo"] = ruta_final(info, ydl)
            registro["ok"] = True
            self.cola.put(("log", f"✔ Terminado: {registro['titulo']}", "ok"))
            self.cola.put(("estado", "✔ Descarga completa.", "ok"))
            if self.var_notificar.get():
                notificar(APP_CORTO, f"Descarga completa: {registro['titulo']}")
            self.cola.put(("historial", registro))
        except DescargaCancelada:
            self._limpiar_parciales()
            self.cola.put(("log", "■ Descarga cancelada; se borraron los archivos a medio "
                                  "bajar.", "aviso"))
            self.cola.put(("estado", "■ Descarga cancelada."))
            self.cola.put(("progreso", 0))
        except yt_dlp.utils.DownloadError as e:
            msg = limpiar(e)
            if "DRM" in msg:
                self.cola.put(("log", "✖ Este video está protegido con DRM; no se puede "
                                      "descargar.", "error"))
            else:
                self.cola.put(("log", f"✖ {msg}", "error"))
            self.cola.put(("estado", "✖ Error en la descarga.", "error"))
            if self.var_notificar.get():
                notificar(APP_CORTO, "La descarga falló.")
            self.cola.put(("historial", registro))
        except Exception as e:
            self.cola.put(("log", f"✖ Error inesperado: {e}", "error"))
            self.cola.put(("estado", "✖ Error inesperado.", "error"))
        finally:
            self.cola.put(("fin",))

    # --------------------------------------------------- sesiones del detector
    def _cerrar_sesiones_detector(self):
        if not messagebox.askyesno(
                "Cerrar sesiones de Geli-VD",
                "Se borrarán las sesiones iniciadas en la ventana de Geli-VD "
                "(YouTube, Instagram, plataformas de cursos…).\n\n"
                "Tus navegadores (Safari, Chrome…) no se tocan.\n¿Continuar?"):
            return
        shutil.rmtree(DIR_PERFIL, ignore_errors=True)
        borrar_archivo(ARCH_COOKIES_DET)
        borrar_sesion()
        if self.var_nav.get() == OPC_SESION:
            self.var_nav.set("(ninguno)")
            self._nav_anterior = "(ninguno)"
            self._guardar_preferencias()
        self._poner_estado("✔ Sesiones cerradas.", "ok")

    # ------------------------------------------------- convertir video local
    def _convertir_local(self):
        if self.trabajando:
            return
        if not shutil.which("ffmpeg"):
            messagebox.showerror("Falta ffmpeg", "Para convertir necesitas ffmpeg.\n"
                                                 "Mac:  brew install ffmpeg")
            return
        archivos = filedialog.askopenfilenames(
            title="Elige uno o varios videos para convertir a MP3",
            filetypes=[("Videos", "*.mp4 *.mkv *.webm *.mov *.avi *.m4v *.flv *.ts"),
                       ("Todos los archivos", "*.*")])
        if not archivos:
            return
        kbps = CALIDADES["Audio (MP3)"].get(self.var_cal.get(), "192")
        self.cancelar.clear()
        self._bloquear(True, descargando=True)
        self.barra.configure(value=0)
        threading.Thread(target=self._convertir, args=(list(archivos), kbps),
                         daemon=True).start()

    def _convertir(self, archivos, kbps):
        hechos = 0
        try:
            for i, ruta in enumerate(archivos, 1):
                if self.cancelar.is_set():
                    break
                base = os.path.splitext(ruta)[0]
                salida = base + ".mp3"
                n = 2
                while os.path.exists(salida):
                    salida = f"{base} ({n}).mp3"
                    n += 1
                nombre = os.path.basename(ruta)
                self.cola.put(("estado", f"🎵 Convirtiendo {i} de {len(archivos)}: {nombre}"))
                self.cola.put(("progreso", 0))
                total = duracion_archivo(ruta)
                proc = subprocess.Popen(
                    ["ffmpeg", "-y", "-i", ruta, "-vn", "-c:a", "libmp3lame",
                     "-b:a", f"{kbps}k", "-progress", "pipe:1", "-nostats",
                     "-loglevel", "error", salida],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **SIN_VENTANA)
                for linea in proc.stdout:
                    if self.cancelar.is_set():
                        proc.terminate()
                        break
                    if total and linea.startswith(("out_time_us=", "out_time_ms=")):
                        try:
                            seg = int(linea.split("=")[1]) / 1_000_000
                            self.cola.put(("progreso", min(seg / total * 100, 100)))
                        except ValueError:
                            pass
                proc.wait()
                error = proc.stderr.read().strip() if proc.stderr else ""
                registro = {"url": ruta, "fecha": datetime.now().isoformat(timespec="seconds"),
                            "titulo": "🎵 " + os.path.basename(salida), "archivo": salida,
                            "ok": proc.returncode == 0}
                if self.cancelar.is_set():
                    borrar_archivo(salida)
                    break
                if proc.returncode == 0:
                    hechos += 1
                    self.cola.put(("log", f"✔ Convertido: {salida}", "ok"))
                else:
                    borrar_archivo(salida)
                    registro["archivo"] = None
                    self.cola.put(("log", f"✖ No se pudo convertir {nombre}: "
                                          f"{error[-300:]}", "error"))
                self.cola.put(("historial", registro))

            if self.cancelar.is_set():
                self.cola.put(("estado", "■ Conversión cancelada."))
                self.cola.put(("progreso", 0))
            elif hechos == len(archivos):
                self.cola.put(("progreso", 100))
                self.cola.put(("estado", f"✔ {hechos} archivo(s) convertidos a MP3.", "ok"))
                if self.var_notificar.get():
                    notificar(APP_CORTO, f"Conversión a MP3 lista ({hechos} archivo/s).")
            else:
                self.cola.put(("estado", f"✖ Se convirtieron {hechos} de {len(archivos)}.",
                               "error"))
        except Exception as e:
            self.cola.put(("log", f"✖ Error al convertir: {e}", "error"))
            self.cola.put(("estado", "✖ Error al convertir.", "error"))
        finally:
            self.cola.put(("fin",))

    # ------------------------------------------------------- actualizar motor
    def _version_motor(self):
        return getattr(getattr(yt_dlp, "version", None), "__version__", None) if yt_dlp else None

    def _revisar_motor_en_segundo_plano(self):
        """Al abrir: revisa en silencio si hay un motor nuevo y solo avisa si lo hay."""
        if yt_dlp is None and not ES_EXE:
            return

        def hilo():
            try:
                nueva = version_motor_disponible()
                if version_mayor(nueva, self._version_motor()):
                    self.cola.put(("motor_nuevo", nueva))
            except Exception:
                pass                     # sin internet: no molestar

        threading.Thread(target=hilo, daemon=True).start()

    def _actualizar_motor(self):
        if self.trabajando:
            messagebox.showinfo("Espera", "Termina la descarga o análisis en curso primero.")
            return
        self._bloquear(True)
        self._poner_estado("Buscando actualizaciones del motor…")

        def revisar():
            actual = self._version_motor() or "no instalado"
            try:
                nueva = version_motor_disponible()
            except Exception as e:
                self.cola.put(("log", f"✖ No se pudo revisar (¿sin internet?): {e}", "error"))
                self.cola.put(("estado", "✖ No se pudo revisar el motor.", "error"))
                self.cola.put(("fin",))
                return
            self.cola.put(("fin",))
            self.cola.put(("llamar", lambda: preguntar(actual, nueva)))

        def preguntar(actual, nueva):
            if not version_mayor(nueva, actual if actual != "no instalado" else "0"):
                self._poner_estado(f"✔ Motor al día (yt-dlp {actual}).", "ok")
                self.btn_motor.configure(text="⟳ Actualizar motor", style="Motor.TButton")
                return
            if not messagebox.askyesno(
                    "Actualizar motor",
                    f"Hay una versión nueva del motor de descargas.\n\n"
                    f"Instalada:   {actual}\nDisponible: {nueva}\n\n"
                    "Conviene actualizar cuando un sitio que antes funcionaba deja de "
                    "descargar.\n¿Actualizar ahora?"):
                self._poner_estado("Listo.")
                return
            self._bloquear(True)
            self._poner_estado("Actualizando motor de descargas…")
            self._alternar_detalles(True)
            threading.Thread(target=instalar, args=(nueva,), daemon=True).start()

        def instalar(nueva):
            if ES_EXE:
                try:
                    v = instalar_motor_exe(lambda t: self.cola.put(("log", t, "tenue")))
                    self.cola.put(("log", f"✔ Motor actualizado a {v}.", "ok"))
                    self.cola.put(("estado", "✔ Motor actualizado.", "ok"))
                    self.cola.put(("llamar", lambda: self.btn_motor.configure(
                        text="⟳ Actualizar motor", style="Motor.TButton")))
                    self.cola.put(("reiniciar",))
                except Exception as e:
                    self.cola.put(("log", f"✖ {e}", "error"))
                    self.cola.put(("estado", "✖ No se pudo actualizar.", "error"))
                finally:
                    self.cola.put(("fin",))
                return
            try:
                base = [sys.executable, "-m", "pip", "install", "-U", "yt-dlp[default,curl-cffi]"]
                r = subprocess.run(base, capture_output=True, text=True, timeout=600)
                if r.returncode != 0 and "externally-managed" in (r.stdout + r.stderr):
                    # Python de Homebrew: pip exige este parámetro
                    r = subprocess.run(base + ["--break-system-packages"],
                                       capture_output=True, text=True, timeout=600)
                for linea in (r.stdout + "\n" + r.stderr).strip().splitlines()[-6:]:
                    self.cola.put(("log", linea, "tenue"))
                if r.returncode == 0:
                    self.cola.put(("log", f"✔ Motor actualizado a {nueva}.", "ok"))
                    self.cola.put(("estado", "✔ Motor actualizado.", "ok"))
                    self.cola.put(("llamar", lambda: self.btn_motor.configure(
                        text="⟳ Actualizar motor", style="Motor.TButton")))
                    self.cola.put(("reiniciar",))
                else:
                    self.cola.put(("estado", "✖ No se pudo actualizar.", "error"))
            except Exception as e:
                self.cola.put(("log", f"✖ {e}", "error"))
                self.cola.put(("estado", "✖ No se pudo actualizar.", "error"))
            finally:
                self.cola.put(("fin",))

        threading.Thread(target=revisar, daemon=True).start()


class _Logger:
    """Redirige los mensajes de yt-dlp al panel de la GUI."""

    def __init__(self, cola):
        self.cola = cola

    def debug(self, msg):
        if msg.startswith("[download] Destination") or msg.startswith("[Merger]"):
            self.cola.put(("log", limpiar(msg), "tenue"))

    def info(self, msg):
        pass

    def warning(self, msg):
        texto = limpiar(msg)
        if "PO Token" in texto:          # aviso informativo de YouTube: no es un error
            self.cola.put(("log", "ℹ YouTube omitió algunos formatos (PO Token); "
                                  "la descarga sigue con los demás.", "tenue"))
            return
        self.cola.put(("log", f"⚠ {texto}", "aviso"))

    def error(self, msg):
        pass  # se informa desde el except


def _diagnostico():
    print(f"{APP_CORTO} {APP_VERSION}  ({'exe' if ES_EXE else 'python'})")
    print("yt-dlp:", getattr(getattr(yt_dlp, "version", None), "__version__", "NO"),
          "->", getattr(yt_dlp, "__file__", "-"))
    print("Motor actualizado:", MOTOR_ACTUALIZADO or "no (se usa el incluido)")
    for b in ("ffmpeg", "ffprobe", "deno"):
        print(f"{b}:", shutil.which(b) or "NO ENCONTRADO")
    print("Pillow:", "sí" if Image is not None else "NO")
    try:
        import curl_cffi
        print("curl_cffi (sitios que exigen imitar un navegador):", curl_cffi.__version__)
    except Exception as e:
        print("curl_cffi: NO", e)


if __name__ == "__main__":
    if sys.stdout is None:               # .exe sin consola: la salida va a un archivo
        os.makedirs(DIR_DATOS, exist_ok=True)
        sys.stdout = sys.stderr = open(os.path.join(DIR_DATOS, "diagnostico.txt"), "w",
                                       encoding="utf-8")
    if "--diag" in sys.argv:
        _diagnostico()
    elif "--actualizar-motor" in sys.argv:
        if ES_EXE:
            print("Motor instalado:", instalar_motor_exe())
        else:
            subprocess.run([sys.executable, "-m", "pip", "install", "-U", "yt-dlp[default,curl-cffi]"])
    else:
        App().mainloop()
