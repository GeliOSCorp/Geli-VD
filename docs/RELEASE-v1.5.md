Descarga videos y audio de YouTube, Vimeo, Dailymotion, TikTok y otros sitios compatibles.
Gratis y sin anuncios. **Pega, descarga, listo.**

[**⬇ Descargar para Windows 10/11 — recomendado (141 MB)**](https://github.com/GeliOSCorp/Geli-VD/releases/download/v1.5/Geli-VD-Setup-win1.5.exe)

**Windows:** instalador y portable · **macOS / Linux:** versión Python.

## Elige tu descarga

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

![Geli-VD 1.5 en funcionamiento](https://raw.githubusercontent.com/GeliOSCorp/Geli-VD/main/docs/captura.png)

## Instalar y empezar

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
2. Elige formato, calidad y carpeta de destino.
3. Pulsa **Descargar**. Algunos videos requieren iniciar sesión.

## Novedades de la 1.5

- **⟳ Actualizar motor:** actualiza el motor sin reinstalar. Puede resolver errores causados
  por cambios en los sitios; no garantiza que todos los videos se puedan descargar.
- La app ofrece iniciar sesión y reintentar cuando el sitio lo requiere.
- La sesión «Geli (mi sesión)» se guarda localmente y caduca tras 30 días sin uso.
  Windows utiliza DPAPI cuando está disponible; macOS/Linux usa permisos de archivo restringidos,
  sin cifrado. Si DPAPI falla en Windows, la sesión puede guardarse sin cifrar.
- Calidades con nombres estándar (480p, 720p, 1080p…) y tema claro u oscuro.

## Ayuda y uso responsable

[Guía completa](https://github.com/GeliOSCorp/Geli-VD/blob/main/escritorio/LEEME.md) ·
[Reportar un problema](https://github.com/GeliOSCorp/Geli-VD/issues/new)

Incluye tu sistema operativo, el paquete utilizado y el mensaje de error.
No publiques contraseñas, cookies ni enlaces privados.

Descarga solo contenido propio, de libre uso o con permiso de su autor.
**Los videos protegidos con DRM no se pueden descargar.**
