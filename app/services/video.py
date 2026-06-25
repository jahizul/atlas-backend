"""
Servicio de corte de video usando FFmpeg.
Instalar: pip install ffmpeg-python
Sistema: sudo apt install ffmpeg (o brew install ffmpeg en Mac)
"""
import asyncio
import os
from pathlib import Path


async def get_duration(video_path: str) -> float:
    """Obtiene la duración del video en segundos."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _get_duration, video_path)


async def cut_reels(
    video_path: str,
    output_dir: str,
    segments: list[dict],
) -> list[str]:
    """
    Corta el video en clips para reels.
    Devuelve lista de paths a los archivos generados.

    segments: [{"start": 0.0, "end": 30.0}, ...]
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, _cut_reels_sync, video_path, output_dir, segments
    )


async def extract_frame(video_path: str, timestamp: float, output_path: str) -> str:
    """Extrae un frame del video en el timestamp dado (segundos)."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, _extract_frame_sync, video_path, timestamp, output_path
    )


def _get_duration(video_path: str) -> float:
    try:
        import ffmpeg
        probe = ffmpeg.probe(video_path)
        return float(probe["format"]["duration"])
    except Exception:
        return 60.0  # fallback


def _cut_reels_sync(
    video_path: str, output_dir: str, segments: list[dict]
) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    outputs = []

    try:
        import ffmpeg

        for i, seg in enumerate(segments):
            out_path = os.path.join(output_dir, f"reel_{i+1}.mp4")
            duration = seg["end"] - seg["start"]
            (
                ffmpeg
                .input(video_path, ss=seg["start"], t=duration)
                .output(
                    out_path,
                    vcodec="libx264",
                    acodec="aac",
                    vf="scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
                    preset="fast",
                    crf=23,
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            outputs.append(out_path)

    except ImportError:
        # ffmpeg-python no instalado: crear archivos stub
        for i, seg in enumerate(segments):
            out_path = os.path.join(output_dir, f"reel_{i+1}.mp4")
            Path(out_path).write_text(f"[stub reel {i+1}]")
            outputs.append(out_path)

    return outputs


def _extract_frame_sync(video_path: str, timestamp: float, output_path: str) -> str:
    try:
        import ffmpeg
        (
            ffmpeg
            .input(video_path, ss=timestamp)
            .output(output_path, vframes=1, format="image2")
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ImportError:
        # stub: crear imagen placeholder
        Path(output_path).write_bytes(b"PNG_STUB")

    return output_path


def pick_reel_segments(duration: float) -> list[dict]:
    """
    Estrategia simple para elegir segmentos para reels:
    - Reel 1: primeros 30 segundos (el hook)
    - Reel 2: 60 segundos del centro del video
    En producción: usar análisis de audio/visión para detectar momentos clave.
    """
    segments = []

    if duration >= 30:
        segments.append({"start": 0.0, "end": 30.0, "label": "30s"})

    mid = duration / 2
    if duration >= mid + 60:
        segments.append({"start": mid, "end": mid + 60.0, "label": "60s"})
    elif duration >= 60:
        segments.append({"start": 0.0, "end": 60.0, "label": "60s"})

    return segments
