import psycopg2
import os

DB_URL = "postgres://postgres.fwyqvyxwzkklhcpzkhyn:ne%2361OPoB*irkQpGFRmb@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require&supa=base-pooler.x"

# We must ensure we connect without session pooling issues for DDL, but supa=base-pooler.x usually allows it.
# If it fails, we will fallback to port 5432 which is the direct port, as provided in POSTGRES_URL_NON_POOLING:
# postgres://postgres.fwyqvyxwzkklhcpzkhyn:ne%2361OPoB*irkQpGFRmb@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require

DDL_SCRIPT = """
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla principal de documentos normativos (Ej: Constitución de la República, Ley 19.889)
CREATE TABLE IF NOT EXISTS legal_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pais VARCHAR(50) DEFAULT 'Uruguay',
    tipo_documento VARCHAR(50), -- Constitución, Ley, Decreto, etc.
    titulo_oficial TEXT NOT NULL,
    numero_norma VARCHAR(50),
    organismo_emisor VARCHAR(255),
    estado_vigencia VARCHAR(50), -- Vigente, Derogada, Histórica...
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Versiones del documento (Ej: Texto original de 1967, Texto con reforma de 1989, Texto actual)
CREATE TABLE IF NOT EXISTS legal_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES legal_documents(id) ON DELETE CASCADE,
    version_nombre VARCHAR(255), -- Ej: "Texto original", "Reforma 2004"
    fecha_promulgacion DATE,
    fecha_publicacion DATE,
    estado_vigencia VARCHAR(50), 
    fuente_oficial VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Fragmentos semánticos estructurados (Títulos, Capítulos, Secciones, Artículos)
CREATE TABLE IF NOT EXISTS legal_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id UUID REFERENCES legal_versions(id) ON DELETE CASCADE,
    jerarquia TEXT, -- Ej: "Constitución > Capítulo II > Artículo 15"
    articulo VARCHAR(100), -- Ej: "Artículo 15"
    titulo TEXT, 
    texto TEXT NOT NULL,
    palabras_clave TEXT[], -- Conceptos jurídicos: Derecho penal, civil, etc.
    vigente BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Embeddings separados (puede ser 1 a 1 con article, o múltiples si hay chunks muy largos)
CREATE TABLE IF NOT EXISTS legal_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID REFERENCES legal_articles(id) ON DELETE CASCADE,
    texto_chunk TEXT NOT NULL, -- El texto exacto usado para el embedding
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Relaciones entre normas (deroga, modifica, etc.)
CREATE TABLE IF NOT EXISTS legal_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    origen_version_id UUID REFERENCES legal_versions(id), -- Norma que modifica
    destino_version_id UUID REFERENCES legal_versions(id), -- Norma modificada
    tipo_relacion VARCHAR(50), -- "modifica", "deroga", "sustituye"
    articulos_afectados TEXT[], -- ["Artículo 7", "Artículo 10"]
    descripcion TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Función de búsqueda híbrida/vectorial actualizada
CREATE OR REPLACE FUNCTION search_legal_articles (
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  article_id UUID,
  documento TEXT,
  version TEXT,
  jerarquia TEXT,
  articulo VARCHAR,
  texto TEXT,
  estado_vigencia VARCHAR,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    la.id as article_id,
    ld.titulo_oficial as documento,
    lv.version_nombre as version,
    la.jerarquia as jerarquia,
    la.articulo as articulo,
    la.texto as texto,
    lv.estado_vigencia as estado_vigencia,
    1 - (le.embedding <=> query_embedding) AS similarity
  FROM legal_embeddings le
  JOIN legal_articles la ON la.id = le.article_id
  JOIN legal_versions lv ON lv.id = la.version_id
  JOIN legal_documents ld ON ld.id = lv.document_id
  WHERE 1 - (le.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
$$;
"""

def setup_db():
    try:
        # Use direct non-pooling URL for DDL
        url = "postgres://postgres.fwyqvyxwzkklhcpzkhyn:ne%2361OPoB*irkQpGFRmb@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"
        conn = psycopg2.connect(url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(DDL_SCRIPT)
        print("Schema and RPC created successfully!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    setup_db()
