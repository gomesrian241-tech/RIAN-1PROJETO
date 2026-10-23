-- PN-03: faltas nao justificadas em >=3 encontros consecutivos da mesma oficina.
-- Falta justificada, presenca ou ausencia de registro interrompem a sequencia.
-- Lacunas documentais conhecidas impedem concluir uma sequencia que as atravesse.
WITH parametros AS (SELECT DATE '2025-07-01' inicio, DATE '2025-10-01' fim_exclusivo),
calendario AS (
 SELECT e.*,ROW_NUMBER() OVER(PARTITION BY e.id_oficina ORDER BY e.data_encontro) AS pos
 FROM encontro e CROSS JOIN parametros p
 WHERE e.data_encontro>=p.inicio AND e.data_encontro<p.fim_exclusivo
), faltas AS (
 SELECT f.id_participante,f.id_oficina,f.data_encontro,
 c.pos-ROW_NUMBER() OVER(PARTITION BY f.id_participante,f.id_oficina ORDER BY f.data_encontro) AS grupo
 FROM frequencia f JOIN calendario c USING(id_oficina,data_encontro)
 WHERE f.presenca='falta'
), sequencias AS (
 SELECT id_participante,id_oficina,MIN(data_encontro) AS primeira_falta,
 MAX(data_encontro) AS ultima_falta,COUNT(*)::integer AS encontros_consecutivos
 FROM faltas GROUP BY id_participante,id_oficina,grupo HAVING COUNT(*)>=3
)
SELECT s.* FROM sequencias s
WHERE NOT EXISTS(SELECT 1 FROM lacuna_frequencia l WHERE l.id_oficina=s.id_oficina
 AND l.inicio<=s.ultima_falta AND l.fim>=s.primeira_falta)
ORDER BY s.id_participante,s.id_oficina,s.primeira_falta;
