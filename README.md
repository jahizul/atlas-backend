# Atlas Content AI — Backend

API en FastAPI que recibe un video y genera automáticamente:
reels, portadas, carrusel, copies y hashtags.

## Instalación rápida

```bash
# 1. Clonar e instalar dependencias
cd atlas-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Instalar FFmpeg en el sistema
# macOS:
brew install ffmpeg
# Ubuntu/Debian:
sudo apt install ffmpeg

# 3. Configurar API key de Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# 4. Levantar el servidor
uvicorn app.main:app --reload --port 8000
```

Documentación interactiva en: http://localhost:8000/docs

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/video/upload` | Sube el video e inicia el pipeline |
| GET | `/api/jobs/{job_id}` | Estado actual del job (polling) |
| GET | `/api/jobs/{job_id}/stream` | Estado en tiempo real (SSE) |
| GET | `/api/video/download/{job_id}` | Descarga el ZIP final |
| GET | `/health` | Health check |

## Flujo completo

```
POST /api/video/upload (multipart/form-data)
  → { job_id: "abc-123", ... }

EventSource /api/jobs/abc-123/stream
  → { tasks: [{id:"transcribe", status:"running"}, ...] }
  → { tasks: [{id:"transcribe", status:"done"}, {id:"analyze", status:"running"}, ...] }
  → event: done → cerrar conexión

GET /api/video/download/abc-123
  → atlas_abc123.zip
```

## Ejemplo de uso con fetch (frontend)

```javascript
// 1. Subir video
const form = new FormData();
form.append('file', videoFile);
const { job_id } = await fetch('/api/video/upload', {
  method: 'POST', body: form
}).then(r => r.json());

// 2. Escuchar progreso en tiempo real
const es = new EventSource(`/api/jobs/${job_id}/stream`);
es.onmessage = (e) => {
  const job = JSON.parse(e.data);
  updateUI(job.tasks);
};
es.addEventListener('done', () => {
  es.close();
  window.location.href = `/api/video/download/${job_id}`;
});
```

## Arquitectura

```
atlas-backend/
├── app/
│   ├── main.py              # FastAPI app + CORS + lifespan
│   ├── routers/
│   │   ├── video.py         # Upload y download
│   │   └── jobs.py          # Estado del job + SSE
│   ├── models/
│   │   ├── job.py           # Modelos Pydantic (Job, Task, TaskStatus)
│   │   └── store.py         # Store en memoria (→ Redis en producción)
│   └── services/
│       ├── pipeline.py      # Orquestador principal
│       ├── transcription.py # OpenAI Whisper
│       ├── video.py         # FFmpeg (reels + frames)
│       └── content.py       # Claude API (copies, hashtags, carrusel)
├── uploads/                 # Videos temporales
├── outputs/                 # Contenido generado por job
└── requirements.txt
```

## Producción

Para producción reemplaza:
- **Store en memoria** → Redis (`app/models/store.py`)
- **Archivos locales** → S3 / Cloudflare R2
- **BackgroundTasks** → Celery + Redis para jobs largos
- **Whisper local** → AssemblyAI o Deepgram (más rápido en cloud)
