import requests
from bs4 import BeautifulSoup
import psycopg2
import psycopg2.extras
import os
import json
import time

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DB_URL = "postgres://postgres.fwyqvyxwzkklhcpzkhyn:ne%2361OPoB*irkQpGFRmb@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"

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
    
    for attempt in range(3):
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            res_json = response.json()
            embeddings = [None] * len(texts)
            for item in res_json['data']:
                embeddings[item['index']] = item['embedding']
            return embeddings
        except Exception as e:
            print(f"Error fetching embeddings (attempt {attempt+1}): {e}")
            time.sleep(2)
    return [None] * len(texts)

def extract_law(numero):
    url = f'https://parlamento.gub.uy/documentosyleyes/leyes/ley/{numero}'
    try:
        r1 = requests.get(url, timeout=10)
        if r1.status_code != 200:
            print(f"Error {r1.status_code} para Ley {numero}")
            return None
            
        s1 = BeautifulSoup(r1.text, 'html.parser')
        iframe = s1.find('iframe', id='documento')
        if not iframe:
            print(f"No se encontró iframe para Ley {numero}")
            return None
            
        r2 = requests.get(iframe['src'], timeout=10)
        r2.encoding = 'utf-8'
        s2 = BeautifulSoup(r2.text, 'html.parser')
        
        ley_num = f"Ley Nº {numero}"
        titulo = ''
        for h2 in s2.find_all('h2'):
            if 'Ley N' not in h2.text:
                titulo += h2.text.strip() + ' '
        titulo = titulo.strip().replace('\n', ' ')
        
        fecha_pub = ''
        for h5 in s2.find_all('h5'):
            if 'Publicada' in h5.text:
                fecha_pub = h5.text.strip()

        articulos = []
        for p in s2.find_all('p'):
            text = p.text.strip()
            if not text:
                continue
            # Ignorar firmas
            if 'Sala de Sesiones' in text or 'Cúmplase' in text or 'Montevideo' in text:
                break
                
            if text.lower().startswith('artículo') or text.lower().startswith('articulo'):
                # Extract number if possible, or just the whole text
                articulos.append({"texto": text})
            elif len(articulos) > 0:
                articulos[-1]["texto"] += '\n' + text
                
        # Si no encontró artículos con la palabra "Artículo", agrupamos todo como Artículo Único
        if len(articulos) == 0:
            content = ''
            for p in s2.find_all('p'):
                text = p.text.strip()
                if not text: continue
                if 'Sala de Sesiones' in text or 'Cúmplase' in text: break
                content += text + '\n'
            if content.strip():
                articulos.append({"texto": content.strip()})
                
        # Limpiar articulos
        final_arts = []
        for i, a in enumerate(articulos):
            t = a["texto"].strip()
            if t:
                final_arts.append({
                    "articulo": f"Artículo {i+1}" if len(articulos) > 1 else "Artículo Único",
                    "texto": t
                })
                
        return {
            "numero": str(numero),
            "titulo": titulo,
            "fecha_pub": fecha_pub,
            "articulos": final_arts
        }
        
    except Exception as e:
        print(f"Excepción al extraer Ley {numero}: {e}")
        return None

def ingest_leyes(start_num, end_num):
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor()
    
    print(f"Iniciando ingesta desde {start_num} hasta {end_num}")
    
    for numero in range(start_num, end_num - 1, -1):
        print(f"Procesando Ley {numero}...")
        
        # Check if exists
        cur.execute("SELECT id FROM legal_versions WHERE version_nombre = %s;", (f"ley_{numero}",))
        if cur.fetchone():
            print(f"  -> Ley {numero} ya existe. Omitiendo.")
            continue
            
        data = extract_law(numero)
        if not data or not data["articulos"]:
            print(f"  -> No se pudieron extraer datos para Ley {numero}")
            continue
            
        print(f"  -> Extraídos {len(data['articulos'])} artículos. Obteniendo embeddings...")
        
        try:
            # 1. Insert Document
            cur.execute(
                """
                INSERT INTO legal_documents (pais, tipo_documento, titulo_oficial, numero_norma, organismo_emisor, estado_vigencia)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
                """,
                ("Uruguay", "Ley", f"Ley {numero} - {data['titulo']}", str(numero), "Poder Legislativo", "Vigente")
            )
            document_id = cur.fetchone()[0]
            
            # 1.5. Insert Version
            cur.execute(
                """
                INSERT INTO legal_versions (document_id, version_nombre, fecha_promulgacion, fecha_publicacion, estado_vigencia, fuente_oficial)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
                """,
                (document_id, f"ley_{numero}", None, None, "Vigente", f"https://parlamento.gub.uy/documentosyleyes/leyes/ley/{numero}")
            )
            version_id = cur.fetchone()[0]
            
            # 2. Batch Insert Articles
            article_data = [(version_id, "Ley", art["articulo"], art["texto"], True) for art in data["articulos"]]
            art_ids_rows = psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO legal_articles (version_id, jerarquia, articulo, texto, vigente)
                VALUES %s RETURNING id;
                """,
                article_data,
                fetch=True
            )
            art_ids = [row[0] for row in art_ids_rows]
            
            # 3. Batch Embeddings
            embed_texts = [f"Ley {numero} - {data['titulo']}\n{art['articulo']}: {art['texto']}" for art in data["articulos"]]
            
            # OpenAI batch
            batch_size = 100
            all_embeddings = []
            for i in range(0, len(embed_texts), batch_size):
                batch = embed_texts[i:i+batch_size]
                embeddings = get_embeddings(batch)
                all_embeddings.extend(embeddings)
                
            # 4. Insert Embeddings
            embedding_data = []
            for idx in range(len(data["articulos"])):
                if all_embeddings[idx] is not None:
                    embedding_data.append((art_ids[idx], embed_texts[idx], all_embeddings[idx]))
                    
            if embedding_data:
                psycopg2.extras.execute_values(
                    cur,
                    """
                    INSERT INTO legal_embeddings (article_id, texto_chunk, embedding)
                    VALUES %s;
                    """,
                    embedding_data
                )
            
            conn.commit()
            print(f"  -> Ley {numero} ingresada con éxito.")
            
        except Exception as e:
            conn.rollback()
            print(f"  -> Error insertando Ley {numero}: {e}")
            
        # Pequeña demora para no saturar al parlamento
        time.sleep(1)

    cur.close()
    conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        start_num = int(sys.argv[1])
        end_num = int(sys.argv[2])
    else:
        start_num = 20488
        end_num = 20485
    ingest_leyes(start_num, end_num)
