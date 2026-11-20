
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.scan import router as scan_router


app = FastAPI(
    title="CipherSight API",
    description="AI-Assisted Source Code Security Analyzer",
    version="0.6.0"
)


# Allow both local React development origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "project": "CipherSight",
        "status": "running",
        "message": "Welcome to CipherSight API"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


app.include_router(scan_router)
