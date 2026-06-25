from app.models.job import Job, Task, TaskStatus
from typing import Optional


# En producción: reemplazar por Redis o una base de datos
_store: dict[str, Job] = {}


def create_job(job_id: str, filename: str) -> Job:
    job = Job(job_id=job_id, filename=filename)
    _store[job_id] = job
    return job


def get_job(job_id: str) -> Optional[Job]:
    return _store.get(job_id)


def set_task_status(job_id: str, task_id: str, status: TaskStatus, error: str = None):
    job = _store.get(job_id)
    if not job:
        return
    for task in job.tasks:
        if task.id == task_id:
            task.status = status
            if error:
                task.error = error
            break


def set_job_output(job_id: str, key: str, files: list[str]):
    job = _store.get(job_id)
    if job:
        job.outputs[key] = files


def set_job_done(job_id: str):
    job = _store.get(job_id)
    if job:
        job.status = TaskStatus.done


def set_job_error(job_id: str, error: str):
    job = _store.get(job_id)
    if job:
        job.status = TaskStatus.error
        job.error = error
