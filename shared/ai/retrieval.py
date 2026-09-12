from sqlalchemy import text

# Filtres AVANT les deux classements ; recherche exacte sur le sous-corpus.
# RRF combine des rangs (constante 60), pas des scores incompatibles.
HYBRID_SQL = text('''
WITH eligible AS MATERIALIZED (
 SELECT p.*,d.url,d.title,d.version,d.level,d.subject FROM rag_passages p
 JOIN rag_documents d ON d.id=p.document_id AND d.tenant_id=p.tenant_id
 WHERE d.status='approved' AND d.level=:level AND d.subject=:subject
 AND d.effective_from<=CURRENT_DATE AND (d.effective_until IS NULL OR d.effective_until>=CURRENT_DATE)
 AND p.embedding_model=:model
), lexical AS (
 SELECT id,row_number() OVER(ORDER BY ts_rank_cd(search_vector,plainto_tsquery('french',:query)) DESC,id) AS rank
 FROM eligible WHERE search_vector @@ plainto_tsquery('french',:query)
 ORDER BY rank LIMIT 32
), semantic AS (
 SELECT id,row_number() OVER(ORDER BY embedding <=> CAST(:vector AS vector),id) AS rank
 FROM eligible WHERE embedding <=> CAST(:vector AS vector) <= 0.65
 ORDER BY rank LIMIT 32
), combined AS (
 SELECT COALESCE(l.id,s.id) AS id,COALESCE(1.0/(60+l.rank),0)+COALESCE(1.0/(60+s.rank),0) AS score
 FROM lexical l FULL JOIN semantic s ON s.id=l.id
)
SELECT e.id,e.document_id,e.body AS text,e.url,e.title,e.level,e.subject,e.version
FROM combined c JOIN eligible e ON e.id=c.id ORDER BY c.score DESC,e.id LIMIT :limit
''')
