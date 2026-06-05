from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import os
from .nlp.rag_pipeline import LegalRAG

app = FastAPI(title="Law Finder Uruguay API", description="API para el RAG y búsqueda de normativa")

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
    return {"status": "Scraping task queued"}
