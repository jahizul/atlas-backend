from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.store import get_job
import asyncio
import json

router = APIRouter()


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    """Estado actual del job (polling)."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, f"Job '{job_id}' no encontrado.")
    return job


@router.get("/{job_id}/stream")
async def stream_job_status(job_id: str):
    """
    Server-Sent Events (SSE): el cliente recibe actualizaciones en tiempo real
    sin tener que hacer polling. Se cierra automáticamente cuando el job termina.

    Uso en el frontend:
        const es = new EventSource(`/api/jobs/${jobId}/stream`);
        es.onmessage = (e) => { const job = JSON.parse(e.data); ... };
        es.addEventListener('done', () => es.close());
        es.addEventListener('error_event', () => es.close());
    """

    async def event_generator():
        while True:
            job = get_job(job_id)
            if not job:
                yield f"event: error_event\ndata: {json.dumps({'error': 'Job no encontrado'})}\n\n"
                break

            yield f"data: {job.model_dump_json()}\n\n"

            if job.status in ("done", "error"):
                yield f"event: done\ndata: {json.dumps({'job_id': job_id})}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # desactiva buffering en Nginx
        },
    )
