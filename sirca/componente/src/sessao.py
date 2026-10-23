"""Lancamentos de sessao em memoria. Nenhuma conexao ao banco.
Exportacao JSON e explicita; desfazer/refazer nao alteram o legado.
"""
import datetime as dt
from indice import indexar_por_chave
from estruturas import criar_pilha,criar_fila,enfileirar
from carregador import normalizar_data

def iniciar(dados):
    return {'participantes':{r['id_participante']:dict(r) for r in dados['participante']},
        'oficinas':{r['id_oficina'] for r in dados['oficina']},
        'registradores':{r['id_colaborador'] for r in dados['colaborador']},
        'frequencias':{(r['id_participante'],r['id_oficina'],r['data_encontro']):dict(r) for r in dados['frequencia']},
        'desfazer':criar_pilha(),'refazer':criar_pilha(),'fila':criar_fila()}

def validar(s,p,o,data,presenca,registrador):
    if p not in s['participantes']:raise ValueError('RF-07 participante inexistente')
    if o not in s['oficinas']:raise ValueError('RF-07 oficina inexistente')
    if presenca not in {'presente','falta','falta justificada'}:raise ValueError('RN-01 dominio invalido')
    d=normalizar_data(data);part=s['participantes'][p];des=part.get('data_desligamento')
    if (part['situacao']=='desligado' and not des) or (des and d>=normalizar_data(des)):raise ValueError('RN-04 desligamento')
    if registrador not in s['registradores']:raise ValueError('RF-10 responsavel inexistente')
    if (p,o,d.isoformat()) in s['frequencias']:raise ValueError('RN-03 frequencia repetida')
    return d.isoformat()

def lancar(s,p,o,data,presenca,registrador,agora=None):
    d=validar(s,p,o,data,presenca,registrador)
    stamp=agora or dt.datetime.now(dt.timezone.utc)
    if stamp.tzinfo is None:raise ValueError('Timestamp precisa de fuso horario')
    row=dict(id_participante=p,id_oficina=o,data_encontro=d,presenca=presenca,id_registrador=registrador,registrado_em=stamp.isoformat(),origem='sessao')
    s['frequencias'][(p,o,d)]=row;s['desfazer'].append(dict(row));s['refazer'].clear();return dict(row)

def desfazer(s):
    if not s['desfazer']:raise IndexError('Nada a desfazer nesta sessao')
    r=s['desfazer'].pop();del s['frequencias'][(r['id_participante'],r['id_oficina'],r['data_encontro'])];s['refazer'].append(r);return dict(r)

def refazer(s):
    if not s['refazer']:raise IndexError('Nada a refazer nesta sessao')
    r=s['refazer'][-1]
    validar(s,r['id_participante'],r['id_oficina'],r['data_encontro'],r['presenca'],r['id_registrador'])
    s['refazer'].pop();s['frequencias'][(r['id_participante'],r['id_oficina'],r['data_encontro'])]=dict(r);s['desfazer'].append(r);return dict(r)

def entrar_fila(s,codigo,prioridade):
    if codigo not in s['participantes']:raise ValueError('Participante inexistente')
    enfileirar(s['fila'],codigo,prioridade)
