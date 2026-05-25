#!/bin/bash

# 1. Validación de argumentos de entrada. Si el número de argumentos es menor que 2...
if [ "$#" -lt 2 ]; then
    echo "❌ Error: Se necesitan al menos 2 archivos de vídeo para unirlos."
    echo "Uso: $0 video1.mp4 video2.mp4 [video3.mp4 ...]"
    exit 1
fi

# 2. Extracción de telemetría del PRIMER archivo (Referencia)
PRIMER_VIDEO="$1"
if [ ! -f "$PRIMER_VIDEO" ]; then
    echo "❌ Error: El archivo '$PRIMER_VIDEO' no existe."
    exit 1
fi

echo "🔍 Analizando formatos de referencia en '$PRIMER_VIDEO'..."
FORMATO_REF=$(ffprobe -v error -select_streams v:0 -show_entries format=format_name -of json "$PRIMER_VIDEO" | jq -r '.format.format_name')
CODEC_V_REF=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of json "$PRIMER_VIDEO" | jq -r '.streams[0].codec_name')
CODEC_A_REF=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of json "$PRIMER_VIDEO" | jq -r '.streams[0].codec_name')

# Determinar extensión de salida según el formato contenedor real
EXT_SALIDA="${PRIMER_VIDEO##*.}"
VIDEO_SALIDA="video_combinado.$EXT_SALIDA"
LISTA_TMP="lista_temporal.txt"
> "$LISTA_TMP"

echo "📊 Formato objetivo: $FORMATO_REF | Vídeo: $CODEC_V_REF | Audio: $CODEC_A_REF"
echo "------------------------------------------------------------"

# 3. Bucle de validación estricta para el resto de archivos
for video in "$@"; do
    if [ ! -f "$video" ]; then
        echo "❌ Error: El archivo '$video' no existe."
        rm -f "$LISTA_TMP"
        exit 1
    fi

    # Extraer datos del archivo actual
    FORMATO_ACTUAL=$(ffprobe -v error -select_streams v:0 -show_entries format=format_name -of json "$video" | jq -r '.format.format_name')
    CODEC_V_ACTUAL=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of json "$video" | jq -r '.streams[0].codec_name')
    CODEC_A_ACTUAL=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of json "$video" | jq -r '.streams[0].codec_name')

    # Validar consistencia técnica
    if [ "$FORMATO_REF" != "$FORMATO_ACTUAL" ] || [ "$CODEC_V_REF" != "$CODEC_V_ACTUAL" ] || [ "$CODEC_A_REF" != "$CODEC_A_ACTUAL" ]; then
        echo "⛔ ERROR DE COMPATIBILIDAD en '$video':"
        echo "   Esperado: Contenedor [$FORMATO_REF], Vídeo [$CODEC_V_REF], Audio [$CODEC_A_REF]"
        echo "   Detectado: Contenedor [$FORMATO_ACTUAL], Vídeo [$CODEC_V_ACTUAL], Audio [$CODEC_A_ACTUAL]"
        echo "❌ Operación cancelada de forma segura para evitar corrupción de datos."
        rm -f "$LISTA_TMP"
        exit 1
    fi

    echo "file '$video'" >> "$LISTA_TMP"
done


echo "✅ Todos los archivos son compatibles estructuralmente."
echo "🎬 Fusionando y clonando metadatos internos en '$VIDEO_SALIDA'..."

# 4. Concatenación segura con mapeo explícito de metadatos globales y de flujo
ffmpeg -v error -f concat -safe 0 -i "$LISTA_TMP" -c copy -map_metadata 0 -map_metadata:s:v 0:s:v -map_metadata:s:a 0:s:a "$VIDEO_SALIDA"

if [ $? -eq 0 ]; then
    echo "------------------------------------------------------------"
    echo "✅ Proceso completado con éxito."
    echo "🛡️ Metadatos internos de '$PRIMER_VIDEO' inyectados en '$VIDEO_SALIDA'."
else
    echo "❌ Ocurrió un error durante la fusión con FFmpeg."
    rm -f "$LISTA_TMP"
    exit 1
fi

