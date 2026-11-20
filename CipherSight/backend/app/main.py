
from fastapi import FastAPI

app = FastAPI(
    title="CipherSight API",
    description="AI-Assisted Source Code Security Analyzer",
    version="0.1.0"
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
    return {
        "status": "healthy"
    }
