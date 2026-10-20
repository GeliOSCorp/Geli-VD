# Geli-VD py1.5

**Pega, descarga, listo.** Descargador de videos gratuito, sencillo y sin anuncios.
Parte del ecosistema Geli.

Esta es la **versión Python** para macOS, Linux y Windows. Requiere Python 3.10+,
Tkinter y FFmpeg. Si usas Windows y quieres empezar sin preparar Python,
[descarga el instalador recomendado](https://github.com/GeliOSCorp/Geli-VD/releases/download/v1.5/Geli-VD-Setup-win1.5.exe).

---

## Preparación en macOS y Linux

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

## Preparación en Windows con Python

1. Instala [Python 3.10 o posterior](https://www.python.org/downloads/) con Tkinter y marca
   **Add python.exe to PATH**.
2. Instala FFmpeg: `winget install Gyan.FFmpeg`. Vuelve a abrir la terminal después de instalarlo.
3. Extrae todo el ZIP y abre `iniciar_windows.bat` con doble clic desde la carpeta extraída.
4. Mantén Internet disponible durante el primer inicio para instalar las dependencias en `.venv`.

Las dependencias del lanzador incluyen el paquete Deno, utilizado por el motor para YouTube.
Si la preparación falla, conserva el mensaje de error para solicitar ayuda.

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
    tu cuenta y la cierras. La sesión se guarda localmente y caduca tras 30 días sin uso.
    En Windows se cifra con DPAPI cuando está disponible; si falla, puede guardarse sin cifrar.
    En macOS/Linux utiliza un archivo sin cifrar con permisos restringidos al usuario.
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
la app se reabre sola con un clic. Actualizar puede resolver errores por cambios de los sitios,
pero no garantiza el acceso a todos los videos ni permite descargar contenido con DRM.

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
| macOS bloquea el lanzador | Verifica que descargaste el paquete oficial y revisa las opciones que ofrece el aviso de seguridad del sistema. |
| Falta tkinter | macOS (Homebrew): `brew install python-tk` · Linux: `sudo apt install python3-tk` |

---

## Créditos

Geli-VD usa [yt-dlp](https://github.com/yt-dlp/yt-dlp) (Unlicense),
[FFmpeg](https://ffmpeg.org) (LGPL/GPL), [deno](https://deno.com) (MIT) y
[Pillow](https://python-pillow.org) (MIT-CMU).

El nombre **Geli** y su logo son de su autor. Si haces tu propia versión a partir de este
código, usa otro nombre y logo.
