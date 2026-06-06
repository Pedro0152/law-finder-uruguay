import sys
import os
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from nlp.rag_pipeline import LegalRAG

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
        from scraper.impo_scraper import ImpoScraper
        import threading
        
        def run_scraper_bg():
            try:
                scraper = ImpoScraper()
                # Modificado temporalmente para evitar 404 en /novedades y usar leyes reales fijas
                urls = [
                    "https://www.impo.com.uy/bases/leyes/19889-2020",
                    "https://www.impo.com.uy/bases/leyes/19133-2013"
                ]
                results = []
                for url in urls:
                    data = scraper.scrape_norm(url)
                    if data:
                        results.append(data)
                
                # Insertar en Supabase
                for res_data in results:
                    meta = res_data["metadata"]
                    # Insertar norma
                    db_res = rag_service.supabase.table("legal_norm").insert({
                        "numero": meta.get("numero", "0"),
                        "tipo": meta.get("tipo", "Ley"),
                        "titulo": meta.get("titulo", "Desconocido")[:255],
                        "fecha_promulgacion": meta.get("fecha_promulgacion") or "2020-01-01",
                        "estado_vigencia": meta.get("estado_vigencia", "Activa")
                    }).execute()
                    
                    if db_res.data:
                        norm_id = db_res.data[0]["id"]
                        
                        # Insertar artículos (limitado a 5 para no demorar)
                        for art in res_data["articulos"][:5]:
                            texto = f"{meta.get('tipo')} {meta.get('numero')} - Art. {art['numero']}: {art['texto']}"
                            embedding = rag_service.generate_embedding(texto)
                            rag_service.supabase.table("legal_article").insert({
                                "norm_id": norm_id,
                                "numero_articulo": art["numero"],
                                "texto_limpio": art["texto"],
                                "embedding": embedding
                            }).execute()
            except Exception as e:
                print(f"Scraper error: {e}")
                
        # NOTA: En Vercel Serverless, los hilos de fondo se congelan cuando termina la request.
        # Ejecutaremos en un hilo de fondo y retornaremos inmediatamente para evitar 504 Timeout.
        threading.Thread(target=run_scraper_bg).start()
        return {"status": "Scraping encolado. (Nota: en Vercel serverless puede interrumpirse, pero intentará avanzar)."}
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
