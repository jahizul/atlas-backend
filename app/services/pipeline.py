"""
Pipeline principal: orquesta todas las tareas en orden.
Se ejecuta como BackgroundTask de FastAPI.
"""
import os
import json
import zipfile
from pathlib import Path

from app.models.store import (
    get_job,
    set_task_status,
    set_job_output,
    set_job_done,
    set_job_error,
)
from app.models.job import TaskStatus
from app.services import transcription, video, content


async def run_pipeline(job_id: str, video_path: str):
    """
    Ejecuta el pipeline completo para un job dado.
    Actualiza el estado en el store en tiempo real para que
    el endpoint SSE lo transmita al frontend.
    """
    output_dir = f"outputs/{job_id}"
    os.makedirs(output_dir, exist_ok=True)

    try:
        # ── 1. TRANSCRIPCIÓN ────────────────────────────────────────────
        await _run_task(job_id, "transcribe")
        transcript_result = await transcription.transcribe(video_path)
        transcript_path = f"{output_dir}/transcript.json"
        Path(transcript_path).write_text(
            json.dumps(transcript_result, ensure_ascii=False, indent=2)
        )
        await _done_task(job_id, "transcribe")

        # ── 2. ANÁLISIS DE MOMENTOS CLAVE ───────────────────────────────
        await _run_task(job_id, "analyze")
        duration = await video.get_duration(video_path)
        reel_segments = video.pick_reel_segments(duration)
        await _done_task(job_id, "analyze")

        # ── 3. CORTE DE REELS ───────────────────────────────────────────
        await _run_task(job_id, "reels")
        reels_dir = f"{output_dir}/reels"
        reel_paths = await video.cut_reels(video_path, reels_dir, reel_segments)
        set_job_output(job_id, "reels", [os.path.basename(p) for p in reel_paths])
        await _done_task(job_id, "reels")

        # ── 4. PORTADAS ─────────────────────────────────────────────────
        await _run_task(job_id, "covers")
        covers_dir = f"{output_dir}/covers"
        os.makedirs(covers_dir, exist_ok=True)
        cover_paths = []
        # Extraer frames en momentos clave
        for i, seg in enumerate(reel_segments[:4]):
            frame_ts = (seg["start"] + seg["end"]) / 2
            frame_path = f"{covers_dir}/cover_{i+1}.jpg"
            await video.extract_frame(video_path, frame_ts, frame_path)
            cover_paths.append(frame_path)
        set_job_output(job_id, "covers", [os.path.basename(p) for p in cover_paths])
        await _done_task(job_id, "covers")

        # ── 5–7. COPIES, CARRUSEL Y HASHTAGS (Claude API) ───────────────
        await _run_task(job_id, "carousel")
        generated = await content.generate_content(transcript_result["text"])

        # Guardar carrusel como JSON
        carousel_path = f"{output_dir}/carousel.json"
        Path(carousel_path).write_text(
            json.dumps(generated["carousel_slides"], ensure_ascii=False, indent=2)
        )
        set_job_output(job_id, "carousel", ["carousel.json"])
        await _done_task(job_id, "carousel")

        await _run_task(job_id, "copies")
        copies_path = f"{output_dir}/copies.json"
        Path(copies_path).write_text(
            json.dumps(generated["copies"], ensure_ascii=False, indent=2)
        )
        set_job_output(job_id, "copies", ["copies.json"])
        await _done_task(job_id, "copies")

        await _run_task(job_id, "hashtags")
        hashtags_path = f"{output_dir}/hashtags.json"
        Path(hashtags_path).write_text(
            json.dumps(generated["hashtags"], ensure_ascii=False, indent=2)
        )
        set_job_output(job_id, "hashtags", ["hashtags.json"])
        await _done_task(job_id, "hashtags")

        # ── EMPAQUETAR TODO EN UN ZIP ────────────────────────────────────
        zip_path = f"{output_dir}/bundle.zip"
        _create_zip(output_dir, zip_path)
        set_job_output(job_id, "zip", ["bundle.zip"])

        set_job_done(job_id)

    except Exception as e:
        job = get_job(job_id)
        if job:
            # Marcar la tarea activa como error
            for task in job.tasks:
                if task.status == TaskStatus.running:
                    set_task_status(job_id, task.id, TaskStatus.error, str(e))
        set_job_error(job_id, str(e))
        raise


async def _run_task(job_id: str, task_id: str):
    set_task_status(job_id, task_id, TaskStatus.running)


async def _done_task(job_id: str, task_id: str):
    set_task_status(job_id, task_id, TaskStatus.done)


def _create_zip(output_dir: str, zip_path: str):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                if file == "bundle.zip":
                    continue
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, output_dir)
                zf.write(full_path, arcname)
