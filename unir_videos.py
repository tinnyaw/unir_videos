#!/usr/bin/env python3
"""
Unificador Inteligente de Vídeos con Selección de Lienzo Dominante.
Prioriza orientación horizontal y máxima resolución disponible.

Notificación Pasiva (notify-send): Se usa para avisos informativos, inicio/fin de procesos en segundo plano o errores leves donde el usuario no necesita hacer clic ni validar nada.
Diálogo Activo (zenity): Se usa para confirmaciones obligatorias (ej. "¿Desea eliminar 20 archivos?") o para informes finales de resumen estructurados que requieren que el usuario lea y presione "Aceptar".
"""

# Importación de librerías estándar del sistema (sin dependencias externas pip)
import json        # Parseo de salida JSON de ffprobe
import os          # Operaciones con el sistema de archivos
import pathlib     # Manejo de rutas orientadas a objetos
import re          # Formateo y limpieza de fechas
import subprocess  # Subprocesos seguros para ejecutar ffprobe, ffmpeg y notify-send
import sys         # Argumentos del sistema y códigos de salida
import tempfile    # Gestión de archivos temporales seguros
import shutil      # Módulo nativo para verificar la presencia de binarios en el PATH del sistema (zenity, notify-send)


def is_gui_mode():
    """Detecta si el script fue lanzado desde la GUI o sin terminal interactiva."""
    """Determina dinámicamente si hay un canal de entrada interactivo de consola. Si devuelve False, el script sabe automáticamente que fue invocado por un gestor de archivos (GUI) y que debe usar zenity"""
    return not sys.stdin.isatty()

def notificar_pasivo(titulo: str, mensaje: str, nivel: str = "info", icono_personalizado: str = None) -> None:
    """
    Envía una notificación flotante no bloqueante usando notify-send.
    Ideal para acciones de Nemo o tareas de segundo plano.

    Ejemplo de uso: notificar_pasivo("Proceso Iniciado", "Analizando archivos...", nivel="info", icono_personalizado="video-x-generic")
    """
    if not is_gui_mode():
        # Salida por consola formateada si hay TTY
        print(f"[{nivel.upper()}] {titulo}: {mensaje}")
        return

    # Mapeo estandarizado de niveles a iconos y urgencias
    mapa_niveles = {
        "info": ("low", icono_personalizado or "dialog-information"),
        "warning": ("normal", icono_personalizado or "dialog-warning"),
        "error": ("critical", icono_personalizado or "dialog-error")
    }
    
    urgencia, icono = mapa_niveles.get(nivel.lower(), ("normal", "dialog-information"))

    # Comprobación segura de existencia del binario: notify-send (paquete libnotify-bin)
    if shutil.which("notify-send"):
        res = subprocess.run([
            "notify-send", "-u", urgencia, "-i", icono, titulo, mensaje
        ], capture_output=True, text=True, check=False)
        
        # Fallback de seguridad: si notify-send falla (código != 0), recurrimos a zenity
        if res.returncode != 0 and shutil.which("zenity"):
            subprocess.run([
                "zenity", "--notification", f"--text={titulo}: {mensaje}"
            ], check=False)

def mostrar_informe_activo(titulo: str, texto_informe: str, es_error: bool = False) -> None:
    """
    Muestra una ventana modal bloqueante usando zenity.
    Ideal para resúmenes de proceso o errores críticos que requieren confirmación.

    Ejemplo de uso: mostrar_informe_activo("Resumen de Operación", "Se procesaron 5 archivos correctamente.\n0 errores detectados.")
    Ejemplo de uso: mostrar_informe_activo("Error", "Ha fallado ffprobe", True)
    """
    if not is_gui_mode():
        prefijo = "❌ ERROR" if es_error else "📋 INFORME"
        print(f"\n=== {prefijo}: {titulo} ===\n{texto_informe}\n")
        return

    # Comprobación segura de existencia del binario: zenity (paquete zenity)
    if shutil.which("zenity"):
        tipo_dialogo = "--error" if es_error else "--info"
        subprocess.run([
            "zenity",
            tipo_dialogo,
            f"--title={titulo}",
            f"--text={texto_informe}",
            "--width=450"
        ], check=False)
    else:
        # Fallback si zenity no está instalado en un entorno gráfico: intenta notify-send
        nivel_fallback = "error" if es_error else "info"
        notificar_pasivo(titulo, texto_informe, nivel=nivel_fallback)


def obtener_telemetria(ruta_video: pathlib.Path) -> dict:
    """Extrae metadatos de vídeo y audio usando ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "stream=codec_type,codec_name,width,height:stream_tags=creation_time:stream_side_data_list:format=format_name:format_tags=creation_time",
        "-of", "json",
        str(ruta_video)
    ]

    # Ejecución segura controlando captura de salida y errores de ejecución
    try:
        resultado = subprocess.run(cmd, capture_output=True, text=True, check=True) # Ejecuta ffprobe directamente mediante llamadas del sistema operativo sin invocar la Shell de Linux (shell=False)
        datos = json.loads(resultado.stdout)
    except subprocess.CalledProcessError as e:
        notificar_pasivo("❌ Error en FFprobe", f"Error al ejecutar ffprobe en {ruta_video.name}: {e.stderr}", nivel="error")
        # mostrar_informe_activo("❌ Error en FFprobe", f"Error al ejecutar ffprobe en {ruta_video.name}: {e.stderr}", True)
        sys.exit(1)
    except json.JSONDecodeError:
        notificar_pasivo("❌ Error en FFprobe", f"Respuesta JSON corrupta o inválida desde ffprobe para {ruta_video.name}", nivel="error")
        # mostrar_informe_activo("❌ Error en FFprobe", f"Respuesta JSON corrupta o inválida desde ffprobe para {ruta_video.name}", True)
        sys.exit(1)

    streams = datos.get("streams", [])
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    has_audio = any(s.get("codec_type") == "audio" for s in streams)

    if not v_stream:
        notificar_pasivo("❌ Formato Inválido", f"No se halló pista de vídeo en {ruta_video.name}", nivel="error")
        # mostrar_informe_activo("❌ Formato Inválido", f"No se halló pista de vídeo en {ruta_video.name}", True)
        sys.exit(1)

    
    # 1. Extracción de rotación (Side Data)
    rotacion = 0
    # En la estructura JSON devuelta por ffprobe, la clave se llama 'side_data_list'
    for side_data in v_stream.get("side_data_list", []):
        if "rotation" in side_data:
            rotacion = abs(int(side_data["rotation"]))

    w_raw = v_stream.get("width", 0)
    h_raw = v_stream.get("height", 0)

    # 2. Transposición de dimensiones si el vídeo fue grabado en vertical ($90^\circ$ o $270^\circ$)
    if rotacion in (90, 270):
        eff_w, eff_h = h_raw, w_raw
    else:
        eff_w, eff_h = w_raw, h_raw

    # 3. Estrategia de Fallback para la fecha de creación
    tags_stream = v_stream.get("tags", {})
    tags_format = datos.get("format", {}).get("tags", {})
    fecha = tags_stream.get("creation_time") or tags_format.get("creation_time")

    return {
        "archivo": ruta_video.name,
        "ruta": ruta_video,
        "width_raw": w_raw,
        "height_raw": h_raw,
        "eff_w": eff_w,
        "eff_h": eff_h,
        "codec": v_stream.get("codec_name"),
        "rotacion": rotacion,
        "has_audio": has_audio,
        "fecha_creacion": fecha
    }


def calcular_lienzo_dominante(metadatos: list[dict]) -> tuple[int, int]:
    """
    Selecciona la resolución objetivo basada en:
    1. Prioridad a vídeos horizontales (eff_w >= eff_h).
    2. Máxima resolución (área eff_w * eff_h).
    """
    horizontales = [m for m in metadatos if m["eff_w"] >= m["eff_h"]]
    if horizontales:
        objetivo = max(horizontales, key=lambda x: x["eff_w"] * x["eff_h"])
    else:
        objetivo = max(metadatos, key=lambda x: x["eff_w"] * x["eff_h"])
        
    return objetivo["eff_w"], objetivo["eff_h"]


def unificar_videos(archivos: list[str]) -> None:
    if not (2 <= len(archivos) <= 10):
        notificar_pasivo("⚠️ Operación Cancelada", "Selecciona al menos 2 vídeos y menos de 10.", nivel="warning")
        # mostrar_informe_activo("⚠️ Operación Cancelada", "Selecciona al menos 2 vídeos y menos de 10.")
        sys.exit(1)

    rutas = [pathlib.Path(f).resolve() for f in archivos] # Introduzco en la lista rutas, las rutas de los videos con que trabajar
    metadatos = [obtener_telemetria(r) for r in rutas] # Obtengo los metadatos de todos los vídeos (para determinar el lienzo, formato óptimo de vídeo, en el siguiente paso)
    
    # 1. Determinar el Lienzo Objetivo Dominante
    w_target, h_target = calcular_lienzo_dominante(metadatos)
    
    # 2. Evaluar si se requiere re-codificación mediante Grafo Complejo
    requiere_transcodificacion = False
    ref_codec = metadatos[0]["codec"]
    
    for m in metadatos:
        if (m["eff_w"] != w_target or 
            m["eff_h"] != h_target or 
            m["rotacion"] != 0 or 
            m["codec"] != ref_codec):
            requiere_transcodificacion = True
            break

    dir_padre = rutas[0].parent
    fecha_str = metadatos[0].get("fecha_creacion") or ""
    fecha_limpia = re.sub(r'[-:]', '', fecha_str).split('.')[0] if fecha_str else "combinado"
    video_salida = dir_padre / f"{fecha_limpia}_unificado{rutas[0].suffix}"

    try:
        if not requiere_transcodificacion:
            notificar_pasivo("🎬 Procesando...", "Unión rápida (Stream Copy)...", nivel="info", icono_personalizado="video-x-generic")
            # mostrar_informe_activo("🎬 Procesando...", "Unión rápida (Stream Copy)...")
            
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as tmp:
                for r in rutas:
                    tmp.write(f"file '{str(r)}'\n")
                ruta_tmp = tmp.name

            # Ejecución del binario externo del sistema: ffmpeg (paquete ffmpeg)
            cmd_ffmpeg = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", ruta_tmp, "-c", "copy", str(video_salida)
            ]
            subprocess.run(cmd_ffmpeg, check=True)
            if os.path.exists(ruta_tmp):
                os.remove(ruta_tmp)
        else:
            notificar_pasivo("⚙️ Re-escalando Vídeos", f"Normalizando lienzo a {w_target}x{h_target}...", nivel="info", icono_personalizado="video-x-generic")
            # mostrar_informe_activo("⚙️ Re-escalando Vídeos", f"Normalizando lienzo a {w_target}x{h_target}...")

            # Ejecución del binario externo del sistema: ffmpeg (paquete ffmpeg)
            cmd_ffmpeg = ["ffmpeg", "-y"]
            for m in metadatos:
                cmd_ffmpeg.extend(["-i", str(m["ruta"])])

            filter_inputs = []
            concat_v_a = []
            
            for i, m in enumerate(metadatos):
                filter_inputs.append(
                    f"[{i}:v]scale={w_target}:{h_target}:force_original_aspect_ratio=decrease,"
                    f"pad={w_target}:{h_target}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v{i}];"
                )
                if m["has_audio"]:
                    filter_inputs.append(
                        f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a{i}];"
                    )
                else:
                    filter_inputs.append(
                        f"anullsrc=channel_layout=stereo:sample_rate=44100[a{i}];"
                    )
                concat_v_a.append(f"[v{i}][a{i}]")

            filter_complex_str = (
                "".join(filter_inputs) +
                "".join(concat_v_a) +
                f"concat=n={len(metadatos)}:v=1:a=1[vOut][aOut]"
            )

            cmd_ffmpeg.extend([
                "-filter_complex", filter_complex_str,
                "-map", "[vOut]", "-map", "[aOut]",
                "-c:v", "libx264", "-preset", "ultrafast",
                "-c:a", "aac", str(video_salida)
            ])

            subprocess.run(cmd_ffmpeg, check=True)

        mostrar_informe_activo("✅ Proceso Completado", f"Guardado como:\n{video_salida.name}")

    except subprocess.CalledProcessError:
        notificar_pasivo("❌ Error en FFmpeg", "Fallo durante la concatenación de vídeos.", nivel="error")
        # mostrar_informe_activo("❌ Error en FFmpeg", "Fallo durante la concatenación de vídeos.", True)
        sys.exit(1)


if __name__ == "__main__":
    unificar_videos(sys.argv[1:])