<div align="center">

<img src="escritorio/icono.png" width="96" alt="Geli-VD">

# Geli-VD

**Pega, descarga, listo.**
Descargador de videos gratuito, sencillo y sin anuncios. Parte del ecosistema **Geli**.

[**⬇ Descargar la última versión**](https://github.com/JuanVicente117/Geli-VD/releases/latest)

[![Descargas](https://img.shields.io/github/downloads/JuanVicente117/Geli-VD/total?label=descargas&color=6a4cf0)](https://github.com/JuanVicente117/Geli-VD/releases)
[![Versión](https://img.shields.io/github/v/release/JuanVicente117/Geli-VD?label=versi%C3%B3n&color=6a4cf0)](https://github.com/JuanVicente117/Geli-VD/releases/latest)
[![Licencia](https://img.shields.io/badge/licencia-GPL--3.0-6a4cf0)](LICENSE)

Windows · macOS · Linux — Android próximamente

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
  la sesión queda guardada cifrada solo en tu equipo y se cierra sola tras 30 días sin uso.
- Tema claro u oscuro según tu sistema.
- **Sin anuncios, sin instaladores con trampas, sin enviar tus datos a ningún lado.**

---

## Descargar e instalar

Entra a [**Releases**](https://github.com/JuanVicente117/Geli-VD/releases/latest) y elige:

| Archivo | Para quién |
|---|---|
| `Geli-VD-Setup-win1.5.exe` | **Windows 10/11** — instalador. No necesitas nada más. |
| `Geli-VD-win1.5-portable.zip` | Windows sin instalar: descomprime y abre `Geli-VD.exe`. |
| `Geli-VD-py1.5.zip` | **macOS, Linux** (y Windows) con Python — para curiosos y programadores. |

### Windows

1. Descarga y abre `Geli-VD-Setup-win1.5.exe`.
2. Windows puede mostrar **"Windows protegió su PC"**: elige **Más información →
   Ejecutar de todas formas**. Aparece porque el programa es nuevo y aún no está firmado
   digitalmente.
3. Sigue el instalador. No pide permisos de administrador.

Para actualizar, instala la versión nueva **encima**: no hace falta desinstalar y se
conservan tu historial y preferencias.

### macOS / Linux (versión Python)

1. Descarga y descomprime `Geli-VD-py1.5.zip`.
2. Instala **Python 3.10+** y **ffmpeg**:
   - macOS: `brew install python python-tk ffmpeg`
   - Debian/Ubuntu: `sudo apt install python3 python3-venv python3-tk ffmpeg`
3. Abre el lanzador:
   - macOS: `iniciar_mac.command` (la primera vez: **clic derecho → Abrir**)
   - Linux: `./iniciar_linux.sh`

La primera vez instala sus librerías solo (un par de minutos). Instrucciones completas en
[`escritorio/LEEME.md`](escritorio/LEEME.md).

---

## Problemas comunes

| Mensaje | Solución |
|---|---|
| "Sign in to confirm you're not a bot" | En **Cookies de** elige **Geli (mi sesión)** e inicia sesión en tu cuenta. |
| Windows: error de cookies de Chrome/Edge | Chrome y Edge protegen sus cookies en Windows. Usa **Geli (mi sesión)** o Firefox. |
| Un sitio que funcionaba dejó de descargar | Pulsa **⟳ Actualizar motor**. |
| Otro problema | Abre un [Issue](https://github.com/JuanVicente117/Geli-VD/issues) con una captura del mensaje. |

---

## Uso responsable

Geli-VD es una herramienta. Descarga solo contenido **propio, de libre uso o con permiso de
su autor**, respetando las condiciones de cada sitio y los derechos de autor. Los videos con
DRM no se pueden descargar.

## Privacidad

Geli-VD funciona solo en tu equipo: no tiene servidores ni recopila datos. Solo se conecta a
los sitios de los videos que pegas y, para "Actualizar motor", a PyPI/GitHub para saber si
hay una versión nueva.

---

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
