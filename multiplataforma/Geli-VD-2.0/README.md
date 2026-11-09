# Geli-VD 2.0 — GeliCorp

Descargador de video/audio de escritorio, en Python/PySide6 para Windows, macOS y Linux.

## Ejecutar desde el código fuente

- **Windows**: `iniciar_windows.bat`
- **macOS**: `bash iniciar_mac.command` (o `chmod +x iniciar_mac.command && ./iniciar_mac.command`)
- **Linux**: `bash iniciar_linux.sh`

Requiere Python 3.11–3.13 (64 bits), acceso a Internet para dependencias y FFmpeg accesible desde `PATH` para unir/convertir formatos. Algunas plataformas requieren Deno/EJS y un navegador independiente, que Geli-VD prepara cuando corresponde. macOS/Linux requieren dependencias gráficas de Qt y sistema X11/Wayland apropiado.

## Construir Windows

En **Windows 10/11 x64**, instala Python 3.11–3.13 x64 e [Inno Setup 6](https://jrsoftware.org/isinfo.php). Ejecuta `CONSTRUIR_WINDOWS.bat`.

El constructor instala dependencias para compilar y genera:
- `release/Geli-VD-2.0-Windows-Portable.zip`: carpeta con `Geli-VD.exe` y sus archivos, no es un solo EXE.
- `release/Geli-VD-2.0-Setup.exe`: instalador Windows, si Inno Setup 6 está disponible.

El proceso de construcción **necesita Windows**; aquí se entrega el código del constructor, no binarios Windows precompilados.

Para distribuir Windows sin requerir Python al usuario, se usa PyInstaller `--onedir`. Las actualizaciones y workers se ejecutan mediante `Geli-VD-Worker.exe`, incluido en el mismo directorio y con pip empaquetado. No borres ese archivo. **Debe validarse con una instalación limpia de Windows antes de una release pública.**

## Compatibilidad de contenido

Facebook Stories se reconoce antes de iniciar el extractor y se informa que **no es compatible en 2.0**. Facebook Reels y videos pueden funcionar, pero dependen de los extractores y permisos de cada plataforma. No se intenta eludir DRM ni los permisos del titular.

## Datos y privacidad

Los datos de usuario se mantienen fuera de la carpeta de la app: Windows `%APPDATA%\Geli-VD-1.8`; macOS/Linux `~/.geli-vd-1.8` por compatibilidad con las betas. **La instalación o actualización no debería borrar sesiones**. Las cookies aún no tienen cifrado propio y equivalen a credenciales: usar con precaución; no subir cookies a GitHub.

## Notas legales y publicación

Antes de publicar, el titular debe decidir y aportar una licencia para **su propio código**. Este paquete no inventa ni presupone licencia open-source. PySide6/Qt, FFmpeg y otros componentes tienen sus propias licencias y obligaciones, especialmente al redistribuir binarios. Revisar esos términos, añadir notices y confirmar el cumplimiento antes de subir el ejecutable. No se redistribuyen navegadores ni ejecutables de terceros dentro de este ZIP fuente.

Ver `docs/GUIA_PUBLICACION.md`.
