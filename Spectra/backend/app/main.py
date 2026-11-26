from contextlib import asynccontextmanager
import joblib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router, set_engine
from app.core.config import MODEL_PATH, settings
from app.database import initialize_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    if MODEL_PATH.exists():
        try:
            engine = joblib.load(MODEL_PATH)
            set_engine(engine)
            print(f"Spectra model loaded: {MODEL_PATH}")
        except Exception as exc:
            print(f"Could not load Spectra model: {exc}")
            set_engine(None)
    else:
        print("Spectra model not found. Run `python -m scripts.train_model` from backend.")
        set_engine(None)
    yield
    set_engine(None)

app = FastAPI(title=settings.api_title, version=settings.api_version, description="Hybrid movie discovery and recommendation API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api/v1")

@app.get("/")
def root():
    return {"name": "Spectra API", "version": settings.api_version, "docs": "/docs", "health": "/api/v1/health"}
