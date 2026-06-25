"""
Servicio de transcripción usando OpenAI Whisper (local, gratis).
Instalar: pip install openai-whisper ffmpeg-python
"""
import asyncio
from pathlib import Path


async def transcribe(video_path: str) -> dict:
    """
    Transcribe el audio del video y devuelve:
    {
        "text": "...",          # transcripción completa
        "segments": [           # segmentos con timestamps
            {"start": 0.0, "end": 3.2, "text": "Hola, hoy vamos a..."},
            ...
        ],
        "language": "es"
    }
    """
    # Whisper es bloqueante, lo ejecutamos en un thread pool
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, _run_whisper, video_path)
    return result


def _run_whisper(video_path: str) -> dict:
    try:
        import whisper

        model = whisper.load_model("base")  # opciones: tiny, base, small, medium, large
        result = model.transcribe(video_path, fp16=False)

        return {
            "text": result["text"].strip(),
            "segments": [
                {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
                for s in result.get("segments", [])
            ],
            "language": result.get("language", "es"),
        }
    except ImportError:
        # Whisper no instalado: devuelve stub para desarrollo
        return _stub_transcription(video_path)


def _stub_transcription(video_path: str) -> dict:
    """Respuesta simulada para cuando Whisper no está instalado."""
    return {
        "text": (
            "En este video aprenderás las tres claves para hacer crecer tu negocio "
            "en redes sociales. Primero, consistencia. Segundo, valor real. "
            "Tercero, comunidad genuina. ¡Empieza hoy!"
        ),
        "segments": [
            {"start": 0.0,  "end": 4.0,  "text": "En este video aprenderás las tres claves"},
            {"start": 4.0,  "end": 9.0,  "text": "para hacer crecer tu negocio en redes sociales."},
            {"start": 9.0,  "end": 14.0, "text": "Primero, consistencia. Segundo, valor real."},
            {"start": 14.0, "end": 20.0, "text": "Tercero, comunidad genuina. ¡Empieza hoy!"},
        ],
        "language": "es",
    }
