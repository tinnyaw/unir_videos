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

## 📖 Modo de uso
```
unir_videos_avanzado.sh parte1.mp4 parte2.mp4 parte3.mp4
```
