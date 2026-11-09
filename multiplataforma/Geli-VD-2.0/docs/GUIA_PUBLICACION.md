# Guía de publicación de Geli-VD 2.0

1. Probar `iniciar_windows.bat`, `iniciar_mac.command` y `iniciar_linux.sh` donde corresponda.
2. En Windows con Inno Setup 6 ejecutar `CONSTRUIR_WINDOWS.bat`; esperar ambos artefactos en `release/`.
3. Probar el portable **sin Python instalado**, incluyendo la instalación de un motor alternativo, el Setup y la instalación/desinstalación con cuentas de prueba; probar actualización de motor, Deno, YouTube autenticado, TikTok, Instagram, Facebook y cancelación.
4. Confirmar que Facebook Stories muestra «no compatible», **sin pedir inicio de sesión**.
5. Verificar cookies no borradas tras actualizar; **no publicar archivos de cookies**, perfiles Firefox/Chromium, registros privados ni `.venv`.
6. Preparar LICENSE de código propio y avisos de licencias de terceros para PySide6 (LGPL/comercial y requisitos de Qt), yt-dlp, FFmpeg y dependencias. No se presupone licencia de GeliCorp.
7. Crear release/tag `v2.0.0` en GitHub e incluir `Setup.exe`, `Portable.zip`, el ZIP de código fuente multiplataforma y checksum SHA256.
8. No incluir carpetas `release/`, `.venv/`, `dist/`, `build` generado, `*.spec`, `__pycache__/`, `sessions/`, `cookies*.txt`, ni perfiles.

**Importante:** este paquete contiene recetas para crear los binarios; el compilado solo se verifica al ejecutarlo en Windows. Los motores alternativos empaquetados requieren pruebas de extracción reales en instalaciones limpias.
