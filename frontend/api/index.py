import re
from typing import List, Dict, Optional
import hashlib
from datetime import datetime
import traceback

global_top_error = None
try:
    import requests
    from bs4 import BeautifulSoup
except Exception as e:
    global_top_error = traceback.format_exc()

class BaseScraper:
    """Clase base para scrapeadores de normativa legal uruguaya"""
    
    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url
        self.session = requests.Session()
        # Header común para no ser bloqueados fácilmente
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def fetch_html(self, url: str) -> Optional[str]:
        """Obtiene el HTML de una URL de manera segura."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            # Forzar encoding si es necesario (IMPO usa a veces iso-8859-1)
            response.encoding = response.apparent_encoding
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def clean_text(self, text: str) -> str:
        """Sanitiza el texto, removiendo espacios extra y saltos múltiples."""
        if not text:
            return ""
        # Reemplazar múltiples espacios o saltos de línea por uno solo
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def generate_hash(self, content: str) -> str:
        """Genera un hash MD5 del contenido para control de versiones y duplicados."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def parse_articles(self, full_text: str) -> List[Dict]:
        """
        Método heurístico genérico para dividir un texto legal en artículos.
        Debe ser sobreescrito si la fuente tiene una estructura HTML clara.
        """
        articles = []
        # Buscar "Artículo 1", "Art. 1", "ARTÍCULO 1º" etc.
        pattern = re.compile(r'(Artículo\s+\d+|Art\.\s*\d+|ARTÍCULO\s+\d+º?)', re.IGNORECASE)
        splits = pattern.split(full_text)
        
        # El split genera [texto_previo, "Artículo 1", "texto_art_1", "Artículo 2", "texto_art_2"...]
        # El texto previo podría ser el preámbulo o considerandos.
        preamble = splits[0].strip()
        if preamble:
            articles.append({
                "numero": "Preámbulo",
                "texto": preamble
            })
            
        for i in range(1, len(splits) - 1, 2):
            art_num = splits[i].strip()
            art_text = splits[i+1].strip()
            articles.append({
                "numero": art_num,
                "texto": art_text
            })
            
        return articles

    def scrape_latest(self):
        """Método principal a implementar por cada scraper específico."""
        raise NotImplementedError("Debe implementarse en la clase hija")



from bs4 import BeautifulSoup
import re
from datetime import datetime

class ImpoScraper(BaseScraper):
    """Scraper para la Dirección Nacional de Impresiones y Publicaciones Oficiales (IMPO)"""

    def __init__(self):
        super().__init__(
            source_name="IMPO", 
            base_url="https://www.impo.com.uy"
        )

    def extract_metadata(self, soup: BeautifulSoup) -> dict:
        """Extrae metadatos comunes del HTML de una norma en IMPO."""
        metadata = {
            "numero": None,
            "tipo": None,
            "titulo": None,
            "fecha_promulgacion": None,
            "estado_vigencia": "Desconocida"
        }
        
        # Ejemplo: Buscar el título principal (suele estar en <h1> o div específico)
        title_tag = soup.find('h1', class_=re.compile('titulo|title', re.I))
        if title_tag:
            metadata["titulo"] = self.clean_text(title_tag.text)
            
            # Inferir tipo a partir del título
            texto_titulo = metadata["titulo"].upper()
            if "LEY N" in texto_titulo:
                metadata["tipo"] = "Ley"
                match = re.search(r'N°?\s*(\d+\.?\d*)', texto_titulo)
                if match:
                    metadata["numero"] = match.group(1).replace(".", "")
            elif "DECRETO" in texto_titulo:
                metadata["tipo"] = "Decreto"
            else:
                metadata["tipo"] = "Otra"

        # Fechas (a menudo en span con clase "fecha" o texto específico)
        # Esto requiere inspeccionar el DOM real de IMPO
        fechas_text = soup.find(text=re.compile(r'Promulgación:', re.I))
        if fechas_text:
            match = re.search(r'(\d{2}/\d{2}/\d{4})', fechas_text)
            if match:
                # Convertir a formato SQL YYYY-MM-DD
                try:
                    fecha_obj = datetime.strptime(match.group(1), '%d/%m/%Y')
                    metadata["fecha_promulgacion"] = fecha_obj.strftime('%Y-%m-%d')
                except ValueError:
                    pass

        return metadata

    def scrape_norm(self, url: str) -> dict:
        """Scrapea una norma legal completa a partir de su URL específica."""
        print(f"Scrapeando {url}...")
        html = self.fetch_html(url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')
        
        # Eliminar scripts y estilos
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()

        # Extraer metadatos
        metadata = self.extract_metadata(soup)
        
        # Extraer texto principal (usualmente en un contenedor principal)
        main_content = soup.find('div', id=re.compile('Cuerpo|main', re.I))
        if not main_content:
            main_content = soup.body

        texto_completo = self.clean_text(main_content.get_text(separator='\n'))
        
        # Generar hash
        content_hash = self.generate_hash(texto_completo)

        # Parsear artículos
        articulos = self.parse_articles(texto_completo)

        return {
            "metadata": metadata,
            "texto_completo": texto_completo,
            "hash": content_hash,
            "articulos": articulos,
            "url": url
        }

    def scrape_latest(self):
        """Scrapea el índice de novedades (ej: Diario Oficial)."""
        # Endpoint de ejemplo, la URL real depende del sitio actual.
        novedades_url = f"{self.base_url}/novedades"
        html = self.fetch_html(novedades_url)
        if not html:
            return []
            
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/bases/' in href or 'normativa' in href:
                full_link = href if href.startswith('http') else f"{self.base_url}{href}"
                links.append(full_link)
                
        # Scrapear las primeras 3 normas como prueba
        results = []
        for link in set(links[:3]): 
            norm_data = self.scrape_norm(link)
            if norm_data:
                results.append(norm_data)
                
        return results

if __name__ == "__main__":
    # Test sencillo
    scraper = ImpoScraper()
    # URL de prueba (Ley de Urgente Consideración o similar)
    url_test = "https://www.impo.com.uy/bases/leyes/19889-2020" 
    resultado = scraper.scrape_norm(url_test)
    if resultado:
        print(f"Éxito extrayendo norma: {resultado['metadata']}")
        print(f"Total artículos parseados: {len(resultado['articulos'])}")


import os
import requests
from supabase import create_client, Client

class LegalRAG:
    """Clase principal para manejar la recuperación (Retrieval) y generación de respuestas."""

    def __init__(self):
        # En producción, estas variables vendrían de .env
        supabase_url = os.environ.get("SUPABASE_URL", "https://your-project.supabase.co")
        supabase_key = os.environ.get("SUPABASE_KEY", "your-anon-key")
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")

    def generate_embedding(self, text: str) -> list[float]:
        """Llama a la API de OpenAI para generar el embedding de la consulta."""
        if not self.openai_api_key:
            # Mock de embedding para desarrollo
            return [0.0] * 1536
            
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "input": text,
            "model": "text-embedding-3-small"
        }
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["data"][0]["embedding"]
        else:
            raise Exception(f"Error generando embedding: {response.text}")

    def search(self, query: str, limit: int = 10):
        """
        Realiza búsqueda híbrida/vectorial invocando a la función RPC de Supabase 'search_legal_articles'.
        """
        query_embedding = self.generate_embedding(query)
        
        try:
            res = self.supabase.rpc(
                'search_legal_articles', 
                {'query_embedding': query_embedding, 'match_threshold': 0.5, 'match_count': limit}
            ).execute()
            
            return res.data
        except Exception as e:
            print(f"Error en búsqueda vectorial: {e}")
            return []

    def chat_completion(self, query: str) -> dict:
        """
        Pipeline RAG completo:
        1. Recupera artículos relevantes.
        2. Construye el prompt con el contexto.
        3. Genera la respuesta.
        """
        # 1. Recuperación
        relevant_docs = self.search(query, limit=5)
        
        # 2. Construcción de Contexto
        context_parts = []
        for doc in relevant_docs:
            context_parts.append(
                f"--- DOCUMENTO: {doc['documento']} | VERSIÓN: {doc['version']} | JERARQUÍA: {doc['jerarquia']} | ARTÍCULO: {doc['articulo']} | VIGENCIA: {doc['estado_vigencia']} ---\n{doc['texto']}\n"
            )
        
        context_text = "\n".join(context_parts)
        
        # 3. Prompting
        system_prompt = (
            "Actúa como un asistente jurídico experto en normativa de Uruguay. "
            "Responde a la pregunta del usuario utilizando ÚNICAMENTE la normativa provista en el contexto. "
            "Presta especial atención a la 'VIGENCIA' de la norma. Si el usuario pregunta por normativa vigente, NO utilices textos marcados como 'Histórica' o 'Derogada' a menos que te pregunten específicamente por historia o constituciones anteriores. "
            "Si la respuesta no se encuentra en el contexto, indica claramente que no tienes información suficiente basada en la normativa oficial. "
            "Debes citar la norma (Documento y Versión), la jerarquía y el artículo correspondiente en tu respuesta para asegurar la trazabilidad. "
            "Diferencia claramente entre el texto legal vigente, texto histórico y reformas. "
            "Aclara siempre que tu respuesta es generada automáticamente y no reemplaza el asesoramiento profesional."
        )
        
        user_prompt = f"CONTEXTO NORMATIVO:\n{context_text}\n\nPREGUNTA DEL USUARIO:\n{query}"
        
        # Llamada al LLM (Mock o Real)
        if not self.openai_api_key:
            answer = "Esta es una respuesta simulada basada en la Ley 19.889. [Nota: Configura OPENAI_API_KEY para respuestas reales]"
        else:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
            data = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2
            }
            resp = requests.post(url, headers=headers, json=data)
            if resp.status_code == 200:
                answer = resp.json()["choices"][0]["message"]["content"]
            else:
                answer = "Error al generar la respuesta."

        return {
            "answer": answer,
            "sources": relevant_docs
        }


import os
import re
from datetime import datetime
import hashlib
from typing import List, Dict, Optional
import traceback

from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Law Finder API",
    description="API interna para Law Finder Uruguay",
    version="1.0.0",
    root_path="/api"
)

global_import_error = None
try:
    import requests
    from supabase import create_client, Client
    from bs4 import BeautifulSoup
except Exception as e:
    global_import_error = traceback.format_exc()
    print(f"Failed to import dependencies: {e}")

rag_service = None
rag_init_error = None
try:
    rag_service = LegalRAG()
except Exception as e:
    import traceback
    rag_init_error = traceback.format_exc()
    print(f"Failed to initialize LegalRAG: {e}")

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
    if global_top_error:
        return {"status": "error", "service": "Law Finder Backend", "error": f"Top import error: {global_top_error}"}
    if global_import_error:
        return {"status": "error", "service": "Law Finder Backend", "error": f"Import error: {global_import_error}"}
    if rag_init_error:
        return {"status": "error", "service": "Law Finder Backend", "error": f"Init error: {rag_init_error}"}
    return {"status": "ok", "service": "Law Finder Backend"}

from fastapi import Request
@app.route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(request: Request, full_path: str):
    return {"detail": "Catch all", "path": request.scope.get("path"), "full_path": full_path, "root_path": request.scope.get("root_path")}

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
    if global_import_error:
        raise HTTPException(status_code=500, detail=f"Import error: {global_import_error}")
    if rag_init_error:
        raise HTTPException(status_code=500, detail=f"Service initialization failed: {rag_init_error}")
    # En un entorno serverless simulamos la activación o despachamos un background task
    try:
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
