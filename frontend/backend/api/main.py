from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import os
from .nlp.rag_pipeline import LegalRAG

app = FastAPI(
    title="Law Finder API",
    description="API interna para Law Finder Uruguay",
    version="1.0.0",
    root_path="/api"
)

rag_service = LegalRAG()

class SearchQuery(BaseModel):
    query: str
    limit: int = 5

class ChatQuery(BaseModel):
    query: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]

@app.get("/internal/health")
def health_check():
    return {"status": "ok", "service": "Law Finder Backend"}

@app.post("/internal/search")
def hybrid_search(req: SearchQuery):
    """
    Realiza una búsqueda híbrida (FTS + Vectorial) y devuelve artículos relevantes.
    """
    try:
        results = rag_service.search(req.query, req.limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/internal/chat", response_model=ChatResponse)
def chat_legal(req: ChatQuery):
    """
    Procesa una pregunta en lenguaje natural y genera una respuesta usando RAG.
    """
    try:
        response = rag_service.chat_completion(req.query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/internal/scrape/trigger")
def trigger_scraping():
    """Endpoint para forzar scraping (Llamaría a Celery/Redis en prod)"""
    # En un entorno serverless simulamos la activación o despachamos un background task
    try:
        from .scraper.impo_scraper import ImpoScraper
        import threading
        
        def run_scraper_bg():
            try:
                scraper = ImpoScraper()
                scraper.scrape_latest()
            except Exception as e:
                print(f"Scraper error: {e}")
                
        threading.Thread(target=run_scraper_bg).start()
        return {"status": "Scraping task queued in background"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/internal/norms/recent")
def get_recent_norms():
    """Devuelve las últimas normas ingresadas en la base de datos."""
    try:
        res = rag_service.supabase.table("legal_norm")\
            .select("id, numero, tipo, titulo, fecha_promulgacion, estado_vigencia")\
            .order("created_at", desc=True)\
            .limit(6)\
            .execute()
        return {"results": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
