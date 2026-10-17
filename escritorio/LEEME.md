# Geli-VD py1.5

**Pega, descarga, listo.** Descargador de videos gratuito, sencillo y sin anuncios.
Parte del ecosistema Geli.

Esta es la **versión Python**: funciona en **macOS, Linux y Windows**. Es ideal si
quieres ver el código o modificarlo. Si usas Windows y solo quieres instalar y usar,
mejor descarga la versión **win1.5** (instalador `.exe`).

---

## Qué necesitas

| | macOS | Linux (Debian/Ubuntu) | Windows |
|---|---|---|---|
| **Python 3.10 o más nuevo** | [python.org](https://www.python.org/downloads/) o `brew install python python-tk` | `sudo apt install python3 python3-venv python3-tk` | [python.org](https://www.python.org/downloads/) (marca **"Add python.exe to PATH"**) |
| **ffmpeg** (unir audio y video, MP3) | `brew install ffmpeg` | `sudo apt install ffmpeg` | `winget install Gyan.FFmpeg` |

Las librerías de Python (yt-dlp, Pillow, deno…) **se instalan solas** la primera vez que
abres la app con el lanzador. deno (necesario para YouTube) viene incluido ahí mismo.

---

## Cómo abrirla

1. Descomprime la carpeta donde quieras (por ejemplo, en Documentos).
2. Abre el lanzador de tu sistema:

| Sistema | Lanzador | Notas |
|---|---|---|
| **macOS** | `iniciar_mac.command` | La primera vez: **clic derecho → Abrir** (macOS bloquea archivos descargados de internet). |
| **Linux** | `iniciar_linux.sh` | En una terminal: `chmod +x iniciar_linux.sh && ./iniciar_linux.sh` |
| **Windows** | `iniciar_windows.bat` | Doble clic. Si Windows avisa, elige **Más información → Ejecutar de todas formas**. |

La primera vez tarda un par de minutos (prepara su entorno en la carpeta `.venv`).
Después abre en segundos.

> ¿Prefieres hacerlo a mano? `pip install -r requirements.txt` y luego
> `python3 descargador_video.py`.

---

## Cómo se usa

1. **Pega el enlace** del video (o usa el botón 📋). La portada y las calidades aparecen solas.
2. Elige **formato** (MP4, MP3 o M4A) y **calidad**.
3. Pulsa **⬇ Descargar**. El archivo queda en la carpeta de destino.

**Extras:**
- **Si un video pide iniciar sesión**, Geli-VD te pregunta de dónde tomarla y reintenta solo.
  La lista **Cookies de** muestra solo los navegadores que tienes instalados.
- **Cookies de:** para sitios que piden iniciar sesión (Instagram, videos privados, o si
  YouTube dice "confirma que no eres un bot"):
  - **Geli (mi sesión)** (recomendado, sobre todo en Windows): se abre una ventana, entras a
    tu cuenta y la cierras. La sesión queda guardada solo en tu equipo, protegida (en
    Windows, cifrada para tu usuario) y se cierra sola tras 30 días sin uso.
    Consejo: usa una cuenta secundaria para descargar.
    También en **Herramientas → Iniciar sesión**.
  - **Tu navegador** (Safari, Chrome, Firefox…): en Mac y Linux funciona con cualquiera. En
    **Windows solo Firefox**, porque Chrome y Edge protegen sus cookies.
  - **archivo cookies.txt…**: un archivo exportado con una extensión como
    "Get cookies.txt LOCALLY".
- **Lista / carrusel completo:** baja todos los videos de una lista o carrusel.
- **🎵 Video → MP3:** convierte videos que ya tienes en tu equipo.
- **Historial:** doble clic abre el video; clic derecho tiene más opciones. Se puede
  borrar o desactivar (modo privado).
- **Herramientas → Apariencia:** tema claro, oscuro o según el sistema.

## ⟳ Actualizar motor

Los sitios de video cambian seguido y a veces una descarga que antes funcionaba deja
de hacerlo. El botón **⟳ Actualizar motor** (arriba, junto a la versión) actualiza
solo el **motor de descargas** (yt-dlp), sin reinstalar nada. La app revisa al abrir
si hay uno nuevo y, si lo hay, el botón se pinta de morado. Después de actualizar,
la app se reabre sola con un clic.

---

## Privacidad

Geli-VD funciona solo en tu equipo: no envía datos a ningún servidor propio. Guarda tus
preferencias e historial en:

- macOS / Linux: `~/.geli-videodownloader/`
- Windows: `%APPDATA%\Geli-VideoDownloader\`

Puedes borrarlo todo desde **Historial → Borrar todos los datos de la app**.

## Uso responsable

Descarga solo contenido propio, de libre uso o con permiso de su autor, respetando las
condiciones de cada sitio. Los videos con DRM no se pueden descargar.

## Problemas comunes

| Mensaje | Solución |
|---|---|
| "Sign in to confirm you're not a bot" | En **Cookies de** elige **Geli (mi sesión)** e inicia sesión en tu cuenta de YouTube. |
| "Failed to decrypt with DPAPI" / "Could not copy Chrome cookie database" | Es Chrome/Edge en Windows. Usa **Geli (mi sesión)** o Firefox. |
| "No se encontró ffmpeg" | Instálalo con el comando de la tabla de arriba y vuelve a abrir la app. |
| Un sitio que funcionaba dejó de descargar | Pulsa **⟳ Actualizar motor**. |
| macOS: "no se puede abrir porque es de un desarrollador no identificado" | Clic derecho sobre el lanzador → **Abrir**. |
| Falta tkinter | macOS (Homebrew): `brew install python-tk` · Linux: `sudo apt install python3-tk` |

---

## Créditos

Geli-VD usa [yt-dlp](https://github.com/yt-dlp/yt-dlp) (Unlicense),
[FFmpeg](https://ffmpeg.org) (LGPL/GPL), [deno](https://deno.com) (MIT) y
[Pillow](https://python-pillow.org) (MIT-CMU).

El nombre **Geli** y su logo son de su autor. Si haces tu propia versión a partir de este
código, usa otro nombre y logo.
