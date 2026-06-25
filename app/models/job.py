from pydantic import BaseModel
from enum import Enum
from typing import Optional
import time


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
    error = "error"


class Task(BaseModel):
    id: str
    label: str
    status: TaskStatus = TaskStatus.pending
    error: Optional[str] = None


class Job(BaseModel):
    job_id: str
    filename: str
    created_at: float = 0.0
    status: TaskStatus = TaskStatus.pending
    tasks: list[Task] = []
    outputs: dict[str, list[str]] = {}   # e.g. {"reels": [...], "copies": [...]}
    error: Optional[str] = None

    def model_post_init(self, __context):
        if self.created_at == 0.0:
            self.created_at = time.time()
        if not self.tasks:
            self.tasks = [
                Task(id="transcribe", label="Transcribiendo audio"),
                Task(id="analyze",   label="Analizando momentos clave"),
                Task(id="reels",     label="Cortando reels"),
                Task(id="covers",    label="Generando portadas"),
                Task(id="carousel",  label="Creando carrusel"),
                Task(id="copies",    label="Redactando copies"),
                Task(id="hashtags",  label="Optimizando hashtags"),
            ]
