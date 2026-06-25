from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.routers import video, jobs

# Crear dirs al importar para que StaticFiles no falle
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Atlas Content AI",
    description="API para generación automática de contenido desde video",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video.router, prefix="/api/video", tags=["video"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])

app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
