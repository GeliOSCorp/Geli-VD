# Geli-VD 1.5.1 — corrección de autorización de Dailymotion

**Preparación para pruebas; instalador Windows todavía pendiente.**

## Problema corregido

Dailymotion puede conservar un encabezado de autorización dentro del extractor durante toda la ejecución. Cambiar «Cookies de» a «(ninguno)» crea una nueva instancia de YoutubeDL, pero no necesariamente limpia ese estado de clase. Así, una autorización rechazada puede seguir causando HTTP 401 aunque ya se haya elegido no usar sesión. En la prueba del usuario, cerrar y abrir Geli sin sesión permitió analizar de nuevo el mismo enlace.

## Comportamiento en 1.5.1

- Renueva la autorización en memoria antes de cada operación directa de Dailymotion, tanto análisis como descarga; también admite enlaces dai.ly.
- Si Dailymotion devuelve específicamente HTTP 401 al consultar la metadata JSON, reintenta **una sola vez** sin la sesión para ese enlace e informa en el registro que está renovando la conexión.
- Conserva las preferencias de cookies del usuario, las sesiones guardadas y las opciones de formato/calidad. No borra datos para arreglar el error.
- Los errores de manifiesto/transferencia, DRM, video privado y otras plataformas no activan ese reintento. Si el segundo intento falla, se informa el error; no hay bucle de reintentos.
- Se conserva el mecanismo anterior para fallos al leer cookies de navegador.
- La carpeta interna de datos sigue siendo Geli-VideoDownloader, para conservar preferencias, historial y sesiones.

## Validación

11 pruebas automatizadas aprobadas con Python 3.12 y el extractor real de yt-dlp 2026.10.26. Se simularon las respuestas de extracción para comprobar token compartido entre instancias, cambio de sesión a ninguno, reintento único, opciones y archivos de sesión conservados, errores que no deben reintentarse y ausencia de efectos en otras plataformas. No se descargaron videos en estas pruebas.

El intento real de consultar el enlace público desde el entorno de preparación se documenta aparte; no sustituye la prueba en Windows/red del usuario. La captura del usuario acredita que el reinicio sin sesión resolvió el caso anterior, pero no valida por sí misma el parche nuevo.

## Prueba antes de publicar

1. Ejecutar esta versión Python o recompilar el .exe con el kit Windows original, usando este descargador_video.py.
2. Analizar el enlace de Dailymotion con «Geli (mi sesión)», cambiar a «(ninguno)» y volver a analizar SIN cerrar Geli. Comprobar que se recupera cuando el fallo es la autorización retenida.
3. Probar análisis y descarga completos de un video autorizado, además de YouTube y las otras funciones habituales.
4. Verificar que historial, preferencias y sesiones anteriores siguen disponibles.
5. Ajustar a 1.5.1 los nombres/versiones del instalador en el kit privado antes de compilar/publicar. Ese kit no está en el repositorio y no se ha modificado desde aquí.

La release pública 1.5 y sus ejecutables siguen sin cambios hasta compilar y validar la actualización.
