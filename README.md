# 🎬 Concatenador Inteligente de Vídeo con Preservación de Metadatos

Un script interactivo en Bash diseñado para entornos Linux (**Ubuntu Studio**, **Linux Mint**, **Ubuntu Server**) que permite unificar múltiples archivos de vídeo de forma secuencial sin pérdida de calidad y clonando los metadatos internos del archivo original.

## 🚀 Características
* ⚡ **Unión ultra rápida:** Utiliza el modo `stream copy` de FFmpeg (sin renderizado ni pérdida de calidad).
* 🛡️ **Validación estricta:** Comprueba de forma automática que los contenedores y códecs de audio/vídeo sean idénticos antes de operar.
* 📅 **Nombrado Cronológico:** Nombra el archivo final automáticamente usando la fecha de creación original (`YYYYMMDDTHHMMSS_fichero_combinado.mp4`).
* 🧠 **Preservación Forense:** Clona las etiquetas y metadatos internos (`creation_time`) del primer fragmento en el archivo final.

## 🛠️ Requisitos
El script depende de herramientas estándar del ecosistema multimedia de Linux:
* `ffmpeg` y `ffprobe`
* `jq` (para el procesamiento de metadatos en formato JSON)

Para instalarlos en sistemas basados en Debian/Ubuntu:
```bash
sudo apt update && sudo apt install -y ffmpeg jq
```

## 📖 Modo de Uso
Pasa los vídeos que deseas unir en orden cronológico como argumentos del comando:

unir_videos_avanzado.sh parte1.mp4 parte2.mp4 parte3.mp4

---

## 🧪 Plan de Pruebas (Control de Calidad)
Para garantizar la robustez del script en tu entorno local antes de procesar archivos críticos, puedes ejecutar el siguiente banco de pruebas de caja negra:

### 1. Validación de Argumentos
* **Acción:** Ejecuta el script sin parámetros o con un solo archivo: `unir_videos_avanzado.sh`
* **Resultado esperado:** El script debe abortar inmediatamente mostrando el uso correcto del comando y devolviendo un código de salida `1`.

### 2. Prueba de Éxito Estándar (Camino Feliz)
* **Acción:** Une dos archivos `.mp4` legítimos y secuenciales de la misma cámara.
* **Resultado esperado:** El proceso debe completarse en pocos segundos, la terminal permanecerá limpia de logs de progreso y se generará el archivo unificado.

### 3. Verificación de Formato y Nombrado
* **Acción:** Revisa el nombre del archivo generado en la prueba anterior.
* **Resultado esperado:** El nombre debe seguir estrictamente el patrón cronológico extraído de la cabecera interna (ej. `20260525T153012_fichero_combinado.mp4`).

### 4. Auditoría de Metadatos Internos
* **Acción:** Analiza el archivo final con `ffprobe` para buscar la etiqueta de tiempo original:
  ffprobe -v error -select_streams v:0 -show_entries stream_tags=creation_time -of default=noprint_wrappers=1:nokey=1 archivo_final.mp4
* **Resultado esperado:** La terminal debe devolver la fecha y hora exactas del primer vídeo, demostrando que el bloque de metadatos no se ha inicializado con la fecha de hoy.

### 5. Control de Incompatibilidad (Fallo Seguro)
* **Acción:** Intenta unir un vídeo de tu cámara con un archivo de formato o códec diferente (ej. un `.mkv` o un `.mp3`).
* **Resultado esperado:** El script debe lanzar el aviso `⛔ ERROR DE COMPATIBILIDAD`, detallar qué parámetros difieren y cerrarse de forma segura sin generar ningún archivo de salida corrupto.

---

## ⚖️ Licencia
Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.



