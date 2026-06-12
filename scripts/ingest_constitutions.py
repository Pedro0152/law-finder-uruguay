import os
import re
import psycopg2
import requests
from pathlib import Path
from datetime import datetime

# Supabase direct connection string
DB_URL = os.environ.get("SUPABASE_URL_DIRECT", "postgres://postgres.fwyqvyxwzkklhcpzkhyn:ne%2361OPoB*irkQpGFRmb@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

import time

def get_embedding(text: str, retries=5) -> list:
    url = "https://api.openai.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {"input": text, "model": "text-embedding-3-small"}
    
    for attempt in range(retries):
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=15)
            if resp.status_code == 200:
                return resp.json()["data"][0]["embedding"]
            else:
                print(f"OpenAI Error ({resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"Request Error: {e}")
        
        print(f"Retrying in {2**attempt} seconds...")
        time.sleep(2**attempt)
        
    raise Exception(f"Failed to get embedding after {retries} retries.")

def parse_markdown(filepath: str):
    """
    Parses the Uruguayan constitution text files.
    Returns metadata and a list of chunks (articles).
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    metadata = {
        "titulo": "",
        "promulgacion": None,
        "version": filepath.split('\\')[-1].replace('.md', ''),
        "estado": "Histórica" if "vigente" not in filepath.lower() else "Vigente"
    }
    
    # Extract basic metadata from first few lines
    for i in range(min(5, len(lines))):
        line = lines[i].strip()
        if not line: continue
        if "CONSTITUCION" in line and not metadata["titulo"]:
            metadata["titulo"] = line
        
        # Look for dates like "PROMULGADA EL 28 DE JUNIO DE 1830"
        match_year = re.search(r'18\d{2}|19\d{2}|20\d{2}', line)
        if match_year and not metadata["promulgacion"]:
            metadata["promulgacion"] = f"{match_year.group()}-01-01"

    articles = []
    
    current_section = ""
    current_chapter = ""
    current_article_num = ""
    current_article_text = []
    
    def save_article():
        if current_article_num and current_article_text:
            text = "\n".join(current_article_text).strip()
            # Clean up extra spaces
            text = re.sub(r'\s+', ' ', text)
            
            hierarchy = []
            if current_section: hierarchy.append(current_section)
            if current_chapter: hierarchy.append(current_chapter)
            hierarchy.append(current_article_num)
            
            articles.append({
                "jerarquia": " > ".join(hierarchy),
                "articulo": current_article_num,
                "texto": text
            })

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
            
        if line.startswith("SECCION"):
            current_section = line
            # Next line is usually the section title
            if i + 1 < len(lines) and lines[i+1].strip() and not lines[i+1].strip().startswith("CAPITULO") and not lines[i+1].strip().startswith("Artículo"):
                current_section += " - " + lines[i+1].strip()
                i += 1
        elif line.startswith("CAPITULO"):
            current_chapter = line
            if i + 1 < len(lines) and lines[i+1].strip() and not lines[i+1].strip().startswith("Artículo"):
                current_chapter += " - " + lines[i+1].strip()
                i += 1
        elif line.lower().startswith("artículo") or line.lower().startswith("art."):
            save_article()
            # Extract article number
            match = re.match(r'(artículo\s*\d+º?|art\.\s*\d+º?)', line, re.IGNORECASE)
            if match:
                current_article_num = match.group(1).title()
                # Text starts after the article number
                rest_of_line = line[match.end():].strip()
                if rest_of_line.startswith(".-") or rest_of_line.startswith("-") or rest_of_line.startswith("."):
                    rest_of_line = rest_of_line.lstrip(".- ").strip()
                current_article_text = [rest_of_line] if rest_of_line else []
            else:
                current_article_num = line.split('.')[0] if '.' in line else line.split(' ')[0]
                current_article_text = [line]
        else:
            if current_article_num:
                current_article_text.append(line)
        
        i += 1

    save_article()
    return metadata, articles

def ingest():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()
    
    base_dir = Path("c:/Law_Finder/law-finder-uruguay/constitucion")
    files = list(base_dir.glob("*.md"))
    
    print(f"Encontrados {len(files)} documentos.")
    
    # 1. Ensure a Main Document exists for "Constitución de la República"
    cur.execute("SELECT id FROM legal_documents WHERE titulo_oficial = 'Constitución de la República Oriental del Uruguay';")
    doc_row = cur.fetchone()
    if doc_row:
        doc_id = doc_row[0]
    else:
        cur.execute("""
            INSERT INTO legal_documents (tipo_documento, titulo_oficial, organismo_emisor) 
            VALUES ('Constitución', 'Constitución de la República Oriental del Uruguay', 'Asamblea General')
            RETURNING id;
        """)
        doc_id = cur.fetchone()[0]
    
    for file in files:
        metadata, articles = parse_markdown(str(file))
        
        # Check if version already exists to skip or delete
        cur.execute("SELECT id FROM legal_versions WHERE version_nombre = %s AND document_id = %s;", (metadata["version"], doc_id))
        existing_version = cur.fetchone()
        
        if existing_version:
            # We delete the version and recreate to ensure it completes, CASCADE will delete articles and embeddings
            cur.execute("DELETE FROM legal_versions WHERE id = %s;", (existing_version[0],))
            
        print(f"Procesando {file.name}...")
        metadata, articles = parse_markdown(str(file))
        
        # Insert Version
        cur.execute("""
            INSERT INTO legal_versions (document_id, version_nombre, fecha_promulgacion, estado_vigencia)
            VALUES (%s, %s, %s, %s) RETURNING id;
        """, (doc_id, metadata["version"], metadata["promulgacion"], metadata["estado"]))
        version_id = cur.fetchone()[0]
        
        print(f"  -> Insertando {len(articles)} artículos...")
        for art in articles:
            # Insert Article
            cur.execute("""
                INSERT INTO legal_articles (version_id, jerarquia, articulo, texto, vigente)
                VALUES (%s, %s, %s, %s, %s) RETURNING id;
            """, (version_id, art["jerarquia"], art["articulo"], art["texto"], metadata["estado"] == "Vigente"))
            art_id = cur.fetchone()[0]
            
            # Generate Embedding
            embed_text = f"Constitución de la República | {metadata['version']} | {art['jerarquia']}\n{art['texto']}"
            embedding = get_embedding(embed_text)
            
            # Insert Embedding
            cur.execute("""
                INSERT INTO legal_embeddings (article_id, texto_chunk, embedding)
                VALUES (%s, %s, %s::vector);
            """, (art_id, embed_text, embedding))
            
    cur.close()
    conn.close()
    print("Ingesta completada!")

if __name__ == "__main__":
    ingest()
