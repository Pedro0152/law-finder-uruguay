import os
import re
import glob
import requests
import psycopg2
import psycopg2.extras
from PyPDF2 import PdfReader

# Credenciales y Configuración
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DB_URL = "postgres://postgres.fwyqvyxwzkklhcpzkhyn:ne%2361OPoB*irkQpGFRmb@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"
PDF_DIR = r"C:\Users\kresh\.gemini\antigravity\brain\d8fbd448-a277-49bd-9c71-59ec0eec8f95"

def get_embeddings(texts):
    if not texts:
        return []
    url = "https://api.openai.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "input": texts,
        "model": "text-embedding-3-small"
    }
    
    return []
    
    # for attempt in range(3):
    #     try:
    #         response = requests.post(url, headers=headers, json=data, timeout=30)
    #         response.raise_for_status()
    #         res_json = response.json()
    #         embeddings = [None] * len(texts)
    #         for item in res_json.get("data", []):
    #             embeddings[item["index"]] = item["embedding"]
    #         return embeddings
    #     except Exception as e:
    #         print(f"  [ERROR] Fallo al obtener embeddings (intento {attempt+1}/3): {e}")
    # return []

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    except Exception as e:
        print(f"  [ERROR] al leer {pdf_path}: {e}")
    return text

def parse_articles(full_text):
    # Separar el texto por la palabra "Artículo X." o "Artículo X-" o similares
    # Utilizamos una expresión regular
    pattern = re.compile(r'(Artículo\s+\d+[\.\-\º]*)', re.IGNORECASE)
    parts = pattern.split(full_text)
    
    articles = []
    # parts[0] contiene texto antes del primer artículo (preámbulo, índice, etc.)
    # parts[1] contiene "Artículo X."
    # parts[2] contiene el contenido del artículo
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            art_num = parts[i].strip()
            art_text = parts[i+1].strip()
            # Limpiar saltos de línea innecesarios
            art_text = re.sub(r'\n+', '\n', art_text)
            
            content = f"{art_num} {art_text}"
            
            # Limitar tamaño si es excesivo para evitar fallos de API
            if len(content) > 30000:
                content = content[:30000]
                
            articles.append(content)
            
    # Si no encontró artículos con ese formato, probar a guardar párrafos grandes (ej. Diario Oficial)
    if not articles:
        print("    [!] No se encontraron 'Artículos', dividiendo por párrafos dobles...")
        paragraphs = re.split(r'\n\s*\n', full_text)
        current_chunk = ""
        for p in paragraphs:
            p = p.strip()
            if not p: continue
            if len(current_chunk) + len(p) > 2000:
                if current_chunk:
                    articles.append(current_chunk)
                current_chunk = p
            else:
                current_chunk += "\n\n" + p
        if current_chunk:
            articles.append(current_chunk)
            
    return articles

def process_pdfs():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    pdf_files = glob.glob(os.path.join(PDF_DIR, "media__*.pdf"))
    print(f"Se encontraron {len(pdf_files)} PDFs.")
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"\nProcesando PDF: {filename}")
        
        text = extract_text_from_pdf(pdf_path)
        if not text:
            print("  -> PDF sin texto.")
            continue
            
        # Intentar deducir un nombre en base al texto o filename
        doc_title = f"Documento: {filename}"
        if "CÓDIGO PENAL" in text.upper():
            doc_title = "Código Penal"
        if "Diario Oficial" in text:
            doc_title = "Diario Oficial"
            
        print(f"  -> Título inferido: {doc_title}")
        
        # Guardar en Base de datos (Documento)
        cursor.execute('''
            INSERT INTO legal_documents (tipo_documento, numero_norma, titulo_oficial) 
            VALUES (%s, %s, %s) RETURNING id
        ''', ("PDF_Subido", "0", doc_title))
        document_id = cursor.fetchone()[0]
        
        cursor.execute('''
            INSERT INTO legal_versions (document_id, version_nombre, fuente_oficial)
            VALUES (%s, %s, 'Versión de PDF importado') RETURNING id
        ''', (document_id, doc_title))
        version_id = cursor.fetchone()[0]
        
        # Parsear artículos
        articles = parse_articles(text)
        print(f"  -> Se extrajeron {len(articles)} fragmentos/artículos.")
        
        # Ingestar en lotes
        batch_size = 20
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i+batch_size]
            print(f"    -> Obteniendo embeddings para lote {i} a {i+len(batch)}...")
            embeddings = get_embeddings(batch)
            
            if not embeddings:
                print(f"    -> [WARNING] Fallo en embeddings. Usando vector cero por defecto para lote {i}.")
                embeddings = [[0.0] * 1536 for _ in batch]
            
            for j, content in enumerate(batch):
                if j >= len(embeddings):
                    break
                emb = embeddings[j]
                if not emb: continue
                
                # Para el número de artículo, tratamos de extraerlo del texto
                art_num_str = f"Párrafo {i+j+1}"
                match = re.match(r'(?i)Artículo\s+(\d+)', content)
                if match:
                    art_num_str = "Artículo " + match.group(1)
                
                cursor.execute('''
                    INSERT INTO legal_articles (version_id, articulo, texto)
                    VALUES (%s, %s, %s) RETURNING id
                ''', (version_id, art_num_str, content))
                article_id = cursor.fetchone()[0]
                
                # Inserción de embedding manual como texto literal [x, y, ...]
                emb_str = "[" + ",".join(str(e) for e in emb) + "]"
                cursor.execute('''
                    INSERT INTO legal_embeddings (article_id, texto_chunk, embedding)
                    VALUES (%s, %s, %s)
                ''', (article_id, content, emb_str))
                
            conn.commit()
        print(f"  -> {filename} insertado con éxito en la BD.")

    conn.close()

if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("ERROR: Falta la variable de entorno OPENAI_API_KEY")
    else:
        process_pdfs()
