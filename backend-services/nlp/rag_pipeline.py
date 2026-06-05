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

    def search(self, query: str, limit: int = 5):
        """
        Realiza búsqueda híbrida invocando a una función RPC de Supabase.
        La función RPC internamente hará:
        - Búsqueda Vectorial (pgvector)
        - Búsqueda Full Text
        - Fusión de resultados (RRF)
        """
        query_embedding = self.generate_embedding(query)
        
        try:
            # Asumimos que creamos una función 'hybrid_search' en Postgres
            res = self.supabase.rpc(
                'hybrid_search', 
                {'query_text': query, 'query_embedding': query_embedding, 'match_count': limit}
            ).execute()
            
            return res.data
        except Exception as e:
            print(f"Error en búsqueda híbrida: {e}")
            # Retorno Mock para que el frontend no falle sin DB real
            return [
                {
                    "id": "uuid-mock-1",
                    "norma": "Ley 19.889",
                    "articulo": "Art. 1",
                    "texto": "Se aprueba la Ley de Urgente Consideración...",
                    "estado_vigencia": "Activa"
                }
            ]

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
                f"--- NORMA: {doc['norma']} | ARTÍCULO: {doc['articulo']} | VIGENCIA: {doc['estado_vigencia']} ---\n{doc['texto']}\n"
            )
        
        context_text = "\n".join(context_parts)
        
        # 3. Prompting
        system_prompt = (
            "Actúa como un asistente jurídico experto en normativa de Uruguay. "
            "Responde a la pregunta del usuario utilizando ÚNICAMENTE la normativa provista en el contexto. "
            "Si la respuesta no se encuentra en el contexto, indica claramente que no tienes información suficiente basada en la normativa oficial. "
            "Debes citar la norma y el artículo correspondiente en tu respuesta para asegurar la trazabilidad. "
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
