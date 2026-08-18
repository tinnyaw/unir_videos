# 🎬 Unificador Inteligente de Vídeos con Selección de Lienzo Dominante

Herramienta de automatización en Python 3 para el ecosistema Linux (Linux Mint Cinnamon, Ubuntu Server y Ubuntu Studio). Automatiza la inspección, re-escalado, normalización y concatenación de vídeos utilizando `ffmpeg` y `ffprobe`, ajustándose automáticamente al entorno gráfico (GUI) o de consola (CLI).

---

## 📌 Características Principales

* **Selección Automática de Lienzo Dominante:**
  * Prioriza orientación horizontal ($W \ge H$).
  * Selecciona la mayor resolución entre los clips procesados.
  * Preserva la relación de aspecto original con relleno (*padding*) si hay discrepancias de resolución o formato.
* **Procesamiento Híbrido Optimizado:**
  * **Stream Copy (Sin Pérdida):** Si los códecs, resoluciones y orientaciones coinciden, unifica en segundos sin re-codificar.
  * **Grafo Complejo (Transcodificación):** Aplica normalización de tasa de fotogramas (30 fps), resolución, formato de audio (Stereo FLTP / AAC) y sintetiza audio nulo (`anullsrc`) para clips silenciosos.
* **Detección Dinámica TTY / GUI:**
  * **Modo CLI:** Salida limpia en terminal para servidores y scripts en segundo plano.
  * **Modo GUI:** Integración con administradores de archivos (ej. Nemo) mediante ventanas modales (`zenity`) y notificaciones flotantes pasivas (`notify-send`).
* **Seguridad y Cero Dependencias PIP:** Construido utilizando exclusivamente la librería estándar de Python (`subprocess`, `json`, `pathlib`, `tempfile`, `shutil`).

---

## 🛠️ Requisitos e Instalación

### 1. Dependencias del Sistema
El script requiere los binarios multimedia y de interfaz estándar de Debian/Ubuntu:

```bash
sudo apt update
sudo apt install -y ffmpeg libnotify-bin zenity
```

### 2. Instalación y Permisos de Grupo

Para compartir la herramienta entre múltiples usuarios del mismo equipo (ej. un grupo `multimedia` o `sudo`) siguiendo el principio de mínimos privilegios:

```bash
# 1. Copiar el script a una ruta global del PATH
sudo cp video_unifier.py /usr/local/bin/video_unifier
sudo chmod 755 /usr/local/bin/video_unifier

# 2. (Opcional) Asignar grupo compartido para mantenimiento
sudo chown root:multimedia /usr/local/bin/video_unifier
sudo chmod 775 /usr/local/bin/video_unifier

```

---

## 🚀 Modos de Uso

### Desde la Terminal (CLI)

Pasa entre 2 y 10 rutas de vídeo como argumentos:

```bash
video_unifier /ruta/al/video1.mp4 /ruta/al/video2.mp4

```

### Integración con Nemo / Linux Mint (GUI)

Para añadir la acción al menú contextual de Nemo (clic derecho sobre vídeos seleccionados):

1. Crear el archivo de acción:

```bash
nano ~/.local/share/nemo/actions/unificar_videos.nemo_action

```

2. Añadir la siguiente configuración:

```ini
[Nemo Action]
Active=true
Name=Unificar vídeos seleccionados
Comment=Unifica y re-escala inteligentemente de 2 a 10 vídeos
Exec=/usr/local/bin/video_unifier %F
Icon-Name=video-x-generic
Selection=s
Extensions=mp4;mkv;avi;mov;
Quote=double

```

---

## 📐 Arquitectura del Script

```
                       ┌────────────────────────┐
                       │  Entrada: 2-10 Vídeos  │
                       └───────────┬────────────┘
                                   │
                         ffprobe (Metadatos)
                                   │
            ┌──────────────────────┴──────────────────────┐
            ▼                                             ▼
  ¿Códecs/Resolución/Rotación                    Discrepancias detectadas
         Idénticos?                                (o rotaciones SideData)
            │                                             │
            ▼                                             ▼
  [Modo Stream Copy]                            [Modo Transcodificación]
 ffmpeg -f concat -c copy                      Construcción de filter_complex
 (Rápido, sin pérdida)                         (Scale, Pad, FPS=30, AAC 44.1k)
            │                                             │
            └──────────────────────┬──────────────────────┘
                                   │
                        Notificación GUI/Terminal

```

---

## 🧪 Pruebas de Humo (Smoke Tests)

Antes de desplegar en producción, verifica la compatibilidad de dependencias sin alterar archivos reales:

### 1. Verificar Binarios del Sistema

```bash
python3 -c "import shutil; print({tool: shutil.which(tool) for tool in ['ffmpeg', 'ffprobe', 'zenity', 'notify-send']})"

```

### 2. Prueba de Humo en Modo Transcodificación (Archivos Temporales Synthetic)

```bash
# Generar dos vídeos sintéticos de prueba con diferentes resoluciones
ffmpeg -f lavfi -i testsrc=duration=3:size=1280x720:rate=30 /tmp/test1.mp4 -y
ffmpeg -f lavfi -i testsrc=duration=3:size=1920x1080:rate=30 /tmp/test2.mp4 -y

# Ejecutar el script en modo prueba
video_unifier /tmp/test1.mp4 /tmp/test2.mp4

# Limpiar entorno
rm /tmp/test1.mp4 /tmp/test2.mp4 /tmp/*_unificado.mp4

```

---

## 🧪 Batería de Pruebas Unitarias y de Integración

Crea un archivo `test_video_unifier.py` para ejecutar los tests automatizados mediante `pytest` o `unittest`:

```python
#!/usr/bin/env python3
import unittest
import pathlib
from video_unifier import calcular_lienzo_dominante

class TestVideoUnifier(unittest.TestCase):

    def test_calcular_lienzo_dominante_prioriza_horizontal(self):
        """Verifica que se elija la mayor resolución horizontal frente a una vertical de mayor área."""
        metadatos = [
            {"eff_w": 1080, "eff_h": 1920, "archivo": "vertical_4k.mp4"}, # Vertical
            {"eff_w": 1280, "eff_h": 720,  "archivo": "horizontal_720.mp4"}, # Horizontal
            {"eff_w": 1920, "eff_h": 1080, "archivo": "horizontal_1080.mp4"} # Horizontal Máximo
        ]
        w, h = calcular_lienzo_dominante(metadatos)
        self.assertEqual((w, h), (1920, 1080))

    def test_calcular_lienzo_dominante_fallback_vertical(self):
        """Verifica que si TODOS son verticales, elija la mayor resolución disponible."""
        metadatos = [
            {"eff_w": 720, "eff_h": 1280, "archivo": "vertical_720.mp4"},
            {"eff_w": 1080, "eff_h": 1920, "archivo": "vertical_1080.mp4"}
        ]
        w, h = calcular_lienzo_dominante(metadatos)
        self.assertEqual((w, h), (1080, 1920))

if __name__ == "__main__":
    unittest.main()

```

Para ejecutar las pruebas:

```bash
python3 -m unittest test_video_unifier.py

```

```

---

## 💡 TIP DE PROGRAMACIÓN PRO: Sanitización de Entradas en Scripts Gráficos y Subprocesos

Cuando integramos Python con administradores de archivos como Nemo, Dolphin o Nautilus, los nombres de archivos seleccionados por el usuario pueden contener espacios, comillas dobles, comillas simples o caracteres especiales UTF-8. 

1. **Inyección de Comandos (Shell Injection):**  
   Nunca uses `shell=True` en `subprocess.run()` cuando proceses rutas de archivos provenientes del usuario. Pasa siempre los argumentos como una **lista de cadenas explicitas**:
   ```python
   # ❌ INSEGURO: Vulnerable a inyección de comandos si el archivo contiene ';' o '$(...)''
   subprocess.run(f"ffmpeg -i '{ruta}' salida.mp4", shell=True)

   # ✅ SEGURO: Subprocess pasa los argumentos directamente a la llamada al sistema execve()
   subprocess.run(["ffmpeg", "-i", str(ruta), "salida.mp4"], check=True)

```

2. **Manejo de Rutas Orientado a Objetos (`pathlib`):**
Utiliza siempre `pathlib.Path` para resolver las rutas (`.resolve()`). Esto normaliza los enlaces simbólicos, elimina dobles barras diagonales y previene ataques de cruce de directorios (*directory traversal*).
