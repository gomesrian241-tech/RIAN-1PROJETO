"""Conferencia independente do SQL, com listas/dicionarios, sem banco."""
from collections import Counter,defaultdict
from decimal import Decimal,ROUND_HALF_UP
INICIO='2025-07-01';FIM='2025-10-01'

def pn01(dados,inicio=INICIO,fim=FIM):
    return len({r['id_participante'] for r in dados['frequencia'] if inicio<=r['data_encontro']<fim and r['presenca']=='presente'})

def pn02(dados,inicio=INICIO,fim=FIM):
    rows=[]
    for o in dados['oficina']:
        records=[r for r in dados['frequencia'] if r['id_oficina']==o['id_oficina'] and inicio<=r['data_encontro']<fim]
        n=len(records);p=sum(r['presenca']=='presente' for r in records)
        taxa=str((Decimal(100*p)/n).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)) if n else None
        rows.append(dict(id_oficina=o['id_oficina'],nome=o['nome'],registros=n,presencas=p,taxa_percentual=taxa))
    return sorted(rows,key=lambda r:r['id_oficina'])

def pn03(dados,inicio=INICIO,fim=FIM):
    calendario=defaultdict(list);fr=defaultdict(dict)
    for r in dados['encontro']:
        if inicio<=r['data_encontro']<fim:calendario[r['id_oficina']].append(r['data_encontro'])
    for r in dados['frequencia']:fr[(r['id_participante'],r['id_oficina'])][r['data_encontro']]=r['presenca']
    result=[]
    for (p,o),marks in fr.items():
        run=[]
        def save():
            if len(run)<3:return
            if any(l['id_oficina']==o and l['inicio']<=run[-1] and l['fim']>=run[0] for l in dados['lacuna_frequencia']):return
            result.append(dict(id_participante=p,id_oficina=o,primeira_falta=run[0],ultima_falta=run[-1],encontros_consecutivos=len(run)))
        for date in sorted(set(calendario[o])):
            if marks.get(date)=='falta':run.append(date)
            else:save();run=[]
        save()
    return sorted(result,key=lambda r:(r['id_participante'],r['id_oficina'],r['primeira_falta']))

def pn04(dados):
    c=Counter(r['bairro'] or 'NAO INFORMADO' for r in dados['familia'] if r['situacao']=='ativo')
    return [dict(bairro=k,familias_ativas=v) for k,v in sorted(c.items())]

def pn05(dados,participante='P002'):
    oficinas={r['id_oficina']:r['nome'] for r in dados['oficina']};cols={r['id_colaborador']:r['nome'] for r in dados['colaborador']};orgaos={r['id_orgao']:r['nome'] for r in dados['orgao']};result=[]
    for r in dados['frequencia']:
        if r['id_participante']==participante:result.append(dict(id_participante=participante,data_evento=r['data_encontro'],tipo='frequencia',referencia=r['id_oficina'],atividade=oficinas[r['id_oficina']],situacao=r['presenca'],responsavel=cols[r['id_registrador']],registrado_em=r['registrado_em'],origem=r['origem']))
    for r in dados['encaminhamento']:
        if r['id_participante']==participante:result.append(dict(id_participante=participante,data_evento=r['data_encaminhamento'],tipo='encaminhamento',referencia=r['id_encaminhamento'],atividade=r['servico']+' / '+orgaos[r['id_orgao']],situacao=r['situacao'] or 'nao informado',responsavel=None,registrado_em=None,origem='legado'))
    return sorted(result,key=lambda r:(r['data_evento'],r['tipo'],r['referencia']))
