<div align="center">

<img src="escritorio/icono.png" width="96" alt="Geli-VD">

# Geli-VD — Descargador de videos y audio

**Pega, descarga, listo.**
Descarga videos y audio de sitios compatibles. Gratis y sin anuncios. Parte del ecosistema **Geli**.

[**⬇ Descargar para Windows 10/11 — recomendado (v1.5 · 141 MB)**](https://github.com/GeliOSCorp/Geli-VD/releases/download/v1.5/Geli-VD-Setup-win1.5.exe)

[Windows portable](https://github.com/GeliOSCorp/Geli-VD/releases/download/v1.5/Geli-VD-win1.5-portable.zip) · [macOS / Linux (Python)](#macos--linux-versión-python) · [Todas las versiones](https://github.com/GeliOSCorp/Geli-VD/releases)

[![Versión](https://img.shields.io/github/v/release/GeliOSCorp/Geli-VD?label=versi%C3%B3n&color=6a4cf0)](https://github.com/GeliOSCorp/Geli-VD/releases/latest)
[![Licencia](https://img.shields.io/badge/licencia-GPL--3.0-6a4cf0)](LICENSE)

**Windows:** instalador y portable · **macOS / Linux:** versión Python

Contenido protegido con DRM no compatible.

</div>

<p align="center"><img src="docs/captura.png" width="760" alt="Geli-VD en funcionamiento"></p>

---

## ¿Qué es?

Geli-VD es una app de escritorio para descargar videos y audio pegando un enlace.
Funciona con YouTube, Dailymotion, Vimeo, TikTok, Instagram, Facebook y
[cientos de sitios más](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).

- **Vista previa** automática: portada, duración y calidades (480p, 720p, 1080p…).
- **Video MP4**, **Audio MP3** o **M4A**, listas y carruseles completos, subtítulos.
- **Historial** de descargas (se puede borrar o desactivar).
- **⟳ Actualizar motor**: cuando un sitio cambia y deja de descargar, se actualiza con
  un clic, **sin reinstalar** la app.
- **Iniciar sesión** para videos que la piden (YouTube "no eres un bot", Instagram…):
  la sesión se guarda localmente y caduca tras 30 días sin uso. Consulta los detalles de
  protección en [Privacidad](#privacidad).
- Tema claro u oscuro según tu sistema.
- **Sin anuncios.** Descargas, historial y preferencias se gestionan en tu equipo.

---

## Descargar e instalar

| Opción | Descarga | Tamaño aproximado | Requisitos |
|---|---|---|---|
| **Windows 10/11 — recomendado** | [Instalador .exe](https://github.com/GeliOSCorp/Geli-VD/releases/download/v1.5/Geli-VD-Setup-win1.5.exe) | 141 MB | No necesitas instalar Python por separado. |
| Windows — sin instalación | [Portable .zip](https://github.com/GeliOSCorp/Geli-VD/releases/download/v1.5/Geli-VD-win1.5-portable.zip) | 196 MB | Extrae todo el ZIP y abre `Geli-VD.exe` desde la carpeta extraída. |
| macOS / Linux — versión Python | [Paquete Python .zip](https://github.com/GeliOSCorp/Geli-VD/releases/download/v1.5/Geli-VD-py1.5.zip) | 64 kB | Python 3.10+, Tkinter y FFmpeg. También disponible para Windows con Python. |

Los tamaños son decimales y corresponden a los archivos de la release 1.5. El paquete
Python descarga dependencias al primer inicio; su ZIP no representa el espacio total instalado.

**¿Cuál elijo?** Si usas Windows y quieres empezar, elige el instalador.
Si prefieres usarlo sin instalar, elige el portable. Para macOS o Linux, utiliza el paquete Python.
Los archivos **Source code** de GitHub contienen el código del repositorio; para usar la app,
elige uno de los paquetes anteriores.

### Windows: instalar o usar el portable

**Instalador (recomendado):**
1. [Descarga el instalador de Geli-VD 1.5](https://github.com/GeliOSCorp/Geli-VD/releases/download/v1.5/Geli-VD-Setup-win1.5.exe).
2. Abre `Geli-VD-Setup-win1.5.exe` y sigue el asistente. No pide permisos de administrador.
3. Abre Geli-VD desde el acceso directo creado por el instalador.

**Portable:** [descarga el ZIP](https://github.com/GeliOSCorp/Geli-VD/releases/download/v1.5/Geli-VD-win1.5-portable.zip), haz clic derecho → **Extraer todo**
y abre `Geli-VD.exe` dentro de la carpeta extraída. Conserva juntos los archivos del paquete;
no ejecutes el programa desde dentro del ZIP.

**Aviso de Windows:** el ejecutable aún no está firmado digitalmente y Windows puede mostrar
«Windows protegió su PC». Verifica que lo descargaste de esta release oficial.
Si decides continuar, selecciona **Más información → Ejecutar de todas formas**.
No es necesario desactivar el antivirus.

**Actualizar el instalador:** instala la versión nueva encima; se conservan el historial
y las preferencias.

### macOS / Linux: versión Python

1. [Descarga el paquete Python](https://github.com/GeliOSCorp/Geli-VD/releases/download/v1.5/Geli-VD-py1.5.zip) y extrae todo su contenido en una carpeta
   donde puedas guardar archivos, por ejemplo Documentos.
2. Instala **Python 3.10+, Tkinter y FFmpeg**:
   - **macOS con [Homebrew](https://brew.sh/):** abre Terminal y ejecuta
     `brew install python python-tk ffmpeg`. Si no tienes Homebrew, consulta primero su
     guía de instalación. Comprueba que Tkinter corresponde al Python que vas a utilizar.
   - **Debian/Ubuntu:** `sudo apt install python3 python3-venv python3-tk ffmpeg`.
     Comprueba que `python3 --version` sea 3.10 o posterior.
3. Abre una terminal **dentro de la carpeta que contiene el lanzador**:
   - **macOS:**
     ```sh
     chmod +x iniciar_mac.command
     ./iniciar_mac.command
     ```
     Después puedes abrir `iniciar_mac.command` con doble clic. Si macOS lo bloquea,
     revisa el aviso de seguridad y confirma la procedencia del archivo antes de autorizarlo.
   - **Linux:**
     ```sh
     chmod +x iniciar_linux.sh
     ./iniciar_linux.sh
     ```

El primer inicio **requiere Internet** para crear el entorno `.venv` e instalar las
dependencias. El tiempo depende de tu conexión y equipo. No cierres la terminal durante
la preparación. Consulta la [guía completa](https://github.com/GeliOSCorp/Geli-VD/blob/main/escritorio/LEEME.md)
si aparece un error.

### Tu primera descarga

1. Pega el enlace de un video compatible.
2. Elige el formato (MP4, MP3 o M4A), la calidad y la carpeta de destino.
3. Pulsa **Descargar**. Algunos sitios o videos requieren iniciar sesión.

---

## Problemas comunes

| Mensaje | Solución |
|---|---|
| "Sign in to confirm you're not a bot" | En **Cookies de** elige **Geli (mi sesión)** e inicia sesión en tu cuenta. |
| Windows: error de cookies de Chrome/Edge | Chrome y Edge protegen sus cookies en Windows. Usa **Geli (mi sesión)** o Firefox. |
| Un sitio que funcionaba dejó de descargar | Pulsa **⟳ Actualizar motor**. |
| Otro problema | Abre un [Issue](https://github.com/GeliOSCorp/Geli-VD/issues) con una captura del mensaje. |

---

## Uso responsable

Geli-VD es una herramienta. Descarga solo contenido **propio, de libre uso o con permiso de
su autor**, respetando las condiciones de cada sitio y los derechos de autor. Los videos con
DRM no se pueden descargar.

## Privacidad

Geli-VD procesa las descargas en tu equipo, sin un servidor propio que las intermedie.
El historial y las preferencias se guardan localmente. La app se conecta a los sitios de los
videos y sus servicios asociados; también consulta PyPI para comprobar actualizaciones del
motor y descarga dependencias cuando corresponde.

La sesión «Geli (mi sesión)» se guarda localmente: en Windows usa DPAPI cuando está
disponible; en macOS/Linux se almacena con permisos restringidos al usuario, sin cifrado.
Si DPAPI falla en Windows, el código permite guardar la sesión sin cifrar.
Puedes borrar los datos desde **Historial → Borrar todos los datos de la app**.

---

## Próximamente

Android está previsto; esta release no incluye una aplicación Android.

[![Descargas](https://img.shields.io/github/downloads/GeliOSCorp/Geli-VD/total?label=descargas&color=6a4cf0)](https://github.com/GeliOSCorp/Geli-VD/releases)

## Para desarrolladores

```
escritorio/
├── descargador_video.py   la app completa (tkinter + yt-dlp)
├── requirements.txt       librerías de Python
└── iniciar_*              lanzadores para Windows, macOS y Linux
```

Para ejecutarla desde el código: `pip install -r escritorio/requirements.txt` y luego
`python escritorio/descargador_video.py`. Las sugerencias y mejoras son bienvenidas vía
Issues y Pull Requests.

## Licencia

Geli-VD se distribuye bajo la licencia [**GPL-3.0**](LICENSE): puedes usarlo, estudiarlo,
modificarlo y compartirlo; si distribuyes una versión modificada, debes publicar su código
bajo la misma licencia.

El nombre **Geli**, **Geli-VD** y su logo son de su autor. Si haces tu propia versión,
usa otro nombre y logo.

## Créditos

Construido sobre [yt-dlp](https://github.com/yt-dlp/yt-dlp) (Unlicense),
[FFmpeg](https://ffmpeg.org) (LGPL/GPL), [Deno](https://deno.com) (MIT),
[Pillow](https://python-pillow.org) (MIT-CMU) y
[Playwright](https://playwright.dev) (Apache-2.0).
