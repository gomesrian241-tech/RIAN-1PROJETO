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
