-- PN-01: atendidos = participantes distintos com >= 1 presente (RN-05).
WITH parametros AS (SELECT DATE '2025-07-01' inicio, DATE '2025-10-01' fim_exclusivo)
SELECT COUNT(DISTINCT f.id_participante)::integer AS participantes_atendidos
FROM frequencia f CROSS JOIN parametros p
WHERE f.data_encontro>=p.inicio AND f.data_encontro<p.fim_exclusivo
AND f.presenca='presente';
