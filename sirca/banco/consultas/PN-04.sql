-- PN-04: situacao cadastral na base de referencia; bairro desconhecido e explicito.
SELECT COALESCE(bairro,'NAO INFORMADO') AS bairro,COUNT(*)::integer AS familias_ativas
FROM familia WHERE situacao='ativo'
GROUP BY COALESCE(bairro,'NAO INFORMADO') ORDER BY bairro;
