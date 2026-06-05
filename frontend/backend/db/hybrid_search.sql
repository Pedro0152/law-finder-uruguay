CREATE OR REPLACE FUNCTION hybrid_search(
  query_text TEXT,
  query_embedding vector(1536),
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  norma TEXT,
  articulo VARCHAR,
  texto TEXT,
  estado_vigencia norm_status,
  similarity FLOAT
)
LANGUAGE sql
STABLE
AS $$
  WITH vector_results AS (
    SELECT
      la.id,
      ln.numero AS norma,
      la.numero_articulo AS articulo,
      la.texto_limpio AS texto,
      la.estado_vigencia,
      1 - (la.embedding <=> query_embedding) AS similarity
    FROM legal_article la
    JOIN legal_norm ln ON la.norm_id = ln.id
    WHERE la.embedding IS NOT NULL
    ORDER BY la.embedding <=> query_embedding
    LIMIT match_count * 2
  ),
  fts_results AS (
    SELECT
      la.id,
      ln.numero AS norma,
      la.numero_articulo AS articulo,
      la.texto_limpio AS texto,
      la.estado_vigencia,
      ts_rank(la.fts, plainto_tsquery('spanish', query_text))::FLOAT AS similarity
    FROM legal_article la
    JOIN legal_norm ln ON la.norm_id = ln.id
    WHERE la.fts @@ plainto_tsquery('spanish', query_text)
    ORDER BY similarity DESC
    LIMIT match_count * 2
  ),
  combined AS (
    SELECT * FROM vector_results
    UNION ALL
    SELECT * FROM fts_results
  )
  SELECT DISTINCT ON (c.id) c.id, c.norma, c.articulo, c.texto, c.estado_vigencia, c.similarity
  FROM combined c
  ORDER BY c.id, c.similarity DESC
  LIMIT match_count;
$$;
