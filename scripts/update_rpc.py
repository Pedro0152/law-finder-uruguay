import psycopg2
conn = psycopg2.connect('postgres://postgres.fwyqvyxwzkklhcpzkhyn:ne%2361OPoB*irkQpGFRmb@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require')
conn.autocommit = True
cur = conn.cursor()
cur.execute("""
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
  ORDER BY 
    (1 - (le.embedding <=> query_embedding)) + CASE WHEN lv.estado_vigencia = 'Vigente' THEN 0.05 ELSE 0 END DESC
  LIMIT match_count;
$$;
""")
cur.close()
conn.close()
