from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(root_path="/api")

@app.get("/internal/health")
def health_check():
    return {"status": "ok", "service": "Law Finder Minimal"}

@app.route("/{full_path:path}", methods=["GET", "POST"])
async def catch_all(request, full_path: str):
    return {"detail": "Minimal catch all", "path": full_path}
