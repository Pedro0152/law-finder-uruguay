import sys
import os

# Set environment keys for local test
# os.environ["OPENAI_API_KEY"] = "sk-proj-..."
os.environ["SUPABASE_URL"] = "https://fwyqvyxwzkklhcpzkhyn.supabase.co"
os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ3eXF2eXh3emtrbGhjcHpraHluIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA2MDgwNTgsImV4cCI6MjA5NjE4NDA1OH0.M11Vqxk8erkVnKErXAMQlf0f3Aw5crfrS884YPDYEoM"

# Add frontend/api to path to import LegalRAG
sys.path.append(os.path.abspath('frontend/api'))
from index import LegalRAG

def test_rag():
    rag = LegalRAG()
    
    queries = [
        "¿Cuál era el artículo 25 de la Constitución de 1830?",
        "¿Qué establece el artículo 7 sobre los derechos de los habitantes en la constitución vigente?",
        "¿Cuáles son los requisitos para ser senador?"
    ]
    
    for q in queries:
        print(f"\n{'='*50}\nPREGUNTA: {q}\n{'='*50}")
        try:
            res = rag.chat_completion(q)
            print(res["answer"])
            print("\nFUENTES USADAS:")
            for s in res["sources"]:
                print(f" - {s.get('version')} | Art. {s.get('articulo')} | Vigencia: {s.get('estado_vigencia')}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_rag()
