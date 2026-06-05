-- Habilitar la extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Enums
CREATE TYPE norm_status AS ENUM ('Activa', 'Derogada', 'Parcial', 'Desconocida');
CREATE TYPE norm_type AS ENUM ('Ley', 'Decreto', 'Resolución', 'Reglamento', 'Decreto Reglamentario', 'Circular', 'Otra');

-- Tabla Principal de Normativas
CREATE TABLE legal_norm (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    numero VARCHAR(50) NOT NULL,
    tipo norm_type NOT NULL,
    titulo TEXT,
    organismo_emisor VARCHAR(255),
    fecha_promulgacion DATE,
    fecha_publicacion DATE,
    fecha_entrada_vigencia DATE,
    estado_vigencia norm_status DEFAULT 'Desconocida',
    fuente_oficial_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para búsqueda rápida
CREATE INDEX idx_legal_norm_numero ON legal_norm(numero);
CREATE INDEX idx_legal_norm_fecha ON legal_norm(fecha_promulgacion);

-- Versiones del texto completo de la norma
CREATE TABLE legal_norm_version (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    norm_id UUID REFERENCES legal_norm(id) ON DELETE CASCADE,
    texto_completo TEXT NOT NULL,
    hash_contenido VARCHAR(64) NOT NULL,
    fecha_version TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(norm_id, hash_contenido)
);

-- Artículos individuales (para vectorización y búsqueda granular)
CREATE TABLE legal_article (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    norm_id UUID REFERENCES legal_norm(id) ON DELETE CASCADE,
    numero_articulo VARCHAR(50),
    titulo_seccion TEXT, -- Capítulo, Título, etc.
    texto_limpio TEXT NOT NULL,
    embedding vector(1536), -- Tamaño del vector (e.g. OpenAI text-embedding-3-small)
    estado_vigencia norm_status DEFAULT 'Activa',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índice para búsqueda por full text (PostgreSQL FTS)
ALTER TABLE legal_article ADD COLUMN fts tsvector GENERATED ALWAYS AS (to_tsvector('spanish', texto_limpio)) STORED;
CREATE INDEX idx_legal_article_fts ON legal_article USING GIN(fts);

-- Índice para búsqueda vectorial (HNSW o IVFFlat)
CREATE INDEX idx_legal_article_embedding ON legal_article USING hnsw (embedding vector_cosine_ops);

-- Referencias Cruzadas
CREATE TABLE legal_reference (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_norm_id UUID REFERENCES legal_norm(id) ON DELETE CASCADE,
    target_norm_id UUID REFERENCES legal_norm(id) ON DELETE CASCADE,
    tipo_relacion VARCHAR(100), -- ej: 'Deroga', 'Modifica', 'Reglamenta'
    descripcion TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Auditoría y Tareas de Scraping
CREATE TABLE scraping_job (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, success, error
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    items_processed INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE scraping_job_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES scraping_job(id) ON DELETE CASCADE,
    log_level VARCHAR(20) DEFAULT 'INFO',
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trazabilidad de consultas y respuestas (RAG)
CREATE TABLE user_query (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text TEXT NOT NULL,
    user_id UUID, -- Opcional, si hay auth
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE answer_trace (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID REFERENCES user_query(id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    prompt_tokens INT,
    completion_tokens INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE answer_article_reference (
    answer_id UUID REFERENCES answer_trace(id) ON DELETE CASCADE,
    article_id UUID REFERENCES legal_article(id) ON DELETE CASCADE,
    PRIMARY KEY (answer_id, article_id)
);
