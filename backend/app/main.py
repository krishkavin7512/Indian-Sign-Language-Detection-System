import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger
from app.config import get_settings
from app.database import init_db
from app.services.recognizer import get_recognizer
from app.api import recognize, jobs, vocab, health
from app.routers import teach
from app.ws.live_recognition import live_recognition_endpoint
from app.ws.teach_ws import teach_session_endpoint

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ISL Recognition System...")
    await init_db()
    logger.info("Database initialized")
    os.makedirs(settings.upload_dir, exist_ok=True)
    recognizer = get_recognizer()
    recognizer.load_models()
    logger.info("Application startup complete")
    yield
    logger.info("Shutting down...")
    from app.services.feature_extractor import get_feature_extractor
    extractor = get_feature_extractor()
    extractor.close()


app = FastAPI(
    title="ISL Recognition API",
    description="Indian Sign Language Recognition System — REST API and WebSocket",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(recognize.router, prefix="/api", tags=["Recognition"])
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(vocab.router, prefix="/api", tags=["Vocabulary"])
app.include_router(teach.router, prefix="/api", tags=["Teach"])


@app.websocket("/ws/recognize/live")
async def websocket_live(websocket: WebSocket):
    await live_recognition_endpoint(websocket)


@app.websocket("/ws/teach")
async def websocket_teach(websocket: WebSocket):
    await teach_session_endpoint(websocket)


@app.get("/")
async def root():
    return {"message": "ISL Recognition System API", "docs": "/api/docs"}
