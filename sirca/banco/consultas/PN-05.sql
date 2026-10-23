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
