"""Indice hash por chave; colisao de chave preserva todos os registros."""
def indexar_por_chave(registros,campo_chave):
    indice={}
    for r in registros:
        if campo_chave not in r or r[campo_chave] in {None,''}:raise ValueError('Chave ausente')
        indice.setdefault(r[campo_chave],[]).append(dict(r))
    return indice

def buscar_em_lista(registros,campo,valor):
    return [dict(r) for r in registros if r.get(campo)==valor]

def buscar_no_indice(indice,valor):
    return [dict(r) for r in indice.get(valor,[])]
