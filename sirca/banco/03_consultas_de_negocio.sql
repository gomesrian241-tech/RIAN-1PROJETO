-- Perguntas oficiais do Edital, secao 2; Ciclo 2: PN-01 a PN-05.

-- PN-01: atendidos = participantes distintos com >= 1 presente (RN-05).
WITH parametros AS (SELECT DATE '2025-07-01' inicio, DATE '2025-10-01' fim_exclusivo)
SELECT COUNT(DISTINCT f.id_participante)::integer AS participantes_atendidos
FROM frequencia f CROSS JOIN parametros p
WHERE f.data_encontro>=p.inicio AND f.data_encontro<p.fim_exclusivo
AND f.presenca='presente';


-- PN-02: percentual sobre os registros validos, incluindo ambas as faltas.
-- Oficinas sem registros: taxa NULL, porque nao ha denominador.
WITH parametros AS (SELECT DATE '2025-07-01' inicio, DATE '2025-10-01' fim_exclusivo)
SELECT o.id_oficina,o.nome,
 COUNT(f.id_participante)::integer AS registros,
 COUNT(f.id_participante) FILTER(WHERE f.presenca='presente')::integer AS presencas,
 ROUND(100.0*COUNT(f.id_participante) FILTER(WHERE f.presenca='presente')
 /NULLIF(COUNT(f.id_participante),0),2) AS taxa_percentual
FROM oficina o CROSS JOIN parametros p
LEFT JOIN frequencia f ON f.id_oficina=o.id_oficina
 AND f.data_encontro>=p.inicio AND f.data_encontro<p.fim_exclusivo
GROUP BY o.id_oficina,o.nome ORDER BY o.id_oficina;


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


-- PN-04: situacao cadastral na base de referencia; bairro desconhecido e explicito.
SELECT COALESCE(bairro,'NAO INFORMADO') AS bairro,COUNT(*)::integer AS familias_ativas
FROM familia WHERE situacao='ativo'
GROUP BY COALESCE(bairro,'NAO INFORMADO') ORDER BY bairro;


-- PN-05: historico integral de P002, sem restricao trimestral.
-- A doacao nao possui vinculo individual na fonte e nao e atribuida a pessoas.
WITH parametros AS (SELECT 'P002'::varchar AS participante), historico AS (
 SELECT f.id_participante,f.data_encontro AS data_evento,'frequencia' AS tipo,
 f.id_oficina AS referencia,o.nome AS atividade,f.presenca AS situacao,
 c.nome AS responsavel,f.registrado_em,f.origem
 FROM frequencia f JOIN oficina o USING(id_oficina)
 JOIN colaborador c ON c.id_colaborador=f.id_registrador
 UNION ALL
 SELECT e.id_participante,e.data_encaminhamento,'encaminhamento',e.id_encaminhamento,
 e.servico||' / '||o.nome,COALESCE(e.situacao,'nao informado'),
 NULL,NULL::timestamptz,'legado'
 FROM encaminhamento e JOIN orgao o USING(id_orgao)
)
SELECT h.* FROM historico h JOIN parametros p ON h.id_participante=p.participante
ORDER BY h.data_evento,h.tipo,h.referencia;
